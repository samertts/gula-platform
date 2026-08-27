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
        "pharmacist": SyntheticActor("pharmacist-001", "pharmacy", "org-001", "workspace-pharmacy", roles=frozenset({"pharmacist"})),
        "pharmacist_reviewer": SyntheticActor("pharmacist-002", "pharmacy", "org-001", "workspace-pharmacy", roles=frozenset({"pharmacist"})),
        "imaging_technician": SyntheticActor("imaging-tech-001", "imaging", "org-001", "workspace-imaging", roles=frozenset({"imaging_technician"})),
        "radiologist": SyntheticActor("radiologist-001", "imaging", "org-001", "workspace-imaging", roles=frozenset({"radiologist"})),
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


def test_synthetic_clinical_commands_are_replay_safe_and_share_is_bounded(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    appointment = core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot="2030-09-01T10:00Z", idempotency_key="replay-book")
    core.confirm_appointment(actors["doctor"], appointment.id)
    core.check_in(actors["citizen"], appointment.id)
    encounter = core.create_encounter(actors["doctor"], appointment.id)
    core.complete_and_sign_note(actors["doctor"], encounter.id)
    order = core.place_lab_order(actors["doctor"], encounter.id, idempotency_key="replay-order")
    specimen = core.collect_and_receive_specimen(actors["lab"], order.id, idempotency_key="replay-specimen")
    assert core.collect_and_receive_specimen(actors["lab"], order.id, idempotency_key="replay-specimen").id == specimen.id
    result = core.release_result(actors["senior_lab"], specimen.id, idempotency_key="replay-result")
    assert core.release_result(actors["senior_lab"], specimen.id, idempotency_key="replay-result").id == result.id
    consent = core.grant_result_share(actors["citizen"], recipient_id=actors["doctor"].id, recipient_organization_id="org-001", result_id=result.id, scope="lab_results", duration_hours=72, idempotency_key="replay-grant")
    assert core.grant_result_share(actors["citizen"], recipient_id=actors["doctor"].id, recipient_organization_id="org-001", result_id=result.id, scope="lab_results", duration_hours=72, idempotency_key="replay-grant").id == consent.id
    assert core.read_result(actors["doctor"], result.id).id == result.id
    with pytest.raises(SyntheticAuthorizationError, match="bounded_scope"):
        core.grant_result_share(actors["citizen"], recipient_id=actors["doctor"].id, recipient_organization_id="org-001", result_id=result.id, scope="all_records", duration_hours=72)
    with pytest.raises(SyntheticConflictError, match="version conflict"):
        core.revoke_share(actors["citizen"], consent.id, expected_version=99)
    revoked = core.revoke_share(actors["citizen"], consent.id, expected_version=1, idempotency_key="replay-revoke")
    assert revoked.state == "REVOKED" and revoked.version == 2
    assert {entry["action"] for entry in core.list_access_history(actors["citizen"], result_id=result.id)} >= {"GRANT_CREATED", "ACCESS_USED", "GRANT_REVOKED"}


def _signed_encounter(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor], slot: str = "synthetic-new-slot"):
    appointment = core.book_appointment(actors["citizen"], patient_id="patient-001", practitioner_id="doctor-001", slot=slot, idempotency_key=f"new-{slot}")
    core.confirm_appointment(actors["doctor"], appointment.id)
    core.check_in(actors["citizen"], appointment.id)
    encounter = core.create_encounter(actors["doctor"], appointment.id)
    core.complete_and_sign_note(actors["doctor"], encounter.id)
    return encounter


