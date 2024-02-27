from typing import Any, Dict, List, Union

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.post("/repos", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k not in {"id", "created_at"}} == expected_response


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail", "expected_idx"),
    [
        (None, 1, 401, "Not authenticated", None),
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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.get(f"/repos/{repo_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == pytest.repo_table[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail", "expected_response"),
    [
        (None, 401, "Not authenticated", None),
        (0, 200, None, pytest.repo_table),
        (1, 403, "Incompatible token scope.", None),
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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.get("/repos", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == expected_response


@pytest.mark.parametrize(
    ("user_idx", "repo_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 0, 422, None),
        (0, 100, 404, "Table Repository has no corresponding entry."),
        (0, 1, 200, None),
        (0, 2, 200, None),
        (1, 1, 403, "Incompatible token scope."),
        (1, 2, 403, "Incompatible token scope."),
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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.delete(f"/repos/{repo_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() is None
