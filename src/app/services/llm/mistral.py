import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Union, cast
from mistralai.client import MistralClient as MistralAPIClient
from mistralai.models.chat_completion import ChatMessage
from .utils import CHAT_PROMPT

logger = logging.getLogger("uvicorn.error")

class MistralModel(str, Enum):
    Mixtral_8x7B = "open-mixtral-8x7b"
    Mixtral_8x225B = "open-mixtral-8x22b"
    Mistral_7B = "open-mistral-7b"
    Mistral_Large = "mistral-large-latest"
    Mistral_Small = "mistral-small-latest"

class MistralClient:
    def __init__(
        self,
        api_key: str,
        model: MistralModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = MistralAPIClient(api_key=api_key)
        # Validate model
        self.model = model
        self.temperature = temperature

        # Assuming there's a way to get model information
        model_card = self._client.models.get(model.value)
        logger.info(
            f"Using Mistral w/ {self.model} (created at {datetime.fromtimestamp(model_card.created).isoformat()})",
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"

        chat_messages = [ChatMessage(role="system", content=_system)]
        for message in messages:
            chat_messages.append(ChatMessage(role=message["role"], content=message["content"]))

        stream = self._client.chat(
            messages=chat_messages,
            model=self.model.value,
            temperature=self.temperature,
            max_tokens=2048,
            stream=True,
            top_p=1,
        )

        for chunk in stream:
            if len(chunk.choices) > 0 and isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.usage:
                logger.info(
                    f"Mistral ({self.model}): {chunk.usage.prompt_tokens} prompt tokens | {chunk.usage.completion_tokens} completion tokens",
                )
