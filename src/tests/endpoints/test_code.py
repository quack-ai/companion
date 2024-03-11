from typing import Any, Dict, Union

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


@pytest.mark.parametrize(
    ("user_idx", "payload", "status_code", "status_detail"),
    [
        (None, {"content": "Is Python 3.11 faster than 3.10?"}, 401, "Not authenticated"),
        (0, {"role": "user", "content": "Is Python 3.11 faster than 3.10?"}, 422, None),
        (0, [{"content": "Is Python 3.11 faster than 3.10?"}], 422, None),
        (0, [{"role": "user", "content": "Is Python 3.11 faster than 3.10?"}], 422, None),
        (0, {"messages": [{"role": "alien", "content": "Is Python 3.11 faster than 3.10?"}]}, 422, None),
        (
            0,
            [
                {"role": "user", "content": "Is Python 3.11 faster than 3.10?"},
                {"role": "assistant", "content": "yes"},
                {"role": "user", "content": "elaborate"},
            ],
            422,
            None,
        ),
        (
            0,
            {
                "messages": [
                    {"role": "user", "content": "Is Python 3.11 faster than 3.10?"},
                    {"role": "assistant", "content": "yes"},
                    {"role": "alien", "content": "elaborate"},
                ]
            },
            422,
            None,
        ),
        (0, {"messages": [{"role": "user", "content": "Is Python 3.11 faster than 3.10?"}]}, 200, None),
        (
            0,
            {
                "messages": [
                    {"role": "user", "content": "Is Python 3.11 faster than 3.10?"},
                    {"role": "assistant", "content": "yes"},
                    {"role": "user", "content": "elaborate"},
                ]
            },
            200,
            None,
        ),
    ],
)
@pytest.mark.asyncio()
async def test_chat(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    payload: Dict[str, Any],
    status_code: int,
    status_detail: Union[str, None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.post("/code/chat", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
