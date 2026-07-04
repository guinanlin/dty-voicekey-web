from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import User, get_async_session
from app.schemas import (
    RelayMessageListResponse,
    RelayMessageRead,
    RelayMessageStatsResponse,
)
from app.service import relay_message_service
from app.users import current_active_user

router = APIRouter(tags=["relay-messages"])


@router.get("/messages", response_model=RelayMessageListResponse)
async def list_relay_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    sort: str = Query("newest", pattern="^(newest|oldest)$"),
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    items, total = await relay_message_service.list_relay_messages(
        db,
        user.id,
        page,
        page_size,
        search,
        sort,
        start_time,
        end_time,
    )
    return RelayMessageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[RelayMessageRead.model_validate(item) for item in items],
    )


@router.get("/messages/stats", response_model=RelayMessageStatsResponse)
async def relay_message_stats(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    stats = await relay_message_service.get_relay_message_stats(db, user.id)
    return RelayMessageStatsResponse(**stats)


@router.get("/messages/{message_id}", response_model=RelayMessageRead)
async def get_relay_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    message = await relay_message_service.get_relay_message(db, user.id, message_id)
    return RelayMessageRead.model_validate(message)


@router.delete("/messages/{message_id}", status_code=204)
async def delete_relay_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await relay_message_service.soft_delete_relay_message(db, user.id, message_id)
