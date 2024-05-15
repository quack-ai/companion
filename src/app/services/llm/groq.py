# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Union, cast

from groq import Groq, Stream
from groq.lib.chat_completion_chunk import ChatCompletionChunk

from .utils import CHAT_PROMPT

logger = logging.getLogger("uvicorn.error")


class GroqModel(str, Enum):
    LLAMA3_7B: str = "llama3-8b-8192"
    LLAMA3_70B: str = "llama3-70b-8192"
    MIXTRAL_8X7b: str = "mixtral-8x7b-32768"


class GroqClient:
    def __init__(
        self,
        api_key: str,
        model: GroqModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = Groq(api_key=api_key)
        # Validate model
        model_card = self._client.models.retrieve(model)
        self.model = model
        self.temperature = temperature
        logger.info(
            f"Using Groq Cloud w/ {self.model} (created at {datetime.fromtimestamp(model_card.created).isoformat()})",  # type: ignore[arg-type]
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        # Prepare the request
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"
        stream = cast(
            Stream[ChatCompletionChunk],
            self._client.chat.completions.create(
                messages=(
                    {"role": "system", "content": _system},
                    *messages,  # type: ignore[arg-type]
                ),
                model=self.model,
                # Optional
                temperature=self.temperature,
                max_tokens=2048,
                top_p=1,
                stop=None,
                stream=True,
            ),
        )
        for chunk in stream:
            if isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.choices[0].finish_reason:
                logger.info(
                    f"Groq Cloud ({self.model}): {chunk.x_groq.usage.prompt_tokens} prompt tokens | {chunk.x_groq.usage.completion_tokens} completion tokens",  # type: ignore[union-attr]
                )
