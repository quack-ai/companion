# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from typing import Any, Dict, List, Union

import requests
from fastapi import HTTPException, status
from pydantic import HttpUrl

from app.core.config import settings
from app.models import User, UserScope
from app.schemas.services import GHToken, GHTokenRequest

logger = logging.getLogger("uvicorn.error")

__all__ = ["gh_client"]


class GitHubClient:
    ENDPOINT: str = "https://api.github.com"
    OAUTH_ENDPOINT: str = "https://github.com/login/oauth/access_token"

    def __init__(self, token: Union[str, None] = None) -> None:
        self.headers = self._get_headers(token)

    @staticmethod
    def _get_headers(token: Union[str, None] = None) -> Dict[str, str]:
        if isinstance(token, str):
            return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        return {"Content-Type": "application/json"}

    def _get(
        self,
        route: str,
        token: Union[str, None] = None,
        timeout: int = 5,
        status_code_tolerance: Union[int, None] = None,
        **kwargs,
    ) -> requests.Response:
        response = requests.get(
            f"{self.ENDPOINT}/{route}",
            headers=self._get_headers(token) if isinstance(token, str) else self.headers,
            timeout=timeout,
            params=kwargs,
        )
        if response.status_code != status.HTTP_200_OK and (
            status_code_tolerance is None or response.status_code != status_code_tolerance
        ):
            json_response = response.json()
            raise HTTPException(
                status_code=response.status_code,
                detail=json_response.get("error", json_response["message"]),
            )
        return response

    def get_repo(self, repo_id: int, **kwargs) -> Dict[str, Any]:
        return self._get(f"repositories/{repo_id}", **kwargs).json()

    def get_user(self, user_id: int, **kwargs) -> Dict[str, Any]:
        return self._get(f"user/{user_id}", **kwargs).json()

    def get_my_user(self, token: str) -> Dict[str, Any]:
        return self._get("user", token).json()

    def get_permission(self, repo_name: str, user_name: str, token: str) -> str:
        return self._get(f"repos/{repo_name}/collaborators/{user_name}/permission", token).json()["role_name"]

    def check_user_permission(
        self,
        user: User,
        repo_full_name: str,
        repo_owner_id: int,
        github_token: Union[str, None],
        repo_installer_id: Union[int, None] = None,
    ) -> None:
        if (
            user.scope != UserScope.ADMIN
            and repo_owner_id != user.id
            and (not isinstance(repo_installer_id, int) or repo_installer_id != user.id)
        ):
            if not isinstance(github_token, str):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Expected `github_token` to check access.",
                )
            if self.get_permission(repo_full_name, user.login, github_token) not in ("maintain", "admin"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Insufficient access (requires maintain or admin).",
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

    def get_readme(self, repo_name: str, token: Union[str, None] = None) -> Union[Dict[str, Any], None]:
        # https://docs.github.com/en/rest/repos/contents#get-a-repository-readme
        response = self._get(f"repos/{repo_name}/readme", token, status_code_tolerance=status.HTTP_404_NOT_FOUND)
        return response.json() if response.status_code != status.HTTP_404_NOT_FOUND else None

    def get_file(self, repo_name: str, file_path: str, token: Union[str, None] = None) -> Union[Dict[str, Any], None]:
        # https://docs.github.com/en/rest/repos/contents#get-repository-content
        response = self._get(
            f"repos/{repo_name}/contents/{file_path}",
            token,
            status_code_tolerance=status.HTTP_404_NOT_FOUND,
        )
        return response.json() if response.status_code != status.HTTP_404_NOT_FOUND else None

    def list_pulls(self, repo_name: str, token: Union[str, None] = None, per_page: int = 30) -> List[Dict[str, Any]]:
        # https://docs.github.com/en/rest/pulls/pulls#list-pull-requests
        return self._get(
            f"repos/{repo_name}/pulls",
            token,
            state="closed",
            sort="popularity",
            direction="desc",
            base=self._get(f"repos/{repo_name}", token).json()["default_branch"],
            per_page=per_page,
        ).json()

    def list_review_comments(self, repo_name: str, token: Union[str, None] = None) -> List[Dict[str, Any]]:
        # https://docs.github.com/en/rest/pulls/comments#list-review-comments-in-a-repository
        comments = self._get(
            f"repos/{repo_name}/pulls/comments",
            token,
            sort="created_at",
            direction="desc",
            per_page=100,
        ).json()
        # Get comments (filter account type == user, & user != author) --> take diff_hunk, body, path
        return [comment for comment in comments if comment["user"]["type"] == "User"]


gh_client = GitHubClient(settings.GH_TOKEN)
