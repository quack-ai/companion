from datetime import datetime, timedelta

import jwt
import pytest

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password


def test_hash_password():
    pwd1 = "my_password"
    hash_pwd1 = hash_password(pwd1)

    assert hash_pwd1 != pwd1
    assert hash_pwd1 != hash_password(pwd1 + "bis")
    # Check that it's non deterministic
    assert hash_pwd1 != hash_password(pwd1)


def test_verify_password():
    pwd1 = "my_password"
    hash_pwd1 = hash_password(pwd1)

    assert verify_password(pwd1, hash_pwd1)
    assert not verify_password("another_try", hash_pwd1)


@pytest.mark.parametrize(
    ("content", "expires_minutes", "expected_delta"),
    [
        ({"data": "my_data"}, 60, 60),
        ({"data": "my_data"}, None, settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    ],
)
def test_create_access_token(content, expires_minutes, expected_delta):
    payload = create_access_token(content, expires_minutes)
    after = datetime.utcnow()
    assert isinstance(payload, str)
    decoded_data = jwt.decode(payload, settings.SECRET_KEY, algorithms=[settings.JWT_ENCODING_ALGORITHM])
    # Verify data integrity
    assert all(v == decoded_data[k] for k, v in content.items())
    # Check expiration
    assert datetime.utcfromtimestamp(decoded_data["exp"]) - timedelta(minutes=expected_delta) < after
