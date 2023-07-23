# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from datetime import datetime

from pydantic import BaseModel, Field


# Template classes
class _CreatedAt(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class _Id(BaseModel):
    id: int = Field(..., gt=0)
