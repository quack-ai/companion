# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

from typing import Any, Dict, Union

import requests
from fastapi import HTTPException

from app.core.config import settings

__all__ = ["gh_client"]


class GitHubClient:
    ENDPOINT: str = "https://api.github.com"

    def __init__(self, token: Union[str, None] = None) -> None:
        self.headers = (
            {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            if token
            else {"Content-Type": "application/json"}
        )

    def _get(self, endpoint: str, entry_id: int) -> Dict[str, Any]:
        response = requests.get(f"{self.ENDPOINT}/{endpoint}{entry_id}", headers=self.headers, timeout=2)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"]["message"])
        return response.json()

    def get_repo(self, repo_id: int) -> Dict[str, Any]:
        return self._get("repositories/", repo_id)

    def get_user(self, user_id: int) -> Dict[str, Any]:
        return self._get("user/", user_id)

    def get_permission(self, repo_name: str, user_name: str, github_token: str) -> str:
        response = requests.get(
            f"{self.ENDPOINT}/repos/{repo_name}/collaborators/{user_name}/permission",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {github_token}",
            },
            timeout=5,
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.json()["error"]["message"])
        return response.json()["role_name"]

    def has_valid_permission(self, repo_name: str, user_name: str, github_token: str) -> bool:
        return self.get_permission(repo_name, user_name, github_token) in ("maintain", "admin")


gh_client = GitHubClient(settings.GH_TOKEN)
