# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import List

from pydantic import BaseModel, Field, HttpUrl

from app.models import UserScope

__all__ = ["Token", "GHAccessToken"]


class GHAccessToken(BaseModel):
    github_token: str = Field(..., example="ghp_eyJhbGciOiJIUzI1NiIsInR5cCI")


class Token(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.423fgFGTfttrvU6D1k7vF92hH5vaJHCGFYd8E")
    token_type: str = Field(..., example="bearer")


class TokenPayload(BaseModel):
    user_id: int = Field(..., gt=0)
    scopes: List[UserScope] = []


class GHTokenRequest(BaseModel):
    code: str
    redirect_uri: HttpUrl


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: HttpUrl


class GHToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
