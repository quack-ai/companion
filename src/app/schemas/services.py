# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, HttpUrl

__all__ = ["ChatCompletion"]


class OpenAIModel(str, Enum):
    # https://platform.openai.com/docs/models/overview
    GPT3_5: str = "gpt-3.5-turbo-0613"
    GPT3_5_LONG: str = "gpt-3.5-turbo-16k-0613"
    GPT4: str = "gpt-4-0613"
    GPT4_LONG: str = "gpt-4-32k-0613"


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


class OpenAIMessage(BaseModel):
    role: OpenAIChatRole
    content: str


class ChatCompletion(BaseModel):
    model: OpenAIModel = OpenAIModel.GPT3_5
    messages: List[OpenAIMessage]
    functions: List[OpenAIFunction]
    function_call: Dict[str, str]
    temperature: float
    frequency_penalty: float


class GHTokenRequest(BaseModel):
    client_id: str
    client_secret: str
    code: str
    redirect_uri: HttpUrl


class GHToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
