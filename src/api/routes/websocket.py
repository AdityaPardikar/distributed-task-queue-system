"""
WebSocket endpoints and connection manager for real-time data streaming.

Provides three WebSocket channels that the frontend hooks connect to:

*   ``/ws/metrics`` — system metrics, worker health snapshots, alerts
*   ``/ws/tasks``   — individual task lifecycle events
*   ``/ws/workers`` — worker status change events

A :class:`ConnectionManager` tracks connected clients per channel and
integrates with :mod:`src.core.event_bus` so that any part of the
application can broadcast updates to all listening clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState

from src.core.event_bus import Event, EventChannel, get_event_bus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ══════════════════════════════════════════════
# Connection Manager
# ══════════════════════════════════════════════

@dataclass
class _ClientInfo:
    """Metadata about a single connected client."""
    websocket: WebSocket
    channels: Set[str] = field(default_factory=set)
    connected_at: float = field(default_factory=time.time)
    messages_sent: int = 0


class ConnectionManager:
    """Track WebSocket clients and broadcast events to them.

    Each client can subscribe to one or more *channels*. When an event
    is published on a channel the manager fans it out to every client
    that is subscribed to that channel.

    The manager also registers itself as a subscriber on the global
    :class:`EventBus` so that any backend component can trigger
    WebSocket pushes without importing this module.
    """

    def __init__(self) -> None:
        self._clients: Dict[int, _ClientInfo] = {}
        self._channel_clients: Dict[str, Set[int]] = {}
        self._lock = asyncio.Lock()
        self._bus_sub_ids: List[str] = []
        self._stats = {
            "total_connections": 0,
            "total_messages_sent": 0,
            "total_errors": 0,
        }

    # ── lifecycle ──────────────────────────────

    async def connect(self, websocket: WebSocket, default_channels: Optional[List[str]] = None) -> int:
        """Accept a WebSocket and register the client."""
        await websocket.accept()

        client_id = id(websocket)
        channels = set(default_channels or [])

        async with self._lock:
            self._clients[client_id] = _ClientInfo(websocket=websocket, channels=channels)
            for ch in channels:
                self._channel_clients.setdefault(ch, set()).add(client_id)
            self._stats["total_connections"] += 1

        logger.info("WebSocket client %s connected (channels=%s)", client_id, channels)
        return client_id

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a client from all channels."""
        client_id = id(websocket)

        async with self._lock:
            info = self._clients.pop(client_id, None)
            if info:
                for ch in info.channels:
                    s = self._channel_clients.get(ch)
                    if s:
                        s.discard(client_id)

        logger.info("WebSocket client %s disconnected", client_id)

    async def subscribe_client(self, websocket: WebSocket, channels: List[str]) -> None:
        """Add *channels* to an existing client's subscriptions."""
        client_id = id(websocket)

        async with self._lock:
            info = self._clients.get(client_id)
            if not info:
                return
            for ch in channels:
                info.channels.add(ch)
                self._channel_clients.setdefault(ch, set()).add(client_id)

    async def unsubscribe_client(self, websocket: WebSocket, channels: List[str]) -> None:
        """Remove *channels* from an existing client's subscriptions."""
        client_id = id(websocket)

        async with self._lock:
            info = self._clients.get(client_id)
            if not info:
                return
            for ch in channels:
                info.channels.discard(ch)
                s = self._channel_clients.get(ch)
                if s:
                    s.discard(client_id)

    # ── broadcasting ───────────────────────────

    async def broadcast(self, channel: str, message: dict[str, Any]) -> int:
        """Send *message* to every client subscribed to *channel*.

        Returns the number of clients that were notified.
        """
        payload = json.dumps(message)
        client_ids: Set[int]

        async with self._lock:
            client_ids = set(self._channel_clients.get(channel, set()))

        sent = 0
        stale: list[int] = []

        for cid in client_ids:
            info = self._clients.get(cid)
            if not info:
                stale.append(cid)
                continue
            try:
                if info.websocket.client_state == WebSocketState.CONNECTED:
                    await info.websocket.send_text(payload)
                    info.messages_sent += 1
                    self._stats["total_messages_sent"] += 1
                    sent += 1
                else:
                    stale.append(cid)
            except Exception:
                self._stats["total_errors"] += 1
                stale.append(cid)
                logger.debug("Failed to send to client %s, marking stale", cid)

        # Clean up stale clients
        if stale:
            async with self._lock:
                for cid in stale:
                    info = self._clients.pop(cid, None)
                    if info:
                        for ch in info.channels:
                            s = self._channel_clients.get(ch)
                            if s:
                                s.discard(cid)

        return sent

    async def broadcast_event(self, event: Event) -> int:
        """Broadcast an :class:`Event` from the event bus."""
        message = {
            "type": event.type,
            "payload": event.payload,
            "timestamp": event.timestamp,
            "event_id": event.event_id,
        }
        return await self.broadcast(event.channel, message)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> bool:
        """Send a message to a single client. Returns ``True`` on success."""
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            self._stats["total_errors"] += 1
            return False

    # ── event-bus bridge ───────────────────────

    def register_with_event_bus(self) -> None:
        """Subscribe to all standard channels on the global event bus."""
        bus = get_event_bus()
        for channel in EventChannel:
            sub_id = bus.subscribe(channel.value, self._on_event_bus_message)
            self._bus_sub_ids.append((channel.value, sub_id))  # type: ignore[arg-type]
        logger.info("ConnectionManager registered with EventBus on %d channels", len(EventChannel))

    def unregister_from_event_bus(self) -> None:
        """Unsubscribe from the event bus."""
        bus = get_event_bus()
        for channel, sub_id in self._bus_sub_ids:
            bus.unsubscribe(channel, sub_id)
        self._bus_sub_ids.clear()

    async def _on_event_bus_message(self, event: Event) -> None:
        """Callback invoked by the event bus; fans out to WebSocket clients."""
        await self.broadcast_event(event)

    # ── introspection ──────────────────────────

    @property
    def active_connections(self) -> int:
        return len(self._clients)

    def get_channel_counts(self) -> Dict[str, int]:
        return {ch: len(clients) for ch, clients in self._channel_clients.items() if clients}

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "active_connections": self.active_connections,
            "channels": self.get_channel_counts(),
        }


