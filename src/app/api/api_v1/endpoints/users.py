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
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    users: UserCRUD = Depends(get_user_crud),
    _=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(payload.id, event="user-creation", properties={"login": payload.login})
    # Hash the password
    pwd = await hash_password(payload.password)

    user = await users.create(
        UserCreation(id=payload.id, login=payload.login, hashed_password=pwd, scope=payload.scope)
    )
    return user


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(user.id, event="user-get", properties={"user_id": user_id})
    return cast(User, await users.get(user_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_users(
    users: UserCRUD = Depends(get_user_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[User]:
    telemetry_client.capture(user.id, event="user-fetch")
    return [elt for elt in await users.fetch_all()]


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user_password(
    payload: Cred,
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(user.id, event="user-pwd", properties={"user_id": user_id})
    pwd = await hash_password(payload.password)
    return await users.update(user_id, CredHash(hashed_password=pwd))


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    user=Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    telemetry_client.capture(user_id, event="user-deletion", properties={"user_id": user_id})
    await users.delete(user_id)
