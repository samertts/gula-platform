"""Hash-chained audit record integrity tests (mutation, deletion, reordering)."""

from __future__ import annotations

from dataclasses import asdict, replace

import pytest
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability import (
    GENESIS_HASH,
    AuditFailure,
    AuditLog,
    AuditRecord,
    canonical_json_bytes,
    sha256_hex,
    verify_chain,
)

RECORDED_AT = "2026-01-01T00:00:00+00:00"


def _three_record_log() -> AuditLog:
    log = AuditLog()
    for index in range(1, 4):
        log.append(
            subject_id=f"SYN-EVT-{index:06d}",
            actor="SYN-NODE-000001",
            action="event_recorded",
            summary="synthetic_event",
            recorded_at=RECORDED_AT,
            payload={"index": index},
        )
    return log


def test_append_produces_verifiable_chain() -> None:
    log = _three_record_log()
    verification = log.verify()
    assert verification.ok
    assert verification.verified_count == 3
    assert verification.failure is None
    assert len(log.head) == 64
    assert log.records[0].previous_hash == GENESIS_HASH
    assert log.records[1].previous_hash == log.records[0].record_hash
    assert log.count == 3


def test_field_mutation_is_detected() -> None:
    log = _three_record_log()
    records = list(log.records)
    records[1] = replace(records[1], summary="tampered_summary")
    result = verify_chain(records, expected_head=log.head, expected_count=log.count)
    assert not result.ok
    assert result.failure is AuditFailure.HASH_MISMATCH


def test_middle_deletion_is_detected() -> None:
    log = _three_record_log()
    records = [log.records[0], log.records[2]]
    result = verify_chain(records, expected_head=log.head)
    assert not result.ok
    assert result.failure in {AuditFailure.SEQUENCE_GAP, AuditFailure.BROKEN_LINK}


def test_tail_deletion_is_detected_with_trusted_head() -> None:
    log = _three_record_log()
    result = verify_chain(log.records[:-1], expected_head=log.head, expected_count=log.count)
    assert not result.ok
    assert result.failure is AuditFailure.COUNT_MISMATCH

    without_count = verify_chain(log.records[:-1], expected_head=log.head)
    assert not without_count.ok
    assert without_count.failure is AuditFailure.HEAD_MISMATCH


def test_reordering_is_detected() -> None:
    log = _three_record_log()
    first, second, third = log.records
    head_swapped = verify_chain(
        [second, first, third], expected_head=log.head, expected_count=log.count
    )
    assert not head_swapped.ok
    assert head_swapped.failure is AuditFailure.GENESIS_MISMATCH
    tail_swapped = verify_chain(
        [first, third, second], expected_head=log.head, expected_count=log.count
    )
    assert not tail_swapped.ok
    assert tail_swapped.failure is AuditFailure.SEQUENCE_GAP


def test_genesis_tampering_and_broken_link_are_detected() -> None:
    log = _three_record_log()
    broken_genesis = [replace(log.records[0], previous_hash="1" * 64), *log.records[1:]]
    assert verify_chain(broken_genesis).failure is AuditFailure.GENESIS_MISMATCH
    rewired = replace(log.records[1], previous_hash="2" * 64)
    rewired = replace(rewired, record_hash=sha256_hex(canonical_json_bytes(rewired.body())))
    broken_link = [log.records[0], rewired, log.records[2]]
    assert verify_chain(broken_link).failure is AuditFailure.BROKEN_LINK


def test_payload_is_reduced_to_digest_without_raw_content() -> None:
    log = AuditLog()
    record = log.append(
        subject_id="SYN-OBS-000001",
        actor="SYN-NODE-000001",
        action="observation_recorded",
        summary="synthetic_observation",
        recorded_at=RECORDED_AT,
        payload={"note": "SYN-PAT-SECRET-VALUE"},
    )
    assert "SYN-PAT-SECRET-VALUE" not in str(asdict(record))
    assert len(record.payload_digest) == 64
    different = AuditLog().append(
        subject_id="SYN-OBS-000001",
        actor="SYN-NODE-000001",
        action="observation_recorded",
        summary="synthetic_observation",
        recorded_at=RECORDED_AT,
        payload={"note": "SYN-PAT-OTHER-VALUE"},
    )
    assert record.payload_digest != different.payload_digest


def test_payload_change_in_earlier_record_breaks_chain() -> None:
    log = _three_record_log()
    records: list[AuditRecord] = list(log.records)
    records[0] = replace(records[0], payload_digest="0" * 64)
    result = verify_chain(records)
    assert not result.ok
    assert result.failure is AuditFailure.HASH_MISMATCH


def test_non_synthetic_subject_is_rejected() -> None:
    log = AuditLog()
    with pytest.raises(InvalidSyntheticReferenceError):
        log.append(
            subject_id="PATIENT-12345",
            actor="SYN-NODE-000001",
            action="event_recorded",
            summary="synthetic_event",
            recorded_at=RECORDED_AT,
        )


def test_tail_deletion_of_anchored_log_is_detected() -> None:
    log = _three_record_log()
    anchored_head = log.head
    assert log.count == 3

    log._records.pop()

    verification = log.verify()
    assert verification.ok is False
    assert verification.failure is AuditFailure.COUNT_MISMATCH
    # The anchors do not move when the private record list is mutated.
    assert log.head == anchored_head
    assert log.count == 3


def test_interior_field_tamper_in_anchored_log_is_detected() -> None:
    log = _three_record_log()
    log._records[1] = replace(log._records[1], summary="tampered_summary")
    verification = log.verify()
    assert verification.ok is False
    assert verification.failure is AuditFailure.HASH_MISMATCH


def test_coherent_rehash_forgery_is_not_detected_by_unsigned_chain() -> None:
    """Lock in the documented limitation: in-process actors can forge coherently."""
    log = _three_record_log()
    forged: list[AuditRecord] = []
    previous_hash = GENESIS_HASH
    for index in range(1, 4):
        candidate = AuditRecord(
            sequence=index,
            subject_id=f"SYN-FORG-{index:06d}",
            actor="SYN-NODE-000001",
            action="event_recorded",
            summary="forged_event",
            recorded_at=RECORDED_AT,
            previous_hash=previous_hash,
            payload_digest=sha256_hex(canonical_json_bytes({"forged": index})),
            record_hash=GENESIS_HASH,
        )
        sealed = replace(candidate, record_hash=sha256_hex(canonical_json_bytes(candidate.body())))
        forged.append(sealed)
        previous_hash = sealed.record_hash

    assert [record.subject_id for record in forged] != [
        record.subject_id for record in log.records
    ]

    # An in-process actor rewrites the private records and the in-process anchors.
    log._records[:] = forged
    log._anchored_head = forged[-1].record_hash
    log._anchored_count = len(forged)

    verification = log.verify()
    assert verification.ok is True
    assert verification.failure is None
    assert verification.verified_count == 3
