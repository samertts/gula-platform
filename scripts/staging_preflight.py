#!/usr/bin/env python3
"""Fail-closed preflight for GULA staging integrations.

This command validates configuration only. It never calls an external provider.
Exit 0 means the configuration is internally consistent; exit 2 means staging
must not be deployed or an external integration test must not start.
"""
from __future__ import annotations

import os
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True)
class Finding:
    code: str
    message: str


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, values: dict[str, str] | os._Environ[str]) -> list[str]:
    return [item.strip() for item in values.get(name, "").split(",") if item.strip()]


def _placeholder(value: str) -> bool:
    lowered = value.strip().lower()
    return not value.strip() or lowered.startswith(("<", "change-me", "replace-me", "dummy", "example"))


def validate_environment(env: dict[str, str] | None = None) -> list[Finding]:
    values = os.environ if env is None else env
    findings: list[Finding] = []

    environment = values.get("ENV", "").strip().lower()
    if environment != "staging":
        findings.append(Finding("ENV_NOT_STAGING", "ENV must be exactly 'staging'."))

    if _truthy(values.get("ALLOW_DEGRADED_REDIS", "false")):
        findings.append(Finding("REDIS_DEGRADED_ALLOWED", "ALLOW_DEGRADED_REDIS must be false in staging."))

    redis_url = values.get("REDIS_URL", "").strip()
    if not redis_url.startswith("rediss://"):
        findings.append(Finding("REDIS_TLS_REQUIRED", "REDIS_URL must use rediss:// in staging."))
    if _placeholder(redis_url):
        findings.append(Finding("REDIS_URL_MISSING", "REDIS_URL is missing or still a placeholder."))

    origins = _csv("CORS_ORIGINS", values) or _csv("CORS_ALLOWED_ORIGINS", values)
    if not origins:
        findings.append(Finding("CORS_ORIGINS_MISSING", "CORS_ALLOWED_ORIGINS must contain the staging origin."))
    trusted_hosts = _csv("TRUSTED_HOSTS", values)
    if not trusted_hosts:
        findings.append(Finding("TRUSTED_HOSTS_MISSING", "TRUSTED_HOSTS must contain the Staging API host."))
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            findings.append(Finding("CORS_ORIGIN_INVALID", f"CORS origin must be credential-free HTTPS: {origin!r}."))
        if any(marker in origin.lower() for marker in ("localhost", "127.0.0.1", "production", "prod.")):
            findings.append(Finding("CORS_ORIGIN_UNSAFE", f"CORS origin appears non-staging: {origin!r}."))

    nid_mode = values.get("GULA_ADAPTER_MODE_NID", values.get("GULA_ADAPTER_MODE", "stub")).strip().lower()
    if nid_mode not in {"stub", "shadow", "live"}:
        findings.append(Finding("NID_MODE_INVALID", f"Unsupported NID adapter mode: {nid_mode!r}."))
    if _truthy(values.get("STAGING_REQUIRE_EXTERNAL_NID", "false")) and nid_mode == "stub":
        findings.append(Finding("NID_STUB_NOT_ALLOWED", "External NID staging gate requires shadow or live mode."))
    if nid_mode in {"shadow", "live"}:
        nid_url = values.get("MOI_NID_API_URL", "").strip()
        nid_key = values.get("MOI_NID_API_KEY", "").strip()
        parsed = urlparse(nid_url)
        if parsed.scheme != "https" or not parsed.netloc:
            findings.append(Finding("NID_HTTPS_REQUIRED", "MOI_NID_API_URL must be a valid HTTPS sandbox URL."))
        if _placeholder(nid_url) or _placeholder(nid_key):
            findings.append(Finding("NID_CREDENTIALS_MISSING", "NID shadow/live requires non-placeholder sandbox URL and API key."))
        if any(marker in nid_url.lower() for marker in ("production", "prod.", "live.")):
            findings.append(Finding("NID_PRODUCTION_URL_FORBIDDEN", "NID URL appears to target production; staging must use sandbox."))

    connector_urls = _csv("GOV_CONNECTOR_URLS", values)
    for connector_url in connector_urls:
        parsed = urlparse(connector_url)
        if parsed.scheme != "https" or not parsed.netloc:
            findings.append(Finding("CONNECTOR_HTTPS_REQUIRED", f"Government connector must use HTTPS: {connector_url!r}."))
        if any(marker in connector_url.lower() for marker in ("production", "prod.", "live.")):
            findings.append(Finding("CONNECTOR_PRODUCTION_URL_FORBIDDEN", f"Connector URL appears to target production: {connector_url!r}."))

    if _truthy(values.get("ACCOUNT_CREATION_STAGING_ONLY", "false")) and _truthy(values.get("PUBLIC_SELF_REGISTRATION_ENABLED", "false")):
        findings.append(Finding("PUBLIC_REGISTRATION_CONFLICT", "PUBLIC_SELF_REGISTRATION_ENABLED must remain false while ACCOUNT_CREATION_STAGING_ONLY is true."))

    anchor_dir = values.get("AUDIT_ANCHOR_DIR", "").strip()
    if not anchor_dir:
        findings.append(Finding("AUDIT_ANCHOR_DIR_MISSING", "AUDIT_ANCHOR_DIR must point to a writable Staging volume."))
    else:
        anchor_path = Path(anchor_dir).expanduser()
        try:
            anchor_path.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(prefix=".staging-preflight-", dir=anchor_path, delete=True):
                pass
        except OSError as exc:
            findings.append(Finding("AUDIT_ANCHOR_DIR_NOT_WRITABLE", f"AUDIT_ANCHOR_DIR is not writable: {exc}"))

    allowlist = _csv("STAGING_EGRESS_ALLOWLIST", values)
    if nid_mode in {"shadow", "live"} and not allowlist:
        findings.append(Finding("EGRESS_ALLOWLIST_MISSING", "STAGING_EGRESS_ALLOWLIST is required for NID shadow/live."))
    for value in allowlist:
        if "://" in value:
            findings.append(Finding("EGRESS_ALLOWLIST_FORMAT", "Egress allowlist must contain host[:port] values, not URLs."))
            break

    return findings


def main() -> int:
    findings = validate_environment()
    if findings:
        sys.stdout.write("STAGING PREFLIGHT: BLOCKED\n")
        for finding in findings:
            sys.stdout.write(f"- {finding.code}: {finding.message}\n")
        return 2
    sys.stdout.write("STAGING PREFLIGHT: PASS\n")
    sys.stdout.write("No external calls were made; configuration is internally consistent.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
