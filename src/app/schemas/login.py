# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List

from pydantic import BaseModel, Field, HttpUrl

from app.models import UserScope

__all__ = ["GHAccessToken", "Token"]


class GHAccessToken(BaseModel):
    github_token: str = Field(..., examples=["ghp_eyJhbGciOiJIUzI1NiIsInR5cCI"])


class Token(BaseModel):
    access_token: str = Field(
        ..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.423fgFGTfttrvU6D1k7vF92hH5vaJHCGFYd8E"]
    )
    token_type: str = Field(..., examples=["bearer"])


class TokenPayload(BaseModel):
    user_id: int = Field(..., gt=0)
    scopes: List[UserScope] = []


class TokenRequest(BaseModel):
    code: str
    redirect_uri: HttpUrl
