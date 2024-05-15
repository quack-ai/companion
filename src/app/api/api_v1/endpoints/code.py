# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.responses import StreamingResponse

from app.api.dependencies import get_guideline_crud, get_quack_jwt
from app.crud.crud_guideline import GuidelineCRUD
from app.models import UserScope
from app.schemas.code import ChatHistory
from app.schemas.login import TokenPayload
from app.services.llm.llm import llm_client
from app.services.telemetry import telemetry_client

router = APIRouter()


GUIDELINE_PROMPT = (
    "When answering user requests, you should at all times keep in mind the following software development guidelines:"
)


@router.post("/chat", status_code=status.HTTP_200_OK, summary="Chat with our code model")
async def chat(
    payload: ChatHistory,
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    token_payload: TokenPayload = Security(get_quack_jwt, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> StreamingResponse:
    telemetry_client.capture(token_payload.sub, event="code-chat")
    # Validate payload
    if len(payload.messages) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Expected a non-empty list of messages.",
        )
    # Retrieve the guidelines of this user
    user_guidelines = [g.content for g in await guidelines.fetch_all(filter_pair=("creator_id", token_payload.sub))]
    _guideline_str = "\n-".join(user_guidelines)
    _system = "" if len(user_guidelines) == 0 else f"{GUIDELINE_PROMPT}\n-{_guideline_str}"
    # Run the request
    return StreamingResponse(
        llm_client.chat(payload.model_dump()["messages"], _system),
        media_type="text/event-stream",
    )
