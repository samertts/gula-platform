from typing import Any

from app.pharmacy.routes import router
from app.security.dependencies import require_institutional_user


def test_pharmacy_router_requires_institutional_account() -> None:
    dependency_calls = [dependency.dependency for dependency in router.dependencies]
    assert require_institutional_user in dependency_calls


def test_prescription_creation_fails_closed_without_server_practitioner_mapping(db: Any, make_lab: Any, make_lab_user: Any) -> None:
    from app.pharmacy.services import PharmacyAuthorizationBlocked, PharmacyService

    lab = make_lab(name="Prescription Guard Lab")
    user = make_lab_user(lab_id=lab.id, role="doctor")
    db.commit()
    service = PharmacyService(db=db, user_id=user.id, lab_id=lab.id)

    try:
        service.create_prescription(
            {
                "patient_id": "national-patient-1",
                "prescription_number": "RX-GUARD-001",
                "prescriber_id": "client-controlled-id",
            },
        )
    except PharmacyAuthorizationBlocked as exc:
        assert str(exc) in {"server_practitioner_mapping_required", "server_practitioner_mapping_missing_or_ambiguous"}
    else:
        raise AssertionError("prescription creation must fail closed without server practitioner proof")
