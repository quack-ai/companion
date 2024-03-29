# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import List, Union, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_token_payload, get_user_crud
from app.core.security import hash_password
from app.crud import UserCRUD
from app.models import Provider, User, UserScope
from app.schemas.login import TokenPayload
from app.schemas.users import Cred, CredHash, UserCreate
from app.services.github import gh_client
from app.services.notifications.slack import slack_client
from app.services.telemetry import telemetry_client

router = APIRouter()


async def _create_user(payload: UserCreate, users: UserCRUD, requester_id: Union[int, None] = None) -> User:
    valid_creds = False
    user_props = {"login": payload.login, "provider_login": None, "name": None, "twitter_username": None}
    notif_info = []
    # Provider check
    if payload.provider_user_id is not None:
        # Check that user exists on GitHub
        gh_user = gh_client.get_user(payload.provider_user_id)
        if gh_user["type"] != "User":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "GitHub account is expected to be a user.")
        # Unicity check
        if (await users.get_by("provider_user_id", payload.provider_user_id, strict=False)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "User already registered")
        valid_creds = True
        user_props.update({
            "provider_login": f"{Provider.GITHUB}|{gh_user['login']}",
            "name": gh_user["name"],
            "twitter_username": gh_user["twitter_username"],
        })
        # Notif
        notif_info = [
            ("Name", gh_user["name"] or "N/A"),
            ("Email", gh_user["email"] or "N/A"),
            ("Company", f"`{gh_user['company']}`" if gh_user["company"] else "N/A"),
            ("GitHub", f"<{gh_user['html_url']}|{gh_user['login']}> ({gh_user['followers']} followers)"),
            (
                "Twitter",
                f"<https://twitter.com/{gh_user['twitter_username']}|{gh_user['twitter_username']}>"
                if gh_user["twitter_username"]
                else "N/A",
            ),
        ]
        # Remove N/A
        notif_info = [(k, v) for k, v in notif_info if v != "N/A"]

    # Creds check
    hashed_password = None
    if payload.login is not None or payload.password is not None:
        # Check both are filled
        if payload.login is None or payload.password is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Login or password need to be specified together")
        # Check for unicity
        if (await users.get_by_login(payload.login, strict=False)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Login already taken")
        valid_creds = True
        hashed_password = await hash_password(payload.password)

    if not valid_creds:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "You need to provide either provider_user_id, or login and password.",
        )

    # Create the entry
    user = await users.create(
        User(
            login=payload.login,
            hashed_password=hashed_password,
            scope=payload.scope,
            provider_user_id=payload.provider_user_id,
        )
    )

    # Enrich user data
    telemetry_client.identify(user.id, properties=user_props)
    if isinstance(payload.provider_user_id, int):
        telemetry_client.alias(user.id, f"{Provider.GITHUB}|{payload.provider_user_id}")

    # Assume the requester is the new user if none was specified
    telemetry_client.capture(
        requester_id if isinstance(requester_id, int) else user.id,
        event="user-creation",
        properties={"created_user_id": user.id},
    )
    # Notify slack
    slack_client.notify("*New user* :partying_face:", notif_info)
    return user


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a new user")
async def create_user(
    payload: UserCreate,
    users: UserCRUD = Depends(get_user_crud),
    token_payload: TokenPayload = Security(get_token_payload, scopes=[UserScope.ADMIN]),
) -> User:
    return await _create_user(payload, users, token_payload.user_id)


@router.get("/{user_id}", status_code=status.HTTP_200_OK, summary="Fetch the information of a specific user")
async def get_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    token_payload: TokenPayload = Security(get_token_payload, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(token_payload.user_id, event="user-get", properties={"user_id": user_id})
    return cast(User, await users.get(user_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all the users")
async def fetch_users(
    users: UserCRUD = Depends(get_user_crud),
    token_payload: TokenPayload = Security(get_token_payload, scopes=[UserScope.ADMIN]),
) -> List[User]:
    telemetry_client.capture(token_payload.user_id, event="user-fetch")
    return [elt for elt in await users.fetch_all()]


@router.patch("/{user_id}", status_code=status.HTTP_200_OK, summary="Updates a user's password")
async def update_user_password(
    payload: Cred,
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    token_payload: TokenPayload = Security(get_token_payload, scopes=[UserScope.ADMIN]),
) -> User:
    telemetry_client.capture(token_payload.user_id, event="user-pwd", properties={"user_id": user_id})
    pwd = await hash_password(payload.password)
    return await users.update(user_id, CredHash(hashed_password=pwd))


@router.delete("/{user_id}", status_code=status.HTTP_200_OK, summary="Delete a user")
async def delete_user(
    user_id: int = Path(..., gt=0),
    users: UserCRUD = Depends(get_user_crud),
    token_payload: TokenPayload = Security(get_token_payload, scopes=[UserScope.ADMIN]),
) -> None:
    telemetry_client.capture(token_payload.user_id, event="user-deletion", properties={"user_id": user_id})
    await users.delete(user_id)
