# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List, Union, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_current_user, get_user_crud
from app.core.security import hash_password
from app.crud import UserCRUD
from app.models import User, UserScope
from app.schemas.users import Cred, CredHash, UserCreate, UserCreation
from app.services.github import gh_client
from app.services.slack import slack_client
from app.services.telemetry import telemetry_client

router = APIRouter()


async def _create_user(payload: UserCreate, users: UserCRUD, requester: Union[User, None] = None) -> User:
    # Check that user exists on GitHub
    gh_user = gh_client.get_user(payload.id)
    if gh_user["type"] != "User":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "GitHub account is expected to be a user")
    telemetry_client.identify(
        gh_user["id"],
        properties={
            "login": gh_user["login"],
            "name": gh_user["name"],
            "email": gh_user["email"],
            "twitter_username": gh_user["twitter_username"],
        },
    )
    # Create the entry
    user = await users.create(
        UserCreation(
            id=payload.id,
            login=gh_user["login"],
            hashed_password=await hash_password(payload.password),
            scope=payload.scope,
        )
    )
    # Assume the requester is the new user if none was specified
    telemetry_client.capture(
        requester.id if isinstance(requester, User) else user.id,
        event="user-creation",
        properties={"login": gh_user["login"]},
    )
    # Notify slack
    slack_client.notify(
        "*New user* :partying_face:",
        [
            ("Name", gh_user["name"]),
            ("Email", gh_user["email"]),
            ("Company", f"`{gh_user['company']}`"),
            ("GitHub", f"<{gh_user['html_url']}|{gh_user['login']}> ({gh_user['followers']} followers)"),
            ("Twitter", f"<https://twitter.com/{gh_user['twitter_username']}|{gh_user['twitter_username']}>"),
        ],
    )
    return user


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    users: UserCRUD = Depends(get_user_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    return await _create_user(payload, users, user)


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(user.id, event="user-get", properties={"user_id": user_id})
    return cast(User, await users.get(user_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK)
async def fetch_users(
    users: UserCRUD = Depends(get_user_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[User]:
    telemetry_client.capture(user.id, event="user-fetch")
    return [elt for elt in await users.fetch_all()]


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
async def update_user_password(
    payload: Cred,
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(user.id, event="user-pwd", properties={"user_id": user_id})
    pwd = await hash_password(payload.password)
    return await users.update(user_id, CredHash(hashed_password=pwd))


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    _: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    telemetry_client.capture(user_id, event="user-deletion", properties={"user_id": user_id})
    await users.delete(user_id)
