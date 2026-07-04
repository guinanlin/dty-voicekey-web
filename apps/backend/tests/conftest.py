from httpx import AsyncClient, ASGITransport
import pytest_asyncio
import os

os.environ.setdefault("REDIS_URL", "memory")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ACCESS_SECRET_KEY", "test-access-secret")
os.environ.setdefault("RESET_PASSWORD_SECRET_KEY", "test-reset-secret")
os.environ.setdefault("VERIFICATION_SECRET_KEY", "test-verification-secret")
os.environ.setdefault("CORS_ORIGINS", '["*"]')

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402
from fastapi_users.db import SQLAlchemyUserDatabase  # noqa: E402
from fastapi_users.password import PasswordHelper  # noqa: E402
import uuid  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.model.base_model import User, Base  # noqa: E402
from app.model.relay_model import RelayPair, RelayMessage  # noqa: F401,E402
from app.core.redis import clear_memory_store  # noqa: E402

from app.core.database import get_user_db, get_async_session  # noqa: E402
from app.main import app  # noqa: E402
from app.users import get_jwt_strategy  # noqa: E402


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create a fresh test database engine for each test function."""
    clear_memory_store()
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Create a fresh database session for each test."""
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_client(db_session):
    """Fixture to create a test client that uses the test database session."""

    # FastAPI-Users database override (wraps session with user operation helpers)
    async def override_get_user_db():
        session = SQLAlchemyUserDatabase(db_session, User)
        try:
            yield session
        finally:
            await db_session.close()

    # General database override (raw session access)
    async def override_get_async_session():
        try:
            yield db_session
        finally:
            await db_session.close()

    # Set up test database overrides
    app.dependency_overrides[get_user_db] = override_get_user_db
    app.dependency_overrides[get_async_session] = override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://localhost:8000"
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def authenticated_user(test_client, db_session):
    """Fixture to create and authenticate a test user directly in the database."""

    # Create user data
    user_data = {
        "id": uuid.uuid4(),
        "email": "test@example.com",
        "hashed_password": PasswordHelper().hash("TestPassword123#"),
        "is_active": True,
        "is_superuser": False,
        "is_verified": True,
    }

    # Create user directly in database
    user = User(**user_data)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Generate token using the strategy directly
    strategy = get_jwt_strategy()
    access_token = await strategy.write_token(user)

    # Return both the headers and the user data
    return {
        "headers": {"Authorization": f"Bearer {access_token}"},
        "user": user,
        "user_data": {"email": user_data["email"], "password": "TestPassword123#"},
    }
