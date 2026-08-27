from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState


@dataclass
class PairChannel:
    pair_id: str
    user_id: UUID
    agent_ws: WebSocket | None = None
    phone_sockets: set[WebSocket] = field(default_factory=set)
    last_agent_seen_at: datetime | None = None
    pending_message_id: UUID | None = None


class RelayConnectionManager:
    def __init__(self) -> None:
        self._channels: dict[str, PairChannel] = {}
        self._token_to_pair_id: dict[str, str] = {}
        self._lock = asyncio.Lock()

    @property
    def ws_connections(self) -> int:
        total = 0
        for channel in self._channels.values():
            if channel.agent_ws is not None:
                total += 1
            total += len(channel.phone_sockets)
        return total

    async def register_token(self, pair_token: str, pair_id: str) -> None:
        async with self._lock:
            self._token_to_pair_id[pair_token] = pair_id

    async def unregister_token(self, pair_token: str) -> None:
        async with self._lock:
            self._token_to_pair_id.pop(pair_token, None)

    async def get_or_create_channel(self, pair_id: str, user_id: UUID) -> PairChannel:
        async with self._lock:
            channel = self._channels.get(pair_id)
            if channel is None:
                channel = PairChannel(pair_id=pair_id, user_id=user_id)
                self._channels[pair_id] = channel
            return channel

    async def get_channel(self, pair_id: str) -> PairChannel | None:
        async with self._lock:
            return self._channels.get(pair_id)

    async def remove_channel_if_empty(self, pair_id: str) -> None:
        async with self._lock:
            channel = self._channels.get(pair_id)
            if channel is None:
                return
            agent_connected = (
                channel.agent_ws is not None
                and channel.agent_ws.client_state == WebSocketState.CONNECTED
            )
            phones = {
                ws
                for ws in channel.phone_sockets
                if ws.client_state == WebSocketState.CONNECTED
            }
            channel.phone_sockets = phones
            if not agent_connected and not phones:
                self._channels.pop(pair_id, None)

    def is_agent_online(self, channel: PairChannel) -> bool:
        return (
            channel.agent_ws is not None
            and channel.agent_ws.client_state == WebSocketState.CONNECTED
        )

    async def bind_agent(
        self, pair_id: str, user_id: UUID, ws: WebSocket
    ) -> PairChannel:
        channel = await self.get_or_create_channel(pair_id, user_id)
        async with self._lock:
            channel.agent_ws = ws
            channel.last_agent_seen_at = datetime.now(timezone.utc)
        return channel

    async def unbind_agent(self, pair_id: str) -> None:
        channel = await self.get_channel(pair_id)
        if channel is None:
            return
        async with self._lock:
            channel.agent_ws = None

    async def add_phone(
        self, pair_id: str, user_id: UUID, ws: WebSocket
    ) -> PairChannel:
        channel = await self.get_or_create_channel(pair_id, user_id)
        async with self._lock:
            channel.phone_sockets.add(ws)
        return channel

    async def remove_phone(self, pair_id: str, ws: WebSocket) -> None:
        channel = await self.get_channel(pair_id)
        if channel is None:
            return
        async with self._lock:
            channel.phone_sockets.discard(ws)

    async def disconnect_pair(self, pair_id: str) -> None:
        channel = await self.get_channel(pair_id)
        if channel is None:
            return
        if channel.agent_ws is not None:
            await _safe_close(channel.agent_ws)
        for phone in list(channel.phone_sockets):
            await _safe_close(phone)
        async with self._lock:
            self._channels.pop(pair_id, None)

    async def broadcast_to_phones(
        self, channel: PairChannel, payload: dict[str, Any]
    ) -> None:
        text = json.dumps(payload, ensure_ascii=False)
        dead: list[WebSocket] = []
        for phone in list(channel.phone_sockets):
            if phone.client_state != WebSocketState.CONNECTED:
                dead.append(phone)
                continue
            try:
                await phone.send_text(text)
            except Exception:
                dead.append(phone)
        for ws in dead:
            await self.remove_phone(channel.pair_id, ws)

    async def send_to_agent(self, channel: PairChannel, raw_text: str) -> bool:
        if not self.is_agent_online(channel):
            return False
        assert channel.agent_ws is not None
        try:
            await channel.agent_ws.send_text(raw_text)
            return True
        except Exception:
            await self.unbind_agent(channel.pair_id)
            return False

    def set_pending_message(self, channel: PairChannel, message_id: UUID) -> None:
        channel.pending_message_id = message_id

    def pop_pending_message(self, channel: PairChannel) -> UUID | None:
        message_id = channel.pending_message_id
        channel.pending_message_id = None
        return message_id

    def get_pair_status(self, pair_id: str) -> tuple[bool, int, datetime | None]:
        channel = self._channels.get(pair_id)
        if channel is None:
            return False, 0, None
        phones = sum(
            1
            for ws in channel.phone_sockets
            if ws.client_state == WebSocketState.CONNECTED
        )
        return self.is_agent_online(channel), phones, channel.last_agent_seen_at


relay_manager = RelayConnectionManager()


async def _safe_close(ws: WebSocket) -> None:
    if ws.client_state == WebSocketState.CONNECTED:
        try:
            await ws.close()
        except Exception:
            pass
