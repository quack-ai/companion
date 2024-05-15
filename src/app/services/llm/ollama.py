# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from typing import Dict, Generator, List, Union

from ollama import Client

from .utils import CHAT_PROMPT

__all__ = ["OllamaClient"]

logger = logging.getLogger("uvicorn.error")


class OllamaClient:
    def __init__(self, endpoint: str, model: str, temperature: float = 0.0) -> None:
        self._client = Client(endpoint)
        # Validate model
        self._client.show(model)
        self.model = model
        self.temperature = temperature
        logger.info(f"Using Ollama w/ {self.model}")

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        # Prepare the request
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"
        stream = self._client.chat(
            messages=[
                {"role": "system", "content": _system},
                *messages,
            ],
            model=self.model,
            # Optional
            keep_alive="30s",
            options={"temperature": self.temperature},
            stream=True,
        )
        for chunk in stream:
            if isinstance(chunk["message"]["content"], str):
                yield chunk["message"]["content"]
            if chunk["done"]:
                logger.info(
                    f"Ollama ({self.model}): {chunk['prompt_eval_count']} prompt tokens | {chunk['eval_count']} completion tokens",
                )
