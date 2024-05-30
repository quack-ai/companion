# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from enum import Enum
from typing import Dict, Generator, List, Union

from anthropic import BaseModel, Client

from .utils import CHAT_PROMPT

logger = logging.getLogger("uvicorn.error")


class ClaudeModel(str, Enum):
    OPUS: str = "claude-3-opus-20240229"
    SONNET: str = "claude-3-sonnet-20240229"
    HAIKU: str = "claude-3-haiku-20240307"


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: ClaudeModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = Client(api_key=api_key)
        self.model = model

        self._validate_model()

        self.temperature = temperature
        # model_card = BaseModel.retrieve(model)
        logger.info(
            f"Using Claude w/ {self.model} (created at "
            # {datetime.fromtimestamp(model_card.created).isoformat()})",
        )

    def _validate_model(self) -> None:
        input_dict = {"model_type": self.model}
        validation_result = BaseModel.model_validate(input_dict)
        if not validation_result:
            raise ValueError(f"Invalid model: {self.model}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        # Prepare the request
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"

        stream = self._client.messages.create(
            messages=[{"role": "user", "content": _system}, *messages],
            model=self.model,
            temperature=self.temperature,
            max_tokens=2048,
            stream=True,
            top_p=1.0,
        )

        for chunk in stream:
            if len(chunk.choices) > 0 and isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.usage:
                logger.info(
                    f"Claude ({self.model}): {chunk.usage.prompt_tokens} prompt tokens | {chunk.usage.completion_tokens} completion tokens",
                )
