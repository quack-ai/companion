# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from enum import Enum
from typing import Any, Dict, List, Union

from pydantic import BaseModel, HttpUrl

__all__ = ["ChatCompletion"]


class OpenAIModel(str, Enum):
    # https://platform.openai.com/docs/models/overview
    GPT3_5_TURBO: str = "gpt-3.5-turbo-1106"
    GPT3_5_TURBO_LEGACY: str = "gpt-3.5-turbo-0613"
    GPT4_TURBO: str = "gpt-4-1106-preview"
    GPT4: str = "gpt-4-0613"


class OpenAIChatRole(str, Enum):
    SYSTEM: str = "system"
    USER: str = "user"
    ASSISTANT: str = "assistant"


class FieldSchema(BaseModel):
    type: str
    description: str


class ObjectSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str]


class ArraySchema(BaseModel):
    type: str = "array"
    items: ObjectSchema


class OpenAIFunction(BaseModel):
    name: str
    description: str
    parameters: ObjectSchema


class OpenAITool(BaseModel):
    type: str = "function"
    function: OpenAIFunction


class _FunctionName(BaseModel):
    name: str


class _OpenAIToolChoice(BaseModel):
    type: str = "function"
    function: _FunctionName


class OpenAIMessage(BaseModel):
    role: OpenAIChatRole
    content: str


class _ResponseFormat(BaseModel):
    type: str = "json_object"


class ChatCompletion(BaseModel):
    model: OpenAIModel = OpenAIModel.GPT3_5_TURBO
    messages: List[OpenAIMessage]
    functions: List[OpenAIFunction]
    function_call: Dict[str, str]
    temperature: float = 0.0
    frequency_penalty: float = 1.0
    response_format: _ResponseFormat = _ResponseFormat(type="json_object")
    user: Union[str, None] = None
    # seed: int = 42


class GHTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: HttpUrl


class GHToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
