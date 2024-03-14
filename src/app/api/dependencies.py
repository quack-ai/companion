# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import cast

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt import DecodeError, ExpiredSignatureError, InvalidSignatureError
from jwt import decode as jwt_decode
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.crud import GuidelineCRUD, RepositoryCRUD, UserCRUD
from app.db import get_session
from app.models import User, UserScope
from app.schemas.login import TokenPayload

__all__ = ["get_current_user", "get_guideline_crud", "get_repo_crud", "get_token_payload", "get_user_crud"]

# Scope definition
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/creds",
    scopes={
        UserScope.ADMIN: "Admin rights on all routes.",
        UserScope.USER: "Read access on available information and write access on owned resources.",
    },
)


async def get_user_crud(session: AsyncSession = Depends(get_session)) -> UserCRUD:
    return UserCRUD(session=session)


async def get_repo_crud(session: AsyncSession = Depends(get_session)) -> RepositoryCRUD:
    return RepositoryCRUD(session=session)


async def get_guideline_crud(session: AsyncSession = Depends(get_session)) -> GuidelineCRUD:
    return GuidelineCRUD(session=session)


async def get_token_payload(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    """Dependency to use as fastapi.security.Security with scopes."""
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"

    try:
        payload = jwt_decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ENCODING_ALGORITHM])
    except (ExpiredSignatureError, InvalidSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": authenticate_value},
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid token.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    try:
        user_id = int(payload["sub"])
        token_scopes = payload.get("scopes", [])
        token_data = TokenPayload(user_id=user_id, scopes=token_scopes)
    except (KeyError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    if set(token_data.scopes).isdisjoint(security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incompatible token scope.",
            headers={"WWW-Authenticate": authenticate_value},
        )

    return token_data


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    users: UserCRUD = Depends(get_user_crud),
) -> User:
    """Dependency to use as fastapi.security.Security with scopes"""
    token_payload = await get_token_payload(security_scopes, token)
    return cast(User, await users.get(token_payload.user_id, strict=True))
