from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import User, get_async_session
from app.schemas import (
    RelayHealthResponse,
    RelayPairCreateRequest,
    RelayPairCreateResponse,
    RelayPairListResponse,
    RelayPairRead,
    RelayPairRefreshResponse,
    RelayPairStatusResponse,
)
from app.service import relay_pair_service
from app.users import current_active_user
from app.ws.connection_manager import relay_manager

router = APIRouter(tags=["relay-pairs"])


def _enrich_pair_read(pair) -> RelayPairRead:
    pc_online, phone_connections, _ = relay_manager.get_pair_status(pair.pair_id)
    return RelayPairRead(
        pair_id=pair.pair_id,
        device_name=pair.device_name,
        expires_at=pair.expires_at,
        revoked_at=pair.revoked_at,
        created_at=pair.created_at,
        pc_online=pc_online,
        phone_connections=phone_connections,
    )


@router.get("/health", response_model=RelayHealthResponse)
async def relay_health():
    return RelayHealthResponse(
        status="ok",
        ws_connections=relay_manager.ws_connections,
    )


@router.post("/pairs", response_model=RelayPairCreateResponse)
async def create_pair(
    payload: RelayPairCreateRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    pair, pair_token, agent_token = await relay_pair_service.create_pair(
        db, user.id, payload.device_name
    )
    return relay_pair_service.build_create_response(pair, pair_token, agent_token)


@router.get("/pairs", response_model=RelayPairListResponse)
async def list_pairs(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    pairs = await relay_pair_service.list_pairs(db, user.id)
    return RelayPairListResponse(items=[_enrich_pair_read(p) for p in pairs])


@router.get("/pairs/{pair_id}/status", response_model=RelayPairStatusResponse)
async def pair_status(
    pair_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    pair = await relay_pair_service.get_pair_by_pair_id(db, pair_id, user.id)
    if pair is None:
        raise HTTPException(status_code=404, detail="配对不存在")
    pc_online, phone_connections, last_seen = relay_manager.get_pair_status(pair_id)
    return RelayPairStatusResponse(
        pair_id=pair_id,
        pc_online=pc_online,
        phone_connections=phone_connections,
        last_agent_seen_at=last_seen,
    )


@router.post("/pairs/{pair_id}/refresh-token", response_model=RelayPairRefreshResponse)
async def refresh_pair_token(
    pair_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    pair, pair_token = await relay_pair_service.refresh_pair_token(db, user.id, pair_id)
    return relay_pair_service.build_refresh_response(pair, pair_token)


@router.delete("/pairs/{pair_id}", status_code=204)
async def revoke_pair(
    pair_id: str,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await relay_pair_service.revoke_pair(db, user.id, pair_id)
    await relay_manager.disconnect_pair(pair_id)
