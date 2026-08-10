"""ABAC route enforcement for protected HTTP routes (Wave B unit B1).

This module is the enforcement point that reuses the certified A1 engine
(``app.security.abac``) on the FastAPI request path:

* **Server-derived subject** — the ABAC subject map is always built from the
  token-verified principal returned by ``get_current_identity`` via
  ``subject_from_principal``. Client-supplied subject attributes are never
  accepted.
* **Fail-closed** — the engine denies when no rule matches; an undecidable
  subject (unsupported principal type) is also denied.
* **Deterministic ordering** — authentication (401) always runs before the
  ABAC decision (403), and the decision is computed before the route handler
  is invoked.
* **Auditable decisions** — every decision is recorded in the engine's
  decision log and streamed to structured logs via the ``on_decision`` hook.
  Immutable hash-chain persistence of route decisions is the scope of a later
  Wave-B unit (audit integration).

The dependency factory ``require_abac`` is the single wire-in point used by
the NIAM composite router and the Domain Platform router.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, HTTPException, Request

from app.identity.security import NIAMPrincipal, get_current_identity
from app.security.abac import (
    ABACDecision,
    ABACEngine,
    ABACRequest,
    Effect,
    subject_from_principal,
)
from app.security.abac_policies import build_default_abac_rules

logger = logging.getLogger("gula.security.abac.enforcement")

_ACTION_BY_METHOD = {
    "GET": "read",
    "HEAD": "read",
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

_ENGINE: ABACEngine | None = None


def get_abac_engine() -> ABACEngine:
    """Return the process-wide ABAC engine, lazily initialized with defaults."""
    global _ENGINE
    if _ENGINE is None:
        engine = ABACEngine(on_decision=_log_decision)
        for rule in build_default_abac_rules():
            engine.add_rule(rule)
        _ENGINE = engine
    return _ENGINE


def reset_abac_engine() -> ABACEngine:
    """Rebuild the engine singleton (test isolation only)."""
    global _ENGINE
    _ENGINE = None
    return get_abac_engine()


def _log_decision(decision: ABACDecision) -> None:
    logger.info(
        "abac_decision resource=%s action=%s effect=%s subject=%s rule=%s reason=%s",
        decision.resource,
        decision.action,
        decision.effect.value,
        decision.subject_id,
        decision.rule_id,
        decision.reason,
    )


def method_to_action(method: str) -> str:
    """Map an HTTP method to an ABAC action verb."""
    return _ACTION_BY_METHOD.get(method.upper(), method.lower())


def enforce_abac_decision(
    principal: Any,
    resource: str,
    action: str,
    path: str,
    purpose: str | None = None,
) -> ABACDecision:
    """Build a server-derived ABAC request and enforce the decision.

    Raises ``HTTPException(403)`` on denial or on an undecidable subject
    (fail-closed). Returns the recorded decision on allow.
    """
    try:
        subject = subject_from_principal(principal)
    except TypeError:
        logger.error(
            "abac fail-closed: cannot derive subject from principal type %s",
            type(principal).__name__,
        )
        raise HTTPException(status_code=403, detail="Access denied") from None

    request = ABACRequest(
        resource=resource,
        action=action,
        subject=subject,
        resource_attrs={"path": path, "method": action},
        environment={
            "path": path,
            "method": action,
            "hour_of_day": datetime.now(UTC).hour,
        },
        purpose=purpose,
    )
    decision = get_abac_engine().decide(request)
    if decision.effect is not Effect.ALLOW:
        logger.info(
            "abac denied resource=%s action=%s subject=%s rule=%s reason=%s",
            decision.resource,
            decision.action,
            decision.subject_id,
            decision.rule_id,
            decision.reason,
        )
        raise HTTPException(status_code=403, detail="Access denied")
    return decision


def require_abac(resource: str, purpose: str | None = None):
    """FastAPI dependency factory enforcing an ABAC decision on a route.

    Marked with ``_abac_guard = True`` so the route-coverage test can walk the
    flattened dependant tree and prove the guard is present on every protected
    route.
    """

    async def checker(
        request: Request,
        principal: NIAMPrincipal = Depends(get_current_identity),
    ):
        enforce_abac_decision(
            principal,
            resource,
            method_to_action(request.method),
            request.url.path,
            purpose,
        )
        return principal

    checker._abac_guard = True  # type: ignore[attr-defined]
    checker._abac_resource = resource  # type: ignore[attr-defined]
    checker._abac_purpose = purpose  # type: ignore[attr-defined]
    return checker
