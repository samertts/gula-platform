from datetime import UTC, datetime, timedelta

import pytest
from app.clinical.device_gateway import SyntheticEMSDeviceGateway, SyntheticHospitalDeviceGateway


@pytest.mark.parametrize("gateway", [SyntheticHospitalDeviceGateway(), SyntheticEMSDeviceGateway()])
def test_synthetic_gateway_normalizes_allowlisted_readings_with_provenance(gateway):
    observations = gateway.normalize_readings(
        patient_person_id="PERSON-SYN-0000000000000001",
        encounter_id="ENCOUNTER-SYN-0000001",
        observer_account_id="ACCOUNT-SYN-00000000001",
        device_type="monitor",
        device_reference="DEVICE-SYN-001",
        readings={"heart_rate": 88, "oxygen_saturation": 98, "raw_payload": "must-not-persist"},
        observed_at=datetime.now(UTC) - timedelta(minutes=1),
    )

    assert {item.vital_type for item in observations} == {"heart_rate", "oxygen_saturation"}
    assert all(item.patient_person_id.startswith("PERSON-SYN") for item in observations)
    assert all(item.method == "DEVICE_VALIDATED" for item in observations)
    assert all(item.source.startswith("synthetic-") for item in observations)


def test_synthetic_gateway_marks_outside_expected_range_as_warning_not_silent_rejection():
    observation = SyntheticEMSDeviceGateway().normalize_readings(
        patient_person_id="PERSON-SYN-0000000000000002",
        encounter_id="ENCOUNTER-SYN-0000002",
        observer_account_id="ACCOUNT-SYN-00000000002",
        device_type="pulse_oximeter",
        device_reference="DEVICE-SYN-002",
        readings={"oxygen_saturation": 140},
        observed_at=datetime.now(UTC),
    )[0]

    assert observation.validation_status == "WARNING"
    assert observation.warning_code == "OUTSIDE_EXPECTED_RANGE"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"device_type": "unknown", "readings": {"heart_rate": 80}},
        {"device_type": "monitor", "readings": {"raw_payload": {"secret": "never-store"}}},
        {"device_type": "monitor", "readings": {"heart_rate": "not-a-number"}},
    ],
)
def test_synthetic_gateway_rejects_unsupported_or_invalid_device_input(kwargs):
    with pytest.raises(ValueError):
        SyntheticEMSDeviceGateway().normalize_readings(
            patient_person_id="PERSON-SYN-0000000000000003",
            encounter_id="ENCOUNTER-SYN-0000003",
            observer_account_id="ACCOUNT-SYN-00000000003",
            device_type=kwargs["device_type"],
            device_reference="DEVICE-SYN-003",
            readings=kwargs["readings"],
            observed_at=datetime.now(UTC),
        )
