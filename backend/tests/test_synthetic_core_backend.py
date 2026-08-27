from concurrent.futures import ThreadPoolExecutor

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


def test_context_aware_identity_session_workspace_is_fail_closed(core: SyntheticCoreBackend) -> None:
    identity = core.register_identity(account_id="account-ctx", person_id="person-ctx")
    session = core.open_session(account_id="account-ctx", device_id="device-ctx")
    core.register_workspace(workspace_id="workspace-ctx", organization_id="org-ctx", facility_id="facility-ctx")
    core.add_membership(account_id="account-ctx", workspace_id="workspace-ctx", roles=frozenset())
    actor = core.build_actor(
        actor_id="actor-ctx",
        account_id="account-ctx",
        identity_id=identity.id,
        organization_id="org-ctx",
        workspace_id="workspace-ctx",
        patient_id="patient-ctx",
        session_id=session.id,
    )
    appointment = core.book_appointment(actor, patient_id="patient-ctx", practitioner_id="provider-ctx", slot="slot-ctx", idempotency_key="ctx-1")
    assert appointment.state == "REQUESTED"

    core.revoke_session(session.id)
    with pytest.raises(SyntheticAuthorizationError, match="DENY:appointment:book"):
        core.book_appointment(actor, patient_id="patient-ctx", practitioner_id="provider-ctx", slot="slot-ctx-2", idempotency_key="ctx-2")


def test_concurrent_synthetic_booking_has_one_winner(core: SyntheticCoreBackend) -> None:
    core.register_workspace(workspace_id="workspace-concurrent", organization_id="org-concurrent", facility_id="facility-concurrent")
    actors = []
    for index in range(2):
        account_id = f"account-concurrent-{index}"
        identity = core.register_identity(account_id=account_id, person_id=f"person-concurrent-{index}")
        session = core.open_session(account_id=account_id, device_id=f"device-concurrent-{index}")
        core.add_membership(account_id=account_id, workspace_id="workspace-concurrent", roles=frozenset())
        actors.append(
            core.build_actor(
                actor_id=f"actor-concurrent-{index}",
                account_id=account_id,
                identity_id=identity.id,
                organization_id="org-concurrent",
                workspace_id="workspace-concurrent",
                patient_id=f"patient-concurrent-{index}",
                session_id=session.id,
            ),
        )

    def attempt(actor: SyntheticActor):
        try:
            return ("success", core.book_appointment(actor, patient_id=actor.patient_id or "", practitioner_id="provider", slot="same-slot", idempotency_key=f"key-{actor.id}"))
        except SyntheticConflictError:
            return ("conflict", None)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, actors))
    assert [outcome[0] for outcome in outcomes].count("success") == 1
    assert [outcome[0] for outcome in outcomes].count("conflict") == 1


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
