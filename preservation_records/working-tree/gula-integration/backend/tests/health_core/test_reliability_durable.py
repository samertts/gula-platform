"""WAL semantics, atomic snapshots and simulated-restart recovery tests."""

from __future__ import annotations

import json

import pytest
from app.health_core.common.errors import InvalidSyntheticReferenceError
from app.health_core.reliability import (
    ChecksumMismatchError,
    InMemoryWALStore,
    InvalidStoreValueError,
    canonical_json_bytes,
    decode_checked_envelope,
    sealed_envelope,
)


def _store_with_three_writes() -> InMemoryWALStore:
    store = InMemoryWALStore()
    for index in range(1, 4):
        store.put(f"SYN-EVT-{index:06d}", {"sequence": index})
    return store


def test_wal_writes_visible_before_commit_and_recovered_by_simulated_restart() -> None:
    store = _store_with_three_writes()
    assert len(store.get("SYN-EVT-000001") or {}) == 1
    assert store.committed_data == {}
    assert store.wal_bytes()
    assert store.snapshot_bytes() == InMemoryWALStore().snapshot_bytes()

    recovered = store.simulate_restart()
    assert recovered.data == store.data
    assert set(recovered.data) == {"SYN-EVT-000001", "SYN-EVT-000002", "SYN-EVT-000003"}
    assert recovered.get("SYN-EVT-000003") == {"sequence": 3}


def test_commit_is_atomic_snapshot_and_clears_wal() -> None:
    store = _store_with_three_writes()
    snapshot = store.commit()
    assert snapshot == store.snapshot_bytes()
    assert store.wal_bytes() == b""
    assert store.committed_data == store.data
    restored = InMemoryWALStore.restore_from(snapshot)
    assert restored.data == store.data


def test_restore_from_snapshot_and_wal_replays_uncommitted_tail() -> None:
    store = InMemoryWALStore()
    store.put("SYN-EVT-000001", {"phase": "committed"})
    snapshot = store.commit()
    store.put("SYN-EVT-000002", {"phase": "uncommitted"})
    combined = InMemoryWALStore.restore_from(snapshot, store.wal_bytes())
    assert combined.data == {
        "SYN-EVT-000001": {"phase": "committed"},
        "SYN-EVT-000002": {"phase": "uncommitted"},
    }
    assert combined.sequence == 2
    assert combined.simulate_restart().data == combined.data


def test_delete_is_logged_and_recovered_after_restart() -> None:
    store = InMemoryWALStore()
    store.put("SYN-EVT-000001", {"v": 1})
    store.put("SYN-EVT-000002", {"v": 2})
    store.commit()
    store.delete("SYN-EVT-000001")
    recovered = store.simulate_restart()
    assert "SYN-EVT-000001" not in recovered.data
    assert recovered.data == {"SYN-EVT-000002": {"v": 2}}


def test_sequence_advances_across_restarts() -> None:
    store = InMemoryWALStore()
    store.put("SYN-EVT-000001", {"n": 1})
    store.commit()
    restarted = store.simulate_restart()
    restarted.put("SYN-EVT-000002", {"n": 2})
    restarted.commit()
    envelope = decode_checked_envelope(
        restarted.snapshot_bytes(), schema="gula-reliability-snapshot-v1", label="snapshot"
    )
    assert envelope["sequence"] == 2


def test_corrupted_snapshot_is_rejected() -> None:
    store = _store_with_three_writes()
    store.commit()
    corrupted = store.snapshot_bytes().replace(b"gula-reliability", b"gula-reliabilitY", 1)
    assert corrupted != store.snapshot_bytes()
    with pytest.raises(ChecksumMismatchError) as exc:
        InMemoryWALStore().restore(corrupted)
    assert exc.value.to_dict()["code"] == "CHECKSUM_MISMATCH"


def test_corrupted_wal_bytes_are_rejected() -> None:
    store = InMemoryWALStore()
    store.put("SYN-EVT-000001", {"v": 1})
    wal = store.wal_bytes()
    parsed = json.loads(wal)
    parsed["records"][0]["value"]["v"] = 2
    tampered = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    with pytest.raises(ChecksumMismatchError):
        InMemoryWALStore.restore_from(store.snapshot_bytes(), tampered)


