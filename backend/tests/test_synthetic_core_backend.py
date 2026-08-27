import pytest

from tests.fixtures.synthetic_core_backend import (
    SyntheticActor,
    SyntheticAuthorizationError,
    SyntheticConflictError,
    SyntheticCoreBackend,
)


@pytest.fixture
def core() -> SyntheticCoreBackend:
    return SyntheticCoreBackend()


@pytest.fixture
def actors() -> dict[str, SyntheticActor]:
    return {
        "citizen": SyntheticActor("citizen-001", "citizen", "org-001", "workspace-citizen", patient_id="patient-001"),
        "doctor": SyntheticActor("doctor-001", "doctor", "org-001", "workspace-doctor", roles=frozenset({"doctor"})),
        "lab": SyntheticActor("lab-001", "laboratory", "org-001", "workspace-lab", roles=frozenset({"lab_technician"})),
        "senior_lab": SyntheticActor("senior-lab-001", "laboratory", "org-001", "workspace-lab", roles=frozenset({"lab_technician", "senior_lab"})),
        "other_org_doctor": SyntheticActor("doctor-002", "org-002", "org-002", "workspace-doctor-2", roles=frozenset({"doctor"})),
    }


def test_golden_path_runs_on_synthetic_backend_with_audit(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    appointment = core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T10:00Z", idempotency_key="book-001")
    assert core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T10:00Z", idempotency_key="book-001").id == appointment.id
    core.confirm_appointment(actors["doctor"], appointment.id)
    core.check_in(actors["citizen"], appointment.id)
    encounter = core.create_encounter(actors["doctor"], appointment.id)
    core.complete_and_sign_note(actors["doctor"], encounter.id)
    order = core.place_lab_order(actors["doctor"], encounter.id, idempotency_key="lab-order-001")
    specimen = core.collect_and_receive_specimen(actors["lab"], order.id)
    result = core.release_result(actors["senior_lab"], specimen.id)
    assert core.read_result(actors["citizen"], result.id).state == "RELEASED"
    consent = core.grant_result_share(actors["citizen"], recipient_id="doctor-001", recipient_organization_id="org-001", result_id=result.id, scope="lab_results", duration_hours=48)
    assert core.read_result(actors["doctor"], result.id).id == result.id
    core.revoke_share(actors["citizen"], consent.id)
    with pytest.raises(SyntheticAuthorizationError, match="DENY:result:read"):
        core.read_result(actors["doctor"], result.id)
    assert len(core.audit) >= 10
    assert all(event.entity_id and event.action for event in core.audit)


def test_duplicate_slot_cross_tenant_and_unauthorized_release_fail_closed(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T11:00Z", idempotency_key="book-002")
    with pytest.raises(SyntheticConflictError, match="slot already booked"):
        core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T11:00Z", idempotency_key="book-003")
    with pytest.raises(SyntheticAuthorizationError, match="DENY"):
        core.book_appointment(actors["other_org_doctor"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T12:00Z", idempotency_key="book-004")


def test_technician_cannot_release_without_senior_validation(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    appointment = core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2026-09-01T13:00Z", idempotency_key="book-005")
    core.confirm_appointment(actors["doctor"], appointment.id)
    core.check_in(actors["citizen"], appointment.id)
    encounter = core.create_encounter(actors["doctor"], appointment.id)
    core.complete_and_sign_note(actors["doctor"], encounter.id)
    order = core.place_lab_order(actors["doctor"], encounter.id, idempotency_key="lab-order-002")
    specimen = core.collect_and_receive_specimen(actors["lab"], order.id)
    with pytest.raises(SyntheticAuthorizationError, match="result:clinical_validate"):
        core.release_result(actors["lab"], specimen.id)
