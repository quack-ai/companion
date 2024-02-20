from typing import Any, Dict, Union

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User

USER_TABLE = [
    {"id": 1, "login": "first_login", "hashed_password": "hashed_first_pwd", "scope": "admin"},
    {"id": 2, "login": "second_login", "hashed_password": "hashed_second_pwd", "scope": "user"},
]


@pytest_asyncio.fixture(scope="function")
async def code_session(async_session: AsyncSession, monkeypatch):
    for entry in USER_TABLE:
        async_session.add(User(**entry))
    await async_session.commit()
    yield async_session


@pytest.mark.parametrize(
    ("user_idx", "payload", "status_code", "status_detail"),
    [
        (None, {"role": "user", "content": "Is Python 3.11 faster than 3.10?"}, 401, "Not authenticated"),
        (0, {"role": "alien", "content": "Is Python 3.11 faster than 3.10?"}, 422, None),
        (0, {"role": "user", "content": "Is Python 3.11 faster than 3.10?"}, 200, None),
    ],
)
@pytest.mark.asyncio()
async def test_chat(
    async_client: AsyncClient,
    code_session: AsyncSession,
    user_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(USER_TABLE[user_idx]["id"], USER_TABLE[user_idx]["scope"].split())

    response = await async_client.post("/code/chat", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
