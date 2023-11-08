import asyncio
from typing import AsyncGenerator, Dict, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.db import engine
from app.main import app


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
    session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
            for table in reversed(SQLModel.metadata.sorted_tables):
                conn.execute(table.delete())
                conn.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")

        yield s

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


async def mock_verify_password(plain_password, hashed_password):
    return hashed_password == f"hashed_{plain_password}"


async def mock_hash_password(password):
    return f"hashed_{password}"


async def get_token(access_id: int, scopes: str) -> Dict[str, str]:
    token_data = {"sub": str(access_id), "scopes": scopes}
    token = await create_access_token(token_data)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def pytest_configure():
    # api.security patching
    pytest.mock_verify_password = mock_verify_password
    pytest.mock_hash_password = mock_hash_password
    pytest.get_token = get_token
