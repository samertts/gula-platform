"""B3 — verified guardian / minor / NHID policy tests (fail-closed).

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B3 (AUD-PRV-005).

Synthetic fixtures only. No real patient data, no identifier is minted, no
protected decision is changed.
"""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from app._compat import UTC
from app.identity.services.verified_guardian_guard import (
    AGE_OF_MAJORITY,
    AGE_OF_REASONING,
    GuardianPolicyError,
    age_transition,
    assert_no_twin_merge,
    canonical_nid_hash,
    derive_age,
    evaluate_guardian_access,
    guardian_relationship_permits,
    is_authorized_verifier_role,
    subject_is_linkable,
)

_TODAY = date(2026, 11, 19)


def _citizen(*, dob=date(2015, 5, 20), cid="CIT-001", nid_hash=None,
             block="ABC2015M", merged=None, deceased=False, status="active"):
    return SimpleNamespace(
        id=cid,
        date_of_birth=dob,
        national_id_hash=nid_hash,
        name_blocking_key=block,
        merged_into_id=merged,
        is_deceased=deceased,
        identity_status=SimpleNamespace(value=status) if isinstance(status, str) else status,
    )


def _relationship(*, rtype="guardian", verified=True, active=True, purpose="guardian_access",
                  gtype="parent", source_verified=True, guardian_verified=None,
                  scope=None, metadata=None):
    meta = {
        "guardian_type": gtype,
        "source_verified": source_verified,
        "guardian_verified": verified if guardian_verified is None else guardian_verified,
    }
    if metadata:
        meta.update(metadata)
    return SimpleNamespace(
        id="REL-001",
        relationship_type=rtype,
        verified_at=datetime(2026, 1, 1, tzinfo=UTC) if verified else None,
        purpose=purpose,
        scope=scope if scope is not None else {"resources": ["clinical_record", "profile"]},
        metadata_=meta,
        citizen_id="CIT-001",
        is_active_at=lambda now=None: active,
    )


# ── Age derivation & transitions ─────────────────────────────────────────────


def test_derive_age_exact_and_eve_of_birthday():
    assert derive_age(date(2015, 11, 19), today=_TODAY) == 11
    assert derive_age(date(2015, 11, 20), today=_TODAY) == 10  # birthday tomorrow


def test_derive_age_from_datetime():
    assert derive_age(datetime(2010, 1, 1, tzinfo=UTC), today=_TODAY) == 16


@pytest.mark.parametrize("bad", [None, date(2030, 1, 1), date(1800, 1, 1)])
def test_derive_age_fails_closed(bad):
    with pytest.raises(GuardianPolicyError):
        derive_age(bad, today=_TODAY)


def test_age_transition_boundaries():
    assert age_transition(date(2020, 1, 1), today=_TODAY) == "pre_reasoning"
    assert age_transition(date(2010, 1, 1), today=_TODAY) == "reasoning"  # 16, far from birthday
    # 17 years old, birthday in 30 days -> near majority
    assert age_transition(date(2008, 12, 19), today=_TODAY) == "near_majority"
    assert age_transition(date(2008, 11, 19), today=_TODAY) == "adult"  # exactly 18
    assert AGE_OF_MAJORITY == 18 and AGE_OF_REASONING == 16


# ── NHID input contract (canonical only; no minting) ─────────────────────────


def test_canonical_nid_hash_collapses_digit_scripts():
    western = canonical_nid_hash("123456789")
    assert canonical_nid_hash("١٢٣٤٥٦٧٨٩") == western  # Arabic-Indic
    assert canonical_nid_hash("۱۲۳۴۵۶۷۸۹") == western  # Extended
    assert canonical_nid_hash("1-2 3/4 5.6 7 8 9") == western
    assert len(western) == 64  # HMAC-SHA256 hex digest; no identifier is stored


@pytest.mark.parametrize("bad", [None, "", "   ", "----", "abc"])
def test_canonical_nid_hash_fails_closed(bad):
    with pytest.raises(GuardianPolicyError):
        canonical_nid_hash(bad)


# ── Twins-never-merged ───────────────────────────────────────────────────────


def test_twins_never_merged_on_nid_collision():
    a = _citizen(cid="CIT-001", nid_hash="HASH-X", dob=date(2015, 5, 20))
    b = _citizen(cid="CIT-002", nid_hash="HASH-X", dob=date(2015, 5, 21))
    with pytest.raises(GuardianPolicyError, match="twins_never_merged"):
        assert_no_twin_merge(a, b)


