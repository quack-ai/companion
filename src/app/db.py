# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from sqlalchemy.ext.asyncio.engine import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import User, UserScope
from app.services.github import gh_client

__all__ = ["get_session", "init_db"]


engine = AsyncEngine(create_engine(settings.POSTGRES_URL, echo=False))


async def get_session() -> AsyncSession:  # type: ignore[misc]
    async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # Fetch authenticated GitHub User
        gh_user = gh_client.get_my_user(settings.SUPERADMIN_GH_PAT)
        statement = select(User).where(User.login == gh_user["login"])
        results = await session.execute(statement=statement)
        current_user = results.scalar_one_or_none()
        if not current_user:
            pwd = await hash_password(settings.SUPERADMIN_PWD)
            session.add(User(id=gh_user["id"], login=gh_user["login"], hashed_password=pwd, scope=UserScope.ADMIN))
        await session.commit()
