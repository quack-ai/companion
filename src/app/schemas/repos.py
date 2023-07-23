# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field

from .base import _Id

__all__ = ["RepoCreate", "RepoCreation", "RepoUpdate"]


class RepoCreate(_Id):
    owner_id: int = Field(..., gt=0)
    full_name: str = Field(..., example="frgfm/torch-cam")
    installed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RepoCreation(RepoCreate):
    installed_by: int = Field(..., gt=0)


class RepoUpdate(BaseModel):
    removed_at: Union[datetime, None]
