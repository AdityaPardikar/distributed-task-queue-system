"""Unit tests for WebSocket connection manager and route helpers."""

import asyncio
import json

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.routes.websocket import (
    ConnectionManager,
    _handle_client_message,
    get_connection_manager,
)
from src.core.event_bus import Event, EventBus, EventChannel


# ─── helpers ───────────────────────────────────

def _make_ws(*, connected: bool = True) -> MagicMock:
    """Return a mock WebSocket object."""
    from starlette.websockets import WebSocketState

    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock(side_effect=Exception("not wired"))
    ws.client_state = WebSocketState.CONNECTED if connected else WebSocketState.DISCONNECTED
    return ws


# ─── fixtures ──────────────────────────────────

@pytest.fixture
def manager():
    return ConnectionManager()


# ─── connect / disconnect ──────────────────────

class TestConnectDisconnect:
    @pytest.mark.asyncio
    async def test_connect_accepts_websocket(self, manager: ConnectionManager):
        ws = _make_ws()
        cid = await manager.connect(ws, default_channels=["metrics"])

        assert isinstance(cid, int)
        ws.accept.assert_awaited_once()
        assert manager.active_connections == 1

    @pytest.mark.asyncio
    async def test_disconnect_removes_client(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["metrics"])
        assert manager.active_connections == 1

        await manager.disconnect(ws)
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_disconnect_unknown_client_is_safe(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.disconnect(ws)  # should not raise
        assert manager.active_connections == 0

    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, manager: ConnectionManager):
        w1, w2 = _make_ws(), _make_ws()
        await manager.connect(w1, default_channels=["metrics"])
        await manager.connect(w2, default_channels=["tasks"])

        assert manager.active_connections == 2
        counts = manager.get_channel_counts()
        assert counts.get("metrics") == 1
        assert counts.get("tasks") == 1


# ─── subscribe / unsubscribe ──────────────────

class TestSubscribeUnsubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_client_to_new_channel(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["metrics"])
        await manager.subscribe_client(ws, ["tasks", "alerts"])

        counts = manager.get_channel_counts()
        assert counts.get("metrics") == 1
        assert counts.get("tasks") == 1
        assert counts.get("alerts") == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_client_from_channel(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["metrics", "tasks"])
        await manager.unsubscribe_client(ws, ["tasks"])

        counts = manager.get_channel_counts()
        assert counts.get("metrics") == 1
        assert counts.get("tasks", 0) == 0

    @pytest.mark.asyncio
    async def test_subscribe_unknown_client_is_safe(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.subscribe_client(ws, ["metrics"])  # not connected
        assert manager.active_connections == 0  # no change


# ─── broadcast ─────────────────────────────────

class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_subscribed_clients(self, manager: ConnectionManager):
        ws1 = _make_ws()
        ws2 = _make_ws()
        await manager.connect(ws1, default_channels=["metrics"])
        await manager.connect(ws2, default_channels=["metrics"])

        sent = await manager.broadcast("metrics", {"type": "metrics_update", "payload": {}})

        assert sent == 2
        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_skips_unsubscribed_clients(self, manager: ConnectionManager):
        ws_m = _make_ws()
        ws_t = _make_ws()
        await manager.connect(ws_m, default_channels=["metrics"])
        await manager.connect(ws_t, default_channels=["tasks"])

        sent = await manager.broadcast("metrics", {"type": "metrics_update", "payload": {}})

        assert sent == 1
        ws_m.send_text.assert_awaited_once()
        ws_t.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_channel(self, manager: ConnectionManager):
        sent = await manager.broadcast("nonexistent", {"type": "test"})
        assert sent == 0

    @pytest.mark.asyncio
    async def test_broadcast_cleans_up_stale_clients(self, manager: ConnectionManager):
        ws = _make_ws()
        ws.send_text.side_effect = RuntimeError("connection lost")
        await manager.connect(ws, default_channels=["metrics"])

        sent = await manager.broadcast("metrics", {"type": "test"})

        assert sent == 0
        assert manager.active_connections == 0  # stale client cleaned

    @pytest.mark.asyncio
    async def test_broadcast_event_formats_correctly(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["tasks"])

        event = Event(
            channel="tasks",
            type="task_update",
            payload={"task_id": "t1", "status": "completed"},
        )

        sent = await manager.broadcast_event(event)
        assert sent == 1

        call_arg = ws.send_text.call_args[0][0]
        parsed = json.loads(call_arg)
        assert parsed["type"] == "task_update"
        assert parsed["payload"]["task_id"] == "t1"
        assert "timestamp" in parsed
        assert "event_id" in parsed


# ─── send_personal ─────────────────────────────

class TestSendPersonal:
    @pytest.mark.asyncio
    async def test_send_personal_success(self, manager: ConnectionManager):
        ws = _make_ws()
        result = await manager.send_personal(ws, {"type": "pong"})
        assert result is True
        ws.send_json.assert_awaited_once_with({"type": "pong"})

    @pytest.mark.asyncio
    async def test_send_personal_failure(self, manager: ConnectionManager):
        ws = _make_ws()
        ws.send_json.side_effect = RuntimeError("broken")
        result = await manager.send_personal(ws, {"type": "pong"})
        assert result is False


# ─── client message handling ────────────────────

class TestClientMessageHandling:
    @pytest.mark.asyncio
    async def test_subscribe_action(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=[])

        await _handle_client_message(ws, manager, json.dumps({
            "action": "subscribe",
            "channels": ["metrics", "alerts"],
        }))

        counts = manager.get_channel_counts()
        assert counts.get("metrics") == 1
        assert counts.get("alerts") == 1
        # Should send confirmation
        ws.send_json.assert_awaited()

    @pytest.mark.asyncio
    async def test_unsubscribe_action(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["metrics", "tasks"])

        await _handle_client_message(ws, manager, json.dumps({
            "action": "unsubscribe",
            "channels": ["tasks"],
        }))

        counts = manager.get_channel_counts()
        assert counts.get("tasks", 0) == 0

    @pytest.mark.asyncio
    async def test_ping_action(self, manager: ConnectionManager):
        ws = _make_ws()
        await _handle_client_message(ws, manager, json.dumps({"action": "ping"}))

        ws.send_json.assert_awaited_once()
        call_arg = ws.send_json.call_args[0][0]
        assert call_arg["type"] == "pong"
        assert "ts" in call_arg

    @pytest.mark.asyncio
    async def test_unknown_action(self, manager: ConnectionManager):
        ws = _make_ws()
        await _handle_client_message(ws, manager, json.dumps({"action": "foobar"}))

        ws.send_json.assert_awaited_once()
        call_arg = ws.send_json.call_args[0][0]
        assert call_arg["type"] == "error"

    @pytest.mark.asyncio
    async def test_invalid_json(self, manager: ConnectionManager):
        ws = _make_ws()
        await _handle_client_message(ws, manager, "not-json!!!")

        ws.send_json.assert_awaited_once()
        call_arg = ws.send_json.call_args[0][0]
        assert call_arg["type"] == "error"
        assert "Invalid JSON" in call_arg["message"]


# ─── stats / introspection ─────────────────────

class TestStats:
    @pytest.mark.asyncio
    async def test_stats_reflect_activity(self, manager: ConnectionManager):
        ws = _make_ws()
        await manager.connect(ws, default_channels=["metrics"])
        await manager.broadcast("metrics", {"type": "test"})

        s = manager.stats
        assert s["total_connections"] == 1
        assert s["total_messages_sent"] == 1
        assert s["active_connections"] == 1


# ─── event bus bridge ──────────────────────────

class TestEventBusBridge:
    def test_register_and_unregister_with_event_bus(self, manager: ConnectionManager):
        bus = EventBus()

        with patch("src.api.routes.websocket.get_event_bus", return_value=bus):
            manager.register_with_event_bus()
            # Should have one subscription per EventChannel member
            assert bus.get_subscriber_count() == len(EventChannel)

            manager.unregister_from_event_bus()
            assert bus.get_subscriber_count() == 0


# ─── singleton ───────────────────────────────

class TestSingleton:
    def test_get_connection_manager_returns_same_instance(self):
        m1 = get_connection_manager()
        m2 = get_connection_manager()
        assert m1 is m2
