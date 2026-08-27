from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState


class WebSubscriberManager:
    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[WebSocket]] = {}

    @property
    def connection_count(self) -> int:
        return sum(len(sockets) for sockets in self._subscribers.values())

    async def subscribe(self, user_id: UUID, ws: WebSocket) -> None:
        self._subscribers.setdefault(user_id, set()).add(ws)

    async def unsubscribe(self, user_id: UUID, ws: WebSocket) -> None:
        sockets = self._subscribers.get(user_id)
        if sockets is None:
            return
        sockets.discard(ws)
        if not sockets:
            self._subscribers.pop(user_id, None)

    async def publish(
        self, user_id: UUID, event_type: str, message: dict[str, Any]
    ) -> None:
        sockets = list(self._subscribers.get(user_id, set()))
        if not sockets:
            return
        payload = json.dumps(
            {"type": event_type, "message": message},
            ensure_ascii=False,
            default=str,
        )
        dead: list[WebSocket] = []
        for ws in sockets:
            if ws.client_state != WebSocketState.CONNECTED:
                dead.append(ws)
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.unsubscribe(user_id, ws)


web_subscriber_manager = WebSubscriberManager()
