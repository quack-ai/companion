# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import HttpUrl

from app.api.api_v1.endpoints.users import _create_user
from app.api.dependencies import get_user_crud
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.crud import UserCRUD
from app.models import Provider, UserScope
from app.schemas.login import GHAccessToken, Token, TokenRequest
from app.schemas.services import GHToken
from app.schemas.users import UserCreate
from app.services.github import gh_client
from app.services.telemetry import telemetry_client

router = APIRouter()


@router.get("/authorize", summary="Request authorization code through GitHub OAuth app")
async def authorize_github(
    scope: str,
    redirect_uri: HttpUrl,
) -> RedirectResponse:
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?scope={scope}&client_id={settings.GH_OAUTH_ID}&redirect_uri={redirect_uri}"
    )


@router.post("/github", status_code=status.HTTP_200_OK, summary="Request a GitHub token from authorization code")
async def request_github_token_from_code(
    payload: TokenRequest,
) -> GHToken:
    return gh_client.get_token_from_code(payload.code, payload.redirect_uri)


@router.post("/creds", status_code=status.HTTP_200_OK, summary="Request an access token using credentials")
async def login_with_creds(
    form_data: OAuth2PasswordRequestForm = Depends(),
    users: UserCRUD = Depends(get_user_crud),
) -> Token:
    """This API follows the OAuth 2.0 specification.

    If the credentials are valid, creates a new access token.

    By default, the token expires after 1 hour.
    """
    # Verify credentials
    user = await users.get_by_login(form_data.username)
    if user is None or not await verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    telemetry_client.capture(user.id, event="user-login", properties={"method": "credentials"})
    # create access token using user user_id/user_scopes
    token_data = {"sub": str(user.id), "scopes": user.scope.split()}
    token = await create_access_token(token_data, settings.ACCESS_TOKEN_UNLIMITED_MINUTES)

    return Token(access_token=token, token_type="bearer")  # nosec B106  # noqa S106


@router.post("/token", status_code=status.HTTP_200_OK, summary="Request an access token using GitHub token")
async def login_with_github_token(
    payload: GHAccessToken,
    users: UserCRUD = Depends(get_user_crud),
) -> Token:
    """This API follows the OAuth 2.0 specification.

    If the credentials are valid, creates a new access token.

    By default, the token expires after 1 hour.
    """
    # Fetch GitHub
    gh_user = gh_client.get_my_user(payload.github_token)
    # Check that GH account is a user
    if gh_user["type"] != "User":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "GitHub account is expected to be a user")
    # Verify credentials
    user = await users.get_by("provider_user_id", f"{Provider.GITHUB}|{gh_user['id']}", strict=False)
    # Register if non existing
    if user is None:
        user = await _create_user(UserCreate(provider_user_id=gh_user["id"], scope=UserScope.USER), users)
    # If user is created, it needs to be identified & aliased before capture
    telemetry_client.capture(user.id, event="user-login", properties={"method": "provider|github"})

    # create access token using user user_id/user_scopes
    token_data = {"sub": str(user.id), "scopes": user.scope.split()}
    token = await create_access_token(token_data, settings.ACCESS_TOKEN_UNLIMITED_MINUTES)

    return Token(access_token=token, token_type="bearer")  # nosec B106  # noqa S106
