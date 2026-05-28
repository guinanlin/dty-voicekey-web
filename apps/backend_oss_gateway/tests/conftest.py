import os

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_async_session
from app.main import app
from app.models.base import Base

SERVICE_HEADERS = {
    "X-Service-Token": "dev-service-token-change-in-production",
    "X-Tenant-Id": "test-tenant",
}


def _test_database_url() -> str:
    return os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture(scope="function")
async def async_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def engine():
    engine = create_async_engine(_test_database_url(), echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session):
    async def override_get_async_session():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as client:
        yield client
    app.dependency_overrides.clear()
