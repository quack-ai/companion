# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_current_user, get_repo_crud
from app.crud import RepositoryCRUD
from app.models import Provider, Repository, User, UserScope
from app.schemas.repos import RepoRegistration
from app.services.github import gh_client
from app.services.slack import slack_client
from app.services.telemetry import telemetry_client

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a GitHub repository")
async def register_repo(
    payload: RepoRegistration,
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    # Check if repo is already registered
    if (await repos.get_by("provider_repo_id", payload.provider_repo_id, strict=False)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Repo already registered")
    # Check if provider repo exists
    gh_repo = gh_client.get_repo(payload.provider_repo_id, token=payload.github_token)
    # Check permission
    if user.scope != UserScope.ADMIN:
        if not isinstance(payload.github_token, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Expected `github_token` to check access.",
            )
        # Check provider link
        if not isinstance(user.provider_user_id, str) or user.provider_user_id.partition("|")[0] != Provider.GITHUB:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "No GitHub profile linked to your account.")
        # Finally, check GH permission
        gh_user = gh_client.get_my_user(payload.github_token)
        if gh_client.get_permission(gh_repo["full_name"], gh_user["login"], payload.github_token) not in {
            "maintain",
            "admin",
        }:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Insufficient GitHub permission (requires maintain or admin).",
            )

    telemetry_client.capture(
        user.id,
        event="repo-creation",
        properties={
            "provider_repo_id": f"{Provider.GITHUB}|{payload.provider_repo_id}",
            "full_name": gh_repo["full_name"],
        },
    )
    # Notify slack
    slack_client.notify(
        "*New GitHub repo* :up:",
        [
            (
                "Name",
                f"<{gh_repo['html_url']}|{gh_repo['full_name']}> ({gh_repo['stargazers_count']} :star:, {gh_repo['forks']} forks)",
            ),
            ("Language", gh_repo["language"]),
        ],
    )
    return await repos.create(Repository(provider_repo_id=payload.provider_repo_id, name=gh_repo["full_name"]))


@router.get("/{repo_id}", status_code=status.HTTP_200_OK, summary="Fetch a specific repository")
async def get_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    telemetry_client.capture(user.id, event="repo-get", properties={"repo_id": repo_id})
    return cast(Repository, await repos.get(repo_id, strict=True))


@router.get("/", status_code=status.HTTP_200_OK, summary="Fetch all repositories")
async def fetch_repos(
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> List[Repository]:
    telemetry_client.capture(user.id, event="repo-fetch")
    return [elt for elt in await repos.fetch_all()]


@router.delete("/{repo_id}", status_code=status.HTTP_200_OK, summary="Delete a specific repository")
async def delete_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    telemetry_client.capture(user.id, event="repo-delete", properties={"repo_id": repo_id})
    await repos.delete(repo_id)


# @router.post(
#     "/{repo_id}/parse", status_code=status.HTTP_200_OK, summary="Extracts the guidelines from a GitHub repository"
# )
# async def parse_guidelines_from_github(
#     payload: OptionalGHToken,
#     repo_id: int = Path(..., gt=0),
#     repos: RepositoryCRUD = Depends(get_repo_crud),
#     user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
# ) -> List[ParsedGuideline]:
#     telemetry_client.capture(user.id, event="repo-parse-guidelines", properties={"repo_id": repo_id})
#     # Sanity check
#     repo = cast(Repository, await repos.get(repo_id, strict=True))
#     # Stage all the text sources
#     sources = []
#     # Parse CONTRIBUTING (README if CONTRIBUTING doesn't exist)
#     contributing = gh_client.get_file(repo.full_name, "CONTRIBUTING.md", payload.github_token)
#     readme = gh_client.get_readme(repo.full_name, payload.github_token) if contributing is None else None
#     if contributing is not None:
#         sources.append((contributing["path"], b64decode(contributing["content"]).decode()))
#     if readme is not None:
#         sources.append((readme["path"], b64decode(readme["content"]).decode()))
#     # Pull request comments (!= review comments/threads)
#     pull_comments = [
#         pull
#         for pull in gh_client.fetch_pull_comments_from_repo(repo.full_name, token=payload.github_token)
#         if len(pull["comments"]) > 0
#     ]
#     if len(pull_comments) > 0:
#         # Keep: body, user/id, reactions/total_count
#         corpus = "# Pull request comments\n\n\n\n\n\n".join([
#             f"PULL REQUEST {pull['pull']['number']} from user {pull['pull']['user_id']}\n\n"
#             + "\n\n".join(f"[User {comment['user_id']}] {comment['body']}" for comment in pull["comments"])
#             for pull in pull_comments
#         ])
#         sources.append(("pull_request_comments", corpus))
#     # Review threads
#     review_comments = [
#         pull
#         for pull in gh_client.fetch_reviews_from_repo(repo.full_name, token=payload.github_token)
#         if len(pull["threads"]) > 0
#     ]
#     # Ideas: filter on pulls with highest amount of comments recently, add the review output rejection/etc
#     if len(review_comments) > 0:
#         # Keep: code, body, user/id, reactions/total_count
#         corpus = "# Code review history\n\n\n\n\n\n".join([
#             f"PULL: {pull['pull']['number']} from user {pull['pull']['user_id']}\n\n"
#             + "\n\n".join(
#                 f"[Code diff]\n```{thread[0]['code']}\n```\n"
#                 + "\n".join(f"[User {comment['user_id']}] {comment['body']}" for comment in thread)
#                 for thread in pull["threads"]
#             )
#             for pull in review_comments
#         ])
#         sources.append(("review_comments", corpus))
#     # If not enough information, raise error
#     if len(sources) == 0:
#         raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No useful information is accessible in the repository")
#     # Process all sources in parallel
#     responses = execute_in_parallel(
#         partial(openai_client.parse_guidelines_from_text, user_id=str(user.id)),
#         (corpus for _, corpus in sources),
#         num_threads=len(sources),
#     )
#     guidelines = [
#         ParsedGuideline(**guideline.dict(), repo_id=repo_id, source=source)
#         for (source, _), response in zip(sources, responses)
#         for guideline in response
#     ]
#     return guidelines


# @router.post("/{repo_id}/waitlist", status_code=status.HTTP_200_OK, summary="Add a GitHub repository to the waitlist")
# async def add_repo_to_waitlist(
#     repo_id: int = Path(..., gt=0),
#     user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
# ) -> None:
#     telemetry_client.capture(user.id, event="repo-waitlist", properties={"repo_id": repo_id})
#     gh_repo = gh_client.get_repo(repo_id)
#     # Notify slack
#     slack_client.notify(
#         f"Request from <https://github.com/{user.login}|{user.login}> :pray:",
#         [
#             (
#                 "Repo",
#                 f"<{gh_repo['html_url']}|{gh_repo['full_name']}> "
#                 f"({gh_repo['stargazers_count']} :star:, {gh_repo['forks']} :fork_and_knife:)",
#             ),
#         ],
#     )
