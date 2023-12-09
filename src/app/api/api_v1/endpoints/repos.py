# Copyright (C) 2023, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import logging
from base64 import b64decode
from datetime import datetime
from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, Path, Security, status

from app.api.dependencies import get_current_user, get_guideline_crud, get_repo_crud
from app.crud import GuidelineCRUD, RepositoryCRUD
from app.models import Guideline, Repository, User, UserScope
from app.schemas.base import OptionalGHToken
from app.schemas.guidelines import OrderUpdate, ParsedGuideline
from app.schemas.repos import GuidelineOrder, RepoCreate, RepoCreation, RepoUpdate
from app.services.github import gh_client
from app.services.openai import openai_client
from app.services.slack import slack_client
from app.services.telemetry import telemetry_client

logger = logging.getLogger("uvicorn.error")
router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, summary="Register a GitHub repository")
async def create_repo(
    payload: RepoCreate,
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    # Check repo exists
    gh_repo = gh_client.get_repo(payload.id)
    telemetry_client.capture(
        user.id,
        event="repo-creation",
        properties={"repo_id": payload.id, "full_name": gh_repo["full_name"]},
    )
    # Check if user is allowed
    gh_client.check_user_permission(user, gh_repo["full_name"], gh_repo["owner"]["id"], payload.github_token)
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
    return await repos.create(
        RepoCreation(
            id=payload.id,
            full_name=gh_repo["full_name"],
            owner_id=gh_repo["owner"]["id"],
            installed_by=user.id,
        ),
    )


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
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> List[Repository]:
    telemetry_client.capture(user.id, event="repo-fetch")
    entries = await repos.fetch_all() if user.scope == UserScope.ADMIN else await repos.fetch_all(("owner_id", user.id))
    return [elt for elt in entries]


@router.put(
    "/{repo_id}/guidelines/order",
    status_code=status.HTTP_200_OK,
    summary="Updates the order of the guidelines for a specific repository",
)
async def reorder_repo_guidelines(
    payload: GuidelineOrder,
    repo_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> List[Guideline]:
    telemetry_client.capture(user.id, event="guideline-order", properties={"repo_id": repo_id})
    # Ensure all IDs are unique
    if len(payload.guideline_ids) != len(set(payload.guideline_ids)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Duplicate IDs were passed.")
    # Check the repo
    repo = cast(Repository, await repos.get(repo_id, strict=True))
    # Ensure all IDs are valid
    guideline_ids = [elt.id for elt in await guidelines.fetch_all(("repo_id", repo_id))]
    if set(payload.guideline_ids) != set(guideline_ids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Guideline IDs for that repo don't match.",
        )
    # Check if user is allowed
    gh_client.check_user_permission(user, repo.full_name, repo.owner_id, payload.github_token, repo.installed_by)
    # Update all order
    return [
        await guidelines.update(guideline_id, OrderUpdate(order=order_idx, updated_at=datetime.utcnow()))
        for order_idx, guideline_id in enumerate(payload.guideline_ids)
    ]


@router.put("/{repo_id}/disable", status_code=status.HTTP_200_OK, summary="Disable a specific repository")
async def disable_repo(
    payload: OptionalGHToken,
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    telemetry_client.capture(user.id, event="repo-disable", properties={"repo_id": repo_id})
    # Check if user is allowed
    repo = cast(Repository, await repos.get(repo_id, strict=True))
    gh_client.check_user_permission(user, repo.full_name, repo.owner_id, payload.github_token, repo.installed_by)
    return await repos.update(repo_id, RepoUpdate(is_active=False))


@router.put("/{repo_id}/enable", status_code=status.HTTP_200_OK, summary="Enable a specific repository")
async def enable_repo(
    payload: OptionalGHToken,
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.USER, UserScope.ADMIN]),
) -> Repository:
    telemetry_client.capture(user.id, event="repo-enable", properties={"repo_id": repo_id})
    # Check if user is allowed
    repo = cast(Repository, await repos.get(repo_id, strict=True))
    gh_client.check_user_permission(user, repo.full_name, repo.owner_id, payload.github_token, repo.installed_by)
    return await repos.update(repo_id, RepoUpdate(is_active=True))


@router.delete("/{repo_id}", status_code=status.HTTP_200_OK, summary="Delete a specific repository")
async def delete_repo(
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN]),
) -> None:
    telemetry_client.capture(user.id, event="repo-delete", properties={"repo_id": repo_id})
    await repos.delete(repo_id)


