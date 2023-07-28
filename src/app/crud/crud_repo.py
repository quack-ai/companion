# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import Any, Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import Repository
from app.schemas.repos import RepoCreation, RepoUpdate

__all__ = ["RepositoryCRUD"]


class RepositoryCRUD(BaseCRUD[Repository, RepoCreation, RepoUpdate]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Repository)

    async def get(self, entry_id: int, **kwargs: Any) -> Union[Repository, None]:
        return await self.get_by("id", entry_id, **kwargs)
