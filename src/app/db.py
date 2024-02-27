# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging

from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import Provider, User, UserScope
from app.services.github import gh_client

__all__ = ["get_session", "init_db"]

logger = logging.getLogger("uvicorn.error")
engine = AsyncEngine(create_engine(settings.POSTGRES_URL, echo=False))


async def get_session() -> AsyncSession:  # type: ignore[misc]
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Check if admin exists
        statement = select(User).where(User.login == settings.SUPERADMIN_LOGIN)
        results = await session.exec(statement=statement)
        user = results.one_or_none()
        if not user:
            logger.info("Initializing PostgreSQL database...")
            # Fetch authenticated GitHub User
            gh_user = gh_client.get_my_user(settings.SUPERADMIN_GH_PAT)
            pwd = await hash_password(settings.SUPERADMIN_PWD)
            session.add(
                User(
                    provider_user_id=f"{Provider.GITHUB}|{gh_user['id']}",
                    login=settings.SUPERADMIN_LOGIN,
                    hashed_password=pwd,
                    scope=UserScope.ADMIN,
                )
            )
        await session.commit()
