# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime
from enum import Enum
from typing import List, Union

from sqlmodel import JSON, Column, Field, SQLModel

__all__ = ["GHRole", "Guideline", "Repository", "User", "UserScope"]


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
    # Allow sign-up/in via provider or login + password
    id: int = Field(None, primary_key=True)
    scope: UserScope = Field(UserScope.USER, nullable=False)
    provider_user_id: Union[str, None] = Field(None, min_length=9, max_length=30)
    login: Union[str, None] = Field(None, min_length=2, max_length=50)
    hashed_password: Union[str, None] = Field(None, min_length=5, max_length=70)


class Repository(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    name: str = Field(..., nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    provider_repo_id = Union[str, None] = Field(None, min_length=9, max_length=30)
    ruleset_id: Union[int, None] = Field(None, foreign_key="ruleset.id", nullable=True)


class Guideline(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    title: str = Field(..., min_length=6, max_length=100, nullable=False)
    details: str = Field(..., min_length=6, max_length=1000, nullable=False)
    creator_user_id: int = Field(..., foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # origin


class RuleSet(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    name: str = Field(..., min_length=6, max_length=100, nullable=False)
    guidelines: List[int] = Field(sa_column=Column(JSON))
    creator_user_id: int = Field(..., foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Needed for Column(JSON)
    class Config:
        arbitrary_types_allowed = True
