from datetime import UTC, datetime, timedelta

import pytest
from app.identity.api.audit import router as audit_router
from app.identity.api.consents import ConsentGrantRequest
from app.identity.api.security import router as security_router
from app.identity.models.audit import IdentityAuditEntry
from app.identity.models.security import IncidentStatus, SecurityIncident
from app.identity.services.canonical_audit import (
    AuditEventInput,
    CanonicalAuditService,
    IntegrityStatus,
)
from app.identity.services.consent_service_v2 import NiamConsentError, NiamConsentService
from app.identity.services.incident_service import IncidentError, IncidentService


class _Result:
    def __init__(self, values=None, scalar=None):
        self.values = values or []
        self.scalar = scalar

    def scalars(self):
        return self

    def all(self):
        return self.values

    def scalar_one_or_none(self):
        return self.scalar

    def first(self):
        return self.values[0] if self.values else None


class _AuditSession:
    def __init__(self):
        self.entries = []
        self._counter = 0

    async def execute(self, statement):
        sql = str(statement)
        if "SELECT niam_audit_entries.entry_hash" in sql or (
            "niam_audit_entries.entry_hash" in sql and "LIMIT" in sql
        ):
            return _Result(scalar=self.entries[-1].entry_hash if self.entries else None)
        return _Result(values=list(self.entries))

    def add(self, entry):
        self._counter += 1
        if isinstance(entry, IdentityAuditEntry):
            entry.id = f"AUDIT9{self._counter:020d}"[:26]
            self.entries.append(entry)

    async def flush(self):
        return None


class _IncidentSession:
    def __init__(self, incident=None):
        self.incident = incident
        self.added = []

    async def get(self, model, identifier, **kwargs):
        del model, identifier, kwargs
        return self.incident

    def add(self, entry):
        self.added.append(entry)
        if isinstance(entry, SecurityIncident):
            entry.id = "INCIDENT9TEST00000000000001"[:26]
            self.incident = entry

    async def flush(self):
        return None

    async def execute(self, statement):
        del statement
        return _Result(scalar=None)


@pytest.mark.asyncio
async def test_canonical_audit_chain_is_linked_and_verifiable():
    session = _AuditSession()
    service = CanonicalAuditService(session)
    first = await service.record(
        AuditEventInput(event_type="LOGIN", category="AUTHENTICATION", action="login", actor_id="a1"),
    )
    second = await service.record(
        AuditEventInput(event_type="AUTHZ_DENY", category="AUTHORIZATION", action="read", actor_id="a1", decision="DENY"),
    )
    assert first.previous_hash is None
    assert second.previous_hash == first.entry_hash
    result = await service.verify()
    assert result["status"] == IntegrityStatus.valid.value
    assert result["entries_checked"] == 2


@pytest.mark.asyncio
async def test_canonical_audit_detects_payload_tampering():
    session = _AuditSession()
    service = CanonicalAuditService(session)
    entry = await service.record(
        AuditEventInput(event_type="ROLE_CHANGE", category="AUTHORIZATION", action="role.assign", actor_id="a1"),
    )
    entry.action = "role.revoke"
    result = await service.verify()
    assert result["status"] == IntegrityStatus.invalid.value
    assert any(item["reason"] == "event_hash_mismatch" for item in result["violations"])


@pytest.mark.asyncio
async def test_canonical_audit_redacts_secret_metadata():
    session = _AuditSession()
    entry = await CanonicalAuditService(session).record(
        AuditEventInput(
            event_type="LOGIN_FAILURE",
            category="AUTHENTICATION",
            action="login.failure",
            metadata={"access_token": "do-not-store", "attempt": 2},
        ),
    )
    assert entry.extra_data == {"access_token": "[REDACTED]", "attempt": 2}


def test_consent_rejects_unknown_purpose_and_long_expiry():
    with pytest.raises(NiamConsentError):
        NiamConsentService._validate_expiry(datetime.now(UTC) + timedelta(hours=73))
    with pytest.raises(NiamConsentError):
        NiamConsentService._validate_scope({})
    assert "status" not in ConsentGrantRequest.model_fields
    assert "created_by" not in ConsentGrantRequest.model_fields


@pytest.mark.asyncio
async def test_incident_state_machine_and_version_guard():
    incident = SecurityIncident(
        id="incident-1",
        uuid="incident-uuid",
        incident_key="INC-1",
        severity="P1",
        category="idor",
        organization_id="org-1",
        status=IncidentStatus.open.value,
        detected_at=datetime.now(UTC),
        created_by="account-1",
        version=1,
    )
    session = _IncidentSession(incident)
    service = IncidentService(session)
    with pytest.raises(IncidentError, match="stale"):
        await service.transition(actor_id="account-1", incident_id="incident-1", target_status="TRIAGED", expected_version=2)
    updated = await service.transition(actor_id="account-1", incident_id="incident-1", target_status="TRIAGED", expected_version=1)
    assert updated.status == IncidentStatus.triaged.value
    assert updated.version == 2
    with pytest.raises(IncidentError, match="invalid transition"):
        await service.transition(actor_id="account-1", incident_id="incident-1", target_status="CLOSED", expected_version=2)


def test_phase9_routes_expose_no_audit_mutation_endpoints():
    paths = {route.path for route in audit_router.routes}
    assert "/audit" in paths
    assert "/audit/export" in paths
    assert "/audit/integrity" in paths
    assert not any(route.path.endswith("/{event_id}") for route in audit_router.routes)
    security_paths = {route.path for route in security_router.routes}
    assert "/security/incidents" in security_paths
    assert "/security/incidents/{incident_id}" in security_paths


def test_security_incident_serialization_does_not_require_client_actor_fields():
    fields = set(ConsentGrantRequest.model_fields)
    assert fields == {
        "subject_account_id",
        "grantee_account_id",
        "purpose",
        "scope",
        "resource_domain",
        "expires_at",
        "legal_basis",
        "reason",
    }



def test_fhir_base_url_rejects_ssrf_and_requires_allowlist(monkeypatch):
    from app.identity.admin.services import EnterprisePortalService

    with pytest.raises(ValueError):
        EnterprisePortalService._validate_fhir_base_url("http://127.0.0.1:8080")
    with pytest.raises(ValueError):
        EnterprisePortalService._validate_fhir_base_url("https://example.com")
    monkeypatch.setenv("FHIR_ALLOWED_HOSTS", "example.com")
    assert EnterprisePortalService._validate_fhir_base_url("https://example.com/fhir") == "https://example.com/fhir"


def test_admin_and_compliance_routes_require_niam_actor():
    from app.identity.admin.routes import router as admin_router
    from app.identity.api.workspaces import get_current_niam_actor
    from app.identity.compliance.routes import router as compliance_router

    for route in [*admin_router.routes, *compliance_router.routes]:
        dependency_calls = {dependency.call for dependency in route.dependant.dependencies}
        assert get_current_niam_actor in dependency_calls, route.path


def test_admin_and_compliance_endpoints_do_not_accept_client_actor_fields():
    import inspect

    from app.identity.admin import routes as admin_routes
    from app.identity.compliance import routes as compliance_routes

    forbidden_names = {"created_by", "checked_by", "generated_by", "is_admin", "credentials_encrypted"}
    for module in (admin_routes, compliance_routes):
        for name, endpoint in vars(module).items():
            if name.startswith("_") or not callable(endpoint):
                continue
            parameter_names = set(inspect.signature(endpoint).parameters)
            assert not parameter_names.intersection(forbidden_names), name
