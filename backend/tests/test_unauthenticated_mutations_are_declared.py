"""No mutating endpoint answers an unauthenticated request unless it is declared (NR-108).

Measured by execution, not by reading decorators. Reading is unreliable in both
directions here: `include_router(..., dependencies=[...])` never appears in a
route's own `dependant`, so a statically "unguarded" route may be guarded by
its mount, and a statically guarded one may be mounted somewhere that bypasses
it. The only honest question is what the served application does when a request
arrives with no credential, so this asks it -- once per mutating operation in
the app's own OpenAPI contract.

What the first run found. 1089 mutating operations; 1031 answered 401. Of the
58 that reached a handler, most are the authentication surface itself, which
must be reachable, but three NIAM sub-routers were mounted with no dependency
and had no actor dependency of their own either:

    POST /niam/sessions/{session_uuid}/terminate            log anyone out
    POST /niam/sessions/account/{account_id}/terminate-all   log an account out
    POST /niam/devices/{device_uuid}/trust                   elevate a device
    POST /niam/devices/{device_uuid}/revoke
    POST /niam/devices/register
    POST /niam/persons/                                      write the registry

`trust` mattered most: a trusted device feeds the adaptive-authentication
decision, so an unauthenticated caller could weaken the MFA outcome for a
device. Those three routers now carry `_AUTH_REQUIRED`, and this test is what
keeps them carrying it.

The ledger below is a ratchet. DECLARED_PUBLIC and DECLARED_RETIRED are
deliberate. DECLARED_GAP is not: each entry is a known, unfixed gap, and the
set may only SHRINK. An operation that reaches its handler without a credential
and is in none of the three fails this test.
"""
from __future__ import annotations

import logging
import re
from collections import Counter

import pytest

# Refusals. 403 counts: the request was identified and rejected.
REFUSED = {401, 403}

#: A floor, so a run that stops enumerating cannot pass vacuously.
#: Measured at 1089 on 2026-09-18.
MINIMUM_MUTATING_OPERATIONS = 1000

#: Reachable without a credential BY DESIGN. Nothing here can be gated: it is
#: the authentication surface itself, plus one pure calculation.
DECLARED_PUBLIC: dict[tuple[str, str], str] = {
    ("POST", "/login"): "legacy login",
    ("POST", "/logout"): "session teardown; must work without a live credential",
    ("POST", "/register"): "self-service registration",
    ("POST", "/register/citizen"): "self-service registration",
    ("POST", "/register/doctor"): "self-service registration",
    ("POST", "/citizen/login"): "citizen portal login",
    ("POST", "/citizen/logout"): "session teardown",
    ("POST", "/auth/forgot-password"): "password reset request",
    ("POST", "/auth/reset-password"): "password reset with a mailed token",
    ("POST", "/auth/verification/request"): "contact verification challenge",
    ("POST", "/auth/verification/confirm"): "contact verification response",
    ("POST", "/auth/saml/acs"): "SAML assertion consumer; the assertion is the credential",
    ("POST", "/oauth2/token"): "OAuth2 token endpoint; client credentials are in the body",
    ("POST", "/oauth2/introspect"): "OAuth2 introspection; the token is the credential",
    ("POST", "/oauth2/revoke"): "OAuth2 revocation; the token is the credential",
    ("POST", "/niam/auth/login"): "NIAM login",
    ("POST", "/niam/auth/logout"): "NIAM session teardown",
    ("POST", "/niam/auth/refresh"): "NIAM refresh; the refresh token is the credential",
    ("POST", "/niam/account-requests/"):
        "self-service intake BY DESIGN -- rate-limited, idempotency-keyed, and its "
        "docstring states it never creates or activates an account",
    ("POST", "/demo/access"):
        "the public synthetic demo entry, on DemoReadOnlyMiddleware's allow-list",
    ("POST", "/lims/quality/indicators/{indicator_id}/evaluate"):
        "a pure calculation: no Session parameter, no persistence, reads two "
        "module-level dicts of published ISO 15189 and CAP thresholds. The "
        "sibling GET /lims/quality/indicators that lists those same thresholds "
        "is public too, so gating the calculator over public data would be "
        "theatre rather than a control",
}