def test_twins_never_merged_on_blocking_key_and_dob_collision():
    a = _citizen(cid="CIT-001", block="SAME", dob=date(2015, 5, 20))
    b = _citizen(cid="CIT-002", block="SAME", dob=date(2015, 5, 20))
    with pytest.raises(GuardianPolicyError, match="twins_never_merged"):
        assert_no_twin_merge(a, b)


def test_same_record_is_not_a_merge():
    a = _citizen(cid="CIT-001", nid_hash="HASH-X")
    assert_no_twin_merge(a, a)  # idempotent, no error


# ── Subject linkability ──────────────────────────────────────────────────────


def test_subject_linkability():
    assert subject_is_linkable(_citizen()) is True
    assert subject_is_linkable(None) is False
    assert subject_is_linkable(_citizen(merged="CIT-999")) is False
    assert subject_is_linkable(_citizen(deceased=True)) is False
    assert subject_is_linkable(_citizen(status="merged")) is False


def test_verifier_role_gate():
    assert is_authorized_verifier_role("master_admin") is True
    assert is_authorized_verifier_role("security_administrator") is True
    assert is_authorized_verifier_role("citizen") is False  # no self-assertion
    assert is_authorized_verifier_role(None) is False


# ── Main decision (fail-closed) ──────────────────────────────────────────────


def _decision(**kwargs):
    defaults = {
        "subject": _citizen(),
        "relationship": _relationship(),
        "action": "read",
        "today": _TODAY,
    }
    defaults.update(kwargs)
    return evaluate_guardian_access(**defaults)


def test_valid_verified_guardian_access_allowed():
    d = _decision()
    assert d.allowed is True
    assert d.reason == "verified_guardian_access"
    assert d.age == 11
    assert d.guardian_type == "parent"


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"subject": None}, "subject_not_linkable"),
        ({"relationship": None}, "no_guardian_relationship"),
        ({"relationship": _relationship(rtype="self")}, "not_guardian_relationship"),
        ({"relationship": _relationship(verified=False)}, "guardian_relationship_unverified"),
        ({"relationship": _relationship(active=False)}, "guardian_relationship_not_active"),
        ({"relationship": _relationship(source_verified=False, guardian_verified=False)}, "guardian_not_verified"),
        ({"relationship": _relationship(purpose="citizen_workspace")}, "guardian_purpose_invalid"),
        ({"relationship": _relationship(gtype="")}, "guardian_type_missing"),
        ({"action": "export"}, "action_not_permitted_for_guardian"),
        ({"action": "delete"}, "action_not_permitted_for_guardian"),
        ({"nhid_input": "bad-input"}, "nid_input_invalid"),
    ],
)
def test_invalid_guardian_conditions_denied(kwargs, reason):
    d = _decision(**kwargs)
    assert d.allowed is False
    assert d.reason == reason


def test_adult_subject_guardian_authority_ended():
    d = _decision(subject=_citizen(dob=date(2008, 1, 1)))
    assert d.allowed is False
    assert d.reason == "guardian_authority_ended"


def test_guardian_rule_table_denies_action():
    # Grandparents cannot receive results per GuardianRulesService.
    d = _decision(relationship=_relationship(gtype="grandparent"), action="receive_results")
    assert d.allowed is False
    assert d.reason == "guardian_action_denied_by_rule_table"


def test_near_majority_requires_fresh_reverification():
    near = _citizen(dob=date(2008, 12, 19))  # 17, birthday in 30 days
    d = _decision(subject=near)
    assert d.allowed is False
    assert d.reason == "reverification_required_at_age_transition"
    d2 = _decision(subject=near, reverified_at_transition=True)
    assert d2.allowed is True
    assert d2.requires_reverification is True


def test_reasoning_age_allows_with_reverification_flag():
    d = _decision(subject=_citizen(dob=date(2010, 1, 1)))
    assert d.allowed is True
    assert d.transition == "reasoning"
    assert d.requires_reverification is True


# ── Adapter used by canonical authorization ──────────────────────────────────


def test_scope_enforcement():
    rel = _relationship(scope={"resources": ["clinical_record", "profile"]})
    assert guardian_relationship_permits(
        rel, action="read", resource_type="clinical_record", subject=_citizen()
    ) is True
    assert guardian_relationship_permits(
        rel, action="read", resource_type="billing", subject=_citizen()
    ) is False
    wildcard = _relationship(scope={"resources": ["*"]})
    assert guardian_relationship_permits(
        wildcard, action="read", resource_type="clinical_record", subject=_citizen()
    ) is False


