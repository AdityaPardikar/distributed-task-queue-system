"""Unit tests for the in-process event bus (src.core.event_bus)."""

import asyncio

import pytest

from src.core.event_bus import EventBus, EventChannel, Event, get_event_bus


# ─── fixtures ──────────────────────────────────

@pytest.fixture
def bus():
    """Return a fresh EventBus for each test."""
    return EventBus(buffer_size=20)


# ─── basic subscribe / publish ─────────────────

class TestSubscribePublish:
    """Core pub/sub mechanics."""

    @pytest.mark.asyncio
    async def test_subscribe_returns_id(self, bus: EventBus):
        sub_id = bus.subscribe("ch1", lambda e: None)
        assert isinstance(sub_id, str)
        assert len(sub_id) > 0

    @pytest.mark.asyncio
    async def test_sync_subscriber_receives_event(self, bus: EventBus):
        received: list[Event] = []
        bus.subscribe("tasks", lambda e: received.append(e))

        delivered = await bus.publish("tasks", {"task_id": "t1"}, event_type="created")

        assert delivered == 1
        assert len(received) == 1
        assert received[0].payload["task_id"] == "t1"
        assert received[0].type == "created"
        assert received[0].channel == "tasks"

    @pytest.mark.asyncio
    async def test_async_subscriber_receives_event(self, bus: EventBus):
        received: list[Event] = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe("metrics", handler)
        delivered = await bus.publish("metrics", {"cpu": 42.5})

        assert delivered == 1
        assert received[0].payload["cpu"] == 42.5

    @pytest.mark.asyncio
    async def test_multiple_subscribers_all_notified(self, bus: EventBus):
        counts = {"a": 0, "b": 0}

        bus.subscribe("ch", lambda _: counts.__setitem__("a", counts["a"] + 1))
        bus.subscribe("ch", lambda _: counts.__setitem__("b", counts["b"] + 1))

        await bus.publish("ch", {"x": 1})

        assert counts["a"] == 1
        assert counts["b"] == 1

    @pytest.mark.asyncio
    async def test_publish_to_channel_with_no_subscribers(self, bus: EventBus):
        delivered = await bus.publish("empty", {"nope": True})
        assert delivered == 0

    @pytest.mark.asyncio
    async def test_subscribers_only_receive_own_channel(self, bus: EventBus):
        aaa: list[Event] = []
        bbb: list[Event] = []
        bus.subscribe("aaa", lambda e: aaa.append(e))
        bus.subscribe("bbb", lambda e: bbb.append(e))

        await bus.publish("aaa", {"v": 1})

        assert len(aaa) == 1
        assert len(bbb) == 0


# ─── unsubscribe ─────────────────────────────

class TestUnsubscribe:
    @pytest.mark.asyncio
    async def test_unsubscribe_stops_delivery(self, bus: EventBus):
        count = {"n": 0}
        sub_id = bus.subscribe("ch", lambda _: count.__setitem__("n", count["n"] + 1))

        await bus.publish("ch", {"a": 1})
        assert count["n"] == 1

        result = bus.unsubscribe("ch", sub_id)
        assert result is True

        await bus.publish("ch", {"a": 2})
        assert count["n"] == 1  # no further delivery

    def test_unsubscribe_nonexistent_returns_false(self, bus: EventBus):
        assert bus.unsubscribe("ch", "no-such-id") is False

    @pytest.mark.asyncio
    async def test_unsubscribe_all(self, bus: EventBus):
        bus.subscribe("ch", lambda _: None)
        bus.subscribe("ch", lambda _: None)
        removed = bus.unsubscribe_all("ch")
        assert removed == 2
        assert bus.get_subscriber_count("ch") == 0


# ─── buffering ──────────────────────────────

class TestBuffering:
    @pytest.mark.asyncio
    async def test_recent_events_buffered(self, bus: EventBus):
        bus.subscribe("tasks", lambda _: None)  # need at least a channel reference
        for i in range(5):
            await bus.publish("tasks", {"i": i})

        recent = bus.get_recent_events("tasks", limit=3)
        assert len(recent) == 3
        assert recent[-1].payload["i"] == 4

    @pytest.mark.asyncio
    async def test_buffer_respects_max_size(self):
        bus = EventBus(buffer_size=3)
        for i in range(10):
            await bus.publish("ch", {"i": i})
        buf = bus.get_recent_events("ch", limit=100)
        assert len(buf) == 3
        assert buf[0].payload["i"] == 7

    @pytest.mark.asyncio
    async def test_empty_channel_has_no_buffer(self, bus: EventBus):
        assert bus.get_recent_events("nonexistent") == []


