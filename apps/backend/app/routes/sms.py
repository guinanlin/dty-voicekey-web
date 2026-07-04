from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import User, get_async_session
from app.schemas import (
    SmsBatchActionResponse,
    SmsBatchDeleteRequest,
    SmsBatchStarRequest,
    SmsBatchUploadRequest,
    SmsBatchUploadResponse,
    SmsListResponse,
    SmsRead,
    SmsStarRequest,
    SmsStatsResponse,
    SmsUploadRequest,
    SmsUploadResponse,
)
from app.service import sms_service
from app.service.verification_service import check_rate_limit
from app.users import current_active_user

router = APIRouter(tags=["sms"])


@router.get("/", response_model=SmsListResponse)
async def list_sms(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
    phone: str | None = None,
    starred: bool | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    items, total = await sms_service.list_sms_messages(
        db,
        user.id,
        page,
        page_size,
        search,
        phone,
        starred,
        start_time,
        end_time,
    )
    return SmsListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[SmsRead.model_validate(item) for item in items],
    )


@router.get("/stats", response_model=SmsStatsResponse)
async def sms_stats(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    stats = await sms_service.get_sms_stats(db, user.id)
    return SmsStatsResponse(**stats)


@router.get("/phones", response_model=list[str])
async def sms_phones(
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    return await sms_service.list_distinct_phones(db, user.id)


@router.get("/{sms_id}", response_model=SmsRead)
async def get_sms(
    sms_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    sms = await sms_service.get_sms_message(db, user.id, sms_id)
    return SmsRead.model_validate(sms)


@router.post("/upload", response_model=SmsUploadResponse)
async def upload_sms(
    payload: SmsUploadRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await check_rate_limit(str(user.id), "upload", 100)
    sms = await sms_service.create_sms_message(db, user.id, payload)
    return SmsUploadResponse(id=sms.id)


@router.post("/upload/batch", response_model=SmsBatchUploadResponse)
async def batch_upload_sms(
    payload: SmsBatchUploadRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await check_rate_limit(str(user.id), "upload_batch", 10)
    success, failed, ids = await sms_service.batch_create_sms_messages(
        db, user.id, payload.messages
    )
    return SmsBatchUploadResponse(success=success, failed=failed, ids=ids)


@router.patch("/{sms_id}/star")
async def star_sms(
    sms_id: UUID,
    payload: SmsStarRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await sms_service.update_star(db, user.id, sms_id, payload.starred)
    return {"message": "更新成功"}


@router.post("/batch-star", response_model=SmsBatchActionResponse)
async def batch_star_sms(
    payload: SmsBatchStarRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    updated = await sms_service.batch_update_star(
        db, user.id, payload.ids, payload.starred
    )
    return SmsBatchActionResponse(updated=updated)


@router.delete("/{sms_id}")
async def delete_sms(
    sms_id: UUID,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    await sms_service.soft_delete_sms(db, user.id, sms_id)
    return {"message": "删除成功"}


@router.post("/batch-delete", response_model=SmsBatchActionResponse)
async def batch_delete_sms(
    payload: SmsBatchDeleteRequest,
    db: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user),
):
    deleted = await sms_service.batch_soft_delete(db, user.id, payload.ids)
    return SmsBatchActionResponse(deleted=deleted)
