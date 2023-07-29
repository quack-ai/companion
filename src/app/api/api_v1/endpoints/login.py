# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import secrets

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_user_crud
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.crud import UserCRUD
from app.models import UserScope
from app.schemas.login import GitHubToken, Token
from app.schemas.users import UserCreation

router = APIRouter()


@router.post("/creds", status_code=status.HTTP_200_OK, summary="Request an access token using credentials")
async def login_creds(
    form_data: OAuth2PasswordRequestForm = Depends(),
    users: UserCRUD = Depends(get_user_crud),
) -> Token:
    """This API follows the OAuth 2.0 specification.

    If the credentials are valid, creates a new access token.

    By default, the token expires after 1 hour.
    """
    # Verify credentials
    entry = await users.get_by_login(form_data.username)
    if entry is None or not await verify_password(form_data.password, entry.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    # create access token using user user_id/user_scopes
    token_data = {"sub": str(entry.id), "scopes": entry.scope.split()}
    token = await create_access_token(token_data, settings.ACCESS_TOKEN_UNLIMITED_MINUTES)

    return Token(access_token=token, token_type="bearer")  # nosec B106


@router.post("/token", status_code=status.HTTP_200_OK, summary="Request an access token using GitHub token")
async def login_token(
    payload: GitHubToken,
    users: UserCRUD = Depends(get_user_crud),
) -> Token:
    """This API follows the OAuth 2.0 specification.

    If the credentials are valid, creates a new access token.

    By default, the token expires after 1 hour.
    """
    # Fetch GitHub
    response = requests.get(
        "https://api.github.com/user",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {payload.github_token}"},
        timeout=5,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GitHub token.")
    gh_user = response.json()
    # Verify credentials
    user = await users.get(gh_user["id"], strict=False)
    # Register if non existing
    if user is None:
        user = await users.create(
            UserCreation(
                id=gh_user["id"],
                login=gh_user["login"],
                hashed_password=await hash_password(secrets.token_urlsafe(32)),
                scope=UserScope.USER,
            )
        )
    # create access token using user user_id/user_scopes
    token_data = {"sub": str(user.id), "scopes": user.scope.split()}
    token = await create_access_token(token_data, settings.ACCESS_TOKEN_UNLIMITED_MINUTES)

    return Token(access_token=token, token_type="bearer")  # nosec B106
