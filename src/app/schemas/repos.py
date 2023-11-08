# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import List

from pydantic import BaseModel, Field

from .base import OptionalGHToken, _Id

__all__ = ["RepoCreate", "RepoCreation", "RepoUpdate", "GuidelineOrder"]


class RepoCreate(_Id, OptionalGHToken):
    pass


class RepoCreation(_Id):
    installed_by: int = Field(..., gt=0)
    owner_id: int = Field(..., gt=0)
    full_name: str = Field(..., example="frgfm/torch-cam")


class RepoUpdate(BaseModel):
    is_active: bool


class GuidelineOrder(OptionalGHToken):
    guideline_ids: List[int]
