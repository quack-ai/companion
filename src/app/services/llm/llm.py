# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import re
from enum import Enum
from typing import Dict, Union

from fastapi import HTTPException, status

from app.core.config import settings

from .groq import GroqClient
from .ollama import OllamaClient
from .openai import OpenAIClient

__all__ = ["llm_client"]

EXAMPLE_PROMPT = (
    "You are responsible for producing concise illustrations of the company coding guidelines. "
    "This will be used to teach new developers our way of engineering software. "
    "Make sure your code is in the specified programming language and functional, don't add extra comments or explanations.\n"
    # Format
    "You should output two code blocks: "
    "a minimal code snippet where the instruction was correctly followed, "
    "and the same snippet with minimal modifications that invalidates the instruction."
)
# Strangely, this doesn't work when compiled
EXAMPLE_PATTERN = r"```[a-zA-Z]*\n(?P<positive>.*?)```\n.*```[a-zA-Z]*\n(?P<negative>.*?)```"


def validate_example_response(response: str) -> Dict[str, str]:
    matches = re.search(EXAMPLE_PATTERN, response.strip(), re.DOTALL)
    if matches is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed output schema validation")

    return matches.groupdict()


class LLMProvider(str, Enum):
    OLLAMA: str = "ollama"
    OPENAI: str = "openai"
    GROQ: str = "groq"


llm_client: Union[OllamaClient, GroqClient, OpenAIClient]
if settings.LLM_PROVIDER == LLMProvider.OLLAMA:
    if not settings.OLLAMA_ENDPOINT:
        raise ValueError("Please provide a value for `OLLAMA_ENDPOINT`")
    llm_client = OllamaClient(settings.OLLAMA_ENDPOINT, settings.OLLAMA_MODEL, settings.LLM_TEMPERATURE)
elif settings.LLM_PROVIDER == LLMProvider.GROQ:
    if not settings.GROQ_API_KEY:
        raise ValueError("Please provide a value for `GROQ_API_KEY`")
    llm_client = GroqClient(settings.GROQ_API_KEY, settings.GROQ_MODEL, settings.LLM_TEMPERATURE)  # type: ignore[arg-type]
elif settings.LLM_PROVIDER == LLMProvider.OPENAI:
    if not settings.OPENAI_API_KEY:
        raise ValueError("Please provide a value for `OPENAI_API_KEY`")
    llm_client = OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL, settings.LLM_TEMPERATURE)  # type: ignore[arg-type]
else:
    raise NotImplementedError("LLM provider is not implemented")
