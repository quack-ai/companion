# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from enum import Enum
from typing import List, Union

from pydantic import BaseModel, HttpUrl

__all__ = ["ChatCompletion"]


class ChatRole(str, Enum):
    SYSTEM: str = "system"
    USER: str = "user"
    ASSISTANT: str = "assistant"


class ChatMessage(BaseModel):
    role: ChatRole
    content: str


class _ResponseFormat(BaseModel):
    type: str = "json_object"


class ChatCompletion(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: float = 0.0
    frequency_penalty: float = 1.0
    response_format: _ResponseFormat = _ResponseFormat(type="json_object")
    user: Union[str, None] = None
    seed: int = 42
    stream: bool = False


class GHTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: HttpUrl


class GHToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
