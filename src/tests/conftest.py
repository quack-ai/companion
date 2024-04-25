import asyncio
from datetime import datetime
from typing import AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.api_v1.endpoints import login, users
from app.core.config import settings
from app.core.security import create_access_token
from app.db import engine
from app.main import app
from app.models import Guideline, Repository, User

dt_format = "%Y-%m-%dT%H:%M:%S.%f"

USER_TABLE = [
    {
        "id": 1,
        "provider_user_id": 123,
        "login": "first_login",
        "hashed_password": "hashed_first_pwd",
        "scope": "admin",
        "created_at": datetime.strptime("2024-02-23T08:18:45.447773", dt_format),
    },
    {
        "id": 2,
        "provider_user_id": 456,
        "login": "second_login",
        "hashed_password": "hashed_second_pwd",
        "scope": "user",
        "created_at": datetime.strptime("2024-02-23T08:18:45.447774", dt_format),
    },
]

REPO_TABLE = [
    {
        "id": 1,
        "provider_repo_id": 12345,
        "name": "quack-ai/dummy-repo",
        "created_at": datetime.strptime("2023-11-07T15:07:19.226673", dt_format),
    },
    {
        "id": 2,
        "provider_repo_id": 123456,
        "name": "quack-ai/another-repo",
        "created_at": datetime.strptime("2023-11-07T15:07:19.226673", dt_format),
    },
]

GUIDELINE_TABLE = [
    {
        "id": 1,
        "content": "Ensure function and class/instance methods have a meaningful & informative name",
        "creator_id": 1,
        "created_at": datetime.strptime("2023-11-07T15:08:19.226673", dt_format),
        "updated_at": datetime.strptime("2023-11-07T15:08:19.226673", dt_format),
    },
    {
        "id": 2,
        "content": "All functions and methods need to have a docstring",
        "creator_id": 2,
        "created_at": datetime.strptime("2023-11-07T15:08:20.226673", dt_format),
        "updated_at": datetime.strptime("2023-11-07T15:08:20.226673", dt_format),
    },
]


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        app=app, base_url=f"http://api.localhost:8050{settings.API_V1_STR}", follow_redirects=True
    ) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_session() -> AsyncSession:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        async with session.begin():
            for table in reversed(SQLModel.metadata.sorted_tables):
                await session.exec(table.delete())
                if hasattr(table.c, "id"):
                    await session.exec(text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH 1"))

        yield session
        await session.rollback()


def mock_verify_password(plain_password, hashed_password):
    return hashed_password == f"hashed_{plain_password}"


def mock_hash_password(password):
    return f"hashed_{password}"


@pytest_asyncio.fixture(scope="function")
async def user_session(async_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(users, "hash_password", mock_hash_password)
    monkeypatch.setattr(login, "verify_password", mock_verify_password)
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    await async_session.exec(
        text(f"ALTER SEQUENCE user_id_seq RESTART WITH {max(entry['id'] for entry in USER_TABLE) + 1}")
    )
    await async_session.commit()
    yield async_session
    await async_session.rollback()


@pytest_asyncio.fixture(scope="function")
async def repo_session(user_session: AsyncSession, monkeypatch):
    for entry in REPO_TABLE:
        user_session.add(Repository(**entry))
    await user_session.commit()
    await user_session.exec(
        text(f"ALTER SEQUENCE repository_id_seq RESTART WITH {max(entry['id'] for entry in REPO_TABLE) + 1}")
    )
    await user_session.commit()
    yield user_session
    await user_session.rollback()


@pytest_asyncio.fixture(scope="function")
async def guideline_session(user_session: AsyncSession, monkeypatch):
    for entry in GUIDELINE_TABLE:
        user_session.add(Guideline(**entry))
    await user_session.commit()
    # Update the guideline index count
    await user_session.exec(
        text(f"ALTER SEQUENCE guideline_id_seq RESTART WITH {max(entry['id'] for entry in GUIDELINE_TABLE) + 1}")
    )
    await user_session.commit()
    yield user_session


def get_token(access_id: int, scopes: str) -> Dict[str, str]:
    token_data = {"sub": str(access_id), "scopes": scopes}
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def pytest_configure():
    # api.security patching
    pytest.get_token = get_token
    # Table
    pytest.user_table = [
        {k: datetime.strftime(v, dt_format) if isinstance(v, datetime) else v for k, v in entry.items()}
        for entry in USER_TABLE
    ]
    pytest.repo_table = [
        {k: datetime.strftime(v, dt_format) if isinstance(v, datetime) else v for k, v in entry.items()}
        for entry in REPO_TABLE
    ]
    pytest.guideline_table = [
        {k: datetime.strftime(v, dt_format) if isinstance(v, datetime) else v for k, v in entry.items()}
        for entry in GUIDELINE_TABLE
    ]
