import pytest
from fastapi import HTTPException
from jose import jwt
from datetime import datetime, timedelta
from uuid import uuid4
from llmsync.config import settings
from llmsync.auth import decode_access_token, create_access_token, create_refresh_token

def test_jwt_missing_user_id_claim():
    """JWT without user_id claim should be rejected."""
    # Create JWT without user_id
    payload = {
        "exp": datetime.utcnow() + timedelta(days=7),
        "sub": "some-user-id"  # Wrong claim
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(HTTPException) as exc_info:
        decode_access_token(token)

    assert exc_info.value.status_code == 401
    assert "user_id" in str(exc_info.value.detail).lower()

def test_create_and_decode_token():
    """Valid token should encode and decode correctly."""
    user_id = uuid4()

    token = create_access_token(user_id)
    decoded = decode_access_token(token)

    assert decoded["user_id"] == str(user_id)
    assert "exp" in decoded

def test_refresh_token_creation():
    """Refresh token should be created with correct type."""
    user_id = uuid4()

    token = create_refresh_token(user_id)

    # Decode manually to check payload
    decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    assert decoded["user_id"] == str(user_id)
    assert decoded["type"] == "refresh"
