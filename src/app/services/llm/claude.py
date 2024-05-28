import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Union
from anthropic import Client
from .utils import CHAT_PROMPT

class ClaudeModel(str, Enum):
    Opus: str = "claude-3-opus-20240229"
    Sonnet: str = "claude-3-sonnet-20240229"
    Haiku: str = "claude-3-haiku-20240307"


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: ClaudeModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = Client(api_key=api_key)
        # Validate model
        model_card = self._client.get_model_info(model)
        self.model = model
        self.temperature = temperature
        logger.info(
            f"Using Claude w/ {self.model} (created at {datetime.fromtimestamp(model_card.created).isoformat()})",
        )



    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        # Prepare the request
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"
        
        stream = cast(
            self._client.messages.create(
                messages=[
                {"role": "system", "content": _system}],
                model=self.model,
                temperature=self.temperature,
                max_tokens=2048,
                stream=True,
                # top_p=1,
                # stop=None,
                # stream=True,
                # stream_options={"include_usage": True},            
            )
        )
        for chunk in stream:
            if len(chunk.choices) > 0 and isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.usage:
                logger.info(
                    f"Claude ({self.model}): {chunk.usage.prompt_tokens} prompt tokens | {chunk.usage.completion_tokens} completion tokens",
                )
