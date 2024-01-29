# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

__all__ = ["create_access_token", "hash_password", "verify_password"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_access_token(content: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Encode content dict using security algorithm, setting expiration."""
    expire_delta = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expire_delta
    return jwt.encode({**content, "exp": expire}, settings.SECRET_KEY, algorithm=settings.JWT_ENCODING_ALGORITHM)


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def hash_password(password: str) -> str:
    return pwd_context.hash(password)
