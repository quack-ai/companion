# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import json
import logging
import re
from typing import Dict, Generator, List, TypeVar, Union

from fastapi import HTTPException, status
from ollama import Client

logger = logging.getLogger("uvicorn.error")

ValidationOut = TypeVar("ValidationOut")


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

GUIDELINE_PROMPT = (
    "When answering user requests, you should at all times keep in mind the following software development guidelines:"
)


def validate_parsing_response(response: str) -> List[Dict[str, str]]:
    guideline_list = json.loads(response.strip())
    if not isinstance(guideline_list, list) or any(
        not isinstance(val, str) for guideline in guideline_list for val in guideline.values()
    ):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed output schema validation")

    return json.loads(response.strip())


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
