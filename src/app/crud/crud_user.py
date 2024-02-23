# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import User
from app.schemas.users import CredHash

__all__ = ["UserCRUD"]


class UserCRUD(BaseCRUD[User, User, CredHash]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_login(self, login: str, **kwargs) -> Union[User, None]:
        return await self.get_by("login", login, **kwargs)
