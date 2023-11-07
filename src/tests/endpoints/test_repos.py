from typing import Any, Dict, List, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.api_v1.endpoints import repos, users
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
]


class MockClient:
    @staticmethod
    def get_repo(repo_id: int) -> Dict[str, Any]:
        return {"full_name": "frgfm/torch-cam", "owner": {"id": 26927750}} if repo_id == 249513553 else {}


@pytest_asyncio.fixture(scope="function")
async def repo_session(async_session: AsyncSession, monkeypatch):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    for entry in REPO_TABLE:
        async_session.add(Repository(**entry))
    await async_session.commit()
    monkeypatch.setattr(users, "hash_password", pytest.mock_hash_password)
    monkeypatch.setattr(repos, "gh_client", MockClient)
    yield async_session


@pytest_asyncio.fixture(scope="function")
async def guideline_session(repo_session: AsyncSession):
    for entry in GUIDELINE_TABLE:
        repo_session.add(Guideline(**entry))
    await repo_session.commit()
    yield repo_session


@pytest.mark.parametrize(
    ("user_idx", "payload", "status_code", "status_detail", "expected_response"),
    [
        (None, {"id": 249513553}, 401, "Not authenticated", None),
        (0, {"full_name": "frgfm/torch-cam"}, 422, None, None),
        (
            0,
            {"id": 249513553},
            201,
            None,
            {
                "id": 249513553,
                "full_name": "frgfm/torch-cam",
                "owner_id": 26927750,
                "installed_by": 1,
                "removed_at": None,
            },
        ),
        (
            1,
            {"id": 249513553},
            201,
            None,
            {
                "id": 249513553,
                "full_name": "frgfm/torch-cam",
                "owner_id": 26927750,
                "installed_by": 2,
                "removed_at": None,
            },
        ),
    ],
)
@pytest.mark.asyncio()
async def test_create_repo(
    async_client: AsyncClient,
    repo_session: AsyncSession,
    user_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_response: Union[Dict[str, Any], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post("/repos", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k != "installed_at"} == expected_response


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 12345, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 1, 404, "Table Repository has no corresponding entry.", None),
        (0, 12345, 200, None, 0),
        (1, 12345, 200, None, 0),
    ],
)
@pytest.mark.asyncio()
async def test_get_repo(
    async_client: AsyncClient,
    repo_session: AsyncSession,
    user_idx: Union[int, None],
    repo_id: int,
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get(f"/repos/{repo_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == REPO_TABLE[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail", "expected_response"),
    [
        (None, 401, "Not authenticated", None),
        (0, 200, None, REPO_TABLE),
        (1, 200, None, REPO_TABLE[1:]),
    ],
)
@pytest.mark.asyncio()
async def test_fetch_repos(
    async_client: AsyncClient,
    repo_session: AsyncSession,
    user_idx: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
    expected_response: Union[List[Dict[str, Any]], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get("/repos", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == expected_response


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail"),
    [
        (None, 12345, 401, "Not authenticated"),
        (0, 0, 422, None),
        (0, 100, 404, "Table Repository has no corresponding entry."),
        (0, 12345, 200, None),
        (0, 123456, 200, None),
        (1, 12345, 401, "Your user scope is not compatible with this operation."),
        (1, 123456, 401, "Your user scope is not compatible with this operation."),
    ],
)
@pytest.mark.asyncio()
async def test_delete_repo(
    async_client: AsyncClient,
    repo_session: AsyncSession,
    user_idx: Union[int, None],
    repo_id: int,
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.delete(f"/repos/{repo_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() is None


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail", "expected_response"),
    [
        (None, 12345, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 100, 404, "Table Repository has no corresponding entry.", None),
        (0, 12345, 200, None, GUIDELINE_TABLE),
        (1, 12345, 200, None, GUIDELINE_TABLE),
    ],
)
@pytest.mark.asyncio()
async def test_fetch_guidelines_from_repo(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    repo_id: int,
    status_code: int,
    status_detail: Union[str, None],
    expected_response: Union[List[Dict[str, Any]], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get(f"/repos/{repo_id}/guidelines", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == expected_response
