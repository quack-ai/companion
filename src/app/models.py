# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from datetime import datetime
from enum import Enum
from typing import Union

from sqlmodel import Field, SQLModel

__all__ = ["UserScope", "User", "Repository", "Guideline"]


class UserScope(str, Enum):
    USER: str = "user"
    ADMIN: str = "admin"


class User(SQLModel, table=True):  # type: ignore[misc]
    id: int = Field(..., primary_key=True)
    login: str = Field(index=True, min_length=2, max_length=50)
    hashed_password: str = Field(..., min_length=5, max_length=70, nullable=False)
    scope: UserScope = Field(UserScope.USER, nullable=False)


class Repository(SQLModel, table=True):  # type: ignore[misc]
    id: int = Field(..., primary_key=True)
    owner_id: int = Field(..., nullable=False)
    full_name: str = Field(..., nullable=False)
    installed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    removed_at: Union[datetime, None] = None
    installed_by: int = Field(..., foreign_key="user.id")


class Guideline(SQLModel, table=True):  # type: ignore[misc]
    id: int = Field(None, primary_key=True)
    repo_id: int = Field(..., foreign_key="repository.id", nullable=False)
    title: str = Field(..., min_length=6, max_length=100, nullable=False)
    details: str
    order: int = Field(..., ge=0, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    # origin: str


# class Event(SQLModel, table=true)