# ─── convenience publishers ──────────────────

class TestConveniencePublishers:
    @pytest.mark.asyncio
    async def test_publish_task_event(self, bus: EventBus):
        received: list[Event] = []
        bus.subscribe(EventChannel.TASKS, lambda e: received.append(e))

        await bus.publish_task_event("t-42", "completed", result="ok")

        assert received[0].type == "task_update"
        assert received[0].payload["task_id"] == "t-42"
        assert received[0].payload["status"] == "completed"
        assert received[0].payload["result"] == "ok"

    @pytest.mark.asyncio
    async def test_publish_worker_event(self, bus: EventBus):
        received: list[Event] = []
        bus.subscribe(EventChannel.WORKERS, lambda e: received.append(e))

        await bus.publish_worker_event("w-1", "paused")

        assert received[0].payload["worker_id"] == "w-1"
        assert received[0].payload["status"] == "paused"

    @pytest.mark.asyncio
    async def test_publish_metrics(self, bus: EventBus):
        received: list[Event] = []
        bus.subscribe(EventChannel.METRICS, lambda e: received.append(e))

        await bus.publish_metrics({"tasks_per_minute": 120})

        assert received[0].type == "metrics_update"
        assert received[0].payload["tasks_per_minute"] == 120

    @pytest.mark.asyncio
    async def test_publish_alert(self, bus: EventBus):
        received: list[Event] = []
        bus.subscribe(EventChannel.ALERTS, lambda e: received.append(e))

        await bus.publish_alert("warning", "High CPU", "CPU usage exceeded 80%")

        assert received[0].type == "alert"
        assert received[0].payload["severity"] == "warning"
        assert received[0].payload["title"] == "High CPU"


# ─── query helpers ───────────────────────────

class TestQueryHelpers:
    def test_subscriber_count(self, bus: EventBus):
        bus.subscribe("a", lambda _: None)
        bus.subscribe("a", lambda _: None)
        bus.subscribe("b", lambda _: None)

        assert bus.get_subscriber_count("a") == 2
        assert bus.get_subscriber_count("b") == 1
        assert bus.get_subscriber_count() == 3

    def test_get_channels(self, bus: EventBus):
        bus.subscribe("x", lambda _: None)
        bus.subscribe("y", lambda _: None)
        assert bus.get_channels() == {"x", "y"}

    @pytest.mark.asyncio
    async def test_stats_counters(self, bus: EventBus):
        bus.subscribe("ch", lambda _: None)
        await bus.publish("ch", {"a": 1})
        await bus.publish("ch", {"a": 2})

        s = bus.stats
        assert s["published"] == 2
        assert s["delivered"] == 2
        assert s["errors"] == 0


# ─── error handling ──────────────────────────

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_sync_subscriber_error_does_not_crash(self, bus: EventBus):
        def bad_handler(event):
            raise RuntimeError("boom")

        bus.subscribe("ch", lambda _: None)  # a good one
        bus.subscribe("ch", bad_handler)

        delivered = await bus.publish("ch", {"x": 1})
        # Good subscriber delivered, bad subscriber errored
        assert delivered == 1
        assert bus.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_async_subscriber_error_does_not_crash(self, bus: EventBus):
        async def bad_handler(event):
            raise RuntimeError("async boom")

        bus.subscribe("ch", lambda _: None)
        bus.subscribe("ch", bad_handler)

        delivered = await bus.publish("ch", {"x": 1})
        assert delivered == 1
        assert bus.stats["errors"] == 1


# ─── reset ───────────────────────────────────

class TestReset:
    @pytest.mark.asyncio
    async def test_reset_clears_everything(self, bus: EventBus):
        bus.subscribe("a", lambda _: None)
        await bus.publish("a", {"v": 1})

        bus.reset()

        assert bus.get_subscriber_count() == 0
        assert bus.get_recent_events("a") == []
        assert bus.stats["published"] == 0


# ─── singleton ───────────────────────────────

class TestSingleton:
    def test_get_event_bus_returns_same_instance(self):
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2


# ─── Event dataclass ────────────────────────

class TestEventDataclass:
    def test_event_is_immutable(self):
        e = Event(channel="ch", type="test", payload={"k": "v"})
        with pytest.raises(AttributeError):
            e.channel = "other"  # type: ignore[misc]

    def test_event_has_auto_fields(self):
        e = Event(channel="ch", type="t", payload={})
        assert e.timestamp  # non-empty ISO string
        assert e.event_id   # non-empty hex id
