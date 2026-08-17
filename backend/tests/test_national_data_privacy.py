from app.national_data.models.mdm.GoldenRecord import GoldenRecord
from app.routes.national_data import _golden_to_dict


def test_golden_record_serializer_redacts_national_identity() -> None:
    record = GoldenRecord(
        id=101,
        patient_id=7,
        national_patient_id="NATIONAL-RAW-MUST-NOT-LEAK",
        citizen_id="GHID-OPAQUE-001",
        confidence_score=0.98,
        matching_algorithm="synthetic-test",
        is_active_golden=1,
    )

    returned = _golden_to_dict(record)

    assert returned["id"] == 101
    assert returned["patient_id"] == 7
    assert returned["citizen_id"] == "GHID-OPAQUE-001"
    assert returned["national_identity_linked"] is True
    assert "national_patient_id" not in returned
    assert "national_id" not in returned


def test_golden_record_serializer_marks_unlinked_identity_without_exposing_value() -> None:
    record = GoldenRecord(
        id=102,
        patient_id=8,
        national_patient_id=None,
        citizen_id="GHID-OPAQUE-002",
        confidence_score=0.5,
        matching_algorithm="synthetic-test",
        is_active_golden=0,
    )

    returned = _golden_to_dict(record)

    assert returned["national_identity_linked"] is False
    assert "national_patient_id" not in returned
    assert "national_id" not in returned
