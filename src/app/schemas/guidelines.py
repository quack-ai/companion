# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime

from pydantic import BaseModel, Field

__all__ = ["ContentUpdate", "GuidelineContent"]


class TextContent(BaseModel):
    content: str = Field(..., min_length=10)


class ExampleRequest(TextContent):
    language: str = Field("python", min_length=1, max_length=20)


class GuidelineExample(BaseModel):
    positive: str = Field(
        ..., min_length=3, description="a minimal code snippet where the instruction was correctly followed."
    )
    negative: str = Field(
        ..., min_length=3, description="the same snippet with minimal modifications that invalidates the instruction."
    )


class GuidelineContent(BaseModel):
    content: str = Field(..., min_length=6, max_length=1000, nullable=False)


class ContentUpdate(GuidelineContent):
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
