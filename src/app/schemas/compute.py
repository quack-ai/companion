# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.


from pydantic import BaseModel, Field

__all__ = ["Snippet", "ComplianceResult"]


class Snippet(BaseModel):
    code: str = Field(..., min_length=1)


class ComplianceResult(BaseModel):
    guideline_id: int = Field(..., gt=0)
    is_compliant: bool
    comment: str
