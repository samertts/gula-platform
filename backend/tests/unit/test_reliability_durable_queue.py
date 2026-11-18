"""Focused tests for the in-process durable-event-queue reliability engine.

All fixtures are synthetic ``SYN-`` values. No filesystem, database, broker,
wall-clock sleep or production durability claim is involved.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from app.health_core.reliability.durable_queue import (
    AttemptOutcome,
    ConflictState,
    DurableEventQueue,
    EventState,
    QueueConfig,
    QueueEvent,
    QueueReason,
    QueueStatus,
    ResolutionAction,
    canonical_json_bytes,
    sealed_envelope,
)

TENANT = "SYN-TNT-000001"
FACILITY = "SYN-FAC-000001"
EVENT_TYPE = "synthetic_result_recorded"


class FakeClock:
    """Deterministic millisecond stand-in; never reads a wall clock."""

    def __init__(self, start: int = 1000) -> None:
        self.value = start

    def __call__(self) -> int:
        self.value += 1
        return self.value


class RecordingSleeper:
    """Capture backoff delays without sleeping."""

    def __init__(self) -> None:
        self.calls: list[int] = []

    def __call__(self, delay_ms: int) -> None:
        self.calls.append(delay_ms)


def _queue(
    *,
    clock: FakeClock | None = None,
    sleeper: RecordingSleeper | None = None,
    max_attempts: int = 3,
    backoff: tuple[int, ...] = (2, 4),
    tenant_id: str = TENANT,
    facility_id: str = FACILITY,
) -> DurableEventQueue:
    return DurableEventQueue(
        QueueConfig(
            tenant_id=tenant_id,
            facility_id=facility_id,
            max_attempts=max_attempts,
            backoff_delays_ms=backoff,
        ),
        clock=clock,
        sleeper=sleeper,
    )


def _event(
    event_id: str = "SYN-EVT-000001",
    *,
    entity_key: str = "SYN-ENT-000001",
    version: int = 1,
    tenant_id: str = TENANT,
    facility_id: str = FACILITY,
    event_type: str = EVENT_TYPE,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "entity_key": entity_key,
        "tenant_id": tenant_id,
        "facility_id": facility_id,
        "version": version,
        "payload": dict(payload or {"value": "SYN-VAL-000001"}),
    }


def _counting_handler(calls: list[str], marker: str = "SYN-OK"):
    def handler(event: QueueEvent) -> str:
        calls.append(event.event_id)
        return f"{marker}-{event.event_id}"

    return handler


# 1. Idempotency: duplicate event -> exactly one side effect
def test_duplicate_event_is_processed_exactly_once() -> None:
    queue = _queue()
    event = _event()
    event_id = str(event["event_id"])
    side_effects: list[str] = []
    handler = _counting_handler(side_effects)

    first = queue.enqueue(event)
    second = queue.enqueue(dict(event))
    assert first.status is QueueStatus.OK
    assert first.reason is QueueReason.ACCEPTED
    assert second.status is QueueStatus.DUPLICATE
    assert second.reason is QueueReason.DUPLICATE_EVENT_ID
    assert len(queue.log_entries) == 1

    processed = queue.process(event_id, handler)
    replayed = queue.process(event_id, handler)
    commit_replay = queue.commit(event_id)
    begin_replay = queue.begin(event_id)

    assert processed.status is QueueStatus.OK
    assert processed.reason is QueueReason.COMMITTED
    assert replayed.status is QueueStatus.DUPLICATE
    assert replayed.reason is QueueReason.ALREADY_COMMITTED
    assert commit_replay.status is QueueStatus.DUPLICATE
    assert commit_replay.reason is QueueReason.ALREADY_COMMITTED
    assert begin_replay.status is QueueStatus.DUPLICATE
    assert begin_replay.reason is QueueReason.ALREADY_COMMITTED
    assert side_effects == [event_id]
    assert queue.processed_keys == frozenset({event_id})
    assert queue.processed_key_count == 1
    assert queue.event_state(event_id) is EventState.COMMITTED


# 2. Retry: transient failures then success with deterministic trace
def test_transient_failures_retry_with_deterministic_attempt_and_backoff_trace() -> None:
    clock = FakeClock()
    sleeper = RecordingSleeper()
    queue = _queue(clock=clock, sleeper=sleeper, max_attempts=4, backoff=(2, 4, 8))
    event = _event("SYN-EVT-000002")
    event_id = str(event["event_id"])
    queue.enqueue(event)
    calls: list[str] = []

    def flaky(evt: QueueEvent) -> str:
        calls.append(evt.event_id)
        if len(calls) < 3:
            raise ValueError("synthetic transient failure")
        return "SYN-RESULT-OK"

    result = queue.process(event_id, flaky)
    assert result.delivery is not None
    assert result.status is QueueStatus.OK
    assert result.reason is QueueReason.COMMITTED
    assert [attempt.attempt for attempt in result.delivery.attempts] == [1, 2, 3]
    assert [attempt.outcome for attempt in result.delivery.attempts] == [
        AttemptOutcome.FAILED,
        AttemptOutcome.FAILED,
        AttemptOutcome.SUCCEEDED,
    ]
    # APPEND and BEGIN each consume one clock tick; log appends interleave with attempts.
    assert [attempt.at_ms for attempt in result.delivery.attempts] == [1003, 1005, 1007]
    assert result.delivery.backoff_trace == (2, 4)
    assert sleeper.calls == [2, 4]
    assert calls == [event_id, event_id, event_id]
    assert len([entry for entry in queue.log_entries if entry.operation == "ATTEMPT"]) == 3
    assert queue.processed_key_count == 1


# 3. Dead letter after exhausted retries, with a structured reason
def test_exhausted_retries_dead_letter_with_reason() -> None:
    sleeper = RecordingSleeper()
    queue = _queue(sleeper=sleeper, max_attempts=3, backoff=(2, 4))
    event = _event("SYN-EVT-000003")
    event_id = str(event["event_id"])
    queue.enqueue(event)
    calls: list[str] = []

    def always_fails(evt: QueueEvent) -> None:
        calls.append(evt.event_id)
        raise RuntimeError("synthetic permanent failure")

    result = queue.process(event_id, always_fails)
    assert result.status is QueueStatus.DEAD_LETTERED
    assert result.reason is QueueReason.MAX_ATTEMPTS_EXHAUSTED
    assert result.delivery is not None
    assert [attempt.attempt for attempt in result.delivery.attempts] == [1, 2, 3]
    assert result.delivery.backoff_trace == (2, 4)
    assert sleeper.calls == [2, 4]
    assert len(calls) == 3
    assert len(queue.dead_letters) == 1
    letter = queue.dead_letters[0]
    assert letter.event_id == event_id
    assert letter.reason is QueueReason.MAX_ATTEMPTS_EXHAUSTED
    assert letter.attempts == 3
    assert letter.letter_id.startswith("SYN-DLQ-")
    assert letter.last_error.startswith("RuntimeError:")
    assert "synthetic permanent failure" not in letter.last_error  # no raw error text in the log
    assert queue.processed_key_count == 0
    assert queue.event_state(event_id) is EventState.DEAD_LETTERED


# 4. Crash before commit -> recover() redelivers exactly the in-flight event
def test_crash_before_commit_recovers_only_in_flight_event() -> None:
    clock = FakeClock()
    queue = _queue(clock=clock)
    committed_event = _event("SYN-EVT-000010", entity_key="SYN-ENT-000010", event_type="synthetic_committed")
    inflight_event = _event("SYN-EVT-000011", entity_key="SYN-ENT-000011", event_type="synthetic_inflight")
    committed_id = str(committed_event["event_id"])
    inflight_id = str(inflight_event["event_id"])
    calls: dict[str, int] = {committed_id: 0, inflight_id: 0}
    queue.register_handler(
        "synthetic_committed",
        lambda evt: _record(calls, evt.event_id),
    )
    queue.register_handler(
        "synthetic_inflight",
        lambda evt: _record(calls, evt.event_id),
    )

    queue.enqueue(committed_event)
    queue.enqueue(inflight_event)
    assert queue.process(committed_id, lambda evt: _record(calls, evt.event_id)).status is QueueStatus.OK

    began = queue.begin(inflight_id)
    delivered = queue.deliver(inflight_id, lambda evt: _record(calls, evt.event_id))
    assert began.status is QueueStatus.OK
    assert delivered.status is QueueStatus.OK
    assert queue.event_state(inflight_id) is EventState.IN_FLIGHT
    assert calls == {committed_id: 1, inflight_id: 1}

    crash = queue.simulate_crash()
    assert crash.status is QueueStatus.OK
    assert crash.reason is QueueReason.CRASHED
    assert crash.log_entries == len(queue.log_entries)
    assert queue.processed_keys == frozenset()  # all derived state, including idempotency, is dropped
    assert queue.event_state(committed_id) is None  # derived state dropped

    recovery = queue.recover()
    assert recovery.status is QueueStatus.OK
    assert recovery.reason is QueueReason.RECOVERED
    assert recovery.entries_replayed == crash.log_entries
    assert [item.event_id for item in recovery.redelivered] == [inflight_id]
    assert recovery.pending_redelivery == ()
    assert calls == {committed_id: 1, inflight_id: 2}
    assert queue.processed_keys == frozenset({committed_id, inflight_id})
    assert queue.event_state(committed_id) is EventState.COMMITTED
    assert queue.event_state(inflight_id) is EventState.COMMITTED


def _record(calls: dict[str, int], event_id: str) -> str:
    calls[event_id] += 1
    return f"SYN-OK-{event_id}"


# 5. Crash after commit -> no redelivery
def test_crash_after_commit_does_not_redeliver() -> None:
    queue = _queue()
    event = _event("SYN-EVT-000012")
    event_id = str(event["event_id"])
    calls: list[str] = []
    queue.enqueue(event)
    queue.register_handler(EVENT_TYPE, _counting_handler(calls))
    assert queue.process(event_id, _counting_handler(calls)).status is QueueStatus.OK

    crash = queue.simulate_crash()
    recovery = queue.recover()

    assert crash.status is QueueStatus.OK
    assert recovery.status is QueueStatus.OK
    assert recovery.redelivered == ()
    assert recovery.pending_redelivery == ()
    assert calls == [event_id]
    assert queue.processed_keys == frozenset({event_id})
    assert queue.event_state(event_id) is EventState.COMMITTED


# 6. Version conflict quarantined, resolution idempotent, no silent overwrite
def test_version_conflict_is_quarantined_and_resolution_is_idempotent() -> None:
    queue = _queue()
    entity_key = "SYN-ENT-000020"
    original = _event("SYN-EVT-000020", entity_key=entity_key, version=1, payload={"value": "SYN-V1"})
    divergent = _event("SYN-EVT-000021", entity_key=entity_key, version=2, payload={"value": "SYN-V2"})
    queue.enqueue(original)
    queue.enqueue(divergent)

    assert queue.process(str(original["event_id"]), lambda evt: "SYN-OK").status is QueueStatus.OK
    conflicted = queue.process(str(divergent["event_id"]), lambda evt: "SYN-OK")

    assert conflicted.status is QueueStatus.QUARANTINED
    assert conflicted.reason is QueueReason.VERSION_CONFLICT
    assert conflicted.conflict_id is not None
    assert queue.entity_version(entity_key) == 1
    assert queue.processed_keys == frozenset({str(original["event_id"])})
    assert queue.event_state(str(divergent["event_id"])) is EventState.QUARANTINED
    conflict = queue.conflicts[conflicted.conflict_id]
    assert conflict.state is ConflictState.QUARANTINED
    assert conflict.local_version == 1
    assert conflict.remote_version == 2
    assert conflict.local_digest != conflict.remote_digest

    resolved = queue.resolve_take_remote(conflicted.conflict_id)
    assert resolved.status is QueueStatus.OK
    assert resolved.reason is QueueReason.RESOLVED
    assert resolved.action is ResolutionAction.TAKE_REMOTE
    assert resolved.chosen_version == 2
    assert resolved.resolution_id
    assert queue.entity_version(entity_key) == 2
    assert queue.resolution_count == 1
    assert queue.conflicts[conflicted.conflict_id].state is ConflictState.RESOLVED

    replay_same = queue.resolve_take_remote(conflicted.conflict_id)
    assert replay_same.status is QueueStatus.DUPLICATE
    assert replay_same.reason is QueueReason.ALREADY_RESOLVED
    assert replay_same.resolution_id == resolved.resolution_id

    changed_mind = queue.resolve_take_local(conflicted.conflict_id)
    assert changed_mind.status is QueueStatus.REJECTED
    assert changed_mind.reason is QueueReason.CONFLICT_ALREADY_DECIDED
    assert queue.entity_version(entity_key) == 2
    assert queue.resolution_count == 1
    assert queue.processed_keys == frozenset({str(original["event_id"]), str(divergent["event_id"])})


def test_manual_resolution_is_explicit_and_idempotent() -> None:
    queue = _queue()
    entity_key = "SYN-ENT-000021"
    first = _event("SYN-EVT-000022", entity_key=entity_key, version=1)
    second = _event("SYN-EVT-000023", entity_key=entity_key, version=2)
    queue.enqueue(first)
    queue.enqueue(second)
    queue.process(str(first["event_id"]), lambda evt: "SYN-OK")
    conflicted = queue.process(str(second["event_id"]), lambda evt: "SYN-OK")
    assert conflicted.conflict_id is not None

    manual = queue.resolve_manual(conflicted.conflict_id, chosen_version=7)
    assert manual.status is QueueStatus.OK
    assert manual.action is ResolutionAction.MANUAL
    assert manual.chosen_version == 7
    assert queue.entity_version(entity_key) == 7
    replay = queue.resolve_manual(conflicted.conflict_id, chosen_version=7)
    assert replay.status is QueueStatus.DUPLICATE
    assert replay.reason is QueueReason.ALREADY_RESOLVED
    invalid = queue.resolve_manual(conflicted.conflict_id, chosen_version=8)
    assert invalid.status is QueueStatus.REJECTED
    assert invalid.reason is QueueReason.CONFLICT_ALREADY_DECIDED
    assert queue.entity_version(entity_key) == 7


def test_same_version_with_different_payload_is_also_quarantined() -> None:
    queue = _queue()
    entity_key = "SYN-ENT-000022"
    first = _event("SYN-EVT-000024", entity_key=entity_key, version=1, payload={"value": "SYN-A"})
    second = _event("SYN-EVT-000025", entity_key=entity_key, version=1, payload={"value": "SYN-B"})
    queue.enqueue(first)
    queue.enqueue(second)
    queue.process(str(first["event_id"]), lambda evt: "SYN-OK")
    result = queue.process(str(second["event_id"]), lambda evt: "SYN-OK")
    assert result.status is QueueStatus.QUARANTINED
    assert result.reason is QueueReason.VERSION_CONFLICT
    assert queue.entity_version(entity_key) == 1


# 7. Malformed events fail closed with typed reason codes
def test_malformed_events_are_rejected_with_reason_codes() -> None:
    queue = _queue()
    valid = _event()
    cases: tuple[tuple[dict[str, Any], QueueReason], ...] = (
        ({}, QueueReason.MISSING_EVENT_ID),
        ({**valid, "event_id": ""}, QueueReason.MISSING_EVENT_ID),
        ({key: value for key, value in valid.items() if key != "entity_key"}, QueueReason.MISSING_ENTITY_KEY),
        ({**valid, "entity_key": "   "}, QueueReason.MISSING_ENTITY_KEY),
        ({**valid, "event_id": "EVT-NOT-SYNTHETIC"}, QueueReason.MALFORMED_EVENT),
        ({**valid, "version": 0}, QueueReason.MALFORMED_EVENT),
        ({**valid, "tenant_id": "TNT-REAL"}, QueueReason.MALFORMED_EVENT),
        ({**valid, "payload": {"bad": object()}}, QueueReason.NON_SERIALIZABLE_PAYLOAD),
    )
    for raw, expected_reason in cases:
        result = queue.enqueue(raw)
        assert result.status is QueueStatus.REJECTED
        assert result.reason is expected_reason
        assert result.sequence == 0
    non_object = queue.enqueue("SYN-EVT-999999")  # type: ignore[arg-type]
    assert non_object.status is QueueStatus.REJECTED
    assert non_object.reason is QueueReason.MALFORMED_EVENT
    assert queue.log_entries == ()
    assert queue.processed_key_count == 0
    assert queue.event_state(str(valid["event_id"])) is None


# 8. Log integrity: tampered and truncated logs are detected on replay
def test_tampered_log_is_detected_on_replay_without_state_corruption() -> None:
    queue = _queue()
    event = _event("SYN-EVT-000030")
    event_id = str(event["event_id"])
    queue.enqueue(event)
    queue.process(event_id, lambda evt: "SYN-OK")
    good = queue.log_bytes()
    assert good

    parsed = json.loads(good)
    parsed["entries"][0]["entity_key"] = "SYN-ENT-999999"
    tampered = canonical_json_bytes(parsed)
    assert queue.verify_log(tampered).status is QueueStatus.REJECTED
    recovery = queue.recover(tampered)

    assert recovery.status is QueueStatus.REJECTED
    assert recovery.reason is QueueReason.LOG_INTEGRITY_FAILURE
    assert recovery.entries_replayed == 0
    assert recovery.detail
    assert queue.processed_keys == frozenset({event_id})
    assert queue.event_state(event_id) is EventState.COMMITTED


def test_truncated_log_with_recomputed_checksum_and_anchors_is_rejected() -> None:
    queue = _queue()
    event = _event("SYN-EVT-000031")
    event_id = str(event["event_id"])
    queue.enqueue(event)
    queue.process(event_id, lambda evt: "SYN-OK")
    good = queue.log_bytes()

    parsed = json.loads(good)
    parsed.pop("checksum")
    parsed["entries"] = parsed["entries"][:-1]
    parsed["record_count"] = len(parsed["entries"])
    parsed["last_sequence"] = len(parsed["entries"])
    parsed["anchored_head"] = parsed["entries"][-1]["entry_hash"]
    truncated = canonical_json_bytes(sealed_envelope(parsed))
    assert truncated != good
    assert queue.verify_log(truncated).status is QueueStatus.REJECTED

    recovery = queue.recover(truncated)
    assert recovery.status is QueueStatus.REJECTED
    assert recovery.reason is QueueReason.LOG_INTEGRITY_FAILURE
    assert "anchors" in recovery.detail
    assert queue.processed_keys == frozenset({event_id})
    assert queue.event_state(event_id) is EventState.COMMITTED

    # Untouched log still replays cleanly after the failed recovery attempt.
    clean = queue.recover(good)
    assert clean.status is QueueStatus.OK
    assert clean.entries_replayed == len(queue.log_entries)


def test_fresh_instance_can_restore_committed_state_from_exported_log() -> None:
    source = _queue()
    event = _event("SYN-EVT-000032")
    event_id = str(event["event_id"])
    source.enqueue(event)
    source.process(event_id, lambda evt: "SYN-OK")
    exported = source.log_bytes()

    restored = _queue()
    assert restored.processed_key_count == 0
    recovery = restored.recover(exported)
    assert recovery.status is QueueStatus.OK
    assert recovery.redelivered == ()
    assert restored.processed_keys == frozenset({event_id})
    assert restored.event_state(event_id) is EventState.COMMITTED


# 9. Tenant and facility scoping: foreign events cannot mutate this queue's state
def test_foreign_tenant_event_cannot_commit_into_this_queues_state() -> None:
    queue = _queue(tenant_id=TENANT, facility_id=FACILITY)
    foreign = _event("SYN-EVT-000040", tenant_id="SYN-TNT-000002", entity_key="SYN-ENT-000040")
    event_id = str(foreign["event_id"])
    appended = queue.enqueue(foreign)
    assert appended.status is QueueStatus.OK  # syntactically valid, logged, never committed here

    begun = queue.begin(event_id)
    delivered = queue.deliver(event_id, lambda evt: "SYN-OK")
    committed = queue.commit(event_id)
    processed = queue.process(event_id, lambda evt: "SYN-OK")

    for result in (begun, delivered, committed, processed):
        assert result.status is QueueStatus.REJECTED
        assert result.reason is QueueReason.TENANT_MISMATCH
    assert queue.processed_key_count == 0
    assert queue.entity_version("SYN-ENT-000040") is None
    assert queue.event_state(event_id) is EventState.PENDING
    assert not [entry for entry in queue.log_entries if entry.operation in {"COMMIT", "QUARANTINE"}]


def test_foreign_facility_event_cannot_commit_into_this_queues_state() -> None:
    queue = _queue(tenant_id=TENANT, facility_id=FACILITY)
    foreign = _event("SYN-EVT-000041", facility_id="SYN-FAC-000002", entity_key="SYN-ENT-000041")
    event_id = str(foreign["event_id"])
    queue.enqueue(foreign)
    begun = queue.begin(event_id)
    committed = queue.commit(event_id)
    processed = queue.process(event_id, lambda evt: "SYN-OK")
    assert begun.status is QueueStatus.REJECTED
    assert begun.reason is QueueReason.FACILITY_MISMATCH
    assert committed.reason is QueueReason.FACILITY_MISMATCH
    assert processed.reason is QueueReason.FACILITY_MISMATCH
    assert queue.processed_key_count == 0
    assert queue.entity_version("SYN-ENT-000041") is None


# Extra invariants
def test_begin_is_required_before_delivery_and_commit() -> None:
    queue = _queue()
    event_id = "SYN-EVT-000050"
    queue.enqueue(_event(event_id))
    delivery = queue.deliver(event_id, lambda evt: "SYN-OK")
    commit = queue.commit(event_id)
    assert delivery.status is QueueStatus.REJECTED
    assert delivery.reason is QueueReason.NOT_IN_FLIGHT
    assert commit.status is QueueStatus.REJECTED
    assert commit.reason is QueueReason.NOT_IN_FLIGHT
    for unknown in (
        queue.begin("SYN-EVT-999999"),
        queue.deliver("SYN-EVT-999999", lambda evt: "SYN-OK"),
        queue.commit("SYN-EVT-999999"),
    ):
        assert unknown.status is QueueStatus.REJECTED
        assert unknown.reason is QueueReason.UNKNOWN_EVENT


def test_resolution_survives_crash_replay_and_remains_idempotent() -> None:
    queue = _queue()
    entity_key = "SYN-ENT-000060"
    first = _event("SYN-EVT-000060", entity_key=entity_key, version=1)
    second = _event("SYN-EVT-000061", entity_key=entity_key, version=2)
    queue.enqueue(first)
    queue.enqueue(second)
    queue.process(str(first["event_id"]), lambda evt: "SYN-OK")
    conflicted = queue.process(str(second["event_id"]), lambda evt: "SYN-OK")
    assert conflicted.conflict_id is not None
    resolved = queue.resolve_take_remote(conflicted.conflict_id)
    assert resolved.status is QueueStatus.OK

    queue.simulate_crash()
    recovery = queue.recover()
    assert recovery.status is QueueStatus.OK
    assert recovery.conflict_count == 1
    assert queue.entity_version(entity_key) == 2
    assert queue.processed_keys == frozenset({str(first["event_id"]), str(second["event_id"])})
    assert queue.conflicts[conflicted.conflict_id].state is ConflictState.RESOLVED
    replay = queue.resolve_take_remote(conflicted.conflict_id)
    assert replay.status is QueueStatus.DUPLICATE
    assert replay.reason is QueueReason.ALREADY_RESOLVED


def test_recovery_without_registered_handler_leaves_event_pending() -> None:
    queue = _queue()
    event = _event("SYN-EVT-000070", event_type="synthetic_unhandled")
    event_id = str(event["event_id"])
    queue.enqueue(event)
    queue.begin(event_id)
    queue.deliver(event_id, lambda evt: "SYN-OK")
    queue.simulate_crash()

    recovery = queue.recover()
    assert recovery.status is QueueStatus.OK
    assert recovery.redelivered == ()
    assert recovery.pending_redelivery == (event_id,)
    assert queue.event_state(event_id) is EventState.IN_FLIGHT
    assert queue.processed_key_count == 0


def test_log_never_contains_raw_payload_or_exception_text() -> None:
    queue = _queue(max_attempts=1, backoff=())
    event = _event("SYN-EVT-000080", payload={"secret_marker": "SYN-PII-MARKER-SHOULD-NOT-APPEAR"})
    event_id = str(event["event_id"])
    queue.enqueue(event)

    def failing(evt: QueueEvent) -> None:
        raise RuntimeError("SYN-RAW-ERROR-MARKER-SHOULD-NOT-APPEAR")

    queue.process(event_id, failing)
    raw = queue.log_bytes().decode("utf-8")
    assert "SYN-PII-MARKER-SHOULD-NOT-APPEAR" not in raw
    assert "SYN-RAW-ERROR-MARKER-SHOULD-NOT-APPEAR" not in raw
    assert len(queue.dead_letters[0].payload_digest) == 64


def test_config_backoff_and_scope_validation_are_deterministic() -> None:
    config = QueueConfig(
        tenant_id=TENANT,
        facility_id=FACILITY,
        max_attempts=4,
        backoff_delays_ms=(2, 4, 8),
    )
    assert tuple(config.delay_for(attempt) for attempt in range(1, 5)) == (2, 4, 8, 0)
    queue = DurableEventQueue(config)
    event = _event()
    queue.enqueue(event)
    assert replace(config).tenant_id == TENANT
    assert queue.verify_log().status is QueueStatus.OK
