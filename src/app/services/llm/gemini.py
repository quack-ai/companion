import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Generator, List, Union
import google.generativeai as genai
from .utils import CHAT_PROMPT

class GeminiModel(str, Enum):
    GeminiPro_1_5_Pro: str = "gemini-1.5-pro-latest"
    Gemini_1_5_Flash: str = "gemini-1.5-flash-latest"
    Gemini_1_0_Pro: str = "gemini-1.0-pro"

class GeminiClient:
    def __init__(
        self,
        api_key: str,
        model: GeminiModel,
        temperature: float = 0.0,
    ) -> None:
        self._client = genai.configure(api_key=api_key)
        # Validate model
        model_card = self.genai.list_models()
        for model in model_card:
            if self.model == model.supported_generation_methods:
                self.model = model
                self.temperature = temperature
                logger.info(
                    f"Using Gemini w/ {self.model} (created at {datetime.fromtimestamp(model_card.created).isoformat()})",
                )

    def chat(
        self,
        messages: List[Dict[str, str]],
        system: Union[str, None] = None,
    ) -> Generator[str, None, None]:
        # Prepare the request
        _system = CHAT_PROMPT if not system else f"{CHAT_PROMPT} {system}"
        
        stream = cast(
            self.genai.generate_content(   #####
            messages = [
                {'role':'user',
                'content':_system}
            ],
                model_name=self.model,
                temperature=self.temperature,
                max_output_tokens=2048,
                topP=1,
            )
        )
        for chunk in stream:
            if len(chunk.choices) > 0 and isinstance(chunk.choices[0].delta.content, str):
                yield chunk.choices[0].delta.content
            if chunk.usage:
                logger.info(
                    f"Gemini ({self.model}): {chunk.usage.prompt_tokens} prompt tokens | {chunk.usage.completion_tokens} completion tokens",
                )
