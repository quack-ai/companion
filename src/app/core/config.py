# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import os
import secrets
import socket
from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

__all__ = ["settings"]


class Settings(BaseSettings):
    # State
    PROJECT_NAME: str = "Quack API - Guideline curation"
    PROJECT_DESCRIPTION: str = "Your cohesive framework of seamless sharing and understanding of team expectations."
    VERSION: str = "0.1.0.dev0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGIN: str = "*"
    SUPPORT_EMAIL: Union[str, None] = os.environ.get("SUPPORT_EMAIL")
    # Authentication
    SUPERADMIN_GH_PAT: str = os.environ["SUPERADMIN_GH_PAT"]
    SUPERADMIN_LOGIN: str = os.environ["SUPERADMIN_LOGIN"]
    SUPERADMIN_PWD: str = os.environ["SUPERADMIN_PWD"]
    GH_OAUTH_ID: str = os.environ["GH_OAUTH_ID"]
    GH_OAUTH_SECRET: str = os.environ["GH_OAUTH_SECRET"]
    GH_TOKEN: Union[str, None] = os.environ.get("GH_TOKEN")
    # DB
    POSTGRES_URL: str = os.environ["POSTGRES_URL"]

    @field_validator("POSTGRES_URL")
    @classmethod
    def sqlachmey_uri(cls, v: str) -> str:
        # Fix for SqlAlchemy 1.4+
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v

    # Security
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ACCESS_TOKEN_UNLIMITED_MINUTES: int = 60 * 24 * 365
    JWT_ENCODING_ALGORITHM: str = "HS256"
    # LLM Compute
    OLLAMA_ENDPOINT: str = os.environ["OLLAMA_ENDPOINT"]
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "dolphin-mistral:7b-v2.6-dpo-laser-q4_0")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", 60))
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0.0))

    # Error monitoring
    SENTRY_DSN: Union[str, None] = os.environ.get("SENTRY_DSN")
    SERVER_NAME: str = os.environ.get("SERVER_NAME", socket.gethostname())

    @field_validator("SENTRY_DSN")
    @classmethod
    def sentry_dsn_can_be_blank(cls, v: str) -> Union[str, None]:
        if not isinstance(v, str) or len(v) == 0:
            return None
        return v

    # Product analytics
    POSTHOG_KEY: Union[str, None] = os.environ.get("POSTHOG_KEY")

    @field_validator("POSTHOG_KEY")
    @classmethod
    def posthog_key_can_be_blank(cls, v: str) -> Union[str, None]:
        if not isinstance(v, str) or len(v) == 0:
            return None
        return v

    # Event notifications
    SLACK_API_TOKEN: Union[str, None] = os.environ.get("SLACK_API_TOKEN")
    SLACK_CHANNEL: str = os.environ.get("SLACK_CHANNEL", "#general")

    @field_validator("SLACK_API_TOKEN")
    @classmethod
    def slack_token_can_be_blank(cls, v: str) -> Union[str, None]:
        if not isinstance(v, str) or len(v) == 0:
            return None
        return v

    DEBUG: bool = os.environ.get("DEBUG", "").lower() != "false"
    LOGO_URL: str = ""
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "").lower() == "true"

    model_config = SettingsConfigDict(case_sensitive=True)


settings = Settings()
