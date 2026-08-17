from __future__ import annotations

from scripts.staging_preflight import validate_environment


def _base() -> dict[str, str]:
    return {
        "ENV": "staging",
        "ALLOW_DEGRADED_REDIS": "false",
        "REDIS_URL": "rediss://redis-staging.internal:6380/0",
        "CORS_ALLOWED_ORIGINS": "https://staging.gula-platform.example",
        "CORS_ORIGINS": "https://staging.gula-platform.example",
        "TRUSTED_HOSTS": "api.staging.gula-platform.example",
        "AUDIT_ANCHOR_DIR": "/tmp/gula-test-audit-anchors",
        "ACCOUNT_CREATION_STAGING_ONLY": "true",
        "PUBLIC_SELF_REGISTRATION_ENABLED": "false",
        "GULA_ADAPTER_MODE_NID": "shadow",
        "MOI_NID_API_URL": "https://nid-sandbox.gov.example",
        "MOI_NID_API_KEY": "sandbox-key-not-real",
        "STAGING_EGRESS_ALLOWLIST": "nid-sandbox.gov.example:443",
        "GOV_CONNECTOR_URLS": "https://health-sandbox.gov.example",
    }


def test_staging_preflight_accepts_consistent_sandbox_configuration() -> None:
    assert validate_environment(_base()) == []


def test_staging_preflight_rejects_degraded_redis_and_http_connector() -> None:
    values = _base()
    values["ALLOW_DEGRADED_REDIS"] = "true"
    values["REDIS_URL"] = "redis://redis-staging.internal:6379/0"
    values["GOV_CONNECTOR_URLS"] = "http://government.example"
    codes = {finding.code for finding in validate_environment(values)}
    assert {"REDIS_DEGRADED_ALLOWED", "REDIS_TLS_REQUIRED", "CONNECTOR_HTTPS_REQUIRED"} <= codes


def test_staging_preflight_rejects_nid_production_url() -> None:
    values = _base()
    values["MOI_NID_API_URL"] = "https://nid.production.example"
    codes = {finding.code for finding in validate_environment(values)}
    assert "NID_PRODUCTION_URL_FORBIDDEN" in codes


def test_staging_preflight_rejects_live_without_credentials() -> None:
    values = _base()
    values["GULA_ADAPTER_MODE_NID"] = "live"
    values["MOI_NID_API_KEY"] = ""
    codes = {finding.code for finding in validate_environment(values)}
    assert "NID_CREDENTIALS_MISSING" in codes


def test_staging_preflight_rejects_stub_when_external_gate_is_required() -> None:
    values = _base()
    values["GULA_ADAPTER_MODE_NID"] = "stub"
    values["STAGING_REQUIRE_EXTERNAL_NID"] = "true"
    codes = {finding.code for finding in validate_environment(values)}
    assert "NID_STUB_NOT_ALLOWED" in codes
