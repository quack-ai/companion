# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import User
from app.schemas.users import CredHash, UserCreation

__all__ = ["UserCRUD"]


class UserCRUD(BaseCRUD[User, UserCreation, CredHash]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_login(self, login: str, **kwargs) -> Union[User, None]:
        return await self.get_by("login", login, **kwargs)
