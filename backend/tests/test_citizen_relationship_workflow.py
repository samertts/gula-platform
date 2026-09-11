from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.models.citizen_relationship import CitizenRelationshipStatus
from app.identity.services import citizen_relationship_service as workflow_module
from app.identity.services.citizen_relationship_service import (
    CitizenRelationshipConflict,
    CitizenRelationshipWorkflow,
)

_SCOPE = {"resources": ["dashboard", "profile", "health-summary:read"]}


class _FakeQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self

    def filter_by(self, **kwargs):
        self.filters.extend((key, value) for key, value in kwargs.items())
        return self

    def with_for_update(self):
        return self

    def order_by(self, *ordering):
        return self

    def first(self):
        if self.model is workflow_module.User:
            return self.db.source
        if self.model is workflow_module.Citizen:
            return self.db.citizen
        if self.model is workflow_module.Patient:
            return None
        if self.model is workflow_module.CitizenRelationship:
            for relationship in self.db.relationships:
                if all(self._matches(relationship, condition) for condition in self.filters):
                    return relationship
            return None
        return None

    def _matches(self, relationship, condition):
        if isinstance(condition, tuple):
            return getattr(relationship, condition[0]) == condition[1]
        return True


class _FakeDb:
    def __init__(self, source, citizen):
        self.source = source
        self.citizen = citizen
        self.relationships = []
        self.commits = 0

    def query(self, model):
        return _FakeQuery(self, model)

    def add(self, relationship):
        self.relationships.append(relationship)

    def flush(self):
        for relationship in self.relationships:
            if not relationship.id:
                relationship.id = f"REL{len(self.relationships):023d}"

    def commit(self):
        self.commits += 1

    def refresh(self, relationship):
        return None


def _actor():
    return SimpleNamespace(id=9001, role="ministry_admin")


def _source(*, verified: bool = True):
    return SimpleNamespace(id=101, is_active=True, is_verified=verified, role="citizen")


def _citizen():
    return SimpleNamespace(id="CITIZEN000000000001", is_deceased=False, merged_into_id=None)


def _identity_proven(*_args, **_kwargs):
    """Stand in for the AUTH-005 identity-evidence gate.

    These tests exercise the state machine, idempotency and scoping. Whether
    identity was actually established is a separate question, answered by
    `can_link_health_identity` and covered against the migrated schema in
    tests/test_identity_link_and_assurance.py. Stubbing it here keeps each test
    about one thing; `test_activation_is_refused_without_identity_evidence`
    below proves the real gate is wired in.
    """
    from app.identity.services.identity_link_policy import LinkDecision
    from app.identity.services.verification_service import AssuranceLevel

    return LinkDecision(
        allowed=True, reason_code="identity_assurance_satisfied",
        detail="stubbed for state-machine tests",
        identity_assurance=AssuranceLevel.L2,
        canonical_account_id="acct-stub",
    )


def _workflow(monkeypatch, db, *, identity_gate=_identity_proven):
    monkeypatch.setattr(workflow_module, "log_action", lambda *args, **kwargs: None)
    monkeypatch.setattr(workflow_module, "can_link_health_identity", identity_gate)
    return CitizenRelationshipWorkflow(db, _actor(), request_ip="127.0.0.1")


def _create(workflow, db, key="c2-idempotency-key-0001", scope=None):
    return workflow.create_pending(
        source_kind="legacy_user",
        legacy_user_id=db.source.id,
        citizen_id=db.citizen.id,
        patient_id=None,
        relationship_type="self",
        purpose="citizen_workspace",
        scope=scope or _SCOPE,
        idempotency_key=key,
    )


def test_create_pending_is_idempotent(monkeypatch):
    db = _FakeDb(_source(), _citizen())
    workflow = _workflow(monkeypatch, db)

    first = _create(workflow, db)
    second = _create(workflow, db)

    assert first.id == second.id
    assert first.status == CitizenRelationshipStatus.pending.value
    assert len(db.relationships) == 1


def test_create_pending_rejects_wildcard_scope(monkeypatch):
    db = _FakeDb(_source(), _citizen())
    workflow = _workflow(monkeypatch, db)

    with pytest.raises(CitizenRelationshipConflict):
        _create(workflow, db, key="c2-idempotency-key-0002", scope={"resources": ["*"]})


def test_activation_requires_an_active_source_and_then_changes_state(monkeypatch):
    source = _source()
    db = _FakeDb(source, _citizen())
    workflow = _workflow(monkeypatch, db)
    relationship = _create(workflow, db, key="c2-idempotency-key-0003")

    # Deactivated after the request was raised, before it was activated.
    source.is_active = False
    with pytest.raises(CitizenRelationshipConflict, match="active"):
        workflow.activate(relationship.id, verification_reference="review-0003")

    source.is_active = True
    activated = workflow.activate(relationship.id, verification_reference="review-0003")

    assert activated.status == CitizenRelationshipStatus.active.value
    assert activated.version == 2
    assert activated.allows("profile") is True
    # What was established, recorded separately from who authorized it.
    assert activated.metadata_["identity_assurance"] == "L2"


def test_activation_is_refused_without_identity_evidence(monkeypatch):
    """NR-039. The gate used to read `users.is_verified`, which an emailed code
    sets. A ministry actor authorizes the operation; it does not establish who
    the subject is, and activation now requires both."""
    from app.identity.services.identity_link_policy import LinkDecision
    from app.identity.services.verification_service import AssuranceLevel

    def _contact_only(*_args, **_kwargs):
        return LinkDecision(
            allowed=False, reason_code="insufficient_identity_assurance",
            detail="Identity assurance L0 is below the required L2",
            identity_assurance=AssuranceLevel.L0,
        )

    source = _source(verified=True)   # contact-verified, as the OTP path leaves it
    db = _FakeDb(source, _citizen())
    workflow = _workflow(monkeypatch, db, identity_gate=_contact_only)
    relationship = _create(workflow, db, key="c2-identity-gate-0001")

    with pytest.raises(CitizenRelationshipConflict, match="Identity evidence is insufficient"):
        workflow.activate(relationship.id, verification_reference="review-9001")

    assert relationship.status == CitizenRelationshipStatus.pending.value


def test_activation_rejects_missing_version_without_mutating_state(monkeypatch):
    db = _FakeDb(_source(), _citizen())
    workflow = _workflow(monkeypatch, db)
    relationship = _create(workflow, db, key="c2-idempotency-key-0005")
    relationship.version = None

    with pytest.raises(CitizenRelationshipConflict, match="version"):
        workflow.activate(relationship.id, verification_reference="review-0005")

    assert relationship.status == CitizenRelationshipStatus.pending.value


def test_revocation_is_scoped_and_idempotent(monkeypatch):
    db = _FakeDb(_source(), _citizen())
    workflow = _workflow(monkeypatch, db)
    relationship = _create(workflow, db, key="c2-idempotency-key-0004")
    workflow.activate(relationship.id, verification_reference="review-0004")

    revoked = workflow.revoke(relationship.id, reason="user_request")
    repeated = workflow.revoke(relationship.id, reason="user_request")

    assert revoked.status == CitizenRelationshipStatus.revoked.value
    assert repeated.id == revoked.id
    assert repeated.allows("profile") is False
