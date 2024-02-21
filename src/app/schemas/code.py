# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from enum import Enum
from typing import List

from pydantic import BaseModel, Field

__all__ = ["ChatHistory", "ChatMessage", "ChatRole", "ComplianceResult", "Snippet"]


class Snippet(BaseModel):
    code: str = Field(..., min_length=1)


class ComplianceResult(BaseModel):
    guideline_id: int = Field(..., gt=0)
    is_compliant: bool
    comment: str


class ChatRole(str, Enum):
    SYSTEM: str = "system"
    USER: str = "user"
    ASSISTANT: str = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole = Field(ChatRole.USER, example=ChatRole.USER)
    content: str = Field(..., min_length=1)


class ChatHistory(BaseModel):
    messages: List[ChatMessage]
