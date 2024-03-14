import pytest
from fastapi import HTTPException
from fastapi.security import SecurityScopes

from app.api.dependencies import get_token_payload
from app.core.security import create_access_token


@pytest.mark.parametrize(
    ("scopes", "token", "expires_minutes", "error_code", "expected_payload"),
    [
        (["admin"], "", None, 406, None),
        (["admin"], {"user_id": "123", "scopes": ["admin"]}, None, 422, None),
        (["admin"], {"sub": "123", "scopes": ["admin"]}, -1, 401, None),
        (["admin"], {"sub": "123", "scopes": ["admin"]}, None, None, {"user_id": 123, "scopes": ["admin"]}),
        (["admin"], {"sub": "123", "scopes": ["user"]}, None, 403, None),
    ],
)
@pytest.mark.asyncio()
async def test_get_token_payload(scopes, token, expires_minutes, error_code, expected_payload):
    _token = await create_access_token(token, expires_minutes) if isinstance(token, dict) else token
    if isinstance(error_code, int):
        with pytest.raises(HTTPException):
            await get_token_payload(SecurityScopes(scopes), _token)
    else:
        payload = await get_token_payload(SecurityScopes(scopes), _token)
        if expected_payload is not None:
            assert payload.model_dump() == expected_payload
