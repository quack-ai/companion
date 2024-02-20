# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Type, TypeVar, Union

import requests
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.models import Guideline
from app.schemas.code import ComplianceResult
from app.schemas.guidelines import GuidelineContent, GuidelineExample
from app.schemas.services import (
    ArraySchema,
    ChatCompletion,
    FieldSchema,
    ObjectSchema,
    OpenAIChatRole,
    OpenAIFunction,
    OpenAIMessage,
    OpenAIModel,
)

logger = logging.getLogger("uvicorn.error")

# __all__ = ["openai_client"]


class ExecutionMode(str, Enum):
    SINGLE = "single-thread"
    MULTI = "multi-thread"


MONO_SCHEMA = ObjectSchema(
    type="object",
    properties={
        "is_compliant": FieldSchema(
            type="boolean",
            description="whether the guideline has been followed in the code snippet",
        ),
        "comment": FieldSchema(
            type="string",
            description="short instruction to make the snippet compliant, addressed to the developer who wrote the code. Should be empty if the snippet is compliant",
        ),
        # "suggestion": FieldSchema(type="string", description="the modified code snippet that meets the guideline, with minimal modifications. Should be empty if the snippet is compliant"),
    },
    required=["is_compliant", "comment"],
)

MONO_PROMPT = (
    "As a code compliance agent, you are going to receive requests from user with two elements: a code snippet, and a guideline. "
    "You should answer in JSON format with an analysis result. The comment should be an empty string if the code is compliant with the guideline."
)


MULTI_SCHEMA = ObjectSchema(
    type="object",
    properties={
        "result": ArraySchema(
            type="array",
            items=ObjectSchema(
                type="object",
                properties={
                    "is_compliant": FieldSchema(
                        type="boolean",
                        description="whether the guideline has been followed in the code snippet",
                    ),
                    "comment": FieldSchema(
                        type="string",
                        description="short instruction to make the snippet compliant, addressed to the developer who wrote the code. Should be empty if the snippet is compliant",
                    ),
                    # "suggestion": FieldSchema(type="string", description="the modified code snippet that meets the guideline, with minimal modifications. Should be empty if the snippet is compliant"),
                },
                required=["is_compliant", "comment"],
            ),
        ),
    },
    required=["result"],
)

MULTI_PROMPT = (
    "As a code compliance agent, you are going to receive requests from user with two elements: a code snippet, and a list of guidelines. "
    "You should answer in JSON format with a list of compliance results, one for each guideline, no more, no less (in the same order). "
    "For a given compliance results, the comment should be an empty string if the code is compliant with the corresponding guideline."
)

PARSING_SCHEMA = ObjectSchema(
    type="object",
    properties={
        "result": ArraySchema(
            type="array",
            items=ObjectSchema(
                type="object",
                properties={
                    "source": FieldSchema(
                        type="string",
                        description="the text section the guideline was extracted from",
                    ),
                    "category": {
                        "type": "string",
                        "description": "the high-level category of the guideline",
                        "enum": [
                            "naming",
                            "error handling",
                            "syntax",
                            "comments",
                            "docstring",
                            "documentation",
                            "testing",
                            "signature",
                            "type hint",
                            "formatting",
                            "other",
                        ],
                    },
                    "details": FieldSchema(
                        type="string",
                        description="a descriptive, comprehensive, inambiguous and specific explanation of the guideline.",
                    ),
                    "title": FieldSchema(type="string", description="a summary title of the guideline"),
                    "examples": ObjectSchema(
                        type="object",
                        properties={
                            "positive": FieldSchema(
                                type="string",
                                description="a short code snippet where the guideline was correctly followed.",
                            ),
                            "negative": FieldSchema(
                                type="string",
                                description="the same snippet with minimal modification that invalidate the instruction.",
                            ),
                        },
                        required=["positive", "negative"],
                    ),
                },
                required=["category", "details", "title", "examples"],
            ),
        ),
    },
    required=["result"],
)

PARSING_PROMPT = (
    "You are responsible for summarizing the list of distinct coding guidelines for the company, by going through documentation. "
    "This list will be used by developers to avoid hesitations in code reviews and to onboard new members. "
    "Consider only guidelines that can be verified for a specific snippet of code (nothing about git, commits or community interactions) "
    "by a human developer without running additional commands or tools, it should only relate to the code within each file. "
    "Only include guidelines for which you could generate positive and negative code snippets, "
    "don't invent anything that isn't present in the input text or someone will die. "
    "You should answer in JSON format with only the list of string guidelines."
)

EXAMPLE_SCHEMA = ObjectSchema(
    type="object",
    properties={
        "positive": FieldSchema(
            type="string",
            description="a short code snippet where the instruction was correctly followed.",
        ),
        "negative": FieldSchema(
            type="string",
            description="the same snippet with minimal modification that invalidate the instruction.",
        ),
    },
    required=["positive", "negative"],
)

EXAMPLE_PROMPT = (
    "You are responsible for producing concise code snippets to illustrate the company coding guidelines. "
    "This will be used to teach new developers our way of engineering software. "
    "You should answer in JSON format with only two short code snippets in the specified programming language: one that follows the rule correctly, "
    "and a similar version with minimal modifications that violates the rule. "
    "Make sure your code is functional, don't extra comments or explanation, or someone will die."
)

