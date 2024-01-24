# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from pydantic import BaseModel, Field

__all__ = ["Snippet", "ComplianceResult"]


class Snippet(BaseModel):
    code: str = Field(..., min_length=1)


class ComplianceResult(BaseModel):
    guideline_id: int = Field(..., gt=0)
    is_compliant: bool
    comment: str
