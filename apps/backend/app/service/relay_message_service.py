from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.model.relay_model import RelayMessage, utcnow


async def create_relay_message(
    db: AsyncSession,
    user_id: UUID,
    pair_id: str,
    text: str,
    mode: str | None,
    after_key: str | None,
    smart_mode: bool,
    smart_action: str | None,
    client_ip: str | None,
    delivery_status: str = "pending",
    ack_ok: bool | None = None,
    ack_error: str | None = None,
) -> RelayMessage:
    message = RelayMessage(
        user_id=user_id,
        pair_id=pair_id,
        text=text,
        mode=mode,
        after_key=after_key,
        smart_mode=smart_mode,
        smart_action=smart_action,
        delivery_status=delivery_status,
        ack_ok=ack_ok,
        ack_error=ack_error,
        client_ip=client_ip,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def update_relay_message_ack(
    db: AsyncSession,
    message_id: UUID,
    delivery_status: str,
    ack_ok: bool,
    ack_error: str | None = None,
) -> None:
    result = await db.execute(select(RelayMessage).where(RelayMessage.id == message_id))
    message = result.scalar_one_or_none()
    if message is None:
        return
    message.delivery_status = delivery_status
    message.ack_ok = ack_ok
    message.ack_error = ack_error
    await db.commit()


async def list_relay_messages(
    db: AsyncSession,
    user_id: UUID,
    page: int,
    page_size: int,
    search: str | None,
    sort: str,
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[list[RelayMessage], int]:
    query = select(RelayMessage).where(
        RelayMessage.user_id == user_id, RelayMessage.deleted.is_(False)
    )

    if search:
        query = query.where(
            or_(
                RelayMessage.text.ilike(f"%{search}%"),
                RelayMessage.pair_id.ilike(f"%{search}%"),
            )
        )
    if start_time:
        query = query.where(RelayMessage.created_at >= start_time)
    if end_time:
        query = query.where(RelayMessage.created_at <= end_time)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    order = (
        RelayMessage.created_at.asc()
        if sort == "oldest"
        else RelayMessage.created_at.desc()
    )
    result = await db.execute(
        query.order_by(order).offset((page - 1) * page_size).limit(page_size)
    )
    return list(result.scalars().all()), total


async def get_relay_message(
    db: AsyncSession, user_id: UUID, message_id: UUID
) -> RelayMessage:
    result = await db.execute(
        select(RelayMessage).where(
            RelayMessage.id == message_id,
            RelayMessage.user_id == user_id,
            RelayMessage.deleted.is_(False),
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    return message


async def soft_delete_relay_message(
    db: AsyncSession, user_id: UUID, message_id: UUID
) -> None:
    message = await get_relay_message(db, user_id, message_id)
    message.deleted = True
    await db.commit()


async def get_relay_message_stats(db: AsyncSession, user_id: UUID) -> dict[str, int]:
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    base = RelayMessage.user_id == user_id, RelayMessage.deleted.is_(False)

    total = (await db.execute(select(func.count()).where(*base))).scalar_one()
    today = (
        await db.execute(
            select(func.count()).where(*base, RelayMessage.created_at >= today_start)
        )
    ).scalar_one()
    delivered = (
        await db.execute(
            select(func.count()).where(
                *base, RelayMessage.delivery_status == "delivered"
            )
        )
    ).scalar_one()
    pc_offline = (
        await db.execute(
            select(func.count()).where(
                *base, RelayMessage.delivery_status == "pc_offline"
            )
        )
    ).scalar_one()

    return {
        "total": total,
        "today": today,
        "delivered": delivered,
        "pc_offline": pc_offline,
    }
