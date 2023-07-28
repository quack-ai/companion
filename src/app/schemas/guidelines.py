# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import _CreatedAt

__all__ = ["GuidelineCreate", "GuidelineEdit", "ContentUpdate", "OrderUpdate"]


class GuidelineEdit(BaseModel):
    title: str = Field(..., min_length=6, max_length=100)
    details: str


class GuidelineCreate(_CreatedAt, GuidelineEdit):
    repo_id: int = Field(..., gt=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    order: int = Field(..., ge=0, nullable=False)


class ContentUpdate(GuidelineEdit):
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OrderUpdate(BaseModel):
    order: int = Field(..., ge=0, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
