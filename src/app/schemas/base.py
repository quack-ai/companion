# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime

from pydantic import BaseModel, Field


# Template classes
class _CreatedAt(BaseModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class _Id(BaseModel):
    id: int = Field(..., gt=0)