#: Authenticated, but by a SHARED SECRET or a DEVICE token rather than a user
#: credential, so an anonymous HTTP probe cannot produce a 401 from them.
DECLARED_SECRET_AUTHENTICATED: dict[tuple[str, str], str] = {
    ("POST", "/device-integration/wearables/webhook/{provider}"):
        "requires X-Signature-256 over the body and rejects a missing signature "
        "with 401; the probe sees 404 only because the dummy provider name is "
        "not in the allow-list",
    ("POST", "/api/v1/telegram/webhook"):
        "requires the Telegram secret token, compared with hmac.compare_digest, "
        "plus an allowed chat-id list; 503 here means unconfigured in the test "
        "environment",
    ("POST", "/edge/agent/tasks/{task_uid}/result"):
        "per-device token signed with EDGE_TASK_SIGNING_KEY in the Authorization "
        "header; the module documents that it never accepts a user JWT and never "
        "calls get_current_user",
}

#: Retired. Every route answers 410 Gone, so there is nothing behind them.
DECLARED_RETIRED: dict[tuple[str, str], str] = {
    ("POST", "/niam/accounts/"): "410 Gone",
    ("POST", "/niam/accounts/{account_uuid}/lock"): "410 Gone",
    ("POST", "/niam/accounts/{account_uuid}/unlock"): "410 Gone",
}

#: Behind a feature flag whose check runs BEFORE the credential check, so they
#: answer 503 rather than 401 while the flag is off. That is not evidence of
#: authorization, so it was proven separately: with ENABLE_AI_DATASET=true and
#: ENABLE_AI_FEEDBACK=true all four answer
#: 401 AUTHENTICATION_REQUIRED. Verified 2026-09-18.
DECLARED_FLAG_GATED: dict[tuple[str, str], str] = {
    ("POST", "/api/ai/feedback"): "ENABLE_AI_FEEDBACK; 401 when enabled",
    ("POST", "/api/ai/interactions"): "ENABLE_AI_DATASET; 401 when enabled",
    ("POST", "/api/ai/interactions/{interaction_id}/refs"):
        "ENABLE_AI_DATASET; 401 when enabled",
    ("POST", "/api/ai/unresolved"): "ENABLE_AI_DATASET; 401 when enabled",
}

#: KNOWN GAPS, not approved: operations that answer an unauthenticated request
#: and should not. SHRINK-ONLY. It is empty, and _GAP_CEILING keeps it that way:
#: a new unauthenticated mutating endpoint is a defect to fix, never an entry to
#: add here.
DECLARED_GAP: dict[tuple[str, str], str] = {}

_GAP_CEILING = 0


@pytest.fixture(scope="module")
def probe():
    """(method, path) -> status for an unauthenticated request, once per op."""
    logging.disable(logging.CRITICAL)
    from app.core import startup_guard
    from app.factory import create_app
    from fastapi.testclient import TestClient

    app = create_app()
    # ReadinessMiddleware 503s every non-whitelisted path until the startup
    # guard passes, which would make this measure readiness instead of
    # authorization. Flipped for the probe only; no application code changes.
    was_ready = startup_guard.system_ready
    original = startup_guard.is_system_ready
    startup_guard.set_system_ready(True, "NR-108 probe")
    startup_guard.is_system_ready = lambda: (True, "NR-108 probe")  # type: ignore[assignment]

    try:
        spec = app.openapi()
        mutating = {"post", "put", "patch", "delete"}
        ops = sorted({
            (method.upper(), path)
            for path, operations in spec["paths"].items()
            for method in operations
            if method in mutating
        })
        client = TestClient(app, raise_server_exceptions=False)
        out: dict[tuple[str, str], int | str] = {}
        for method, path in ops:
            url = re.sub(r"\{[^}]+\}", "1", path)
            try:
                out[(method, path)] = client.request(method, url, json={}).status_code
            except Exception as exc:
                out[(method, path)] = f"EXC:{type(exc).__name__}"
        yield out
    finally:
        # Restore BOTH, not just the function. Leaving system_ready True would
        # leak into any test that runs after this one in the same process and
        # make a not-ready platform look ready.
        startup_guard.is_system_ready = original  # type: ignore[assignment]
        startup_guard.set_system_ready(was_ready, "NR-108 probe restored")
        logging.disable(logging.NOTSET)


def test_the_probe_still_sees_the_api_it_is_supposed_to_check(probe) -> None:
    """Guard the guard, in both directions."""
    assert len(probe) >= MINIMUM_MUTATING_OPERATIONS, (
        f"only {len(probe)} mutating operations enumerated, expected at least "
        f"{MINIMUM_MUTATING_OPERATIONS}. Either the API shrank -- lower the "
        f"floor deliberately -- or this probe has stopped seeing it, in which "
        f"case every assertion below is vacuous."
    )
    refused = sum(1 for s in probe.values() if s in REFUSED)
    assert refused > len(probe) // 2, (
        f"only {refused} of {len(probe)} operations refused an "
        f"unauthenticated request. A probe whose requests never arrive would "
        f"look like this, so treat it as broken rather than as a finding."
    )
    # And the inverse: if NOTHING reaches a handler, the probe is sending
    # something that cannot reach one -- the authentication surface itself must
    # be reachable.
    assert refused < len(probe), (
        "every single operation refused, including login and registration. "
        "That is not possible for a working API, so the probe is at fault."
    )


