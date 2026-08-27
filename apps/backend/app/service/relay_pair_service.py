from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.model.relay_model import RelayPair, utcnow
from app.schemas import (
    RelayPairCreateResponse,
    RelayPairRefreshResponse,
    RelayQrPayload,
)
from app.service.relay_token import (
    generate_agent_token,
    generate_pair_id,
    generate_pair_token,
    hash_token,
)


def _relay_agent_url() -> str:
    ws_url = settings.RELAY_PUBLIC_WS_URL.rstrip("/")
    if ws_url.endswith("/ws"):
        return ws_url[:-3] + "/agent"
    return ws_url + "/agent"


def _build_qr_payload(pair_token: str) -> RelayQrPayload:
    return RelayQrPayload(
        ws=settings.RELAY_PUBLIC_WS_URL,
        pair=pair_token,
    )


def _pair_expires_at() -> datetime:
    days = settings.RELAY_PAIR_TOKEN_TTL_DAYS
    if days <= 0:
        return datetime(2099, 12, 31, tzinfo=timezone.utc)
    return utcnow() + timedelta(days=days)


def _ensure_pair_active(pair: RelayPair) -> None:
    if pair.revoked_at is not None:
        raise HTTPException(status_code=410, detail="配对已吊销")
    if settings.RELAY_PAIR_TOKEN_TTL_DAYS > 0 and pair.expires_at <= utcnow():
        raise HTTPException(status_code=410, detail="配对已过期")


async def get_pair_by_pair_id(
    db: AsyncSession, pair_id: str, user_id: UUID | None = None
) -> RelayPair | None:
    query = select(RelayPair).where(RelayPair.pair_id == pair_id)
    if user_id is not None:
        query = query.where(RelayPair.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_pair_by_token_hash(
    db: AsyncSession, pair_token_hash: str
) -> RelayPair | None:
    result = await db.execute(
        select(RelayPair).where(RelayPair.pair_token_hash == pair_token_hash)
    )
    return result.scalar_one_or_none()


async def create_pair(
    db: AsyncSession, user_id: UUID, device_name: str | None
) -> tuple[RelayPair, str, str]:
    pair_id = generate_pair_id()
    pair_token = generate_pair_token()
    agent_token = generate_agent_token()
    expires_at = _pair_expires_at()

    pair = RelayPair(
        user_id=user_id,
        pair_id=pair_id,
        pair_token_hash=hash_token(pair_token),
        agent_token_hash=hash_token(agent_token),
        device_name=device_name,
        expires_at=expires_at,
    )
    db.add(pair)
    await db.commit()
    await db.refresh(pair)
    return pair, pair_token, agent_token


async def list_pairs(db: AsyncSession, user_id: UUID) -> list[RelayPair]:
    result = await db.execute(
        select(RelayPair)
        .where(RelayPair.user_id == user_id, RelayPair.revoked_at.is_(None))
        .order_by(RelayPair.created_at.desc())
    )
    return list(result.scalars().all())


async def refresh_pair_token(
    db: AsyncSession, user_id: UUID, pair_id: str
) -> tuple[RelayPair, str]:
    pair = await get_pair_by_pair_id(db, pair_id, user_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="配对不存在")
    _ensure_pair_active(pair)

    pair_token = generate_pair_token()
    pair.pair_token_hash = hash_token(pair_token)
    pair.expires_at = _pair_expires_at()
    pair.updated_at = utcnow()
    await db.commit()
    await db.refresh(pair)
    return pair, pair_token


async def revoke_pair(db: AsyncSession, user_id: UUID, pair_id: str) -> RelayPair:
    pair = await get_pair_by_pair_id(db, pair_id, user_id)
    if pair is None:
        raise HTTPException(status_code=404, detail="配对不存在")
    pair.revoked_at = utcnow()
    pair.updated_at = utcnow()
    await db.commit()
    await db.refresh(pair)
    return pair


def build_create_response(
    pair: RelayPair, pair_token: str, agent_token: str
) -> RelayPairCreateResponse:
    return RelayPairCreateResponse(
        pair_id=pair.pair_id,
        pair_token=pair_token,
        agent_token=agent_token,
        relay_ws_url=settings.RELAY_PUBLIC_WS_URL,
        relay_agent_url=_relay_agent_url(),
        expires_at=pair.expires_at,
        qr_payload=_build_qr_payload(pair_token),
    )


def build_refresh_response(
    pair: RelayPair, pair_token: str
) -> RelayPairRefreshResponse:
    return RelayPairRefreshResponse(
        pair_token=pair_token,
        expires_at=pair.expires_at,
        qr_payload=_build_qr_payload(pair_token),
    )
