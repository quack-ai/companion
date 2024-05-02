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
    PROJECT_NAME: str = "Quack Companion API - Type smarter, ship faster"
    PROJECT_DESCRIPTION: str = "Leverage team insights with a cohesive framework to code efficiently."
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
    JWT_SECRET: str = os.environ.get("JWT_SECRET", secrets.token_urlsafe(32))
    JWT_EXPIRE_MINUTES: int = 60
    JWT_UNLIMITED: int = 60 * 24 * 365
    JWT_ALGORITHM: str = "HS256"
    # LLM
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "ollama")
    LLM_TEMPERATURE: float = float(os.environ.get("LLM_TEMPERATURE") or 0)
    OLLAMA_ENDPOINT: Union[str, None] = os.environ.get("OLLAMA_ENDPOINT")
    OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "dolphin-llama3:8b-v2.9-q4_K_M")
    GROQ_API_KEY: Union[str, None] = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL: str = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
    OPENAI_API_KEY: Union[str, None] = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4-turbo-2024-04-09")

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
    POSTHOG_HOST: str = os.getenv("POSTHOG_HOST", "https://eu.posthog.com")
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
