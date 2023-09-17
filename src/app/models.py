# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime
from enum import Enum
from typing import Union

from sqlmodel import Field, SQLModel

__all__ = ["GHRole", "UserScope", "User", "Repository", "Guideline"]


class GHRole(str, Enum):
    ADMIN: str = "admin"
    MAINTAIN: str = "maintain"
    WRITE: str = "write"
    TRIAGE: str = "triage"
    READ: str = "read"


class UserScope(str, Enum):
    ADMIN: str = "admin"
    USER: str = "user"


class User(SQLModel, table=True):
    id: int = Field(..., primary_key=True)
    login: str = Field(index=True, min_length=2, max_length=50)
    hashed_password: str = Field(..., min_length=5, max_length=70, nullable=False)
    scope: UserScope = Field(UserScope.USER, nullable=False)


class Repository(SQLModel, table=True):
    id: int = Field(..., primary_key=True)
    owner_id: int = Field(..., nullable=False, foreign_key="user.id")
    full_name: str = Field(..., nullable=False)
    installed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    removed_at: Union[datetime, None] = None
    installed_by: int = Field(..., foreign_key="user.id")


class Guideline(SQLModel, table=True):
    id: int = Field(None, primary_key=True)
    repo_id: int = Field(..., foreign_key="repository.id", nullable=False)
    title: str = Field(..., min_length=6, max_length=100, nullable=False)
    details: str = Field(..., min_length=6, max_length=1000, nullable=False)
    order: int = Field(..., ge=0, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # origin: str
