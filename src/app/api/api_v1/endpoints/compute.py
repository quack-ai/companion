# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List, cast

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud, get_repo_crud
from app.crud import GuidelineCRUD, RepositoryCRUD
from app.models import Guideline, User, UserScope
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
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> List[ComplianceResult]:
    telemetry_client.capture(user.id, event="compute-analyze", properties={"repo_id": repo_id})
    # Check repo
    await repos.get(repo_id, strict=True)
    # Fetch guidelines
    guideline_list = [elt for elt in await guidelines.fetch_all(("repo_id", repo_id))]
    # Run analysis
    return openai_client.check_code_against_guidelines(
        payload.code, guideline_list, mode=ExecutionMode.MULTI, user_id=str(user.id)
    )


@router.post("/check/{guideline_id}", status_code=status.HTTP_200_OK)
async def check_code_against_guideline(
    payload: Snippet,
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> ComplianceResult:
    # Check repo
    guideline = cast(Guideline, await guidelines.get(guideline_id, strict=True))
    telemetry_client.capture(
        user.id, event="compute-check", properties={"repo_id": guideline.repo_id, "guideline_id": guideline_id}
    )
    # Run analysis
    return openai_client.check_code(payload.code, guideline, user_id=str(user.id))
