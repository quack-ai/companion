# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserScope

__all__ = ["get_session", "init_db"]


engine = create_async_engine(settings.POSTGRES_URL, echo=settings.DEBUG)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        statement = select(User).where(User.login == settings.SUPERUSER_LOGIN)
        results = await session.execute(statement=statement)
        current_user = results.scalar_one_or_none()
        if not current_user:
            pwd = await hash_password(settings.SUPERUSER_PWD)
            session.add(
                User(
                    id=settings.SUPERUSER_ID, login=settings.SUPERUSER_LOGIN, hashed_password=pwd, scope=UserScope.ADMIN
                )
            )
        await session.commit()
