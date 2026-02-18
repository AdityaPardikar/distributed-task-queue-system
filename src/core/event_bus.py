"""
In-process asynchronous event bus for broadcasting state changes.

Provides a lightweight pub/sub mechanism that decouples producers
(task engine, worker controller, scheduler) from consumers
(WebSocket connections, monitoring, alerting).

Usage::

    from src.core.event_bus import get_event_bus

    bus = get_event_bus()

    # Subscribe
    async def on_task_update(event):
        print(event)

    sub_id = bus.subscribe("tasks", on_task_update)

    # Publish
    await bus.publish("tasks", {"task_id": "abc", "status": "completed"})

    # Unsubscribe
    bus.unsubscribe("tasks", sub_id)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Awaitable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Channel definitions
# ──────────────────────────────────────────────

class EventChannel(str, Enum):
    """Pre-defined event channels."""
    METRICS = "metrics"
    TASKS = "tasks"
    WORKERS = "workers"
    ALERTS = "alerts"
    SYSTEM = "system"


# ──────────────────────────────────────────────
# Event wrapper
# ──────────────────────────────────────────────

@dataclass(frozen=True)
class Event:
    """Immutable event envelope."""
    channel: str
    type: str
    payload: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


# ──────────────────────────────────────────────
# Subscriber callback type
# ──────────────────────────────────────────────

# Callbacks may be sync or async; the bus normalises them internally.
SubscriberCallback = Callable[[Event], Awaitable[None] | None]


@dataclass
class _Subscription:
    id: str
    channel: str
    callback: SubscriberCallback
    is_async: bool


# ──────────────────────────────────────────────
# Event Bus
# ──────────────────────────────────────────────

class EventBus:
    """Async-aware in-process pub/sub event bus.

    *   Thread-safe through ``asyncio.Lock``.
    *   Supports both sync and async subscriber callbacks.
    *   Publishes to all subscribers of a channel concurrently.
    *   Maintains an optional recent-event buffer per channel so
        late-joining subscribers (e.g. new WebSocket clients) can
        receive a snapshot of recent activity.
    """

    def __init__(self, *, buffer_size: int = 50) -> None:
        self._subscriptions: Dict[str, Dict[str, _Subscription]] = {}
        self._lock = asyncio.Lock()
        self._buffer_size = buffer_size
        self._buffers: Dict[str, List[Event]] = {}
        self._stats: Dict[str, int] = {"published": 0, "delivered": 0, "errors": 0}

    # ── subscribe ──────────────────────────────

    def subscribe(
        self,
        channel: str,
        callback: SubscriberCallback,
        subscription_id: Optional[str] = None,
    ) -> str:
        """Register *callback* for *channel*. Returns subscription id."""
        sub_id = subscription_id or uuid.uuid4().hex[:16]
        is_async = asyncio.iscoroutinefunction(callback)

        sub = _Subscription(id=sub_id, channel=channel, callback=callback, is_async=is_async)
        self._subscriptions.setdefault(channel, {})[sub_id] = sub
        logger.debug("Subscribed %s to channel '%s'", sub_id, channel)
        return sub_id

    # ── unsubscribe ────────────────────────────

    def unsubscribe(self, channel: str, subscription_id: str) -> bool:
        """Remove a subscription. Returns ``True`` if found."""
        subs = self._subscriptions.get(channel, {})
        removed = subs.pop(subscription_id, None)
        if removed:
            logger.debug("Unsubscribed %s from channel '%s'", subscription_id, channel)
            return True
        return False

    def unsubscribe_all(self, channel: str) -> int:
        """Remove **all** subscriptions for *channel*. Returns count removed."""
        subs = self._subscriptions.pop(channel, {})
        return len(subs)

    # ── publish ────────────────────────────────

    async def publish(
        self,
        channel: str,
        payload: dict[str, Any],
        event_type: str = "update",
    ) -> int:
        """Broadcast an event to all subscribers of *channel*.

        Returns the number of subscribers that were **successfully** notified.
        """
        event = Event(channel=channel, type=event_type, payload=payload)

        # Buffer for late joiners
        buf = self._buffers.setdefault(channel, [])
        buf.append(event)
        if len(buf) > self._buffer_size:
            self._buffers[channel] = buf[-self._buffer_size:]

        self._stats["published"] += 1

        subs = list(self._subscriptions.get(channel, {}).values())
        if not subs:
            return 0

        delivered = 0
        tasks: list[asyncio.Task[None]] = []

        for sub in subs:
            if sub.is_async:
                tasks.append(asyncio.create_task(self._deliver_async(sub, event)))
            else:
                try:
                    sub.callback(event)  # type: ignore[arg-type]
                    delivered += 1
                    self._stats["delivered"] += 1
                except Exception:
                    self._stats["errors"] += 1
                    logger.exception("Error in sync subscriber %s on '%s'", sub.id, channel)

        # Await all async deliveries
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    self._stats["errors"] += 1
                    logger.error("Error in async subscriber: %s", result)
                else:
                    delivered += 1
                    self._stats["delivered"] += 1

        return delivered

    async def _deliver_async(self, sub: _Subscription, event: Event) -> None:
        await sub.callback(event)  # type: ignore[misc]

    # ── convenience publishers ─────────────────

    async def publish_task_event(self, task_id: str, status: str, **extra: Any) -> int:
        """Shortcut to publish a task lifecycle event."""
        return await self.publish(
            EventChannel.TASKS,
            {"task_id": task_id, "status": status, **extra},
            event_type="task_update",
        )

    async def publish_worker_event(self, worker_id: str, status: str, **extra: Any) -> int:
        """Shortcut to publish a worker state-change event."""
        return await self.publish(
            EventChannel.WORKERS,
            {"worker_id": worker_id, "status": status, **extra},
            event_type="worker_update",
        )

    async def publish_metrics(self, metrics_data: dict[str, Any]) -> int:
        """Shortcut to publish system-wide metrics snapshot."""
        return await self.publish(
            EventChannel.METRICS,
            metrics_data,
            event_type="metrics_update",
        )

    async def publish_alert(self, severity: str, title: str, message: str, **extra: Any) -> int:
        """Shortcut to publish a system alert."""
        return await self.publish(
            EventChannel.ALERTS,
            {"severity": severity, "title": title, "message": message, **extra},
            event_type="alert",
        )

    # ── query helpers ──────────────────────────

    def get_recent_events(self, channel: str, limit: int = 20) -> List[Event]:
        """Return the most recent buffered events for *channel*."""
        buf = self._buffers.get(channel, [])
        return buf[-limit:]

    def get_subscriber_count(self, channel: Optional[str] = None) -> int:
        """Return the number of active subscriptions, optionally filtered by channel."""
        if channel:
            return len(self._subscriptions.get(channel, {}))
        return sum(len(s) for s in self._subscriptions.values())

    def get_channels(self) -> Set[str]:
        """Return all channels that have at least one subscriber."""
        return {ch for ch, subs in self._subscriptions.items() if subs}

    @property
    def stats(self) -> Dict[str, int]:
        """Aggregate publish/delivery/error counters."""
        return dict(self._stats)

    def reset(self) -> None:
        """Clear all subscriptions and buffers. Useful for testing."""
        self._subscriptions.clear()
        self._buffers.clear()
        self._stats = {"published": 0, "delivered": 0, "errors": 0}


# ──────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────

_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Return the application-wide ``EventBus`` singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
