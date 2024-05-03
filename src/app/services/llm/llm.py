# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from enum import Enum
from typing import Union

from app.core.config import settings

from .groq import GroqClient
from .ollama import OllamaClient

__all__ = ["llm_client"]


class LLMProvider(str, Enum):
    OLLAMA: str = "ollama"
    OPENAI: str = "openai"
    GROQ: str = "groq"


llm_client: Union[OllamaClient, GroqClient]
if settings.LLM_PROVIDER == LLMProvider.OLLAMA:
    if not settings.OLLAMA_ENDPOINT:
        raise ValueError("Please provide a value for `OLLAMA_ENDPOINT`")
    llm_client = OllamaClient(settings.OLLAMA_ENDPOINT, settings.OLLAMA_MODEL, settings.LLM_TEMPERATURE)
elif settings.LLM_PROVIDER == LLMProvider.GROQ:
    if not settings.GROQ_API_KEY:
        raise ValueError("Please provide a value for `GROQ_API_KEY`")
    llm_client = GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL, settings.LLM_TEMPERATURE)  # type: ignore[arg-type]
else:
    raise NotImplementedError("LLM provider is not implemented")
