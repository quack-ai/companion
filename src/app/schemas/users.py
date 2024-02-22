# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import Union

from pydantic import BaseModel, Field

from app.models import UserScope

__all__ = ["Cred", "CredHash", "UserCreate", "UserCreation"]


# Accesses
class Login(BaseModel):
    login: str = Field(..., min_length=3, max_length=50, example="JohnDoe")


class Cred(BaseModel):
    password: str = Field(..., min_length=3, example="PickARobustOne")


class CredHash(BaseModel):
    hashed_password: str


class Scope(BaseModel):
    scope: UserScope = Field(UserScope.USER, nullable=False)


class UserCreate(Scope):
    provider_user_id: Union[int, None] = Field(None, gt=0)
    login: Union[str, None] = Field(None, min_length=3, max_length=50, example="JohnDoe")
    password: Union[str, None] = Field(None, min_length=3, example="PickARobustOne")


class UserCreation(Scope):
    provider_user_id: Union[str, None] = Field(None, min_length=9, max_length=30)
    login: Union[str, None] = Field(None, min_length=3, max_length=50, example="JohnDoe")
    hashed_password: Union[str, None] = Field(None, min_length=3, example="PickARobustOne")
