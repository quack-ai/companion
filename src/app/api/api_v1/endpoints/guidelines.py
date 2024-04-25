# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_guideline_crud, get_quack_jwt
from app.crud import GuidelineCRUD
from app.models import Guideline, UserScope
from app.schemas.guidelines import (
    ContentUpdate,
    GuidelineContent,
)
from app.schemas.login import TokenPayload
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Create a coding guideline")
async def create_guideline(
    payload: GuidelineContent,
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> Guideline:
    telemetry_client.capture(token_payload.sub, event="guideline-creation")
    return await guidelines.create(Guideline(creator_id=token_payload.sub, **payload.model_dump()))


@router.get("/{guideline_id}", status_code=status.HTTP_200_OK, summary="Read a specific guideline")
async def get_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> Guideline:
    telemetry_client.capture(token_payload.sub, event="guideline-get", properties={"guideline_id": guideline_id})
    return cast(Guideline, await guidelines.get(guideline_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all the guidelines")
async def fetch_guidelines(
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> List[Guideline]:
    telemetry_client.capture(token_payload.sub, event="guideline-fetch")
    filter_pair = ("creator_id", token_payload.sub) if UserScope.ADMIN not in token_payload.scopes else None
    return [elt for elt in await guidelines.fetch_all(filter_pair=filter_pair)]


@router.patch("/{guideline_id}", status_code=status.HTTP_200_OK, summary="Update a guideline content")
async def update_guideline_content(
    payload: GuidelineContent,
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> Guideline:
    telemetry_client.capture(
        token_payload.sub, event="guideline-update-content", properties={"guideline_id": guideline_id}
    )
    guideline = cast(Guideline, await guidelines.get(guideline_id, strict=True))
    if UserScope.ADMIN not in token_payload.scopes and token_payload.sub != guideline.creator_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions.")
    return await guidelines.update(guideline_id, ContentUpdate(**payload.model_dump()))


@router.delete("/{guideline_id}", status_code=status.HTTP_200_OK, summary="Delete a guideline")
async def delete_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> None:
    telemetry_client.capture(token_payload.sub, event="guideline-deletion", properties={"guideline_id": guideline_id})
    guideline = cast(Guideline, await guidelines.get(guideline_id, strict=True))
    if UserScope.ADMIN not in token_payload.scopes and token_payload.sub != guideline.creator_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions.")
    await guidelines.delete(guideline_id)


# @router.post("/parse", status_code=status.HTTP_200_OK, summary="Extract guidelines from a text corpus")
# async def parse_guidelines_from_text(
#     payload: TextContent,
#     user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
# ) -> List[GuidelineContent]:
#     telemetry_client.capture(user.id, event="guideline-parse")
#     # Analyze with LLM
#     return openai_client.parse_guidelines_from_text(payload.content, user_id=str(user.id))
#     # return ollama_client.parse_guidelines_from_text(payload.content)


# @router.post("/examples", status_code=status.HTTP_200_OK, summary="Request examples for a guideline")
# async def generate_examples_for_text(
#     payload: ExampleRequest,
#     user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
# ) -> GuidelineExample:
#     telemetry_client.capture(user.id, event="guideline-examples")
#     # Analyze with LLM
#     return openai_client.generate_examples_for_instruction(payload.content, payload.language, user_id=str(user.id))
#     # return ollama_client.generate_examples_for_instruction(payload.content, payload.language)
