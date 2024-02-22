# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List

from pydantic import BaseModel, Field

from .base import OptionalGHToken, _Id

__all__ = ["GuidelineOrder", "RepoCreate", "RepoCreation", "RepoUpdate"]


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


class RepoRegistration(OptionalGHToken):
    repo_id: int = Field(..., gt=0)
