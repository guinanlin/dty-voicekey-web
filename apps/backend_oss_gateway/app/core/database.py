from typing import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.models.base import Base


def _build_async_url(database_url: str) -> str:
    parsed = urlparse(database_url)
    port = f":{parsed.port}" if parsed.port else ""
    return (
        f"postgresql+asyncpg://{parsed.username}:{parsed.password}@"
        f"{parsed.hostname}{port}{parsed.path}"
    )


engine = create_async_engine(
    _build_async_url(settings.DATABASE_URL), poolclass=NullPool
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=settings.EXPIRE_ON_COMMIT
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
