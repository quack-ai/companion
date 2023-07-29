# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_repo_crud
from app.crud import RepositoryCRUD
from app.models import Repository, User, UserScope
from app.schemas.repos import RepoCreate, RepoCreation, RepoUpdate

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_repo(
    payload: RepoCreate,
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    entry = await repos.get(payload.id, strict=False)
    # If repo exists, set it back to active
    if entry is not None:
        await repos.update(payload.id, RepoUpdate(removed_at=None))
        entry.removed_at = None
        return entry

    return await repos.create(RepoCreation(**payload.dict(), installed_by=user.id))


@router.get("/{repo_id}", status_code=status.HTTP_200_OK)
async def get_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    return cast(Repository, await repos.get(repo_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_repos(
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> List[Repository]:
    entries = await repos.fetch_all() if user.scope == UserScope.ADMIN else await repos.fetch_all(("owner_id", user.id))
    return [elt for elt in entries]


@router.put("/{repo_id}/disable", status_code=status.HTTP_200_OK)
async def disable_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    return await repos.update(repo_id, RepoUpdate(removed_at=datetime.utcnow()))


@router.put("/{repo_id}/enable", status_code=status.HTTP_200_OK)
async def enable_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    _=Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    return await repos.update(repo_id, RepoUpdate(removed_at=None))


@router.delete("/{repo_id}", status_code=status.HTTP_200_OK)
async def delete_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    await repos.delete(repo_id)
