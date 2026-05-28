import asyncio
import os
import uuid

from dotenv import load_dotenv
from fastapi_users.password import PasswordHelper
from sqlalchemy import select

from app.core.database import async_session_maker
from app.model.base_model import User
import app.model.item_model  # noqa: F401 — register Item for User relationship

load_dotenv()

SEED_ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@dty.com")
SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "admin123")


async def seed_admin() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.email == SEED_ADMIN_EMAIL)
        )
        if result.scalar_one_or_none():
            print(f"Admin user already exists: {SEED_ADMIN_EMAIL}")
            return

        user = User(
            id=uuid.uuid4(),
            email=SEED_ADMIN_EMAIL,
            hashed_password=PasswordHelper().hash(SEED_ADMIN_PASSWORD),
            is_active=True,
            is_superuser=True,
            is_verified=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created admin user: {SEED_ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
