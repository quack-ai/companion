# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from typing import Any, Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import User
from app.schemas.users import CredHash, UserCreation

__all__ = ["UserCRUD"]


class UserCRUD(BaseCRUD[User, UserCreation, CredHash]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_login(self, login: str, **kwargs: Any) -> Union[User, None]:
        return await self.get_by("login", login, **kwargs)

    async def get(self, entry_id: int, **kwargs: Any) -> Union[User, None]:
        return await self.get_by("id", entry_id, **kwargs)