def test_login_is_reachable_and_a_clinical_write_is_not(probe) -> None:
    """A concrete pair, so the measurement cannot be uniformly wrong."""
    login = next((s for (m, p), s in probe.items() if p == "/login" and m == "POST"), None)
    assert login is not None, "POST /login is not in the contract"
    assert login not in REFUSED, (
        f"POST /login refused an anonymous request with {login}; nobody could "
        f"ever authenticate, so the rest of this file is measuring nothing"
    )
    patients = next((s for (m, p), s in probe.items() if p == "/patients" and m == "POST"), None)
    if patients is not None:
        assert patients in REFUSED, (
            f"POST /patients answered an unauthenticated request with "
            f"{patients} -- a clinical write is open"
        )


def test_no_undeclared_operation_answers_an_unauthenticated_request(probe) -> None:
    declared = (set(DECLARED_PUBLIC) | set(DECLARED_SECRET_AUTHENTICATED)
                | set(DECLARED_RETIRED) | set(DECLARED_FLAG_GATED)
                | set(DECLARED_GAP))
    reached = {op for op, status in probe.items() if status not in REFUSED}
    undeclared = sorted(reached - declared)
    assert not undeclared, (
        "these mutating operations answered a request with no credential and "
        "are declared nowhere. Either gate them or declare them with a reason:"
        + "".join(f"\n  {probe[op]}  {op[0]:6} {op[1]}" for op in undeclared)
    )


def test_the_declarations_have_not_rotted(probe) -> None:
    """Every declared operation must still exist and still be reachable."""
    stale_missing = sorted(
        op for op in (set(DECLARED_PUBLIC) | set(DECLARED_SECRET_AUTHENTICATED)
                      | set(DECLARED_RETIRED) | set(DECLARED_FLAG_GATED)
                      | set(DECLARED_GAP))
        if op not in probe
    )
    assert not stale_missing, (
        f"declared operations that no longer exist in the contract: "
        f"{stale_missing}. Remove them so the ledger keeps meaning something."
    )
    now_guarded = sorted(op for op in DECLARED_GAP if probe[op] in REFUSED)
    assert not now_guarded, (
        f"these are declared as gaps but now refuse an unauthenticated "
        f"request: {now_guarded}. Remove them from DECLARED_GAP -- that is the "
        f"ratchet tightening, which is the point."
    )


def test_the_gap_ledger_cannot_grow(probe) -> None:
    """The one assertion that makes this a ratchet rather than a record."""
    assert len(DECLARED_GAP) <= _GAP_CEILING, (
        f"DECLARED_GAP has {len(DECLARED_GAP)} entries, above the ceiling of "
        f"{_GAP_CEILING}. It may only shrink. A new unauthenticated mutating "
        f"endpoint is a defect to fix, not an entry to add."
    )


def test_the_niam_identity_routers_are_gated(probe) -> None:
    """The NR-108 fix itself, asserted by behaviour rather than by source."""
    must_refuse = [
        ("POST", "/niam/sessions/{session_uuid}/terminate"),
        ("POST", "/niam/sessions/account/{account_id}/terminate-all"),
        ("POST", "/niam/devices/{device_uuid}/trust"),
        ("POST", "/niam/devices/{device_uuid}/revoke"),
        ("POST", "/niam/devices/register"),
        ("POST", "/niam/persons/"),
    ]
    missing = [op for op in must_refuse if op not in probe]
    assert not missing, (
        f"these operations are no longer served, so this test no longer "
        f"proves anything about them: {missing}"
    )
    open_ops = {op: probe[op] for op in must_refuse if probe[op] not in REFUSED}
    assert not open_ops, (
        f"identity operations answered an unauthenticated request: {open_ops}. "
        f"Session termination, device trust and registry writes must never be "
        f"reachable without a credential."
    )


def test_the_status_distribution_is_reported(probe) -> None:
    """Not an assertion about the platform -- a readable record in the log."""
    counts = Counter(str(s) for s in probe.values())
    print(f"\nunauthenticated-request status distribution over "
          f"{len(probe)} mutating operations: {dict(counts)}")
    assert counts
