from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.sms_model import SmsMessage, utcnow
from app.schemas import SmsUploadRequest


def parse_received_at(value: str | None) -> datetime:
    if not value:
        return utcnow()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="received_at 格式无效") from exc


async def list_sms_messages(
    db: AsyncSession,
    user_id: UUID,
    page: int,
    page_size: int,
    search: str | None,
    phone: str | None,
    starred: bool | None,
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[list[SmsMessage], int]:
    query = select(SmsMessage).where(
        SmsMessage.user_id == user_id, SmsMessage.deleted.is_(False)
    )

    if search:
        query = query.where(
            or_(
                SmsMessage.content.ilike(f"%{search}%"),
                SmsMessage.phone == search,
            )
        )
    if phone:
        query = query.where(SmsMessage.phone == phone)
    if starred is not None:
        query = query.where(SmsMessage.starred.is_(starred))
    if start_time:
        query = query.where(SmsMessage.received_at >= start_time)
    if end_time:
        query = query.where(SmsMessage.received_at <= end_time)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        query.order_by(SmsMessage.received_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_sms_message(db: AsyncSession, user_id: UUID, sms_id: UUID) -> SmsMessage:
    result = await db.execute(
        select(SmsMessage).where(
            SmsMessage.id == sms_id,
            SmsMessage.user_id == user_id,
            SmsMessage.deleted.is_(False),
        )
    )
    sms = result.scalar_one_or_none()
    if sms is None:
        raise HTTPException(status_code=404, detail="短信不存在")
    return sms


async def create_sms_message(
    db: AsyncSession, user_id: UUID, payload: SmsUploadRequest
) -> SmsMessage:
    if not payload.phone.strip():
        raise HTTPException(status_code=400, detail="发送号码不能为空")
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="短信内容不能为空")
    if len(payload.content) > 10000:
        raise HTTPException(status_code=400, detail="短信内容过长")

    sms = SmsMessage(
        user_id=user_id,
        phone=payload.phone.strip(),
        content=payload.content.strip(),
        received_at=parse_received_at(payload.received_at),
    )
    db.add(sms)
    await db.commit()
    await db.refresh(sms)
    return sms


async def batch_create_sms_messages(
    db: AsyncSession, user_id: UUID, messages: list[SmsUploadRequest]
) -> tuple[int, int, list[UUID]]:
    if len(messages) > 100:
        raise HTTPException(status_code=400, detail="单次最多上传 100 条")

    ids: list[UUID] = []
    failed = 0
    for payload in messages:
        try:
            sms = SmsMessage(
                user_id=user_id,
                phone=payload.phone.strip(),
                content=payload.content.strip(),
                received_at=parse_received_at(payload.received_at),
            )
            if not sms.phone or not sms.content:
                failed += 1
                continue
            db.add(sms)
            await db.flush()
            ids.append(sms.id)
        except HTTPException:
            failed += 1

    await db.commit()
    return len(ids), failed, ids


async def update_star(
    db: AsyncSession, user_id: UUID, sms_id: UUID, starred: bool
) -> None:
    sms = await get_sms_message(db, user_id, sms_id)
    sms.starred = starred
    sms.updated_at = utcnow()
    await db.commit()


async def batch_update_star(
    db: AsyncSession, user_id: UUID, ids: list[UUID], starred: bool
) -> int:
    result = await db.execute(
        select(SmsMessage).where(
            SmsMessage.id.in_(ids),
            SmsMessage.user_id == user_id,
            SmsMessage.deleted.is_(False),
        )
    )
    messages = result.scalars().all()
    for sms in messages:
        sms.starred = starred
        sms.updated_at = utcnow()
    await db.commit()
    return len(messages)


async def soft_delete_sms(db: AsyncSession, user_id: UUID, sms_id: UUID) -> None:
    sms = await get_sms_message(db, user_id, sms_id)
    sms.deleted = True
    sms.updated_at = utcnow()
    await db.commit()


async def batch_soft_delete(db: AsyncSession, user_id: UUID, ids: list[UUID]) -> int:
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="单次最多删除 100 条")

    result = await db.execute(
        select(SmsMessage).where(
            SmsMessage.id.in_(ids),
            SmsMessage.user_id == user_id,
            SmsMessage.deleted.is_(False),
        )
    )
    messages = result.scalars().all()
    for sms in messages:
        sms.deleted = True
        sms.updated_at = utcnow()
    await db.commit()
    return len(messages)


async def list_distinct_phones(db: AsyncSession, user_id: UUID) -> list[str]:
    result = await db.execute(
        select(SmsMessage.phone)
        .where(SmsMessage.user_id == user_id, SmsMessage.deleted.is_(False))
        .distinct()
        .order_by(SmsMessage.phone)
    )
    return [row[0] for row in result.all()]


async def get_sms_stats(db: AsyncSession, user_id: UUID) -> dict[str, int]:
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    base = SmsMessage.user_id == user_id, SmsMessage.deleted.is_(False)

    total = (await db.execute(select(func.count()).where(*base))).scalar_one()

    starred = (
        await db.execute(
            select(func.count()).where(*base, SmsMessage.starred.is_(True))
        )
    ).scalar_one()

    today = (
        await db.execute(
            select(func.count()).where(*base, SmsMessage.received_at >= today_start)
        )
    ).scalar_one()

    this_week = (
        await db.execute(
            select(func.count()).where(*base, SmsMessage.received_at >= week_start)
        )
    ).scalar_one()

    this_month = (
        await db.execute(
            select(func.count()).where(*base, SmsMessage.received_at >= month_start)
        )
    ).scalar_one()

    return {
        "total": total,
        "starred": starred,
        "today": today,
        "this_week": this_week,
        "this_month": this_month,
    }
