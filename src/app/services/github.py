# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from functools import partial
from operator import itemgetter
from typing import Any, Dict, List, Union, cast

import requests
from fastapi import HTTPException, status
from pydantic import HttpUrl

from app.core.config import settings
from app.models import User, UserScope
from app.schemas.services import GHToken, GHTokenRequest
from app.services.utils import execute_in_parallel

logger = logging.getLogger("uvicorn.error")

__all__ = ["gh_client"]


def resolve_diff_section(diff_hunk: str, first_line: int, last_line: int) -> str:
    """Assumes the diff_hunk's last line is the last_line"""
    num_lines = last_line - first_line + 1
    return "\n".join(diff_hunk.split("\n")[-num_lines:])


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
            sort="created",
            direction="desc",
            base=self._get(f"repos/{repo_name}", token).json()["default_branch"],
            per_page=per_page,
        ).json()

    def list_comments_from_issue(
        self, issue_number: int, repo_name: str, token: Union[str, None] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        # https://docs.github.com/en/rest/issues/comments#list-issue-comments
        return [
            comment
            for comment in self._get(
                f"repos/{repo_name}/issues/{issue_number}/comments",
                token,
                **kwargs,
            ).json()
            if comment["user"]["type"] == "User"
        ]

    def list_reviews_from_pull(
        self, repo_name: str, pull_number: int, token: Union[str, None] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        # https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request
        # Get comments (filter account type == user, & user != author)
        return self._get(
            f"repos/{repo_name}/pulls/{pull_number}/reviews",
            token,
            **kwargs,
        ).json()

    def list_threads_from_review(
        self, repo_name: str, pull_number: int, review_id: int, token: Union[str, None] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        # https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request
        # Get comments (filter account type == user, & user != author)
        return self._get(
            f"repos/{repo_name}/pulls/{pull_number}/reviews/{review_id}/comments",
            token,
            **kwargs,
        ).json()

    def list_review_comments_from_pull(
        self, pull_number: int, repo_name: str, token: Union[str, None] = None, **kwargs
    ) -> List[List[Dict[str, Any]]]:
        # https://docs.github.com/en/rest/pulls/comments#list-review-comments-on-a-pull-request
        # Get comments (filter account type == user, & user != author)
        return [
            comment
            for comment in self._get(
                f"repos/{repo_name}/pulls/{pull_number}/comments",
                token,
                sort="created_at",
                **kwargs,
            ).json()
            if comment["user"]["type"] == "User"
        ]

    def fetch_reviews_from_repo(
        self, repo_name: str, num_pulls: int = 30, token: Union[str, None] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        # Fetch pulls & filter them
        pulls = self.list_pulls(repo_name, token, per_page=num_pulls)
        # Fetch reviews from those (parallelize)
        # reviews = [self.list_reviews_from_pull(repo_name, pull["number"], token, per_page=100) for pull in pulls]
        # Fetch comments (parallelize)
        comments = cast(
            List[List[Dict[str, Any]]],
            execute_in_parallel(
                partial(self.list_review_comments_from_pull, repo_name=repo_name, token=token, per_page=100, **kwargs),
                (pull["number"] for pull in pulls),
                len(pulls),
            ),
        )
        # Arrange them in threads
        id_map = {
            # diff_hunk, body, path, user/id, pull_request_url, reactions/total_count, in_reply_to_id, id, original_start_line, original_line
            comment["id"]: {
                "id": comment["id"],
                "code": resolve_diff_section(
                    comment["diff_hunk"],
                    comment["original_start_line"] or comment["original_line"],
                    comment["original_line"],
                ),
                "body": comment["body"],
                "path": comment["path"],
                "user_id": comment["user"]["id"],
                "reactions_total_count": comment["reactions"]["total_count"],
                "in_reply_to_id": comment.get("in_reply_to_id"),
                "start_line": comment["original_start_line"] or comment["original_line"],
                "end_line": comment["original_line"],
                "commit_id": comment["commit_id"],
            }
            for pull in comments
            for comment in pull
        }
        return [
            {
                "pull": {
                    "number": pull["number"],
                    "title": pull["title"],
                    "body": pull["body"],
                    "user_id": pull["user"]["id"],
                },
                "threads": [[id_map[_id] for _id in thread] for thread in self.arrange_in_threads(_comments)],
            }
            for pull, _comments in zip(pulls, comments)
        ]

    @staticmethod
    def arrange_in_threads(comments: List[Dict[str, Any]]) -> List[List[int]]:
        # Chain the threads together
        unused_nodes = {comment["id"] for comment in comments}
        prev_map = {comment["id"]: comment.get("in_reply_to_id") for comment in comments}
        next_map = {
            comment["in_reply_to_id"]: comment["id"]
            for comment in comments
            if isinstance(comment.get("in_reply_to_id"), int)
        }

        threads = []
        while len(unused_nodes) > 0:
            _id = next(iter(unused_nodes))
            _thread = [_id]
            unused_nodes.remove(_id)
            while isinstance(next_map.get(_thread[-1]), int):
                unused_nodes.remove(next_map[_thread[-1]])
                _thread.append(next_map[_thread[-1]])
            while isinstance(prev_map.get(_thread[0]), int):
                unused_nodes.remove(prev_map[_thread[0]])
                _thread.insert(0, prev_map[_thread[0]])
            threads.append(_thread)

        # Sort threads by the ID of the first comment
        return sorted(threads, key=itemgetter(0))

    def fetch_pull_comments_from_repo(
        self, repo_name: str, num_pulls: int = 30, token: Union[str, None] = None, **kwargs
    ) -> List[Dict[str, Any]]:
        # Fetch pulls & filter them
        pulls = self.list_pulls(repo_name, token, per_page=num_pulls)
        # Fetch comments from those (parallelize)
        comments = execute_in_parallel(
            partial(self.list_comments_from_issue, repo_name=repo_name, token=token, per_page=100, **kwargs),
            (pull["number"] for pull in pulls),
            len(pulls),
        )
        return [
            {
                "pull": {
                    "number": pull["number"],
                    "title": pull["title"],
                    "body": pull["body"],
                    "user_id": pull["user"]["id"],
                },
                "comments": [
                    {
                        "id": _comment["id"],
                        "body": _comment["body"],
                        "user_id": _comment["user"]["id"],
                        "reactions_total_count": _comment["reactions"]["total_count"],
                    }
                    for _comment in _comments
                ],
            }
            for pull, _comments in zip(pulls, comments)
        ]


gh_client = GitHubClient(settings.GH_TOKEN)
