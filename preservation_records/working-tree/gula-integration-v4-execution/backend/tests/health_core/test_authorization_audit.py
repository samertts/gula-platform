"""Tamper-detection and append-only guarantees for the authorization audit chain."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.health_core.authorization import (
    GENESIS_HASH,
    AuditRecord,
    AuthorizationAuditLog,
    Decision,
    PolicyId,
    Principal,
    ResourceContext,
    compute_record_hash,
    verify_audit_chain,
)
from app.health_core.contracts.authorization import Role
from app.health_core.contracts.catalogue import ContractOperation as Op

TENANT = "SYN-LAB-0001"
OTHER_TENANT = "SYN-LAB-0002"
PATIENT = "SYN-PAT-0001"
PRINCIPAL = "SYN-PRC-0001"


def _principal() -> Principal:
    return Principal(principal_id=PRINCIPAL, tenant_id=TENANT)


def _resource(action: Op = Op.ENCOUNTER_READ) -> ResourceContext:
    return ResourceContext(tenant_id=TENANT, resource_id="SYN-RES-0001", action=action)


def _populate(count: int = 4) -> AuthorizationAuditLog:
    log = AuthorizationAuditLog()
    for index in range(count):
        log.append(
            principal_id=PRINCIPAL,
            tenant_id=TENANT,
            action=f"health_core:test.{index}",
            resource_id=f"SYN-RES-{index:04d}",
            decision=Decision.ALLOW.value,
            policy_id=PolicyId.ALLOW_EXPLICIT.value,
            reason="explicit permission and scope checks passed",
            occurred_at=(datetime.now(UTC) - timedelta(minutes=count - index)).isoformat(),
        )
    return log


def test_empty_chain_is_valid():
    result = verify_audit_chain(())
    assert result.is_valid is True
    assert result.records_checked == 0
    assert result.errors == ()


def test_first_record_links_to_genesis_hash():
    log = _populate(1)
    record = log.records()[0]
    assert record.sequence == 1
    assert record.previous_hash == GENESIS_HASH
    assert log.verify().is_valid is True


def test_pristine_chain_verifies():
    log = _populate()
    assert len(log) == 4
    assert log.verify().is_valid is True
    assert verify_audit_chain(log.records()).is_valid is True


def test_records_are_frozen_and_cannot_be_mutated_in_place():
    log = _populate(1)
    record = log.records()[0]
    try:
        record.decision = Decision.DENY.value  # type: ignore[misc]
    except (AttributeError, TypeError):
        pass
    else:
        raise AssertionError("audit record must be frozen")
    assert log.verify().is_valid is True


def test_records_snapshot_is_a_immutable_tuple():
    log = _populate(2)
    records = log.records()
    assert isinstance(records, tuple)
    assert len(records) == 2


def test_tampered_field_is_detected():
    log = _populate(3)
    records = list(log.records())
    records[1] = replace(records[1], decision=Decision.DENY.value)
    result = verify_audit_chain(records)
    assert result.is_valid is False
    assert any("record hash" in error for error in result.errors)


def test_replaced_hash_is_detected():
    log = _populate(3)
    records = list(log.records())
    records[0] = replace(records[0], record_hash="0" * 64)
    result = verify_audit_chain(records)
    assert result.is_valid is False
    assert any("record hash" in error for error in result.errors)


def test_removed_record_is_detected():
    log = _populate(4)
    records = list(log.records())
    del records[2]
    result = verify_audit_chain(records)
    assert result.is_valid is False
    assert any("sequence" in error for error in result.errors)
    assert any("predecessor" in error for error in result.errors)


def test_first_record_deletion_is_detected():
    log = _populate(4)
    records = list(log.records())
    del records[0]
    result = verify_audit_chain(records)
    assert result.is_valid is False
    assert any("sequence" in error for error in result.errors)
    assert any("predecessor" in error for error in result.errors)


def test_reordered_records_are_detected():
    log = _populate(3)
    records = list(log.records())
    records[0], records[1] = records[1], records[0]
    result = verify_audit_chain(records)
    assert result.is_valid is False


def test_tail_truncation_is_not_detected_without_an_external_anchor():
    """LIMITATION: dropping the final records leaves a valid-looking prefix.

    The verifier only checks links *between surviving records*, so it cannot know
    that the log used to be longer. A durable, externally anchored checkpoint is
    required to make truncation evident; none exists here.
    """
    log = _populate(4)
    truncated = list(log.records())[:-1]
    assert len(truncated) == 3

    result = verify_audit_chain(truncated)
    assert result.is_valid is True
    assert result.errors == ()
    assert result.records_checked == 3


def test_coherent_full_chain_rehash_forgery_is_not_detected():
    """LIMITATION: rewriting the whole chain with consistent hashes verifies.

    Hashes are public and unsigned and the log is in-memory, so an attacker who
    can replace the records can recompute every hash and predecessor link. Only
    an external keyed/durable anchor could contradict such a coherent forgery.
    """
    original = list(_populate(3).records())
    forged: list[AuditRecord] = []
    previous_hash = GENESIS_HASH
    for record in original:
        edited = replace(
            record,
            decision=Decision.DENY.value,
            policy_id=PolicyId.DENY_TENANT.value,
            reason="forged but internally consistent history",
            previous_hash=previous_hash,
        )
        edited = replace(
            edited,
            record_hash=compute_record_hash(edited.canonical_payload(), previous_hash),
        )
        previous_hash = edited.record_hash
        forged.append(edited)

    result = verify_audit_chain(forged)
    assert [record.decision for record in forged] == [Decision.DENY.value] * 3
    assert forged[0].reason == "forged but internally consistent history"
    assert result.is_valid is True
    assert result.errors == ()
    assert result.records_checked == 3


def test_append_only_log_has_no_mutation_surface():
    log = _populate(2)
    forbidden = {"remove", "clear", "delete", "pop", "update", "insert", "replace"}
    assert forbidden.isdisjoint(dir(log))


def test_denials_are_audited_with_their_internal_policy_id():
    from app.health_core.authorization import AuthorizationEngine

    engine = AuthorizationEngine()
    reader = Principal(
        principal_id=PRINCIPAL,
        tenant_id=TENANT,
        roles=frozenset({Role.VIEWER}),
    )
    engine.evaluate(reader, _resource(Op.PRACTITIONER_READ))
    engine.evaluate(reader, _resource(Op.ENCOUNTER_CREATE))
    engine.evaluate(
        reader,
        ResourceContext(
            tenant_id=OTHER_TENANT,
            resource_id="SYN-RES-0002",
            action=Op.ENCOUNTER_READ,
        ),
    )
    records = engine.audit.records()
    assert [record.decision for record in records] == [
        Decision.ALLOW.value,
        Decision.DENY.value,
        Decision.DENY.value,
    ]
    assert records[1].policy_id == PolicyId.DENY_MISSING_PERMISSION.value
    assert records[2].policy_id == PolicyId.DENY_TENANT.value
    assert records[2].tenant_id == OTHER_TENANT
    assert engine.audit.verify().is_valid is True
