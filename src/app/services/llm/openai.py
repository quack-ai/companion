# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Union, cast

from openai import OpenAI, Stream
from openai.types.chat import ChatCompletionChunk

from .utils import CHAT_PROMPT

logger = logging.getLogger("uvicorn.error")


class OpenAIModel(str, Enum):
    # https://platform.openai.com/docs/models/overview
    GPT4o: str = "gpt-4o-2024-05-13"
    GPT3_5: str = "gpt-3.5-turbo-0125"


class OpenAIClient:
    def __init__(
        self,
        api_key: str,
        model: OpenAIModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = OpenAI(api_key=api_key)
        # Validate model
        model_card = self._client.models.retrieve(model)
        self.model = model
        self.temperature = temperature
        logger.info(
            f"Using OpenAI w/ {self.model} (created at {datetime.fromtimestamp(model_card.created).isoformat()})",
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
            self._client.chat.completions.create(  # type: ignore[call-overload]
                messages=(
                    {"role": "system", "content": _system},
                    *messages,
                ),
                model=self.model,
                # Optional
                temperature=self.temperature,
                max_tokens=2048,
                top_p=1,
                stop=None,
                stream=True,
                stream_options={"include_usage": True},
            ),
        )
        for chunk in stream:
            if len(chunk.choices) > 0 and isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.usage:
                logger.info(
                    f"OpenAI ({self.model}): {chunk.usage.prompt_tokens} prompt tokens | {chunk.usage.completion_tokens} completion tokens",
                )
