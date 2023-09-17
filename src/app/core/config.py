# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import os
import secrets
from typing import Optional

from pydantic import BaseSettings, validator

__all__ = ["settings"]


class Settings(BaseSettings):
    # State
    PROJECT_NAME: str = "Contribution guideline API"
    PROJECT_DESCRIPTION: str = "API for contribution guideline curation"
    VERSION: str = "0.1.0.dev0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGIN: str = "*"
    # Ext API endpoints
    GH_AUTHORIZE_ENDPOINT: str = "https://github.com/login/oauth/authorize"
    GH_TOKEN_ENDPOINT: str = "https://github.com/login/oauth/access_token"
    GH_OAUTH_ID: str = os.environ["GH_OAUTH_ID"]
    GH_OAUTH_SECRET: str = os.environ["GH_OAUTH_SECRET"]
    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ACCESS_TOKEN_UNLIMITED_MINUTES: int = 60 * 24 * 365
    JWT_ENCODING_ALGORITHM: str = "HS256"
    # DB
    POSTGRES_URL: str = os.environ["POSTGRES_URL"]
    SUPERUSER_LOGIN: str = os.environ["SUPERUSER_LOGIN"]
    SUPERUSER_ID: int = int(os.environ["SUPERUSER_ID"])
    SUPERUSER_PWD: str = os.environ["SUPERUSER_PWD"]

    @validator("POSTGRES_URL", pre=True)
    @classmethod
    def sqlachmey_uri(cls, v: str) -> str:
        # Fix for SqlAlchemy 1.4+
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    SENTRY_DSN: Optional[str] = os.environ.get("SENTRY_DSN")
    SERVER_NAME: str = os.environ["SERVER_NAME"]

    @validator("SENTRY_DSN", pre=True)
    @classmethod
    def sentry_dsn_can_be_blank(cls, v: str) -> Optional[str]:
        if not isinstance(v, str) or len(v) == 0:
            return None
        return v

    POSTHOG_KEY: Optional[str] = os.environ.get("POSTHOG_KEY")

    @validator("POSTHOG_KEY", pre=True)
    @classmethod
    def posthog_key_can_be_blank(cls, v: str) -> Optional[str]:
        if not isinstance(v, str) or len(v) == 0:
            return None
        return v

    DEBUG: bool = os.environ.get("DEBUG", "").lower() != "false"
    LOGO_URL: str = ""

    class Config:
        case_sensitive = True


settings = Settings()
