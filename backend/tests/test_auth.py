"""Unit tests for auth (ADR-0021): password hashing/verification, JWT
issuance/verification (app/core/security.py), and deriving the X-Nova-*
header shape from a decoded token's claims (app/api/v1/deps.py)."""
import pytest
from fastapi import HTTPException

from app.api.v1.deps import get_auth_headers
from app.core.security import create_access_token, hash_password, verify_password


def test_hash_password_round_trip():
    hashed = hash_password("Nova123!")
    assert verify_password("Nova123!", hashed)
    assert not verify_password("wrong-password", hashed)


def test_get_auth_headers_derives_business_units_from_token():
    token = create_access_token(
        {"sub": "u1", "business_units": [{"code": "tv", "role": "employee"}, {"code": "plus", "role": "finance"}]}
    )
    headers = get_auth_headers(authorization=f"Bearer {token}")

    assert headers["x-nova-user"] == "u1"
    assert set(headers["x-nova-business-units"].split(",")) == {"tv", "plus"}
    assert headers["x-nova-roles"] == ""


def test_get_auth_headers_bridges_group_admin_to_roles():
    """ADR-0021's "group"/"admin" membership must still satisfy every
    business unit's existing `ALLOWED_ROLES` check (e.g. mcp_servers/tv/auth.py),
    which looks for the "group_admin" role string, not a business unit claim."""
    token = create_access_token({"sub": "u1", "business_units": [{"code": "group", "role": "admin"}]})
    headers = get_auth_headers(authorization=f"Bearer {token}")

    assert headers["x-nova-roles"] == "group_admin"


def test_get_auth_headers_group_employee_is_not_bridged_to_a_role():
    token = create_access_token({"sub": "u1", "business_units": [{"code": "group", "role": "employee"}]})
    headers = get_auth_headers(authorization=f"Bearer {token}")

    assert headers["x-nova-roles"] == ""
    assert "group" in headers["x-nova-business-units"].split(",")


def test_get_auth_headers_rejects_missing_authorization():
    with pytest.raises(HTTPException) as exc_info:
        get_auth_headers(authorization=None)
    assert exc_info.value.status_code == 401


def test_get_auth_headers_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        get_auth_headers(authorization="Bearer not-a-real-token")
    assert exc_info.value.status_code == 401
