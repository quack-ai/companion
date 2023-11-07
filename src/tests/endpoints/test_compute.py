from typing import Any, Dict, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Guideline, Repository, User

USER_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_first_pwd", "scope": "admin"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_second_pwd", "scope": "user"},
]

REPO_TABLE = [
    {
        "id": 12345,
        "full_name": "quack-ai/dummy-repo",
        "installed_by": 1,
        "owner_id": 1,
        "installed_at": "2023-11-07T15:07:19.226673",
        "removed_at": None,
    },
    {
        "id": 123456,
        "full_name": "quack-ai/another-repo",
        "installed_by": 2,
        "owner_id": 2,
        "installed_at": "2023-11-07T15:07:19.226673",
        "removed_at": None,
    },
]

GUIDELINE_TABLE = [
    {
        "id": 1,
        "repo_id": 12345,
        "title": "Object naming",
        "details": "Ensure function and class/instance methods have a meaningful & informative name",
        "order": 1,
        "created_at": "2023-11-07T15:08:19.226673",
        "updated_at": "2023-11-07T15:08:19.226673",
    },
    {
        "id": 2,
        "repo_id": 12345,
        "title": "Docstrings",
        "details": "All functions and methods need to have a docstring",
        "order": 2,
        "created_at": "2023-11-07T15:08:20.226673",
        "updated_at": "2023-11-07T15:08:20.226673",
    },
]


@pytest_asyncio.fixture(scope="function")
async def compute_session(async_session: AsyncSession, monkeypatch):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    for entry in REPO_TABLE:
        async_session.add(Repository(**entry))
    await async_session.commit()
    for entry in GUIDELINE_TABLE:
        async_session.add(Guideline(**entry))
    await async_session.commit()
    # Update the guideline index count
    await async_session.execute(
        text(f"ALTER SEQUENCE guideline_id_seq RESTART WITH {max(entry['id'] for entry in GUIDELINE_TABLE) + 1}")
    )
    await async_session.commit()
    yield async_session


@pytest.mark.parametrize(
    ("user_idx", "guideline_id", "payload", "status_code", "status_detail"),
    [
        (None, 1, {"code": "def hello_world():\n\tprint('hello')"}, 401, "Not authenticated"),
        (0, 1, {"code": ""}, 422, None),
        (0, 100, {"code": "def hello_world():\n\tprint('hello')"}, 404, "Table Guideline has no corresponding entry."),
    ],
)
@pytest.mark.asyncio()
async def test_check_code_against_guideline(
    async_client: AsyncClient,
    compute_session: AsyncSession,
    user_idx: Union[int, None],
    guideline_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post(f"/compute/check/{guideline_id}", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "payload", "status_code", "status_detail"),
    [
        (None, 12345, {"code": "def hello_world():\n\tprint('hello')"}, 401, "Not authenticated"),
        (0, 12345, {"code": ""}, 422, None),
        (0, 100, {"code": "def hello_world():\n\tprint('hello')"}, 404, "Table Repository has no corresponding entry."),
    ],
)
@pytest.mark.asyncio()
async def test_check_code_against_repo_guidelines(
    async_client: AsyncClient,
    compute_session: AsyncSession,
    user_idx: Union[int, None],
    repo_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post(f"/compute/analyze/{repo_id}", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
