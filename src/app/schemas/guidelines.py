# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime

from pydantic import BaseModel, Field

from .base import OptionalGHToken

__all__ = ["GuidelineCreate", "GuidelineEdit", "ContentUpdate", "OrderUpdate"]


class GuidelineContent(BaseModel):
    title: str = Field(..., min_length=6, max_length=100)
    details: str = Field(..., min_length=6, max_length=1000)


class GuidelineLocation(BaseModel):
    repo_id: int = Field(..., gt=0)
    order: int = Field(0, ge=0, nullable=False)


class GuidelineEdit(GuidelineContent, OptionalGHToken):
    pass


class GuidelineCreate(GuidelineEdit, GuidelineLocation):
    pass


class GuidelineCreation(GuidelineContent, GuidelineLocation):
    pass


class ContentUpdate(GuidelineContent):
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class OrderUpdate(OptionalGHToken):
    order: int = Field(..., ge=0, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
