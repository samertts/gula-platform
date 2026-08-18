from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.doctor_duty_offline import authorize_verified_offline_context
from app.services.doctor_duty_service import DutyAuthorizationError

NOW = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)


def ctx(**changes):
    values = dict(id="dctx-1", status="ACTIVE", started_at=NOW - timedelta(minutes=5), expires_at=NOW + timedelta(hours=1), organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", assigned_patient_ids=[100, 101])
    values.update(changes)
    return SimpleNamespace(**values)


def test_offline_requires_preverified_active_context():
    with pytest.raises(DutyAuthorizationError) as error:
        authorize_verified_offline_context(duty_context=None, now=NOW, requested_patient_ids=[100])
    assert error.value.code == "OFFLINE_DUTY_NOT_VERIFIED"


def test_offline_rejects_patient_outside_verified_scope():
    with pytest.raises(DutyAuthorizationError) as error:
        authorize_verified_offline_context(duty_context=ctx(), now=NOW, requested_patient_ids=[999])
    assert error.value.code == "OFFLINE_PATIENT_SCOPE_DENIED"


def test_offline_returns_bounded_descriptor():
    result = authorize_verified_offline_context(duty_context=ctx(), now=NOW, requested_patient_ids=[100])
    assert result.duty_context_id == "dctx-1"
    assert result.encryption_required is True
    assert result.sync_required_on_reconnect is True
    assert len(result.dataset_fingerprint) == 64
