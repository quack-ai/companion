# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import Union

from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud.base import BaseCRUD
from app.models import Guideline
from app.schemas.guidelines import ContentUpdate, GuidelineCreation, OrderUpdate

__all__ = ["GuidelineCRUD"]


class GuidelineCRUD(BaseCRUD[Guideline, GuidelineCreation, Union[ContentUpdate, OrderUpdate]]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Guideline)
