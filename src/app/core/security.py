# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

__all__ = ["create_access_token", "verify_password", "hash_password"]

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
