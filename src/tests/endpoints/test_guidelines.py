from typing import Any, Dict, List, Union

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession


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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.post("/guidelines", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {
            k: v for k, v in response.json().items() if k not in {"created_at", "updated_at", "id", "creator_id"}
        } == payload
        assert response.json()["id"] == max(entry["id"] for entry in pytest.guideline_table) + 1


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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.get(f"/guidelines/{guideline_id}", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == pytest.guideline_table[expected_idx]


@pytest.mark.parametrize(
    ("user_idx", "status_code", "status_detail", "expected_result"),
    [
        (None, 401, "Not authenticated", None),
        (0, 200, None, pytest.guideline_table),
        (1, 200, None, pytest.guideline_table[1:]),
    ],
)
@pytest.mark.asyncio()
async def test_fetch_guidelines(
    async_client: AsyncClient,
    guideline_session: AsyncSession,
    user_idx: Union[int, None],
    status_code: int,
    status_detail: Union[str, None],
    expected_result: Union[List[Dict[str, Any]], None],
):
    auth = None
    if isinstance(user_idx, int):
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.get("/guidelines", headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert response.json() == expected_result


@pytest.mark.parametrize(
    ("user_idx", "guideline_id", "status_code", "status_detail"),
    [
        (None, 1, 401, "Not authenticated"),
        (0, 0, 422, None),
        (0, 100, 404, "Table Guideline has no corresponding entry."),
        (0, 1, 200, None),
        (0, 2, 200, None),
        (1, 1, 403, None),
        (1, 2, 200, None),
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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

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
        (1, 1, {"content": "New guideline details"}, 403, None, 0),
        (1, 2, {"content": "New guideline details"}, 200, None, 1),
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
        auth = await pytest.get_token(pytest.user_table[user_idx]["id"], pytest.user_table[user_idx]["scope"].split())

    response = await async_client.patch(f"/guidelines/{guideline_id}", json=payload, headers=auth)
    assert response.status_code == status_code, print(response.__dict__)
    if isinstance(status_detail, str):
        assert response.json()["detail"] == status_detail
    if response.status_code // 100 == 2:
        assert {k: v for k, v in response.json().items() if k != "updated_at"} == {
            **{
                k: v
                for k, v in pytest.guideline_table[expected_idx].items()
                if k not in {"title", "details", "updated_at"}
            },
            **payload,
        }
