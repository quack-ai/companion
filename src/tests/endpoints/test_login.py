from typing import Any, Dict, Union
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User

USER_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_first_pwd", "scope": "user"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_second_pwd", "scope": "user"},
]


@pytest_asyncio.fixture
async def session(async_session: AsyncSession):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
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
