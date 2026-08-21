from __future__ import annotations

from app.clinical.observability import clinical_safety_metrics, prometheus_lines, reason_code
from app.factory import scrub_sentry_event


def test_clinical_metrics_export_only_allow_listed_labels() -> None:
    clinical_safety_metrics.reset_for_test()
    patient_identifier = "PATIENT-SECRET-123"
    idempotency_key = "idempotency-secret-456"

    clinical_safety_metrics.record_command(
        operation="lims.result.release",
        resource_type="lims_result",
        outcome="rejected",
        reason=f"Invalid state for {patient_identifier} using {idempotency_key}",
    )
    clinical_safety_metrics.record_audit_failure(
        operation="lims.result.release",
        resource_type="lims_result",
    )

    exported = "\n".join(prometheus_lines())
    assert 'operation="lims.result.release"' in exported
    assert 'resource_type="lims_result"' in exported
    assert 'reason_code="duplicate_command"' in exported
    assert "gula_clinical_audit_write_failure_total" in exported
    assert patient_identifier not in exported
    assert idempotency_key not in exported


def test_reason_code_never_returns_untrusted_free_text() -> None:
    assert reason_code("") == "unknown"
    assert reason_code("Permission denied for user 99") == "authorization_denied"
    assert reason_code("A clinical record changed version") == "clinical_version_conflict"
    assert reason_code("Patient Ada Lovelace says arbitrary thing") == "workflow_rejected"
    assert reason_code("Invalid state for synthetic patient") == "invalid_state_transition"


def test_sentry_scrubber_removes_request_identity_and_exception_text() -> None:
    event = {
        "request": {"data": {"patient_name": "Sensitive Patient"}, "headers": {"Authorization": "secret"}},
        "user": {"id": "42", "email": "clinician@example.test"},
        "extra": {"clinical_note": "sensitive note"},
        "breadcrumbs": {"values": [{"message": "patient result"}]},
        "transaction": "/lims/results/123/release",
        "contexts": {"trace": {"trace_id": "trace"}},
        "logentry": {"message": "Patient Sensitive Patient failed"},
        "exception": {"values": [{"type": "ValueError", "value": "Patient Sensitive Patient result"}]},
    }

    scrubbed = scrub_sentry_event(event)

    for forbidden in ("request", "user", "extra", "breadcrumbs", "transaction", "contexts"):
        assert forbidden not in scrubbed
    assert scrubbed["logentry"] == {"message": "redacted_application_error"}
    assert scrubbed["exception"] == {"values": [{"type": "ValueError"}]}
    assert "Sensitive Patient" not in str(scrubbed)
