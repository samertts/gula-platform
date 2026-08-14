from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from app.routes.admin_log_level import _ALLOWED_LOGGER_PREFIX, _PRODUCTION_LEVELS
from app.routes.ai_platform import _assert_session_owner
from app.security.saml_service import parse_saml_response, verify_saml_signature
from defusedxml import ElementTree as ET
from fastapi import HTTPException


def _user(user_id: int, lab_id: int):
    return SimpleNamespace(id=user_id, lab_id=lab_id)


def test_ai_session_owner_rejects_cross_user_access() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _assert_session_owner(
            SimpleNamespace(user_id=22, lab_id=7),
            _user(user_id=23, lab_id=7),
        )
    assert exc_info.value.status_code == 404


def test_ai_session_owner_rejects_cross_lab_access() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _assert_session_owner(
            SimpleNamespace(user_id=22, lab_id=7),
            _user(user_id=22, lab_id=8),
        )
    assert exc_info.value.status_code == 404


def test_saml_parser_rejects_malformed_base64() -> None:
    assert parse_saml_response("not-base64") is None


def test_saml_signature_verification_fails_closed_without_signature() -> None:
    assertion = ET.fromstring(b"<Assertion xmlns='urn:oasis:names:tc:SAML:2.0:assertion'/>")
    assert verify_saml_signature(assertion, "not-a-certificate") is False


def test_production_log_levels_exclude_debug() -> None:
    assert "DEBUG" not in _PRODUCTION_LEVELS
    assert _ALLOWED_LOGGER_PREFIX == "gula"


@pytest.mark.parametrize(
    "relative_path",
    [
        "app/document_intelligence/api/routes.py",
        "app/kernel/routes.py",
        "app/national/observability/api/routes.py",
        "app/national/document_platform/api/routes.py",
        "app/command_center/api/routes.py",
        "app/blood_bank/api/routes.py",
        "app/biomedical/api/routes.py",
        "app/critical_care/api/routes.py",
        "app/ems/api/routes.py",
        "app/health_data/routes.py",
        "app/research_platform/routes.py",
        "app/public_health/api/routes.py",
        "app/integration/connectors/routes.py",
        "app/integration/routes.py",
        "app/platform/routes.py",
        "app/governance/routes/analytics_routes.py",
        "app/governance/routes/constitution_routes.py",
        "app/national/ecosystem/gateway/routes.py",
        "app/national/ecosystem/routes.py",
        "app/national/background_platform/api/routes.py",
        "app/national/notification_platform/api/routes.py",
        "app/national/rules_engine/api/routes.py",
        "app/national/scheduling_platform/api/routes.py",
        "app/national/search_platform/api/routes.py",
        "app/national/api/routes/consent.py",
        "app/national/api/routes/fhir.py",
        "app/national/api/routes/referral.py",
        "app/national/api/routes/reference.py",
        "app/reference/routes/patients.py",
        "app/reference/routes/orders.py",
        "app/reference/routes/results.py",
    ],
)
def test_sensitive_router_has_system_admin_guard(relative_path: str) -> None:
    source = (Path(__file__).parents[1] / relative_path).read_text()
    assert 'require_permission("system:admin")' in source
