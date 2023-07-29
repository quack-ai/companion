# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

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