def test_returned_values_are_defensive_copies() -> None:
    store = InMemoryWALStore()
    store.put("SYN-EVT-000001", {"nested": {"v": 1}})
    value = store.get("SYN-EVT-000001")
    assert value is not None
    value["nested"] = {"v": 99}  # type: ignore[assignment]
    snapshot = store.data
    snapshot.clear()
    assert store.get("SYN-EVT-000001") == {"nested": {"v": 1}}


def test_invalid_keys_and_values_are_rejected() -> None:
    store = InMemoryWALStore()
    with pytest.raises(InvalidSyntheticReferenceError):
        store.put("", {"v": 1})
    with pytest.raises(InvalidStoreValueError):
        store.put("SYN-EVT-000001", {"v": object()})  # type: ignore[dict-item]
    with pytest.raises(InvalidStoreValueError):
        store.delete("SYN-EVT-999999")


def test_non_synthetic_store_key_is_rejected() -> None:
    store = InMemoryWALStore()
    with pytest.raises(InvalidSyntheticReferenceError) as exc:
        store.put("12345678901", {"v": 1})
    assert exc.value.to_dict()["code"] == "INVALID_SYNTHETIC_REFERENCE"
    assert exc.value.to_dict()["details"] == {"field": "key"}
    assert store.data == {}
    store.put("SYN-KEY-0001", {"v": 1})
    assert store.get("SYN-KEY-0001") == {"v": 1}


def test_wal_carries_authoritative_terminal_anchors() -> None:
    store = _store_with_three_writes()
    envelope = decode_checked_envelope(
        store.wal_bytes(), schema="gula-reliability-wal-v1", label="wal"
    )
    assert envelope["base_sequence"] == 0
    assert envelope["record_count"] == 3
    assert envelope["last_sequence"] == 3
    assert len(envelope["records"]) == 3


def test_wal_tail_truncation_with_recomputed_checksum_is_rejected() -> None:
    store = _store_with_three_writes()
    snapshot = store.snapshot_bytes()
    wal = store.wal_bytes()
    parsed = json.loads(wal)
    parsed.pop("checksum")
    parsed["records"] = parsed["records"][:-1]
    tampered = canonical_json_bytes(sealed_envelope(parsed))
    assert tampered != wal

    with pytest.raises(ChecksumMismatchError) as exc:
        InMemoryWALStore.restore_from(snapshot, tampered)
    assert exc.value.to_dict()["code"] == "CHECKSUM_MISMATCH"
    assert "record count" in exc.value.to_dict()["message"]

    # The untouched WAL is still a legitimate, fully recoverable restart.
    recovered = InMemoryWALStore.restore_from(snapshot, wal)
    assert set(recovered.data) == {"SYN-EVT-000001", "SYN-EVT-000002", "SYN-EVT-000003"}
    assert recovered.get("SYN-EVT-000003") == {"sequence": 3}
    assert recovered.sequence == 3


def test_wal_middle_record_drop_is_rejected() -> None:
    store = _store_with_three_writes()
    wal = store.wal_bytes()
    parsed = json.loads(wal)
    parsed.pop("checksum")
    del parsed["records"][1]
    tampered = canonical_json_bytes(sealed_envelope(parsed))
    with pytest.raises(ChecksumMismatchError) as exc:
        InMemoryWALStore.restore_from(store.snapshot_bytes(), tampered)
    assert exc.value.to_dict()["code"] == "CHECKSUM_MISMATCH"


def test_wal_with_missing_or_stale_terminal_anchors_is_rejected() -> None:
    store = _store_with_three_writes()
    snapshot = store.snapshot_bytes()
    wal = store.wal_bytes()

    no_anchor = json.loads(wal)
    no_anchor.pop("checksum")
    no_anchor.pop("record_count")
    with pytest.raises(ChecksumMismatchError) as missing:
        InMemoryWALStore.restore_from(snapshot, canonical_json_bytes(sealed_envelope(no_anchor)))
    assert "terminal anchors" in missing.value.to_dict()["message"]

    stale_last = json.loads(wal)
    stale_last.pop("checksum")
    stale_last["last_sequence"] = 2
    with pytest.raises(ChecksumMismatchError) as stale:
        InMemoryWALStore.restore_from(snapshot, canonical_json_bytes(sealed_envelope(stale_last)))
    assert "last sequence" in stale.value.to_dict()["message"]
