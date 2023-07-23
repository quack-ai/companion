# Copyright (C) 2023, Quack AI.

# This program is licensed under the Attribution-NonCommercial-ShareAlike 4.0 International.
# See LICENSE or go to <https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.txt> for full license details.

from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud
from app.crud import GuidelineCRUD
from app.models import Guideline, UserScope
from app.schemas.guidelines import GuidelineCreate, GuidelineEdit, GuidelineUpdate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_guideline(
    payload: GuidelineCreate,
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    return await guidelines.create(payload)


@router.get("/{guideline_id}", status_code=status.HTTP_200_OK)
async def get_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    return cast(Guideline, await guidelines.get(guideline_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_guidelines(
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[Guideline]:
    return [elt for elt in await guidelines.fetch_all()]


@router.get("/from/{repo_id}", status_code=status.HTTP_200_OK)
async def fetch_guidelines_from_repo(
    repo_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[Guideline]:
    return [elt for elt in await guidelines.fetch_all(("repo_id", repo_id))]


@router.put("/{guideline_id}", status_code=status.HTTP_200_OK)
async def update_guideline(
    payload: GuidelineEdit,
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    return await guidelines.update(guideline_id, GuidelineUpdate(**payload.dict(), updated_at=datetime.utcnow()))


@router.delete("/{guideline_id}", status_code=status.HTTP_200_OK)
async def delete_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> None:
    await guidelines.delete(guideline_id)
