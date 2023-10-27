from typing import Any, Dict, Union
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security
from app.models import User

USER_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_first_pwd", "scope": "user"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_second_pwd", "scope": "user"},
]


@pytest_asyncio.fixture(scope="function")
async def session(async_session: AsyncSession, monkeypatch):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    monkeypatch.setattr(security, "verify_password", pytest.mock_verify_password)
    yield async_session


@pytest.mark.parametrize(
    ("payload", "status_code", "status_detail"),
    [
        ({"username": "foo"}, 422, None),
        ({"github_token": "foo"}, 401, None),
    ],
)
@pytest.mark.asyncio()
async def test_login_with_github_token(
    async_client: AsyncClient,
    session: AsyncSession,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    response = await async_client.post("/login/token", json=payload)
    assert response.status_code == status_code
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail


@pytest.mark.parametrize(
    ("payload", "status_code", "status_detail"),
    [
        ({"username": "foo"}, 422, None),
        ({"username": "foo", "password": "bar"}, 401, None),
        # ({"username": "first_login", "password": "first_pwd"}, 200, None),
    ],
)
@pytest.mark.asyncio()
async def test_login_with_creds(
    async_client: AsyncClient,
    session: AsyncSession,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    response = await async_client.post("/login/creds", data=payload)
    assert response.status_code == status_code
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        response_json = response.json()
        assert response_json["token_type"] == "Bearer"  # noqa: S105
        assert isinstance(response_json["access_token"], str)
        assert len(response_json["access_token"]) == 10


@pytest.mark.parametrize(
    ("payload", "status_code", "status_detail", "expected_response"),
    [
        ({"code": "foo", "redirect_uri": 0}, 422, None, None),
        # Github 422
        ({"code": "foo", "redirect_uri": ""}, 422, None, None),
        ({"code": "foo", "redirect_uri": "https://quackai.com"}, 401, None, None),
    ],
)
@pytest.mark.asyncio()
async def test_request_github_token_from_code(
    async_client: AsyncClient,
    session: AsyncSession,
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
    expected_response: Union[Dict[str, Any], None],
):
    response = await async_client.post("/login/github", json=payload)
    assert response.status_code == status_code
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if isinstance(expected_response, dict):
        assert response.json() == expected_response


@pytest.mark.parametrize(
    ("scope", "redirect_uri", "status_code"),
    [
        ("read:user%20user:email%20repo", "https://app.quack-ai.com", 307),
    ],
)
@pytest.mark.asyncio()
async def test_authorize_github(
    async_client: AsyncClient,
    session: AsyncSession,
    scope: Any,
    redirect_uri: Any,
    status_code: int,
):
    response = await async_client.get("/login/authorize", params={"scope": scope, "redirect_uri": redirect_uri})
    assert response.status_code == status_code
    for key, _, val in response.headers._list:
        if key == "location":
            u = urlparse(val)
            assert u.scheme == "https"
            assert u.netloc == "github.com/login/oauth/authorize"
            q = parse_qs(u.query)
            assert q.keys() == {"scope", "client_id", "redirect_uri"}
            assert q["scope"][0] == scope
            assert q["redirect_uri"][0] == redirect_uri
