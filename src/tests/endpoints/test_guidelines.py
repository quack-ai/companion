from typing import Any, Dict, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

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
        "content": "Ensure function and class/instance methods have a meaningful & informative name",
        "creator_id": 1,
        "created_at": "2023-11-07T15:08:19.226673",
        "updated_at": "2023-11-07T15:08:19.226673",
    },
    {
        "id": 2,
        "title": "Docstrings",
        "content": "All functions and methods need to have a docstring",
        "creator_id": 2,
        "created_at": "2023-11-07T15:08:20.226673",
        "updated_at": "2023-11-07T15:08:20.226673",
    },
]


@pytest_asyncio.fixture(scope="function")
async def guideline_session(async_session: AsyncSession, monkeypatch):
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
    ("user_idx", "payload", "status_code", "status_detail"),
    [
        (None, {"content": "Quacky quack"}, 401, "Not authenticated"),
        (0, {"title": "Hello there!"}, 422, None),
        (0, {"content": "Quacky quack"}, 201, None),
        (1, {"content": "Quacky quack"}, 201, None),
    ],
)
@pytest.mark.asyncio()
async def test_create_guideline(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post("/guidelines", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k not in {"created_at", "updated_at", "id"}} == payload
        assert response.json()["id"] == max(entry["id"] for entry in GUIDELINE_TABLE) + 1


@pytest.mark.parametrize(
    ("user_idx", "guideline_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 10, 404, "Table Guideline has no corresponding entry.", None),
        (0, 1, 200, None, 0),
        (0, 2, 200, None, 1),
        (1, 1, 200, None, 0),
        (1, 2, 200, None, 1),
    ],
)
@pytest.mark.asyncio()
async def test_get_guideline(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    guideline_id: int,
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get(f"/guidelines/{guideline_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == GUIDELINE_TABLE[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail"),
    [
        (None, 401, "Not authenticated"),
        (0, 200, None),
        (1, 401, "Your user scope is not compatible with this operation."),
    ],
)
@pytest.mark.asyncio()
async def test_fetch_guidelines(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get("/guidelines", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == GUIDELINE_TABLE


@pytest.mark.parametrize(
    ("user_idx", "guideline_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 0, 422, None),
        (0, 100, 404, "Table Guideline has no corresponding entry."),
        (0, 1, 200, None),
        (0, 2, 200, None),
        (1, 1, 422, None),
        (1, 2, 422, None),
    ],
)
@pytest.mark.asyncio()
async def test_delete_guideline(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    guideline_id: int,
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.request("DELETE", f"/guidelines/{guideline_id}", json={}, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() is None


@pytest.mark.parametrize(
    ("user_idx", "guideline_id", "payload", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, {"content": "New guideline details"}, 401, "Not authenticated", None),
        (0, 0, {"content": "New guideline title"}, 422, None, None),
        (0, 1, {"title": "New guideline title"}, 422, None, None),
        (0, 1, {"content": "New guideline details"}, 200, None, 0),
        (0, 2, {"content": "New guideline details"}, 200, None, 1),
        (1, 1, {"content": "New guideline details"}, 422, None, 0),
        (1, 2, {"content": "New guideline details"}, 422, None, 1),
    ],
)
@pytest.mark.asyncio()
async def test_update_guideline_content(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    guideline_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.patch(f"/guidelines/{guideline_id}", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k != "updated_at"} == {
            **{k: v for k, v in GUIDELINE_TABLE[expected_idx].items() if k not in {"title", "details", "updated_at"}},
            **payload,
        }
