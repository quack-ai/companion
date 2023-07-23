# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from pydantic import BaseModel, Field

from app.models import UserScope

from .base import _Id

__all__ = ["UserCreate", "UserCreation", "Cred", "CredHash"]


# Accesses
class Login(BaseModel):
    login: str = Field(..., min_length=3, max_length=50, example="JohnDoe")


class Cred(BaseModel):
    password: str = Field(..., min_length=3, example="PickARobustOne")


class CredHash(BaseModel):
    hashed_password: str


class Scope(BaseModel):
    scope: UserScope = Field(UserScope.USER, nullable=False)


class UserCreate(_Id, Login, Cred, Scope):
    pass


class UserCreation(_Id, Login, CredHash, Scope):
    pass
