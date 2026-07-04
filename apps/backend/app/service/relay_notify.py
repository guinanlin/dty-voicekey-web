from uuid import UUID

from sqlalchemy import select
from app.core.database import async_session_maker
from app.model.relay_model import RelayMessage
from app.schemas import RelayMessageRead
from app.ws.web_subscriber_manager import web_subscriber_manager


def _serialize_message(message: RelayMessage) -> dict:
    return RelayMessageRead.model_validate(message).model_dump(mode="json")


async def notify_message_created(message: RelayMessage) -> None:
    await web_subscriber_manager.publish(
        message.user_id,
        "message_new",
        _serialize_message(message),
    )


async def notify_message_updated_by_id(message_id: UUID) -> None:
    async with async_session_maker() as db:
        result = await db.execute(
            select(RelayMessage).where(
                RelayMessage.id == message_id,
                RelayMessage.deleted.is_(False),
            )
        )
        message = result.scalar_one_or_none()
        if message is None:
            return
        await web_subscriber_manager.publish(
            message.user_id,
            "message_updated",
            _serialize_message(message),
        )


async def notify_message_updated(message: RelayMessage) -> None:
    await web_subscriber_manager.publish(
        message.user_id,
        "message_updated",
        _serialize_message(message),
    )
