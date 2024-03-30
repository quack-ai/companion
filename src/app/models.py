# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from enum import Enum
from typing import Union

from sqlmodel import Field, SQLModel

__all__ = ["Guideline", "Repository", "User"]


class GHRole(str, Enum):
    ADMIN: str = "admin"
    MAINTAIN: str = "maintain"
    WRITE: str = "write"
    TRIAGE: str = "triage"
    READ: str = "read"


class UserScope(str, Enum):
    ADMIN: str = "admin"
    USER: str = "user"


class Provider(str, Enum):
    GITHUB: str = "github"


class User(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    scope: UserScope = Field(UserScope.USER, nullable=False)
    # Allow sign-up/in via provider or login + password
    provider_user_id: Union[int, None] = Field(None, gt=0)
    login: Union[str, None] = Field(None, min_length=2, max_length=50)
    hashed_password: Union[str, None] = Field(None, min_length=5, max_length=70)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Repository(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    provider_repo_id: int = Field(index=True, nullable=True, gt=0)
    name: str = Field(..., min_length=2, max_length=100, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Guideline(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    content: str = Field(..., min_length=6, max_length=1000, nullable=False)
    creator_id: int = Field(..., foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# class Collection(SQLModel, table=True):
#     id: int = Field(None, primary_key=True)
#     name: str = Field(..., min_length=6, max_length=100, nullable=False)
#     guidelines: List[int] = Field(sa_column=Column(JSON))
#     creator_user_id: int = Field(..., foreign_key="user.id", nullable=False)
#     created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
#     updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

#     # Needed for Column(JSON)
#     class Config:
#         arbitrary_types_allowed = True
