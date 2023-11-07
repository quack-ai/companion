# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud
from app.crud import GuidelineCRUD
from app.models import Guideline, UserScope
from app.schemas.guidelines import ContentUpdate, GuidelineCreate, GuidelineEdit, OrderUpdate
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_guideline(
    payload: GuidelineCreate,
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    telemetry_client.capture(user.id, event="guideline-creation", properties={"repo_id": payload.repo_id})
    return await guidelines.create(payload)


@router.get("/{guideline_id}", status_code=status.HTTP_200_OK)
async def get_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    guideline = cast(Guideline, await guidelines.get(guideline_id, strict=True))
    telemetry_client.capture(user.id, event="guideline-get", properties={"repo_id": guideline.repo_id})
    return guideline


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_guidelines(
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[Guideline]:
    telemetry_client.capture(user.id, event="guideline-fetch")
    return [elt for elt in await guidelines.fetch_all()]


@router.put("/{guideline_id}", status_code=status.HTTP_200_OK)
async def update_guideline_content(
    payload: GuidelineEdit,
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    guideline = await guidelines.update(guideline_id, ContentUpdate(**payload.dict(), updated_at=datetime.utcnow()))
    telemetry_client.capture(user.id, event="guideline-content", properties={"repo_id": guideline.repo_id})
    return guideline


@router.put("/{guideline_id}/order/{order_idx}", status_code=status.HTTP_200_OK)
async def update_guideline_order(
    guideline_id: int = Path(..., gt=0),
    order_idx: int = Path(..., gte=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Guideline:
    guideline = await guidelines.update(guideline_id, OrderUpdate(order=order_idx, updated_at=datetime.utcnow()))
    telemetry_client.capture(user.id, event="guideline-order", properties={"repo_id": guideline.repo_id})
    return guideline


@router.delete("/{guideline_id}", status_code=status.HTTP_200_OK)
async def delete_guideline(
    guideline_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> None:
    guideline = cast(Guideline, await guidelines.get(guideline_id, strict=True))
    telemetry_client.capture(user.id, event="guideline-deletion", properties={"repo_id": guideline.repo_id})
    await guidelines.delete(guideline_id)
