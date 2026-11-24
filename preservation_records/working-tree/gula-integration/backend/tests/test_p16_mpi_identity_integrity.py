"""P-16 / AUD-F16 (roadmap P-14) — MPI identity integrity regression tests.

Owner mandate requirements exercised here:
  * temporary identity on MPI outage (care is never denied)
  * explicit, monitored reconciliation state and key
  * identity source + confidence + change history in the audit trail
  * no untrusted automatic merge
  * no duplicate identities on retry
  * no silent promotion to a confirmed national identity

All records are synthetic. Tests run against the isolated SQLite test database;
no production service, real patient data, PHI or secret is used.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.models.audit_log import AuditLog
from app.models.patient import Patient
from app.services import patient_service
from app.services.mpi.models import Citizen, IdentityClaim, MergeAudit
from app.services.patient_service import create_patient

SERVICE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "patient_service.py"
NID = "987654321001"
ULID = "01SYNTHETIC16MPI00000000000000"[:26]


def _fake_outcome(method: str = "nid_exact", score: float | None = 0.98):
    citizen = SimpleNamespace(
        citizen_ulid=ULID,
        nid_verified=False,
        status="active",
        merged_into_id=None,
        version=1,
    )
    return SimpleNamespace(
        citizen=citizen,
        claim=SimpleNamespace(match_method=method, match_score=score),
        created=False,
        match_method=method,
        match_score=score,
        features={"source": "synthetic"},
    )


def _create(db, lab, **overrides):
    args = {
        "db": db,
        "lab_id": lab.id,
        "user_id": 1,
        "user_role": "admin",
        "full_name": "Synthetic Patient",
        "phone": "+9647700000001",
        "national_id": NID,
    }
    args.update(overrides)
    return create_patient(**args)


def test_p16_mpi_outage_returns_degraded_temporary_identity_without_denying_care(
    db, make_lab, monkeypatch
):
    """A resolver outage must yield an explicit temporary identity, not a silent null."""
    lab = make_lab()

    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic MPI outage")

    monkeypatch.setattr(patient_service.mpi_resolver, "resolve_identity", _boom)

    result = _create(db, lab)
    assert "patient" in result, result
    patient = result["patient"]
    assert patient["full_name"] == "Synthetic Patient"
    assert patient["citizen_ulid"] is None
    assert patient["mpi_status"] == "degraded"
    assert patient["mpi_identity_source"] == "mpi_resolver"
    assert patient["mpi_confidence"] is None
    assert patient["mpi_reconciliation_required"] is True
    assert patient["mpi_reconciliation_key"] == f"mpi:{lab.id}:{patient['id']}"

    audit = db.query(AuditLog).filter(AuditLog.action == "mpi_resolve_failed").one()
    details = json.loads(audit.details)
    assert details["status"] == "degraded"
    assert details["source"] == "mpi_resolver"
    assert details["reconciliation_key"] == f"mpi:{lab.id}:{patient['id']}"
    assert details["error_type"] == "RuntimeError"
    assert NID not in json.dumps(details), "raw national identifier leaked into audit"


def test_p16_successful_resolution_reports_status_source_and_confidence(db, make_lab, monkeypatch):
    monkeypatch.setattr(
        patient_service.mpi_resolver,
        "resolve_identity",
        lambda *args, **kwargs: _fake_outcome(),
    )
    patient = _create(db, make_lab())["patient"]
    assert patient["mpi_status"] == "resolved"
    assert patient["citizen_ulid"] == ULID
    assert patient["mpi_identity_source"] == "nid_exact"
    assert patient["mpi_confidence"] == 0.98
    assert patient["mpi_reconciliation_required"] is False
    assert patient["mpi_reconciliation_key"] is None


def test_p16_pending_review_is_temporary_and_monitored(db, make_lab, monkeypatch):
    monkeypatch.setattr(
        patient_service.mpi_resolver,
        "resolve_identity",
        lambda *args, **kwargs: _fake_outcome(method="pending_review", score=0.66),
    )
    lab = make_lab()
    patient = _create(db, lab)["patient"]
    assert patient["mpi_status"] == "temporary"
    assert patient["citizen_ulid"] == ULID
    assert patient["mpi_identity_source"] == "pending_review"
    assert patient["mpi_confidence"] == 0.66
    assert patient["mpi_reconciliation_required"] is True
    audit = db.query(AuditLog).filter(AuditLog.action == "mpi_pending_review").one()
    assert json.loads(audit.details)["reconciliation_key"] == f"mpi:{lab.id}:{patient['id']}"


def test_p16_retry_after_outage_reuses_one_claim_without_duplicate_citizens(
    db, make_lab, make_lab_user
):
    """Reconciliation retry is idempotent: one patient -> one claim -> one citizen."""
    lab = make_lab()
    user = make_lab_user(lab.id)
    db.flush()
    real_resolve = patient_service.mpi_resolver.resolve_identity
    state = {"fail": True}
    attempted = []

    def _flaky(resolve_db, **kwargs):
        attempted.append(kwargs["local_patient_id"])
        if state["fail"]:
            raise RuntimeError("synthetic transient MPI outage")
        return real_resolve(resolve_db, **kwargs)

    patient = Patient(lab_id=lab.id, full_name="Retry Patient", phone="+9647700000002")
    db.add(patient)
    db.flush()

    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(patient_service.mpi_resolver, "resolve_identity", _flaky)
        first = patient_service._resolve_mpi(db, patient, None, None, user.id, lab.id)
        state["fail"] = False
        second = patient_service._resolve_mpi(db, patient, None, None, user.id, lab.id)
        third = patient_service._resolve_mpi(db, patient, None, None, user.id, lab.id)
    finally:
        monkeypatch.undo()

    assert first.status == "degraded"
    assert second.status == "resolved"
    assert third.status == "resolved"
    assert second.citizen_ulid == third.citizen_ulid
    assert attempted == [patient.id, patient.id, patient.id]
    assert db.query(Citizen).count() == 1
    assert db.query(IdentityClaim).count() == 1


def test_p16_unverified_identity_is_never_promoted_or_auto_merged(db, make_lab, make_lab_user):
    """A shared unverified NID may be claimed with pending_review, never merged.

    The resolver deliberately reuses an existing citizen for an unverified NID
    and records ``nid_not_authoritative`` + ``pending_review`` instead of
    auto-merging or promoting the identity. This test pins those safe outcomes.
    """
    lab_a = make_lab()
    lab_b = make_lab()
    user_a = make_lab_user(lab_a.id)
    user_b = make_lab_user(lab_b.id)
    db.flush()

    patient_a = Patient(lab_id=lab_a.id, full_name="Alpha Synthetic", phone="+9647700000010")
    patient_b = Patient(lab_id=lab_b.id, full_name="Beta Synthetic", phone="+9647700000020")
    db.add_all([patient_a, patient_b])
    db.flush()

    outcome_a = patient_service.mpi_resolver.resolve_identity(
        db,
        lab_id=lab_a.id,
        local_patient_id=patient_a.id,
        name=patient_a.full_name,
        phone=patient_a.phone,
        national_id=NID,
        claimed_by_user_id=user_a.id,
    )
    outcome_b = patient_service.mpi_resolver.resolve_identity(
        db,
        lab_id=lab_b.id,
        local_patient_id=patient_b.id,
        name=patient_b.full_name,
        phone=patient_b.phone,
        national_id=NID,
        claimed_by_user_id=user_b.id,
    )

    for outcome in (outcome_a, outcome_b):
        assert outcome.match_method in {"pending_review", "new"}
        assert outcome.citizen.nid_verified is False
        assert outcome.citizen.merged_into_id is None
        assert outcome.citizen.status != "verified"
    merge_events = {
        row.event_type
        for row in db.query(MergeAudit).all()
        if row.event_type in {"auto_merge", "manual_merge", "split", "reassign"}
    }
    assert merge_events == set(), f"an unverified NID triggered a merge: {merge_events}"


def test_p16_source_has_no_untrusted_merge_or_bare_null_return():
    """Static guard: patient creation never auto-merges or returns a bare null pair."""
    tree = ast.parse(SERVICE_PATH.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            assert "merge" not in name.lower(), f"untrusted merge call at line {node.lineno}"
    source = SERVICE_PATH.read_text(encoding="utf-8")
    assert "mpi_status" in source
    assert "degraded" in source
    assert "reconciliation_key" in source


# ── Independent-review conditions F1-F5 ──────────────────────────────────────


def test_p16_f4_mpi_resolution_is_genuinely_frozen():
    import dataclasses

    resolution = patient_service.MpiResolution(
        status="degraded",
        citizen_ulid=None,
        source="mpi_resolver",
        confidence=None,
        match_method=None,
        reconciliation_key="mpi:1:2",
        reconciliation_required=True,
    )
    assert resolution.__dataclass_params__.frozen is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        resolution.status = "resolved"


def test_p16_f5_safe_match_score_normalises_malformed_values():
    guard = patient_service._safe_match_score
    assert guard(None) is None
    assert guard("not-a-number") is None
    assert guard(float("nan")) is None
    assert guard(float("inf")) is None
    assert guard(float("-inf")) is None
    assert guard(object()) is None
    assert guard("0.66") == 0.66
    assert guard(-2.5) == 0.0
    assert guard(7.5) == 1.0


def test_p16_f5_non_finite_score_never_emits_nonstandard_json(db, make_lab, monkeypatch):
    lab = make_lab()
    outcome = _fake_outcome(method="pending_review", score=float("nan"))
    monkeypatch.setattr(
        patient_service.mpi_resolver, "resolve_identity", lambda *a, **k: outcome
    )
    patient = Patient(lab_id=lab.id, full_name="NaN Synthetic", phone="+9647700000031")
    db.add(patient)
    db.flush()
    resolution = patient_service._resolve_mpi(db, patient, None, None, 1, lab.id)
    assert resolution.confidence is None
    audit = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "mpi_pending_review",
            AuditLog.resource_id == patient.id,
        )
        .one()
    )
    assert "NaN" not in audit.details
    assert "Infinity" not in audit.details


def test_p16_f2_pending_review_marker_is_idempotent_on_retry(db, make_lab, monkeypatch):
    monkeypatch.setattr(
        patient_service.mpi_resolver,
        "resolve_identity",
        lambda *a, **k: _fake_outcome(method="pending_review", score=0.66),
    )
    lab = make_lab()
    patient = Patient(lab_id=lab.id, full_name="Retry Marker Synthetic", phone="+9647700000032")
    db.add(patient)
    db.flush()
    for _ in range(3):
        assert patient_service._resolve_mpi(db, patient, None, None, 1, lab.id).status == "temporary"
    markers = (
        db.query(AuditLog)
        .filter(
            AuditLog.action == "mpi_pending_review",
            AuditLog.resource_id == patient.id,
        )
        .count()
    )
    assert markers == 1, "repeated reconciliation retries duplicated the queue marker"


def test_p16_f1_outstanding_reconciliation_monitor_groups_markers_without_phi(
    db, make_lab, monkeypatch
):
    from app.services.mpi.api import list_outstanding_reconciliations

    def _boom(*args, **kwargs):
        raise RuntimeError("synthetic MPI outage")

    monkeypatch.setattr(patient_service.mpi_resolver, "resolve_identity", _boom)
    lab = make_lab()
    patient = Patient(lab_id=lab.id, full_name="Monitor Synthetic", phone="+9647700000033")
    db.add(patient)
    db.flush()
    for _ in range(3):
        assert patient_service._resolve_mpi(db, patient, NID, None, 1, lab.id).status == "degraded"

    page = list_outstanding_reconciliations(limit=50, offset=0, current_user=None, db=db)
    assert page.total == 1, "retries inflated the outstanding-reconciliation count"
    item = page.items[0]
    assert item.status == "degraded"
    assert item.patient_id == patient.id
    assert item.lab_id == lab.id
    assert item.marker_count == 3
    serialised = json.dumps(page.model_dump(), default=str)
    assert NID not in serialised, "national identifier leaked into the monitoring endpoint"
    assert "Monitor Synthetic" not in serialised, "patient name leaked into the monitoring endpoint"
    assert "+9647700000033" not in serialised, "phone leaked into the monitoring endpoint"
