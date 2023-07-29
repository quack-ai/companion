# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import Any, Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import Guideline
from app.schemas.guidelines import ContentUpdate, GuidelineCreate, OrderUpdate

__all__ = ["GuidelineCRUD"]


class GuidelineCRUD(BaseCRUD[Guideline, GuidelineCreate, Union[ContentUpdate, OrderUpdate]]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Guideline)

    async def get(self, entry_id: int, **kwargs: Any) -> Union[Guideline, None]:
        return await self.get_by("id", entry_id, **kwargs)
