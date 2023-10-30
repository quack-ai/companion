# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import List

from fastapi import APIRouter, Depends, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud, get_repo_crud
from app.crud import GuidelineCRUD, RepositoryCRUD
from app.models import UserScope
from app.schemas.compute import ComplianceResult, Snippet
from app.services.openai import openai_client
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_snippet(
    payload: Snippet,
    repos: RepositoryCRUD = Depends(get_repo_crud),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> List[ComplianceResult]:
    telemetry_client.capture(user.id, event="snippet-analysis", properties={"repo_id": payload.repo_id})
    # Check repo
    await repos.get(payload.repo_id, strict=True)
    # Fetch guidelines
    guideline_list = [elt for elt in await guidelines.fetch_all(("repo_id", payload.repo_id))]
    # Run analysis
    return openai_client.analyze_snippet(payload.code, guideline_list)
