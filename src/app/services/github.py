# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import Any, Dict, Union

import requests
from fastapi import HTTPException, status
from pydantic import HttpUrl

from app.core.config import settings
from app.models import User, UserScope
from app.schemas.services import GHToken, GHTokenRequest

__all__ = ["gh_client"]


class GitHubClient:
    ENDPOINT: str = "https://api.github.com"
    OAUTH_ENDPOINT: str = "https://github.com/login/oauth/access_token"

    def __init__(self, token: Union[str, None] = None) -> None:
        self.headers = self._get_headers(token)

    def _get_headers(self, token: Union[str, None] = None) -> Dict[str, str]:
        if isinstance(token, str):
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

    def _get(self, route: str, token: Union[str, None] = None, timeout: int = 5) -> Dict[str, Any]:
        response = requests.get(
            f"{self.ENDPOINT}/{route}",
            headers=self._get_headers(token) if isinstance(token, str) else self.headers,
            timeout=timeout,
        )
        json_response = response.json()
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(
                status_code=response.status_code, detail=json_response.get("error", json_response["message"])
            )
        return json_response

    def get_repo(self, repo_id: int, **kwargs: Any) -> Dict[str, Any]:
        return self._get(f"repositories/{repo_id}", **kwargs)

    def get_user(self, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        return self._get(f"user/{user_id}", **kwargs)

    def get_my_user(self, token: str) -> Dict[str, Any]:
        return self._get("user", token)

    def get_permission(self, repo_name: str, user_name: str, github_token: str) -> str:
        return self._get(f"repos/{repo_name}/collaborators/{user_name}/permission", github_token)["role_name"]

    def check_user_permission(
        self, user: User, repo_full_name: str, repo_owner_id: int, github_token: Union[str, None]
    ) -> None:
        if user.scope != UserScope.ADMIN and repo_owner_id != user.id:
            if not isinstance(github_token, str):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Expected `github_token` to check access."
                )
            if self.get_permission(repo_full_name, user.login, github_token) not in ("maintain", "admin"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Insufficient access (requires maintain or admin)."
                )

    def get_token_from_code(self, code: str, redirect_uri: HttpUrl, timeout: int = 5) -> GHToken:
        gh_payload = GHTokenRequest(
            client_id=settings.GH_OAUTH_ID,
            client_secret=settings.GH_OAUTH_SECRET,
            redirect_uri=redirect_uri,
            code=code,
        )
        response = requests.post(
            self.OAUTH_ENDPOINT,
            json=gh_payload.dict(),
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        if response.status_code != status.HTTP_200_OK:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"])
        if response.status_code == status.HTTP_200_OK and isinstance(response.json().get("error_description"), str):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.json()["error_description"])
        return GHToken(**response.json())


gh_client = GitHubClient(settings.GH_TOKEN)