# ══════════════════════════════════════════════
# Singleton
# ══════════════════════════════════════════════

_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Return the application-wide ``ConnectionManager`` singleton."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# ══════════════════════════════════════════════
# Client message handler
# ══════════════════════════════════════════════

async def _handle_client_message(
    websocket: WebSocket,
    manager: ConnectionManager,
    raw: str,
) -> None:
    """Parse and act on a message received from a client."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await manager.send_personal(websocket, {"type": "error", "message": "Invalid JSON"})
        return

    action = data.get("action")

    if action == "subscribe":
        channels = data.get("channels", [])
        if isinstance(channels, list):
            await manager.subscribe_client(websocket, channels)
            await manager.send_personal(websocket, {
                "type": "subscribed",
                "channels": channels,
            })
    elif action == "unsubscribe":
        channels = data.get("channels", [])
        if isinstance(channels, list):
            await manager.unsubscribe_client(websocket, channels)
            await manager.send_personal(websocket, {
                "type": "unsubscribed",
                "channels": channels,
            })
    elif action == "ping":
        await manager.send_personal(websocket, {"type": "pong", "ts": time.time()})
    else:
        await manager.send_personal(websocket, {
            "type": "error",
            "message": f"Unknown action: {action}",
        })


# ══════════════════════════════════════════════
# Shared connection loop helper
# ══════════════════════════════════════════════

async def _ws_loop(
    websocket: WebSocket,
    manager: ConnectionManager,
    default_channels: List[str],
) -> None:
    """Accept, listen for client messages, and clean up on disconnect."""
    await manager.connect(websocket, default_channels=default_channels)

    # Send buffered recent events so the client gets an initial snapshot
    bus = get_event_bus()
    for ch in default_channels:
        for event in bus.get_recent_events(ch, limit=10):
            await manager.send_personal(websocket, {
                "type": event.type,
                "payload": event.payload,
                "timestamp": event.timestamp,
                "event_id": event.event_id,
            })

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_client_message(websocket, manager, raw)
    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket)


# ══════════════════════════════════════════════
# WebSocket Routes
# ══════════════════════════════════════════════

@router.websocket("/ws/metrics")
async def ws_metrics(websocket: WebSocket) -> None:
    """Stream system metrics, worker health snapshots, and alerts.

    This is the primary endpoint used by the frontend
    ``useMetricsStream`` hook.
    """
    manager = get_connection_manager()
    await _ws_loop(
        websocket,
        manager,
        default_channels=[
            EventChannel.METRICS.value,
            EventChannel.WORKERS.value,
            EventChannel.ALERTS.value,
        ],
    )


@router.websocket("/ws/tasks")
async def ws_tasks(websocket: WebSocket) -> None:
    """Stream task lifecycle events (created, started, completed, failed)."""
    manager = get_connection_manager()
    await _ws_loop(
        websocket,
        manager,
        default_channels=[EventChannel.TASKS.value],
    )


@router.websocket("/ws/workers")
async def ws_workers(websocket: WebSocket) -> None:
    """Stream worker status-change events (registered, paused, drained, offline)."""
    manager = get_connection_manager()
    await _ws_loop(
        websocket,
        manager,
        default_channels=[EventChannel.WORKERS.value],
    )


# ── REST introspection endpoint ────────────────

@router.get("/api/v1/ws/status", tags=["websocket"])
async def ws_status() -> dict[str, Any]:
    """Return WebSocket connection statistics (admin / debugging)."""
    manager = get_connection_manager()
    bus = get_event_bus()
    return {
        "connections": manager.stats,
        "event_bus": {
            "subscriber_count": bus.get_subscriber_count(),
            "channels": list(bus.get_channels()),
            "stats": bus.stats,
        },
    }
