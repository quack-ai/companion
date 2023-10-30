# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import json
import logging
from datetime import datetime
from typing import List

import requests
from fastapi import HTTPException, status

from app.core.config import settings
from app.models import Guideline
from app.schemas.compute import ComplianceResult
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

__all__ = ["openai_client"]


RESPONSE_SCHEMA = ObjectSchema(
    type="object",
    properties={
        "result": ArraySchema(
            type="array",
            items=ObjectSchema(
                type="object",
                properties={
                    "is_compliant": FieldSchema(
                        type="boolean", description="whether the guideline has been followed in the code snippet"
                    ),
                    "comment": FieldSchema(
                        type="string",
                        description="instruction to make the snippet compliant, addressed to the developer who wrote the code. Should be empty if the snippet is compliant",
                    ),
                    # "suggestion": FieldSchema(type="string", description="the modified code snippet that meets the guideline, with minimal modifications. Should be empty if the snippet is compliant"),
                },
                required=["is_compliant", "comment"],
            ),
        ),
    },
    required=["result"],
)


class OpenAIClient:
    ENDPOINT: str = "https://api.openai.com/v1/chat/completions"

    def __init__(
        self, api_key: str, model: OpenAIModel, temperature: float = 0.0, frequency_penalty: float = 1.0
    ) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        # Validate model
        model_card = requests.get(f"https://api.openai.com/v1/models/{model}", headers=self.headers, timeout=2)
        if model_card.status_code != 200:
            raise HTTPException(status_code=model_card.status_code, detail=model_card.json()["error"]["message"])
        self.model = model
        self.temperature = temperature
        self.frequency_penalty = frequency_penalty
        logger.info(
            f"Using OpenAI model: {self.model} (created at {datetime.fromtimestamp(model_card.json()['created']).isoformat()})"
        )

    def analyze_snippet(self, code: str, guidelines: List[Guideline], timeout: int = 10) -> List[ComplianceResult]:
        # Check args before sending a request
        if len(code) == 0 or len(guidelines) == 0 or any(len(guideline.details) == 0 for guideline in guidelines):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No code or guideline provided for analysis."
            )
        # Ideas: check which programming language & whether it's correct code
        # Prepare the request
        payload = ChatCompletion(
            model=self.model,
            messages=[
                OpenAIMessage(
                    role=OpenAIChatRole.SYSTEM,
                    content=(
                        "As a code compliance agent, you are going to receive requests from user with two elements: a code snippet, and a list of guidelines. "
                        "You should answer with a list of compliance results, one for each guideline (in the same order). "
                        "For a given compliance results, the comment should be an empty string if the code is compliant with the corresponding guideline."
                    ),
                ),
                OpenAIMessage(
                    role=OpenAIChatRole.USER,
                    content=json.dumps({"code": code, "guidelines": [guideline.details for guideline in guidelines]}),
                ),
            ],
            functions=[
                OpenAIFunction(
                    name="analyze_code",
                    description="Check code against a set of guidelines",
                    parameters=RESPONSE_SCHEMA,
                )
            ],
            function_call={"name": "analyze_code"},
            temperature=self.temperature,
            frequency_penalty=self.frequency_penalty,
        )
        # Send the request
        response = requests.post(self.ENDPOINT, json=payload.dict(), headers=self.headers, timeout=10)

        # Check status
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"]["message"])
        # Ideas: check the returned code can run
        parsed_response = json.loads(response.json()["choices"][0]["message"]["function_call"]["arguments"])["result"]
        if len(parsed_response) != len(guidelines):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Invalid model response")
        # Return with pydantic validation
        return [
            # ComplianceResult(is_compliant=res["is_compliant"], comment="" if res["is_compliant"] else res["comment"])
            ComplianceResult(guideline_id=guideline.id, **res)
            for guideline, res in zip(guidelines, parsed_response)
        ]


openai_client = OpenAIClient(settings.OPENAI_API_KEY, settings.OPENAI_MODEL)
