# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import json
import logging
import re
from typing import Callable, Dict, List, TypeVar

import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.guidelines import GuidelineContent, GuidelineExample

logger = logging.getLogger("uvicorn.error")

ValidationOut = TypeVar("ValidationOut")
__all__ = ["ollama_client"]


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


PARSING_PROMPT = (
    "You are responsible for summarizing the list of distinct coding guidelines for the company, by going through documentation. "
    "This list will be used by developers to avoid hesitations in code reviews and to onboard new members. "
    "Consider only guidelines that can be verified for a specific snippet of code (nothing about git, commits or community interactions) "
    "by a human developer without running additional commands or tools, it should only relate to the code within each file. "
    "Only include guidelines for which you could generate positive and negative code snippets, "
    "don't invent anything that isn't present in the input text.\n"
    # Format
    "You should answer with a list of JSON dictionaries, one dictionary per guideline, where each dictionary has two keys with string values:\n"
    "- title: a short summary title of the guideline\n"
    "- details: a descriptive, comprehensive and inambiguous explanation of the guideline."
)
PARSING_PATTERN = r"\{\s*\"title\":\s+\"(?P<title>.*?)\",\s+\"details\":\s+\"(?P<details>.*?)\"\s*\}"


CHAT_PROMPT = (
    "You are an AI programming assistant, developed by the company Quack AI, and you only answer questions related to computer science "
    "(refuse to answer for the rest)."
)


def validate_parsing_response(response: str) -> List[Dict[str, str]]:
    guideline_list = json.loads(response.strip())
    if not isinstance(guideline_list, list) or any(
        not isinstance(val, str) for guideline in guideline_list for val in guideline.values()
    ):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed output schema validation")

    return json.loads(response.strip())


class OllamaClient:
    def __init__(self, endpoint: str, model_name: str, temperature: float = 0.0) -> None:
        self.endpoint = endpoint
        # Check endpoint
        response = requests.get(f"{self.endpoint}/api/tags", timeout=2)
        if response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_404, detail="Unavailable endpoint")
        # Pull model
        logger.info("Loading Ollama model...")
        response = requests.post(f"{self.endpoint}/api/pull", json={"name": model_name, "stream": False}, timeout=10)
        if response.status_code != 200 or response.json()["status"] != "success":
            raise HTTPException(status_code=status.HTTP_404, detail="Unavailable model")
        self.temperature = temperature
        self.model_name = model_name
        logger.info(f"Using Ollama model: {self.model_name}")

    def _request(
        self,
        system_prompt: str,
        message: str,
        validate_fn: Callable[[str], ValidationOut],
        timeout: int = 20,
    ) -> ValidationOut:
        # Send the request
        response = requests.post(
            f"{self.endpoint}/api/generate",
            json={
                "model": self.model_name,
                "stream": False,
                "options": {"temperature": self.temperature},
                "system": system_prompt,
                "prompt": message,
                "format": "json",
            },
            timeout=timeout,
        )

        # Check status
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"])

        # Regex to locate JSON string
        logger.info(response.json()["response"].strip())
        return validate_fn(response.json()["response"])

    def _chat(
        self,
        system_prompt: str,
        message: str,
        timeout: int = 20,
    ) -> requests.Response:
        return requests.post(
            f"{self.endpoint}/api/chat",
            json={
                "model": self.model_name,
                "stream": True,
                "options": {"temperature": self.temperature},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
            },
            stream=True,
            timeout=timeout,
        )

    def chat(
        self,
        message: str,
        **kwargs,
    ) -> requests.Response:
        return self._chat(CHAT_PROMPT, message, **kwargs)

    def parse_guidelines_from_text(
        self,
        corpus: str,
        timeout: int = 20,
    ) -> List[GuidelineContent]:
        if not isinstance(corpus, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The input corpus needs to be a string.",
            )
        if len(corpus) == 0:
            return []

        response = self._request(
            PARSING_PROMPT,
            json.dumps(corpus),
            validate_parsing_response,
            timeout,
        )

        return [GuidelineContent(**elt) for elt in response]

    def generate_examples_for_instruction(
        self,
        instruction: str,
        language: str,
        timeout: int = 20,
    ) -> GuidelineExample:
        if (
            not isinstance(instruction, str)
            or len(instruction) == 0
            or not isinstance(language, str)
            or len(language) == 0
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="The instruction and language need to be non-empty strings.",
            )

        return GuidelineExample(
            **self._request(
                EXAMPLE_PROMPT,
                json.dumps({"guideline": instruction, "language": language}),
                validate_example_response,
                timeout,
            ),
        )


ollama_client = OllamaClient(settings.OLLAMA_ENDPOINT, settings.OLLAMA_MODEL)
