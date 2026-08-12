#!/usr/bin/env python3
"""Guard client transport and local-secret invariants in tracked source."""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.exists():
        raise SystemExit(f"missing required security file: {relative}")
    return path.read_text(encoding="utf-8")


def require(text: str, marker: str, label: str, errors: list[str]) -> None:
    if marker not in text:
        errors.append(f"{label}: required marker is missing: {marker}")


def forbid(text: str, marker: str, label: str, errors: list[str]) -> None:
    if marker in text:
        errors.append(f"{label}: forbidden marker found: {marker}")


def main() -> int:
    errors: list[str] = []

    android_release = read("mobile/android/app/src/main/res/xml/network_security_config.xml")
    require(android_release, "api.gula-platform.org", "Android release network config", errors)
    require(android_release, "g9F05XEMwoJmxPy/otHWQ4jyLsg5jcPWyh4PYBrOEM0=", "Android release pin", errors)
    forbid(android_release, 'cleartextTrafficPermitted="true"', "Android release network config", errors)
    forbid(android_release, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=", "Android release pin", errors)
    forbid(android_release, "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=", "Android release pin", errors)
    forbid(android_release, "api.gulaplatform.com", "Android release network config", errors)

    ios_auth = read("mobile/ios/Gula/Core/Networking/APIAuthMiddleware.swift")
    forbid(ios_auth, "URLSession.shared", "iOS auth refresh transport", errors)
    require(ios_auth, "refreshTokenForMiddleware", "iOS auth refresh transport", errors)

    ios_pinner = read("mobile/ios/Gula/Core/Security/CertificatePinner.swift")
    require(ios_pinner, "subjectPublicKeyInfo", "iOS certificate pinner", errors)
    require(ios_pinner, "g9F05XEMwoJmxPy/otHWQ4jyLsg5jcPWyh4PYBrOEM0=", "iOS certificate pin", errors)

    desktop_config = read("hospital_desktop/config.py")
    require(desktop_config, 'DEFAULT_API_BASE_URL = "https://api.gula-platform.org/api/v1"', "hospital desktop default URL", errors)
    forbid(desktop_config, 'api_base_url: str = "http://localhost:8000"', "hospital desktop default URL", errors)

    desktop_client = read("hospital_desktop/api_client.py")
    forbid(desktop_client, 'mount("http://"', "hospital desktop transport", errors)
    require(desktop_client, "allow_redirects=False", "hospital desktop redirect policy", errors)
    require(desktop_client, "validate_api_base_url", "hospital desktop URL validation", errors)

    flutter_auth = read("mobile/desktop/lib/core/api/api_interceptor.dart")
    forbid(flutter_auth, "Dio().fetch", "Flutter auth retry transport", errors)
    require(flutter_auth, "EndpointGuardInterceptor", "Flutter endpoint guard", errors)

    flutter_client = read("mobile/desktop/lib/core/api/api_client.dart")
    require(flutter_client, "validateApiBaseUrl", "Flutter base URL validation", errors)
    require(flutter_client, "followRedirects: false", "Flutter redirect policy", errors)

    flutter_secure = read("mobile/desktop/lib/core/security/secure_config.dart")
    forbid(flutter_secure, "DateTime.now().microsecondsSinceEpoch", "Flutter key generation", errors)
    require(flutter_secure, "Random.secure()", "Flutter key generation", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("OK: client transport security invariants hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
