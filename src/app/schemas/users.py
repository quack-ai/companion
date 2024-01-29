# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from pydantic import BaseModel, Field

from app.models import UserScope

from .base import _Id

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


class UserCreate(_Id, Cred, Scope):
    pass


class UserCreation(_Id, Login, CredHash, Scope):
    pass
