# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from fastapi import APIRouter, Depends, Security, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_guideline_crud, quack_token
from app.core.config import settings
from app.crud.crud_guideline import GuidelineCRUD
from app.models import UserScope
from app.schemas.code import ChatHistory
from app.schemas.login import TokenPayload
from app.services.llm.ollama import ollama_client
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/chat", status_code=status.HTTP_200_OK, summary="Chat with our code model")
async def chat(
    payload: ChatHistory,
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(quack_token, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> StreamingResponse:
    telemetry_client.capture(token_payload.user_id, event="compute-chat")
    # Retrieve the guidelines of this user
    user_guidelines = [g.content for g in await guidelines.fetch_all(filter_pair=("creator_id", token_payload.user_id))]
    # Run analysis
    return StreamingResponse(
        ollama_client.chat(
            payload.model_dump()["messages"], user_guidelines, timeout=settings.OLLAMA_TIMEOUT
        ).iter_content(chunk_size=8192),
        media_type="text/event-stream",
    )