ModelInp = TypeVar("ModelInp")


def validate_model(model: Type[ModelInp], data: Dict[str, Any]) -> Union[ModelInp, None]:
    try:
        return model(**data)
    except (ValidationError, TypeError):
        return None


class OpenAIClient:
    ENDPOINT: str = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self,
        api_key: str,
        model: OpenAIModel,
        temperature: float = 0.0,
        frequency_penalty: float = 1.0,
    ) -> None:
        self.headers = self._get_headers(api_key)
        # Validate model
        model_card = requests.get(f"https://api.openai.com/v1/models/{model}", headers=self.headers, timeout=5)
        if model_card.status_code != 200:
            raise HTTPException(status_code=model_card.status_code, detail=model_card.json()["error"]["message"])
        self.model = model
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        logger.info(
            f"Using OpenAI model: {self.model} (created at {datetime.fromtimestamp(model_card.json()['created']).isoformat()})",
        )

    @staticmethod
    def _get_headers(api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    def check_code_against_guidelines(
        self,
        code: str,
        guidelines: List[Guideline],
        mode: ExecutionMode = ExecutionMode.SINGLE,
        **kwargs,
    ) -> List[ComplianceResult]:
        # Check args before sending a request
        if len(code) == 0 or len(guidelines) == 0 or any(len(guideline.details) == 0 for guideline in guidelines):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No code or guideline provided for analysis.",
            )
        # Ideas: check which programming language & whether it's correct code
        if mode == ExecutionMode.SINGLE:
            parsed_response = self._analyze(
                MULTI_PROMPT,
                {"code": code, "guidelines": [guideline.details for guideline in guidelines]},
                MULTI_SCHEMA,
                **kwargs,
            )["result"]
            if len(parsed_response) != len(guidelines):
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid model response")
        elif mode == ExecutionMode.MULTI:
            with ThreadPoolExecutor() as executor:
                tasks = [
                    executor.submit(
                        self._analyze,
                        MONO_PROMPT,
                        {"code": code, "guideline": guideline.details},
                        MONO_SCHEMA,
                        **kwargs,
                    )
                    for guideline in guidelines
                ]
            # Collect results
            parsed_response = [task.result() for task in tasks]
        else:
            raise ValueError("invalid value for argument `mode`")

        # Return with pydantic validation
        return [
            # ComplianceResult(is_compliant=res["is_compliant"], comment="" if res["is_compliant"] else res["comment"])
            ComplianceResult(guideline_id=guideline.id, **res)
            for guideline, res in zip(guidelines, parsed_response)
        ]

    def check_code(self, code: str, guideline: Guideline, **kwargs) -> ComplianceResult:
        # Check args before sending a request
        if len(code) == 0 or len(guideline.details) == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No code or guideline provided for analysis.",
            )
        res = self._analyze(MONO_PROMPT, {"code": code, "guideline": guideline.details}, MONO_SCHEMA, **kwargs)
        # Return with pydantic validation
        return ComplianceResult(guideline_id=guideline.id, **res)

    def _request(
        self,
        system_prompt: str,
        openai_fn: OpenAIFunction,
        message: str,
        timeout: int = 20,
        model: Union[OpenAIModel, None] = None,
        user_id: Union[str, None] = None,
    ) -> Dict[str, Any]:
        # Prepare the request
        _payload = ChatCompletion(
            model=model or self.model,
            messages=[
                OpenAIMessage(
                    role=OpenAIChatRole.SYSTEM,
                    content=system_prompt,
                ),
                OpenAIMessage(
                    role=OpenAIChatRole.USER,
                    content=message,
                ),
            ],
            functions=[openai_fn],
            function_call={"name": openai_fn.name},
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
            user=user_id,
        )
        # Send the request
        response = requests.post(self.ENDPOINT, json=_payload.dict(), headers=self.headers, timeout=timeout)

        # Check status
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"]["message"])

        return json.loads(response.json()["choices"][0]["message"]["function_call"]["arguments"])

    def _analyze(
        self,
        prompt: str,
        payload: Dict[str, Any],
        schema: ObjectSchema,
        **kwargs,
    ) -> Dict[str, Any]:
        return self._request(
            prompt,
            OpenAIFunction(
                name="analyze_code",
                description="Analyze code",
                parameters=schema,
            ),
            json.dumps(payload),
            **kwargs,
        )

    def parse_guidelines_from_text(
        self,
        corpus: str,
        **kwargs,
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
            OpenAIFunction(
                name="validate_guidelines_from_text",
                description="Validate extracted coding guidelines from corpus",
                parameters=PARSING_SCHEMA,
            ),
            json.dumps(corpus),
            **kwargs,
        )
        guidelines = [validate_model(GuidelineContent, elt) for elt in response["result"]]
        if any(guideline is None for guideline in guidelines):
            logger.info("Validation errors on some guidelines")
        return [guideline for guideline in guidelines if guideline is not None]

    def generate_examples_for_instruction(
        self,
        instruction: str,
        language: str,
        **kwargs,
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
                OpenAIFunction(
                    name="generate_examples_from_instruction",
                    description="Generate code examples for a coding instruction",
                    parameters=EXAMPLE_SCHEMA,
                ),
                json.dumps({"instruction": instruction, "language": language}),
                **kwargs,
            )
        )


# openai_client = OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
