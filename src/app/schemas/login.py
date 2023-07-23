# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from typing import List

from pydantic import BaseModel, Field

from app.models import UserScope

__all__ = ["Token", "GitHubToken"]


class GitHubToken(BaseModel):
    github_token: str = Field(..., example="ghp_eyJhbGciOiJIUzI1NiIsInR5cCI")


class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.423fgFGTfttrvU6D1k7vF92hH5vaJHCGFYd8E")
    token_type: str = Field(..., example="bearer")


class TokenPayload(BaseModel):
    user_id: int = Field(..., gt=0)
    scopes: List[UserScope] = []
