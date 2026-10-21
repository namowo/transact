import os

os.environ.setdefault("DB_HOSTNAME", "localhost")
os.environ.setdefault("DB_PORT", "55432")
os.environ.setdefault("DB_USERNAME", "transact_test")
os.environ.setdefault("DB_PASSWORD", "transact_test")
os.environ.setdefault("DB_NAME", "transact_test")
os.environ.setdefault("ENVIRONMENT", "local")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-ci-only-not-used-in-prod")

import asyncio
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import Base, async_engine
from app.core.deps import get_async_session
from app.main import app
from app.models.laboratory import Laboratory, LaboratoryApprovalStatus
from app.models.user import User
from app.core.security import create_access_token, hash_password


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    async def _create() -> None:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _drop() -> None:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    asyncio.run(_create())
    yield
    asyncio.run(_drop())


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """A session bound to a connection whose transaction is rolled back
    after each test, so tests don't leak data between each other."""
    async with async_engine.connect() as conn:
        trans = await conn.begin()
        session_maker = async_sessionmaker(
            bind=conn, class_=AsyncSession, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        async with session_maker() as session:
            yield session
        await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override_get_async_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_async_session] = _override_get_async_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_async_session, None)


@pytest_asyncio.fixture
async def laboratory(db_session: AsyncSession) -> Laboratory:
    lab = Laboratory(
        laboratory_name="Test Lab",
        institutional_affiliation="Test Institution",
        city="Testville",
        country="Testland",
        approval_status=LaboratoryApprovalStatus.approved,
    )
    db_session.add(lab)
    await db_session.commit()
    await db_session.refresh(lab)
    return lab


async def _make_user(db_session: AsyncSession, laboratory: Laboratory, **kwargs) -> User:
    defaults = dict(
        email="user@example.com",
        hashed_password=hash_password("Passw0rd!"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        laboratory_id=laboratory.id,
    )
    defaults.update(kwargs)
    user = User(**defaults)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def regular_user(db_session: AsyncSession, laboratory: Laboratory) -> User:
    return await _make_user(db_session, laboratory, email="user@example.com")


@pytest_asyncio.fixture
async def superuser(db_session: AsyncSession, laboratory: Laboratory) -> User:
    return await _make_user(
        db_session, laboratory, email="admin@example.com", is_superuser=True
    )


@pytest_asyncio.fixture
async def lab_admin(db_session: AsyncSession, laboratory: Laboratory) -> User:
    return await _make_user(
        db_session, laboratory, email="labadmin@example.com", can_manage_lab_users=True
    )


def auth_headers(user: User) -> dict:
    token = create_access_token(subject=str(user.id))
    return {"Cookie": f"access_token={token}"}


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, regular_user: User) -> AsyncClient:
    client.cookies.update({"access_token": create_access_token(subject=str(regular_user.id))})
    return client


@pytest_asyncio.fixture
async def superuser_client(client: AsyncClient, superuser: User) -> AsyncClient:
    client.cookies.update({"access_token": create_access_token(subject=str(superuser.id))})
    return client


@pytest_asyncio.fixture
async def lab_admin_client(client: AsyncClient, lab_admin: User) -> AsyncClient:
    client.cookies.update({"access_token": create_access_token(subject=str(lab_admin.id))})
    return client
