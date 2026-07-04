from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session_maker
from app.model.relay_model import RelayPair, utcnow
from app.service.relay_message_service import create_relay_message, update_relay_message_ack
from app.service.relay_notify import notify_message_created, notify_message_updated_by_id
from app.service.relay_token import hash_token, verify_token
from app.service.verification_service import check_rate_limit
from app.ws.connection_manager import relay_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["relay-ws"])

MAX_FRAME_BYTES = 64 * 1024
PC_OFFLINE_ERROR = "PC 离线"


def _client_ip(ws: WebSocket) -> str | None:
    if ws.client:
        return ws.client.host
    return None


async def _load_pair_by_token(db, pair_token: str) -> RelayPair | None:
    token_hash = hash_token(pair_token)
    result = await db.execute(
        select(RelayPair).where(RelayPair.pair_token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def _load_pair_by_id_and_agent(db, pair_id: str, agent_token: str) -> RelayPair | None:
    result = await db.execute(select(RelayPair).where(RelayPair.pair_id == pair_id))
    pair = result.scalar_one_or_none()
    if pair is None:
        return None
    if not verify_token(agent_token, pair.agent_token_hash):
        return None
    return pair


def _pair_is_valid(pair: RelayPair) -> bool:
    from app.core.config import settings

    if pair.revoked_at is not None:
        return False
    if settings.RELAY_PAIR_TOKEN_TTL_DAYS > 0 and pair.expires_at <= utcnow():
        return False
    return True


async def _send_json(ws: WebSocket, payload: dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


@router.websocket("/ws")
async def phone_ws(websocket: WebSocket, pair: str = Query(...)):
    if settings.RELAY_REQUIRE_WSS and websocket.url.scheme != "wss":
        await websocket.close(code=4003, reason="WSS required")
        return

    async with async_session_maker() as db:
        relay_pair = await _load_pair_by_token(db, pair)
        if relay_pair is None:
            await websocket.close(code=4001, reason="Invalid pair token")
            return
        if not _pair_is_valid(relay_pair):
            await websocket.close(code=4001, reason="Pair expired or revoked")
            return

        pair_id = relay_pair.pair_id
        user_id = relay_pair.user_id

    await websocket.accept()
    channel = await relay_manager.add_phone(pair_id, user_id, websocket)

    if relay_manager.is_agent_online(channel):
        await _send_json(websocket, {"type": "connected"})
    else:
        await _send_json(websocket, {"type": "pc_status", "online": False})

    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw.encode()) > MAX_FRAME_BYTES:
                await _send_json(
                    websocket,
                    {"type": "ack", "ok": False, "error": "消息过大"},
                )
                continue

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await _send_json(
                    websocket,
                    {"type": "ack", "ok": False, "error": "无效 JSON"},
                )
                continue

            msg_type = payload.get("type")
            if msg_type != "transmit":
                continue

            text = payload.get("text", "")
            if not isinstance(text, str) or not text.strip():
                await _send_json(
                    websocket,
                    {"type": "ack", "ok": False, "error": "text 不能为空"},
                )
                continue

            async with async_session_maker() as db:
                try:
                    await check_rate_limit(
                        f"relay:{pair_id}",
                        "transmit",
                        settings.RELAY_TRANSMIT_RATE_LIMIT,
                    )
                except Exception:
                    await _send_json(
                        websocket,
                        {"type": "ack", "ok": False, "error": "请求过于频繁"},
                    )
                    continue

                channel = await relay_manager.get_channel(pair_id)
                if channel is None:
                    channel = await relay_manager.get_or_create_channel(pair_id, user_id)

                if not relay_manager.is_agent_online(channel):
                    offline_message = await create_relay_message(
                        db,
                        user_id=user_id,
                        pair_id=pair_id,
                        text=text,
                        mode=payload.get("mode"),
                        after_key=payload.get("after_key"),
                        smart_mode=bool(payload.get("smart_mode", False)),
                        smart_action=payload.get("smart_action"),
                        client_ip=_client_ip(websocket),
                        delivery_status="pc_offline",
                        ack_ok=False,
                        ack_error=PC_OFFLINE_ERROR,
                    )
                    await notify_message_created(offline_message)
                    await _send_json(
                        websocket,
                        {"type": "ack", "ok": False, "error": PC_OFFLINE_ERROR},
                    )
                    continue

                message = await create_relay_message(
                    db,
                    user_id=user_id,
                    pair_id=pair_id,
                    text=text,
                    mode=payload.get("mode"),
                    after_key=payload.get("after_key"),
                    smart_mode=bool(payload.get("smart_mode", False)),
                    smart_action=payload.get("smart_action"),
                    client_ip=_client_ip(websocket),
                    delivery_status="pending",
                )
                await notify_message_created(message)
                relay_manager.set_pending_message(channel, message.id)

            forwarded = await relay_manager.send_to_agent(channel, raw)
            if not forwarded:
                async with async_session_maker() as db:
                    await update_relay_message_ack(
                        db,
                        message.id,
                        "pc_offline",
                        False,
                        PC_OFFLINE_ERROR,
                    )
                await notify_message_updated_by_id(message.id)
                await _send_json(
                    websocket,
                    {"type": "ack", "ok": False, "error": PC_OFFLINE_ERROR},
                )
    except WebSocketDisconnect:
        pass
    finally:
        await relay_manager.remove_phone(pair_id, websocket)
        await relay_manager.remove_channel_if_empty(pair_id)


@router.websocket("/agent")
async def agent_ws(
    websocket: WebSocket,
    pair_id: str = Query(...),
    agent_token: str = Query(...),
):
    if settings.RELAY_REQUIRE_WSS and websocket.url.scheme != "wss":
        await websocket.close(code=4003, reason="WSS required")
        return

    async with async_session_maker() as db:
        relay_pair = await _load_pair_by_id_and_agent(db, pair_id, agent_token)
        if relay_pair is None:
            await websocket.close(code=4001, reason="Invalid agent credentials")
            return
        if not _pair_is_valid(relay_pair):
            await websocket.close(code=4001, reason="Pair expired or revoked")
            return
        user_id = relay_pair.user_id

    await websocket.accept()
    channel = await relay_manager.bind_agent(pair_id, user_id, websocket)
    await relay_manager.broadcast_to_phones(
        channel, {"type": "pc_status", "online": True}
    )
    await relay_manager.broadcast_to_phones(channel, {"type": "connected"})

    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw.encode()) > MAX_FRAME_BYTES:
                continue

            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = payload.get("type")
            if msg_type == "ack":
                pending_id = relay_manager.pop_pending_message(channel)
                if pending_id is not None:
                    async with async_session_maker() as db:
                        await update_relay_message_ack(
                            db,
                            pending_id,
                            "delivered" if payload.get("ok") else "failed",
                            bool(payload.get("ok")),
                            payload.get("error"),
                        )
                    await notify_message_updated_by_id(pending_id)
                await relay_manager.broadcast_to_phones(channel, payload)
            elif msg_type in {"connected", "pc_status"}:
                await relay_manager.broadcast_to_phones(channel, payload)
            else:
                await relay_manager.broadcast_to_phones(channel, payload)
    except WebSocketDisconnect:
        pass
    finally:
        await relay_manager.unbind_agent(pair_id)
        channel = await relay_manager.get_channel(pair_id)
        if channel is not None:
            await relay_manager.broadcast_to_phones(
                channel, {"type": "pc_status", "online": False}
            )
        await relay_manager.remove_channel_if_empty(pair_id)
