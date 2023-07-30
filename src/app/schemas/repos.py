# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, Field

from .base import _Id

__all__ = ["RepoCreate", "RepoCreation", "RepoUpdate", "GuidelineOrder"]


class RepoCreate(_Id):
    owner_id: int = Field(..., gt=0)
    full_name: str = Field(..., example="frgfm/torch-cam")
    installed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RepoCreation(RepoCreate):
    installed_by: int = Field(..., gt=0)


class RepoUpdate(BaseModel):
    removed_at: Union[datetime, None]


class GuidelineOrder(BaseModel):
    guideline_ids: List[int]
