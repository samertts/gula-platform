"""NR-102 — a clinical "verification" whose every input came from the caller.

`POST /nursing/medication-admin/verify` was summarised "Verify five rights" and
returned, for a request body of five client-supplied booleans:

    {"passed": true, "message": "All five rights verified"}

The five rights -- right patient, drug, dose, route, time -- are the standard
barrier against medication error. Nothing in that path read the patient record,
the active MedicationRequest, the ordered dose or route, or the scheduled time.
It bound `db: Session = Depends(get_db)` and never referenced it. It wrote
nothing and audited nothing, so the attestation did not survive the response.

Two things make this worth a guard rather than a one-line fix.

First, the codebase already contains the correct shape of this, in the same
clinical domain: `complete_surgical_safety_checklist` in app/routes/hospital.py
takes ten caller booleans -- including consent_verified and site_marked -- and
records them tenant-scoped, under an optimistic lock, with an idempotency key,
through an audited command. It records attestations and never claims to have
verified them. That is what a WHO checklist is, and it is right.

Second, the failure mode is silent. An endpoint that answers "All five rights
verified" is indistinguishable, to a consumer, from one that checked. Nothing
consumed this one yet; the guard exists so that if a medication-administration
screen is ever wired to it, what it returns is honest.

The fix applied is proportionate: the response no longer claims verification and
carries `verified_against_record: false` explicitly, and the attestation is
written to the hash-chained audit log attributed to the clinician, which is what
gives `db` its purpose. ACTUALLY verifying the five rights against the record is
a larger clinical change -- it needs a decision on the right-time tolerance and
on what must happen when a check fails -- and is registered, not guessed at.
"""

from __future__ import annotations

import types
import typing

import pytest
from app.nursing import routes as nursing_routes
from fastapi.routing import APIRoute
from pydantic import BaseModel


@pytest.fixture
def recorded(monkeypatch):
    """Capture audit writes without needing a database."""
    calls: list[dict] = []
    import app.nursing.medication as med

    monkeypatch.setattr(
        med, "log_action",
        lambda db, action, resource_type, **kw: calls.append(
            {"action": action, "resource_type": resource_type, **kw}
        ),
    )
    return calls


def _call(recorded_user=None, **flags):
    user = recorded_user or types.SimpleNamespace(id=77, lab_id=901)
    body = nursing_routes.MedicationVerifyRequest(**flags)
    return nursing_routes.verify_five_rights(body, user, object())


ALL_TRUE = {
    "right_patient": True, "right_drug": True, "right_dose": True,
    "right_route": True, "right_time": True,
}


def test_the_response_never_claims_the_record_was_checked(recorded):
    result = _call(**ALL_TRUE)
    assert result["verified_against_record"] is False, (
        "the response must state explicitly that nothing was checked against the "
        "medication record, rather than leave a consumer to infer it"
    )
    message = result["message"].lower()
    # The false claim is asserted first on purpose: it is the one that would
    # mislead a clinician, so it should be the failure a reader sees.
    assert "all five rights verified" not in message, (
        "the response claims verification for a request whose every input was "
        f"supplied by the caller: {result['message']}"
    )
    assert "attested" in message, f"message does not say it is an attestation: {result['message']}"


def test_a_complete_attestation_is_recorded_and_attributed(recorded):
    _call(**ALL_TRUE)
    assert len(recorded) == 1, "the attestation was not written to the audit log"
    entry = recorded[0]
    assert entry["action"] == "nursing.medication.five_rights_attested"
    assert entry["user_id"] == 77, "the attestation is not attributed to a clinician"
    assert entry["lab_id"] == 901, "the attestation is not tenant-scoped"
    assert entry["details"]["complete"] is True
    assert entry["details"]["verified_against_record"] is False, (
        "the audit record must not imply the record was checked either"
    )


def test_a_partial_attestation_is_recorded_rather_than_discarded(recorded):
    result = _call(**{**ALL_TRUE, "right_drug": False, "right_time": False})
    assert result["attested"] is False
    assert "right_drug" in result["message"] and "right_time" in result["message"]
    assert len(recorded) == 1, (
        "a clinician declining to attest two of the five rights is exactly the "
        "event worth keeping, and it must not be dropped"
    )
    checks = recorded[0]["details"]["checks"]
    assert checks["right_drug"] is False and checks["right_time"] is False


def test_the_attestation_is_not_a_hidden_gate(recorded):
    """It must not silently authorise anything: it reports, it does not permit."""
    result = _call(**ALL_TRUE)
    assert set(result) == {
        "attested", "passed", "checks", "message", "verified_against_record",
    }, f"unexpected response shape: {sorted(result)}"


#: Served endpoints whose request body is ENTIRELY caller-supplied booleans.
#: Such an endpoint can only ever record what the caller asserts, so it must
#: never present itself as having checked anything. MAY SHRINK, MAY NEVER GROW
#: without a deliberate decision recorded alongside the new entry.
DECLARED_ALL_BOOLEAN_BODIES = frozenset({
    "POST /nursing/medication-admin/verify",
})


def _all_boolean_body_routes(app) -> set[str]:
    found: set[str] = set()
    routes: list[APIRoute] = []

    def walk(container) -> None:
        for r in getattr(container, "routes", []):
            if isinstance(r, APIRoute):
                routes.append(r)
            elif hasattr(r, "original_router"):
                walk(r.original_router)
            else:
                walk(r)

    walk(app)
    assert len(routes) > 1800, f"route scan looks vacuous ({len(routes)})"

    for r in routes:
        try:
            hints = typing.get_type_hints(r.endpoint)
        except Exception:
            continue
        for pname, t in hints.items():
            # `return` is the response model, not a request body -- reading it
            # as one is how an earlier pass mistook GET /consent/check, whose
            # response carries `allowed: bool`, for a client-supplied decision.
            if pname == "return":
                continue
            if isinstance(t, type) and issubclass(t, BaseModel) and t.model_fields:
                fields = t.model_fields
                if all(i.annotation is bool for i in fields.values()):
                    for method in sorted(r.methods - {"HEAD", "OPTIONS"}):
                        found.add(f"{method} {r.path}")
            break
    return found


def test_no_new_endpoint_decides_a_clinical_fact_from_caller_booleans():
    from app.factory import create_app

    current = _all_boolean_body_routes(create_app())
    new = current - DECLARED_ALL_BOOLEAN_BODIES
    assert not new, (
        "these endpoints take a body of nothing but caller-supplied booleans. "
        "Such an endpoint records an attestation and cannot verify anything, so "
        "it must not be named or documented as a verification:\n  "
        + "\n  ".join(sorted(new))
    )
    stale = DECLARED_ALL_BOOLEAN_BODIES - current
    assert not stale, (
        "these declared entries no longer exist and must be removed:\n  "
        + "\n  ".join(sorted(stale))
    )
