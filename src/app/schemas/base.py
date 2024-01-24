# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from typing import Union

from pydantic import BaseModel, Field


# Template classes
class _CreatedAt(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class _Id(BaseModel):
    id: int = Field(..., gt=0)


class OptionalGHToken(BaseModel):
    github_token: Union[str, None] = None
