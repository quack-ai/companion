# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

from datetime import datetime, timedelta, UTC
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

from app.core.config import settings

__all__ = ["create_access_token", "hash_password", "verify_password"]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(content: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Encode content dict using security algorithm, setting expiration."""
    expire_delta = timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    expire = datetime.now(UTC) + expire_delta
    return jwt.encode({**content, "exp": expire}, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
