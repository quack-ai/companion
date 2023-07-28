# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import List, cast

from fastapi import APIRouter, Depends, Path, Security, status

from app.api.dependencies import get_current_user, get_user_crud
from app.core.security import hash_password
from app.crud import UserCRUD
from app.models import User, UserScope
from app.schemas.users import Cred, CredHash, UserCreate, UserCreation

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    # Hash the password
    pwd = await hash_password(payload.password)

    return await users.create(
        UserCreation(id=payload.id, login=payload.login, hashed_password=pwd, scope=payload.scope)
    )


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    return cast(User, await users.get(user_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_users(
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[User]:
    return [elt for elt in await users.fetch_all()]


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user_password(
    payload: Cred,
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    pwd = await hash_password(payload.password)
    return await users.update(user_id, CredHash(hashed_password=pwd))


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    await users.delete(user_id)
