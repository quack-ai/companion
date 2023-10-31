# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import List

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud, get_repo_crud
from app.crud import GuidelineCRUD, RepositoryCRUD
from app.models import UserScope
from app.schemas.compute import ComplianceResult, Snippet
from app.services.openai import ExecutionMode, openai_client
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/analyze/{repo_id}", status_code=status.HTTP_200_OK)
async def check_code_against_repo_guidelines(
    payload: Snippet,
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> List[ComplianceResult]:
    telemetry_client.capture(user.id, event="compute-analyze", properties={"repo_id": repo_id})
    # Check repo
    await repos.get(repo_id, strict=True)
    # Fetch guidelines
    guideline_list = [elt for elt in await guidelines.fetch_all(("repo_id", repo_id))]
    # Run analysis
    return openai_client.analyze_multi(payload.code, guideline_list, mode=ExecutionMode.MULTI)


@router.post("/check/{guideline_id}", status_code=status.HTTP_200_OK)
async def check_code_against_guideline(
    payload: Snippet,
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> ComplianceResult:
    # Check repo
    guideline = await guidelines.get(guideline_id, strict=True)
    telemetry_client.capture(
        user.id, event="compute-check", properties={"repo_id": guideline.repo_id, "guideline_id": guideline_id}
    )
    # Run analysis
    return openai_client.analyze_mono(payload.code, guideline)
