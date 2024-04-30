# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from typing import Dict, Type, TypeVar, Union, cast

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
from app.services.auth.supabase import SupaJWT

JWTTemplate = TypeVar("JWTTemplate")

__all__ = ["get_guideline_crud", "get_repo_crud", "get_user_crud"]

# Scope definition
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/creds",
    scopes={
        UserScope.ADMIN: "Admin rights on all routes.",
        UserScope.USER: "Read access on available information and write access on owned resources.",
    },
)


def get_user_crud(session: AsyncSession = Depends(get_session)) -> UserCRUD:
    return UserCRUD(session=session)


def get_repo_crud(session: AsyncSession = Depends(get_session)) -> RepositoryCRUD:
    return RepositoryCRUD(session=session)


def get_guideline_crud(session: AsyncSession = Depends(get_session)) -> GuidelineCRUD:
    return GuidelineCRUD(session=session)


def decode_token(token: str, authenticate_value: Union[str, None] = None) -> Dict[str, str]:
    try:
        payload = jwt_decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except (ExpiredSignatureError, InvalidSignatureError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": authenticate_value} if authenticate_value else None,
        )
    except DecodeError:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Invalid token.",
            headers={"WWW-Authenticate": authenticate_value} if authenticate_value else None,
        )
    return payload


def process_token(
    token: str, jwt_template: Type[JWTTemplate], authenticate_value: Union[str, None] = None
) -> JWTTemplate:
    payload = decode_token(token)
    # Verify the JWT template
    try:
        return jwt_template(**payload)
    except ValidationError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid token payload.",
            headers={"WWW-Authenticate": authenticate_value} if authenticate_value else None,
        )


def get_supa_jwt(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> SupaJWT:
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    jwt_payload = process_token(token, SupaJWT, authenticate_value=authenticate_value)
    # Retrieve the actual role
    if set(jwt_payload.user_metadata.quack_role).isdisjoint(security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incompatible token scope.",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return jwt_payload


def get_quack_jwt(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
) -> TokenPayload:
    authenticate_value = f'Bearer scope="{security_scopes.scope_str}"' if security_scopes.scopes else "Bearer"
    jwt_payload = process_token(token, TokenPayload)
    if set(jwt_payload.scopes).isdisjoint(security_scopes.scopes):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Incompatible token scope.",
            headers={"WWW-Authenticate": authenticate_value},
        )
    return jwt_payload


async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    users: UserCRUD = Depends(get_user_crud),
) -> User:
    """Dependency to use as fastapi.security.Security with scopes"""
    token_payload = get_quack_jwt(security_scopes, token)
    return cast(User, await users.get(token_payload.sub, strict=True))
