"""Doctor Duty authorization regression tests.

The tests intentionally use an in-memory query double: they exercise the
server-side decision boundary without creating or mutating real clinical data.
"""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.services.doctor_duty_service import ClinicalRequest, DoctorDutyService, DutyAuthorizationError

UTC = timezone.utc
NOW = datetime(2026, 8, 18, 12, 0, tzinfo=UTC)


class QueryDouble:
    def __init__(self, rows):
        self.rows = rows

    def filter(self, *args, **kwargs):
        return self

    def with_for_update(self):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        return self.rows[0] if self.rows else None

    def all(self):
        return list(self.rows)

    def one_or_none(self):
        if len(self.rows) > 1:
            raise AssertionError("test fixture returned more than one row")
        return self.rows[0] if self.rows else None

    def one(self):
        if len(self.rows) != 1:
            raise AssertionError("test fixture did not return exactly one row")
        return self.rows[0]


class DbDouble:
    def __init__(self, *, contexts=None, clinical=None, duties=None, users=None):
        self.contexts = contexts or []
        self.clinical = clinical or []
        self.duties = duties or []
        self.users = users or []
        self.added = []
        self.audit = []

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "DutyContext":
            return QueryDouble(self.contexts)
        if name == "ClinicalAccessContext":
            return QueryDouble(self.clinical)
        if name == "DoctorDuty":
            return QueryDouble(self.duties)
        if name == "User":
            return QueryDouble(self.users)
        if name == "DutyAuditEvent":
            return QueryDouble(self.audit)
        raise AssertionError(f"unexpected model query: {name}")

    def add(self, item):
        self.added.append(item)
        if item.__class__.__name__ == "DutyAuditEvent":
            self.audit.append(item)

    def flush(self):
        return None


def active_context(**changes):
    values = dict(
        id="dctx_1", duty_id=1, user_id=7, tenant_id=10, organization_id=20,
        facility_id=30, department_id="cardiology", ward_id="ward-a", role_id="doctor",
        purpose="patient-care", status="ACTIVE", started_at=NOW - timedelta(minutes=10),
        expires_at=NOW + timedelta(hours=2), authz_version=1,
    )
    values.update(changes)
    return SimpleNamespace(**values)


def clinical_context(**changes):
    values = dict(
        id="cctx_1", duty_context_id="dctx_1", user_id=7, organization_id=20,
        facility_id=30, department_id="cardiology", ward_id="ward-a", active=True,
        expires_at=NOW + timedelta(hours=2), allowed_resources=["patient.read", "clinical.read"],
        patient_scope={"patient_ids": [100], "assigned_only": True},
    )
    values.update(changes)
    return SimpleNamespace(**values)


def request(**changes):
    values = dict(user_id=7, purpose="patient-care", organization_id=20, facility_id=30,
                  department_id="cardiology", ward_id="ward-a", patient_id=100,
                  resource_type="patient.read")
    values.update(changes)
    return ClinicalRequest(**values)


def test_login_without_duty_is_default_deny():
    service = DoctorDutyService(DbDouble(), now=NOW)
    with pytest.raises(DutyAuthorizationError) as error:
        service.authorize(request())
    assert error.value.code == "CLINICAL_ACCESS_DENIED"


def test_wrong_facility_is_denied_even_when_user_has_active_duty():
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    service = DoctorDutyService(DbDouble(contexts=[active_context()], clinical=[clinical_context()], duties=[duty]), now=NOW)
    with pytest.raises(DutyAuthorizationError):
        service.authorize(request(facility_id=999))


def test_wrong_department_and_ward_are_denied():
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    service = DoctorDutyService(DbDouble(contexts=[active_context()], clinical=[clinical_context()], duties=[duty]), now=NOW)
    for changes in ({"department_id": "neurology"}, {"ward_id": "ward-b"}):
        with pytest.raises(DutyAuthorizationError):
            service.authorize(request(**changes))


def test_expired_duty_is_denied_and_cannot_authorize_mutation():
    context = active_context(expires_at=NOW - timedelta(seconds=1))
    clinical = clinical_context(expires_at=NOW - timedelta(seconds=1))
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    service = DoctorDutyService(DbDouble(contexts=[context], clinical=[clinical], duties=[duty]), now=NOW)
    with pytest.raises(DutyAuthorizationError) as error:
        service.authorize(request(resource_type="clinical.mutation"))
    assert error.value.code == "CLINICAL_ACCESS_DENIED"


def test_unassigned_patient_is_denied_without_break_glass():
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    service = DoctorDutyService(DbDouble(contexts=[active_context()], clinical=[clinical_context()], duties=[duty]), now=NOW)
    with pytest.raises(DutyAuthorizationError):
        service.authorize(request(patient_id=101))


def test_valid_patient_scope_is_allowed_at_execution_time():
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    service = DoctorDutyService(DbDouble(contexts=[active_context()], clinical=[clinical_context()], duties=[duty]), now=NOW)
    result = service.authorize(request())
    assert result.duty_context_id == "dctx_1"


def test_second_active_context_is_not_silently_merged():
    context_a = active_context(id="dctx_a", facility_id=30)
    context_b = active_context(id="dctx_b", facility_id=31)
    duty = SimpleNamespace(id=1, user_id=7, status="ACTIVE", organization_id=20, facility_id=30, department_id="cardiology", ward_id="ward-a", purpose="patient-care")
    db = DbDouble(contexts=[context_a, context_b], clinical=[clinical_context()], duties=[duty])
    service = DoctorDutyService(db, now=NOW)
    with pytest.raises(DutyAuthorizationError) as error:
        service.authorize(request())
    assert error.value.code == "CONCURRENT_ACTIVE_DUTIES"
