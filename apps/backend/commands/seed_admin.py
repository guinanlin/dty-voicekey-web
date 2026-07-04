import asyncio
import os
import uuid

from dotenv import load_dotenv
from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from app.core.database import async_session_maker
from app.model.base_model import User
import app.model.item_model  # noqa: F401 — register Item for User relationship
import app.model.sms_model  # noqa: F401 — register SmsMessage for User relationship

load_dotenv()

SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@dty.com")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
SEED_WEBHOOK_API_KEY = os.getenv(
    "SMS_FORWARD_DEFAULT_API_KEY", "dev-sms-forward-key-change-in-production"
)


async def seed_admin() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == SEED_ADMIN_EMAIL)
        )
        admin = result.scalar_one_or_none()

        if admin is None:
            admin = User(
                id=uuid.uuid4(),
                email=SEED_ADMIN_EMAIL,
                hashed_password=PasswordHelper().hash(SEED_ADMIN_PASSWORD),
                is_active=True,
                is_superuser=True,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            print(f"Created admin user: {SEED_ADMIN_EMAIL}")
        else:
            print(f"Admin user already exists: {SEED_ADMIN_EMAIL}")

        if not admin.webhook_api_key:
            admin.webhook_api_key = SEED_WEBHOOK_API_KEY
            await session.commit()
            print(f"Set webhook API key for {SEED_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
