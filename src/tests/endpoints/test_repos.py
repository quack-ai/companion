from typing import Any, Dict, List, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.api_v1.endpoints import users
from app.models import Guideline, Repository, User

USER_TABLE = [
    {
        "id": 1,
        "provider_user_id": 123,
        "login": "first_login",
        "hashed_password": "hashed_first_pwd",
        "scope": "admin",
        "created_at": "2024-02-23T08:18:45.447773",
    },
    {
        "id": 2,
        "provider_user_id": 456,
        "login": "second_login",
        "hashed_password": "hashed_second_pwd",
        "scope": "user",
        "created_at": "2024-02-23T08:18:45.447774",
    },
]

REPO_TABLE = [
    {
        "id": 1,
        "provider_repo_id": 12345,
        "name": "quack-ai/dummy-repo",
        "created_at": "2023-11-07T15:07:19.226673",
    },
    {
        "id": 2,
        "provider_repo_id": 123456,
        "name": "quack-ai/another-repo",
        "created_at": "2023-11-07T15:07:19.226673",
    },
]


GUIDELINE_TABLE = [
    {
        "id": 1,
        "creator_id": 2,
        "content": "Ensure function and class/instance methods have a meaningful & informative name",
        "created_at": "2024-11-07T15:08:19.226673",
        "updated_at": "2024-11-07T15:08:19.226673",
    },
]


@pytest_asyncio.fixture(scope="function")
async def repo_session(async_session: AsyncSession, monkeypatch):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    for entry in REPO_TABLE:
        async_session.add(Repository(**entry))
    await async_session.commit()
    monkeypatch.setattr(users, "hash_password", pytest.mock_hash_password)
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
        (None, {"provider_repo_id": 249513553}, 401, "Not authenticated", None),
        (0, {"full_name": "frgfm/torch-cam"}, 422, None, None),
        (
            0,
            {"provider_repo_id": 249513553},
            201,
            None,
            {
                "id": 3,
                "provider_repo_id": 249513553,
                "name": "frgfm/torch-cam",
            },
        ),
        (
            1,
            {"provider_repo_id": 249513553},
            422,
            None,
            {
                "id": 3,
                "provider_repo_id": 249513553,
                "name": "frgfm/torch-cam",
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
        assert {k: v for k, v in response.json().items() if k != "created_at"} == expected_response


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 12345, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 100, 404, "Table Repository has no corresponding entry.", None),
        (0, 1, 200, None, 0),
        (1, 1, 200, None, 0),
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
        (1, 403, "Not authorized", None),
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


# @pytest.mark.parametrize(
#     ("user_idx", "repo_id", "status_code", "status_detail"),
#     [
#         (None, 12345, 401, "Not authenticated"),
#         (0, 100, 404, "Not Found"),
#         (0, 249513553, 200, None),
#         (1, 249513553, 200, None),
#     ],
# )
# @pytest.mark.asyncio()
# async def test_add_repo_to_waitlist(
#     async_client: AsyncClient,
#     guideline_session: AsyncSession,
#     user_idx: Union[int, None],
#     repo_id: int,
#     status_code: int,
#     status_detail: Union[str, None],
# ):
#     auth = None
#     if isinstance(user_idx, int):
#         auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

#     response = await async_client.post(f"/repos/{repo_id}/waitlist", headers=auth)
#     assert response.status_code == status_code, print(response.json())
#     if isinstance(status_detail, str):
#         assert response.json()["detail"] == status_detail


# @pytest.mark.parametrize(
#     ("user_idx", "repo_id", "status_code", "status_detail"),
#     [
#         (None, 12345, 401, "Not authenticated"),
#         (0, 100, 404, "Table Repository has no corresponding entry."),
#     ],
# )
# @pytest.mark.asyncio()
# async def test_parse_guidelines_from_github(
#     async_client: AsyncClient,
#     guideline_session: AsyncSession,
#     user_idx: Union[int, None],
#     repo_id: int,
#     status_code: int,
#     status_detail: Union[str, None],
# ):
#     auth = None
#     if isinstance(user_idx, int):
#         auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

#     response = await async_client.post(f"/repos/{repo_id}/parse", json={}, headers=auth)
#     assert response.status_code == status_code, print(response.json())
#     if isinstance(status_detail, str):
#         assert response.json()["detail"] == status_detail