def test_pharmacy_synthetic_workflow_is_replay_safe_and_separates_duties(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    encounter = _signed_encounter(core, actors, "pharmacy-synthetic-slot")
    medication = core.create_medication(actors["doctor"], code="SYN-MED-001", name="Synthetic Medication", idempotency_key="med-001")
    assert core.create_medication(actors["doctor"], code="SYN-MED-001", name="Synthetic Medication", idempotency_key="med-001").id == medication.id
    core.receive_medication_stock(actors["pharmacist"], medication.id, quantity=5)
    prescription = core.create_prescription(actors["doctor"], encounter.id, medication_id=medication.id, quantity=5, idempotency_key="rx-001")
    assert core.create_prescription(actors["doctor"], encounter.id, medication_id=medication.id, quantity=5, idempotency_key="rx-001").id == prescription.id
    core.sign_prescription(actors["doctor"], prescription.id, expected_version=1)
    with pytest.raises(SyntheticConflictError, match="version conflict"):
        core.sign_prescription(actors["doctor"], prescription.id, expected_version=1)
    amended = core.amend_prescription(actors["doctor"], prescription.id, quantity=4, reason="synthetic correction", expected_version=2)
    assert amended.fields["supersedes_id"] == prescription.id
    core.sign_prescription(actors["doctor"], amended.id, expected_version=3)
    prepared = core.prepare_dispense(actors["pharmacist"], amended.id, quantity=2, idempotency_key="dispense-001")
    with pytest.raises(SyntheticAuthorizationError, match="DENY:dispense:complete"):
        core.complete_dispense(actors["pharmacist"], prepared.id, expected_version=1)
    completed = core.complete_dispense(actors["pharmacist_reviewer"], prepared.id, expected_version=1)
    assert completed.state == "PARTIAL"
    assert medication.fields["stock"] == 3


def test_imaging_synthetic_adapter_path_rejects_duplicate_uid_and_releases_report(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    encounter = _signed_encounter(core, actors, "imaging-synthetic-slot")
    order = core.place_imaging_order(actors["doctor"], encounter.id, modality="CT", idempotency_key="image-order-001")
    technician = actors["imaging_technician"]
    study = core.ingest_imaging_study(technician, order.id, study_uid="1.2.840.synthetic.1", source_message_id="synthetic-message-1", idempotency_key="study-001")
    assert core.ingest_imaging_study(technician, order.id, study_uid="1.2.840.synthetic.1", source_message_id="synthetic-message-1", idempotency_key="study-001").id == study.id
    with pytest.raises(SyntheticConflictError, match="duplicate DICOM"):
        core.ingest_imaging_study(technician, order.id, study_uid="1.2.840.synthetic.1", source_message_id="synthetic-message-2", idempotency_key="study-002")
    core.complete_imaging_study(technician, study.id)
    report = core.release_imaging_report(actors["radiologist"], study.id, critical=True)
    assert report.state == "RELEASED"
    assert report.version == 3
    assert report.fields["critical"] is True


def test_unified_record_is_read_only_minimum_necessary_and_cursor_bounded(core: SyntheticCoreBackend, actors: dict[str, SyntheticActor]) -> None:
    encounter = _signed_encounter(core, actors, "record-synthetic-slot")
    medication = core.create_medication(actors["doctor"], code="SYN-MED-002", name="Synthetic Record Medication", idempotency_key="record-med-001")
    core.receive_medication_stock(actors["pharmacist"], medication.id, quantity=2)
    prescription = core.create_prescription(actors["doctor"], encounter.id, medication_id=medication.id, quantity=2, idempotency_key="record-rx-001")
    core.sign_prescription(actors["doctor"], prescription.id)
    order = core.place_imaging_order(actors["doctor"], encounter.id, modality="XR", idempotency_key="record-image-001")
    study = core.ingest_imaging_study(actors["imaging_technician"], order.id, study_uid="1.2.840.synthetic.2", source_message_id="record-message-1", idempotency_key="record-study-001")
    core.complete_imaging_study(actors["imaging_technician"], study.id)
    core.release_imaging_report(actors["radiologist"], study.id)
    first = core.unified_clinical_record(actors["citizen"], patient_id="patient-001", limit=1)
    assert first["minimum_necessary"] is True
    assert first["next_cursor"] == "1"
    assert first["items"][0]["source"]["domain"] in {"encounter", "pharmacy", "imaging"}
    second = core.unified_clinical_record(actors["citizen"], patient_id="patient-001", limit=1, cursor=first["next_cursor"])
    assert second["items"]
    with pytest.raises(SyntheticAuthorizationError, match="DENY:clinical-record:read"):
        core.unified_clinical_record(actors["other_org_doctor"], patient_id="patient-001")
    with pytest.raises(SyntheticConflictError, match="invalid record cursor"):
        core.unified_clinical_record(actors["citizen"], patient_id="patient-001", cursor="not-a-cursor")
