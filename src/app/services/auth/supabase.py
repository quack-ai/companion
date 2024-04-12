# Copyright (C) 2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from enum import Enum
from typing import Dict, List, Union
from urllib.parse import urljoin

import jwt
import requests
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

__all__ = ["supabase_client"]


class Login(BaseModel):
    email: str
    password: str


class OauthProvider(str, Enum):
    GITHUB: str = "github"
    GOOGLE: str = "google"
    TWITTER: str = "twitter"


class Provider(OauthProvider):
    EMAIL: str = "email"


class OIDCProvider(str, Enum):
    GOOGLE: str = "google"
    APPLE: str = "apple"
    AZURE: str = "azure"
    FACEBOOK: str = "facebook"


class IDToken(BaseModel):
    provider: OIDCProvider
    id_token: str


class AppMetaData(BaseModel):
    provider: str
    providers: List[str]


class UserRole(str, Enum):
    ADMIN: str = "admin"
    USER: str = "user"


class UserMetaData(BaseModel):
    quack_role: UserRole = UserRole.USER
    sub: Union[str, None] = None
    user_name: Union[str, None] = None
    full_name: Union[str, None] = None
    iss: Union[str, None] = None


class SupaJWT(BaseModel):
    sub: str
    email: str
    iat: int
    exp: int
    app_metadata: AppMetaData
    user_metadata: UserMetaData


class SupaUser(BaseModel):
    id: str
    email: str
    created_at: str
    updated_at: str
    # Check providers to see connected Oauth
    app_metadata: AppMetaData
    # Check username and sub for Github username & ID (+ quack_role)
    user_metadata: UserMetaData


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    refresh_token: str
    user: SupaUser


def issue_admin_token(secret_key: str, role: str = "service_role", algorithm: str = "HS256") -> str:
    return jwt.encode({"role": role}, secret_key, algorithm=algorithm)


class SupaClient:
    ENDPOINT: str = "https://api.clerk.com/v1"

    def __init__(self, endpoint: str, api_key: str, service_token: str) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.token = service_token
        self.headers = self._get_headers(api_key)
        # Validate token
        self._request("get", "/health", headers=self.headers)
        logger.info("Using Supabase authentication service")

    @staticmethod
    def _get_headers(api_key: str) -> Dict[str, str]:
        return {"apiKey": api_key, "Content-Type": "application/json"}

    def _request(
        self, operation: str, route: str, expected_status_code: int = 200, timeout: int = 2, **kwargs
    ) -> Dict[str, str]:
        response = getattr(requests, operation)(urljoin(self.endpoint, route), timeout=timeout, **kwargs)
        json_response = response.json()
        if response.status_code != expected_status_code:
            raise HTTPException(status_code=response.status_code, detail=json_response["errors"][0]["message"])

        return json_response

    def sign_up(self, payload: Login, metadata: Union[Dict[str, str], None] = None) -> LoginResponse:
        json_payload = (
            {**payload.model_dump_json(), "data": metadata} if isinstance(metadata, dict) else payload.model_dump_json()
        )
        return self._request("post", "/signup", json=json_payload, headers=self.headers)

    def login_with_password(self, payload: Login) -> LoginResponse:
        return self._request(
            "post", "/token", params={"grant_type": "password"}, json=payload.model_dump_json(), headers=self.headers
        )

    def login_with_idtoken(self, payload: IDToken) -> LoginResponse:
        return self._request(
            "post", "/token", params={"grant_type": "id_token"}, json=payload.model_dump_json(), headers=self.headers
        )

    def magic_link(self, email: str) -> Dict[str, str]:
        return self._request("post", "/magiclink", json={"email": email}, headers=self.headers)

    def authorize(self, provider: Provider = Provider.GITHUB) -> Dict[str, str]:
        return self._request(
            "get",
            "/authorize",
            params={"provider": provider},
            headers={**self.headers, "Authorization": f"Bearer {self.token}"},
        )

    def get_authenticated_user(self, token: str) -> SupaUser:
        return self._request("get", "/user", headers={**self.headers, "Authorization": f"Bearer {token}"})

    def get_user(self, uid: str) -> SupaUser:
        return self._request(
            "get", f"/admin/users/{uid}", headers={**self.headers, "Authorization": f"Bearer {self.token}"}
        )

    def update_user(self, uid: str, payload: Dict[str, str]) -> SupaUser:
        return self._request(
            "put",
            f"/admin/users/{uid}",
            json=payload,
            headers={**self.headers, "Authorization": f"Bearer {self.token}"},
        )

    def delete_user(self, uid: str) -> Dict[str, str]:
        return self._request(
            "delete", f"/admin/users/{uid}", headers={**self.headers, "Authorization": f"Bearer {self.token}"}
        )

    def recover(self, email: str) -> Dict[str, str]:
        return self._request("post", "/recover", json={"email": email}, headers=self.headers)

    def invite_user(self, email: str) -> Dict[str, str]:
        return self._request(
            "post", "/invite", json={"email": email}, headers={**self.headers, "Authorization": f"Bearer {self.token}"}
        )


supabase_client = SupaClient(
    settings.SUPABASE_AUTH_ENDPOINT, settings.SUPABASE_API_KEY, issue_admin_token(settings.SECRET_KEY)
)
