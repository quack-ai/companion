from typing import Any, Dict, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.api_v1.endpoints import users
from app.models import User

USER_TABLE = [
    {
        "id": 1,
        "provider_user_id": 26927750,
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


@pytest_asyncio.fixture(scope="function")
async def user_session(async_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(users, "hash_password", pytest.mock_hash_password)
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    await async_session.execute(
        text(f"ALTER SEQUENCE user_id_seq RESTART WITH {max(entry['id'] for entry in USER_TABLE) + 1}")
    )
    await async_session.commit()
    yield async_session


@pytest.mark.parametrize(
    ("user_idx", "payload", "status_code", "status_detail"),
    [
        (
            None,
            {"provider_user_id": 241138, "login": "karpathy", "password": "bar", "scope": "user"},
            401,
            "Not authenticated",
        ),
        (
            0,
            {"provider_user_id": 26927750, "login": "karpathy", "password": "bar", "scope": "user"},
            409,
            "User already registered",
        ),
        (0, {"provider_user_id": 241138, "login": "karpathy", "password": "bar", "scope": "user"}, 201, None),
        (0, {"provider_user_id": 241138, "login": "karpathy", "scope": "user"}, 422, None),
        (
            1,
            {"provider_user_id": 241138, "login": "karpathy", "password": "bar", "scope": "user"},
            401,
            "Your user scope is not compatible with this operation.",
        ),
    ],
)
@pytest.mark.asyncio()
async def test_create_user(
    async_client: AsyncClient,
    user_session: AsyncSession,
    user_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post("/users", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k != "created_at"} == {
            "provider_user_id": payload["provider_user_id"],
            "login": payload["login"],
            "hashed_password": f"hashed_{payload['password']}",
            "scope": payload["scope"],
            "id": max(entry["id"] for entry in USER_TABLE) + 1,
        }


@pytest.mark.parametrize(
    ("user_idx", "user_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, 401, "Not authenticated", None),
        (0, 0, 422, None, None),
        (0, 400, 404, "Table User has no corresponding entry.", None),
        (1, 1, 401, "Your user scope is not compatible with this operation.", None),
        (0, 1, 200, None, 0),
        (0, 2, 200, None, 1),
    ],
)
@pytest.mark.asyncio()
async def test_get_user(
    async_client: AsyncClient,
    user_session: AsyncSession,
    user_idx: Union[int, None],
    user_id: int,
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get(f"/users/{user_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == USER_TABLE[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail"),
    [
        (None, 401, "Not authenticated"),
        (0, 200, None),
        (1, 401, "Your user scope is not compatible with this operation."),
    ],
)
@pytest.mark.asyncio()
async def test_fetch_users(
    async_client: AsyncClient,
    user_session: AsyncSession,
    user_idx: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.get("/users/", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == USER_TABLE


@pytest.mark.parametrize(
    ("user_idx", "user_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 1, 200, None),
        (0, 2, 200, None),
        (1, 1, 401, "Your user scope is not compatible with this operation."),
        (1, 2, 401, "Your user scope is not compatible with this operation."),
    ],
)
@pytest.mark.asyncio()
async def test_delete_user(
    async_client: AsyncClient,
    user_session: AsyncSession,
    user_idx: Union[int, None],
    user_id: int,
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.delete(f"/users/{user_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() is None


@pytest.mark.parametrize(
    ("user_idx", "user_id", "payload", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, {"password": "HeyQuack!"}, 401, "Not authenticated", None),
        (0, 1, {"login": "HeyQuack!"}, 422, None, None),
        (0, 1, {"password": "HeyQuack!"}, 200, None, 0),
        (0, 2, {"password": "HeyQuack!"}, 200, None, 1),
        (1, 1, {"password": "HeyQuack!"}, 401, "Your user scope is not compatible with this operation.", None),
        (1, 2, {"password": "HeyQuack!"}, 401, "Your user scope is not compatible with this operation.", None),
    ],
)
@pytest.mark.asyncio()
async def test_update_user_password(
    async_client: AsyncClient,
    user_session: AsyncSession,
    user_idx: Union[int, None],
    user_id: int,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_idx: Union[int, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.patch(f"/users/{user_id}", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == {
            "id": USER_TABLE[expected_idx]["id"],
            "provider_user_id": USER_TABLE[expected_idx]["provider_user_id"],
            "created_at": USER_TABLE[expected_idx]["created_at"],
            "login": USER_TABLE[expected_idx]["login"],
            "hashed_password": f"hashed_{payload['password']}",
            "scope": USER_TABLE[expected_idx]["scope"],
        }
