# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import _CreatedAt

__all__ = ["GuidelineCreate", "GuidelineEdit", "ContentUpdate", "OrderUpdate"]


class GuidelineEdit(BaseModel):
    title: str = Field(..., min_length=6, max_length=100)
    details: str = Field(..., min_length=6, max_length=1000)


class GuidelineCreate(_CreatedAt, GuidelineEdit):
    repo_id: int = Field(..., gt=0)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    order: int = Field(..., ge=0, nullable=False)


class ContentUpdate(GuidelineEdit):
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OrderUpdate(BaseModel):
    order: int = Field(..., ge=0, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
