import pytest
from app.security.service_accounts import validate_requested_scopes


def test_service_account_scopes_are_normalized_and_deduplicated():
    assert validate_requested_scopes([" patients:read ", "patients:read"]) == ["patients:read"]


def test_unknown_service_account_scope_is_rejected():
    with pytest.raises(ValueError, match="Unsupported service account scopes"):
        validate_requested_scopes(["patients:read", "admin:*", "*"])