def test_adapter_denies_when_policy_denies():
    rel = _relationship(rtype="self")
    assert guardian_relationship_permits(
        rel, action="read", resource_type="clinical_record", subject=_citizen()
    ) is False


# ── Canonical workflow: verified guardian creation path ──────────────────────


class _WorkflowQuery:
    def __init__(self, db, model):
        self.db = db
        self.model = model
        self.filters = []

    def filter(self, *conditions):
        self.filters.extend(conditions)
        return self

    def with_for_update(self):
        return self

    def first(self):
        from app.identity.services import citizen_relationship_service as m
        if self.model is m.User:
            return self.db.source
        if self.model is m.Citizen:
            # The twin-ambiguity query (blocking key + DOB) vs the subject lookup.
            if any("name_blocking_key" in str(c) for c in self.filters):
                return self.db.collision
            return self.db.citizen
        if self.model is m.CitizenRelationship:
            return self.db.relationships[0] if self.db.relationships else None
        return None


class _WorkflowDb:
    def __init__(self, source, citizen, collision=None):
        self.source = source
        self.citizen = citizen
        self.collision = collision
        self.relationships = []
        self.commits = 0

    def query(self, model):
        return _WorkflowQuery(self, model)

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


def _workflow(monkeypatch, db, role="ministry_admin"):
    from app.identity.services import citizen_relationship_service as m

    monkeypatch.setattr(m, "log_action", lambda *args, **kwargs: None)
    return m.CitizenRelationshipWorkflow(
        db, SimpleNamespace(id=9001, role=role), request_ip="127.0.0.1"
    )


def _valid_guardian_kwargs():
    return {
        "legacy_user_id": 101,
        "citizen_id": "CIT-001",
        "guardian_type": "parent",
        "guardian_nid_input": "123456789",
        "purpose": "guardian_access",
        "scope": {"resources": ["clinical_record", "profile"]},
        "idempotency_key": "b3-guardian-idempotency-key-0001",
    }


def _source():
    return SimpleNamespace(id=101, is_active=True, is_verified=True)


def _minor_citizen():
    # 11 years old at the pinned date.
    return _citizen(dob=date(2015, 5, 20), nid_hash=None)


def test_workflow_creates_pending_guardian(monkeypatch):
    db = _WorkflowDb(_source(), _minor_citizen())
    rel = _workflow(monkeypatch, db).create_pending_guardian(**_valid_guardian_kwargs())
    assert rel.relationship_type == "guardian"
    assert rel.status == "pending"
    assert rel.metadata_["guardian_type"] == "parent"
    assert rel.metadata_["guardian_verified"] is True
    assert rel.metadata_["workflow"] == "b3"
    assert "123456789" not in str(rel.metadata_)  # raw NID never persisted


def test_workflow_rejects_self_asserted_guardianship(monkeypatch):
    db = _WorkflowDb(_source(), _minor_citizen())
    with pytest.raises(Exception, match="authorized guardian verifier"):
        _workflow(monkeypatch, db, role="citizen").create_pending_guardian(
            **_valid_guardian_kwargs()
        )


def test_workflow_rejects_adult_subject(monkeypatch):
    db = _WorkflowDb(_source(), _citizen(dob=date(2000, 1, 1)))
    with pytest.raises(Exception, match="requires a minor subject"):
        _workflow(monkeypatch, db).create_pending_guardian(**_valid_guardian_kwargs())


def test_workflow_rejects_merged_subject(monkeypatch):
    db = _WorkflowDb(_source(), _citizen(dob=date(2015, 5, 20), merged="CIT-999"))
    with pytest.raises(Exception, match="not linkable"):
        _workflow(monkeypatch, db).create_pending_guardian(**_valid_guardian_kwargs())


def test_workflow_rejects_twin_collision(monkeypatch):
    # Distinct citizen with the SAME blocking key + DOB as the subject (a twin).
    collision = _citizen(cid="CIT-002", dob=date(2015, 5, 20), block="ABC2015M")
    db = _WorkflowDb(_source(), _minor_citizen(), collision=collision)
    with pytest.raises(Exception, match="Ambiguous identity"):
        _workflow(monkeypatch, db).create_pending_guardian(**_valid_guardian_kwargs())


def test_workflow_rejects_invalid_nid_input(monkeypatch):
    db = _WorkflowDb(_source(), _minor_citizen())
    kwargs = _valid_guardian_kwargs()
    kwargs["guardian_nid_input"] = "not-a-valid-nid"
    with pytest.raises(Exception, match="Invalid guardian NID input"):
        _workflow(monkeypatch, db).create_pending_guardian(**kwargs)