@router.get("/{repo_id}/guidelines", status_code=status.HTTP_200_OK, summary="Fetch the guidelines of a repository")
async def fetch_guidelines_from_repo(
    repo_id: int = Path(..., gt=0),
    guidelines: GuidelineCRUD = Depends(get_guideline_crud),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> List[Guideline]:
    telemetry_client.capture(user.id, event="repo-fetch-guidelines", properties={"repo_id": repo_id})
    await repos.get(repo_id, strict=True)
    return [elt for elt in await guidelines.fetch_all(("repo_id", repo_id))]


@router.post(
    "/{repo_id}/parse", status_code=status.HTTP_200_OK, summary="Extracts the guidelines from a GitHub repository"
)
async def parse_guidelines_from_github(
    payload: OptionalGHToken,
    repo_id: int = Path(..., gt=0),
    repos: RepositoryCRUD = Depends(get_repo_crud),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> List[ParsedGuideline]:
    telemetry_client.capture(user.id, event="repo-parse-guidelines", properties={"repo_id": repo_id})
    # Sanity check
    repo = cast(Repository, await repos.get(repo_id, strict=True))
    # STATIC CONTENT
    # Parse CONTRIBUTING (README if CONTRIBUTING doesn't exist)
    contributing = gh_client.get_file(repo.full_name, "CONTRIBUTING.md", payload.github_token)
    readme = gh_client.get_readme(payload.github_token)
    # Pull request comments (!= review comments/threads)
    # Remove the first pull comments since they're a description
    pull_comments = [
        pull[1:] for pull in gh_client.list_issue_comments(repo.full_name, payload.github_token) if len(pull) > 1
    ]
    logger.info(len(pull_comments))
    # Review threads
    # Keep: diff_hunk, body, path, user/id, reactions/total_count
    # review_comments = gh_client.get_pull_review_threads(repo.full_name, payload.github_token)
    # Ideas: filter on pulls with highest amount of comments recently, add the review output rejection/etc
    # If not enough information, raise error
    if contributing is None and readme is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="No useful information is accessible in the repository")
    # Analyze with LLM
    guidelines = []
    if contributing is not None:
        guidelines.extend([
            ParsedGuideline(**guideline.dict(), repo_id=repo_id, origin_path=contributing["path"])
            for guideline in openai_client.parse_guidelines_from_text(
                b64decode(contributing["content"]).decode(),
                user_id=str(user.id),
            )
        ])
    if readme is not None:
        guidelines.extend([
            ParsedGuideline(**guideline.dict(), repo_id=repo_id, origin_path=readme["path"])
            for guideline in openai_client.parse_guidelines_from_text(
                b64decode(readme["content"]).decode(),
                user_id=str(user.id),
            )
        ])
    if len(pull_comments) > 0:
        # Keep: body, user/id, reactions/total_count
        pull_comments_corpus = "# Code review history\n\n\n\n\n\n".join([
            f"ISSUE: {issue[0]['issue_url']}\n\n"
            + "\n\n".join(
                f"Comment by user {comment['user']['id']} with {comment['reactions']['total_count']} reactions:\n{comment['body']}"
                for comment in issue
            )
            for issue in pull_comments
        ])
        logger.info(len(pull_comments_corpus))
        guidelines.extend([
            ParsedGuideline(**guideline.dict(), repo_id=repo_id, origin_path="pull_request_comments")
            for guideline in openai_client.parse_guidelines_from_text(
                pull_comments_corpus,
                user_id=str(user.id),
            )
        ])
    return guidelines


@router.post("/{repo_id}/waitlist", status_code=status.HTTP_200_OK, summary="Add a GitHub repository to the waitlist")
async def add_repo_to_waitlist(
    repo_id: int = Path(..., gt=0),
    user: User = Security(get_current_user, scopes=[UserScope.ADMIN, UserScope.USER]),
) -> None:
    telemetry_client.capture(user.id, event="repo-waitlist", properties={"repo_id": repo_id})
    gh_repo = gh_client.get_repo(repo_id)
    # Notify slack
    slack_client.notify(
        f"Request from <https://github.com/{user.login}|{user.login}> :pray:",
        [
            (
                "Repo",
                f"<{gh_repo['html_url']}|{gh_repo['full_name']}> "
                f"({gh_repo['stargazers_count']} :star:, {gh_repo['forks']} :fork_and_knife:)",
            ),
        ],
    )
