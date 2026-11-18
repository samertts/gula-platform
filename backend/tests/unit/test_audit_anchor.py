"""Tests for the self-contained, file-backed audit-anchor engine.

All tenants, actors, keys and payloads are synthetic. The tested chain is a
local engineering building block, not an external notary.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from app.health_core.audit_anchor import (
    REDACTED,
    AuditChainError,
    RotatingKeyProvider,
    append,
    open_store,
    record_authorization_failure,
    redact,
    verify_chain,
)

TENANT_A = "SYN-TENANT-A"
TENANT_B = "SYN-TENANT-B"
ACTOR = "SYN-ACTOR-1"
SEED = "SYNTHETIC-TEST-SEED-NOT-A-CREDENTIAL"


def _provider() -> RotatingKeyProvider:
    return RotatingKeyProvider(seed=SEED)


def _append_entries(store: Any, provider: RotatingKeyProvider, count: int) -> None:
    for index in range(1, count + 1):
        append(
            store,
            provider,
            tenant_id=TENANT_A,
            actor=f"SYN-ACTOR-{index:02d}",
            action="SYN_ACTION_PERFORMED",
            payload={"index": index, "note": "synthetic"},
        )


def _write_records(store: Any, records: list[dict[str, Any]]) -> None:
    store.path.write_text(
        "".join(
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )


def _records(store: Any) -> list[dict[str, Any]]:
    return [json.loads(line) for line in store.path.read_text(encoding="utf-8").splitlines()]


def test_append_five_entries_and_verify_after_reopen(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 5)

    assert len(store.read_all()) == 5
    first = verify_chain(store, provider, tenant_id=TENANT_A)
    assert first.ok is True
    assert first.total == 5
    assert first.first_bad_seq is None
    assert first.reason is None

    reopened = open_store(store.path)
    assert reopened.path == store.path
    assert len(reopened.read_all()) == 5
    second = verify_chain(reopened, provider, tenant_id=TENANT_A)
    assert second.ok is True
    assert second.total == 5
    assert second.first_bad_seq is None
    assert second.reason is None


def test_payload_tampering_fails_at_exact_seq(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 5)

    records = _records(store)
    records[2]["payload"]["note"] = "tampered"
    _write_records(store, records)

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    assert report.total == 5
    assert report.first_bad_seq == 3
    assert report.reason == "payload_tampered"


def test_deleted_entry_fails_chain(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 5)

    records = _records(store)
    del records[2]
    _write_records(store, records)

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    assert report.total == 4
    assert report.first_bad_seq == 4
    assert report.reason == "sequence_gap"


def test_reordered_entries_fail_chain(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 5)

    records = _records(store)
    records[1], records[2] = records[2], records[1]
    _write_records(store, records)

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    # Position 2 now holds the original seq 3 record, which is the first bad record.
    assert report.first_bad_seq == 3
    assert report.reason == "sequence_gap"


def test_forged_signature_fails(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 4)

    records = _records(store)
    records[2]["signature"] = "0" * 64
    _write_records(store, records)

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    assert report.first_bad_seq == 3
    assert report.reason == "invalid_signature"


def test_unknown_key_id_fails(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 4)

    records = _records(store)
    unknown_id = "synthetic-key-9999"
    assert provider.has_key(unknown_id) is False
    records[2]["key_id"] = unknown_id
    _write_records(store, records)

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    assert report.first_bad_seq == 3
    assert report.reason == "unknown_key_id"


def test_key_rotation_preserves_historical_and_new_entries(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 3)
    old_key_id = provider.current_key_id()

    new_key_id = provider.rotate()
    assert new_key_id != old_key_id
    assert provider.has_key(old_key_id) is True
    assert provider.current_key_id() == new_key_id

    for index in range(4, 7):
        append(
            store,
            provider,
            tenant_id=TENANT_A,
            actor=f"SYN-ACTOR-{index:02d}",
            action="SYN_ACTION_PERFORMED",
            payload={"index": index},
        )

    records = store.read_all()
    assert [record["key_id"] for record in records] == [old_key_id] * 3 + [new_key_id] * 3
    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is True
    assert report.total == 6
    assert report.first_bad_seq is None
    assert report.reason is None


def test_cross_tenant_contamination_is_rejected(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 3)

    records = _records(store)
    records[1]["tenant_id"] = TENANT_B
    _write_records(store, records)
    reopened = open_store(store.path)

    for requested_tenant in (TENANT_A, TENANT_B, None):
        report = verify_chain(reopened, provider, tenant_id=requested_tenant)
        assert report.ok is False
        assert report.total == 3
        assert report.reason == "cross_tenant_contamination"
        assert report.first_bad_seq == (2 if requested_tenant != TENANT_B else 1)


def test_authorization_failure_is_always_recorded(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 1)

    def deny() -> bool:
        return False

    record_authorization_failure(
        store,
        provider,
        tenant_id=TENANT_A,
        actor=ACTOR,
        action="SYN_LAB_RESULT_VIEW",
        reason="rbac_denied",
        detail={"resource": "SYN-RESULT-1"},
        authorization_check=deny,
    )

    entries = store.read_all()
    assert len(entries) == 2
    failure = entries[-1]
    assert failure["action"] == "authorization_failure"
    assert failure["tenant_id"] == TENANT_A
    assert failure["payload"]["outcome"] == "denied"
    assert failure["payload"]["reason"] == "rbac_denied"
    assert failure["payload"]["requested_action"] == "SYN_LAB_RESULT_VIEW"
    assert verify_chain(open_store(store.path), provider, tenant_id=TENANT_A).ok is True


def test_authorization_check_exception_is_still_recorded(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    secret_context = "SYN-EXCEPTION-CONTEXT-MUST-NOT-BE-STORED"

    def broken_check() -> bool:
        raise RuntimeError(secret_context)

    record_authorization_failure(
        store,
        provider,
        tenant_id=TENANT_A,
        actor=ACTOR,
        action="SYN_ACTION_VIEW",
        reason="rbac_denied",
        authorization_check=broken_check,
    )

    entries = store.read_all()
    assert len(entries) == 1
    assert entries[0]["payload"]["outcome"] == "error"
    assert entries[0]["payload"]["reason"] == "authorization_check_error"
    assert secret_context not in store.path.read_text(encoding="utf-8")
    assert verify_chain(store, provider, tenant_id=TENANT_A).ok is True


def test_redaction_removes_sensitive_fields_before_append(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    secret = "SYN-SUPER-SECRET-VALUE-12345"
    payload = {
        "username": "syn-user",
        "password": secret,
        "access_token": secret,
        "nested": {"api_key": secret, "safe_field": "kept"},
        "items": [{"client_secret": secret, "label": "kept"}],
    }

    redacted = redact(payload, extra_sensitive_keys=("username",))
    assert redacted["password"] == REDACTED
    assert redacted["access_token"] == REDACTED
    assert redacted["nested"]["api_key"] == REDACTED
    assert redacted["items"][0]["client_secret"] == REDACTED
    assert redacted["username"] == REDACTED
    assert redacted["nested"]["safe_field"] == "kept"
    assert secret not in json.dumps(redacted)

    append(
        store,
        provider,
        tenant_id=TENANT_A,
        actor=ACTOR,
        action="SYN_ACTION_PERFORMED",
        payload=payload,
    )
    stored_text = store.path.read_text(encoding="utf-8")
    assert secret not in stored_text
    assert store.read_all()[0]["payload"]["nested"]["safe_field"] == "kept"
    assert verify_chain(open_store(store.path), provider, tenant_id=TENANT_A).ok is True


def test_duplicate_seq_detected(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 2)

    line = store.path.read_text(encoding="utf-8").splitlines()[0]
    store.path.write_text(line + "\n" + line + "\n", encoding="utf-8")

    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)
    assert report.ok is False
    assert report.total == 2
    assert report.first_bad_seq == 1
    assert report.reason == "duplicate_seq"


def test_append_fails_closed_on_invalid_tail(tmp_path: Path) -> None:
    provider = _provider()
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 3)

    records = _records(store)
    records[-1]["payload"]["index"] = 999
    _write_records(store, records)
    before = store.path.read_text(encoding="utf-8")

    with pytest.raises(AuditChainError) as exc_info:
        append(
            store,
            provider,
            tenant_id=TENANT_A,
            actor=ACTOR,
            action="SYN_ACTION_PERFORMED",
            payload={"index": 4},
        )
    assert "payload_tampered" in str(exc_info.value)
    assert "seq 3" in str(exc_info.value)
    assert store.path.read_text(encoding="utf-8") == before
    assert len(store.read_all()) == 3


def test_reports_and_provider_repr_expose_no_secret_material(tmp_path: Path) -> None:
    provider = RotatingKeyProvider(seed="SYN-SEED-MATERIAL-MUST-NOT-LEAK")
    store = open_store(tmp_path / "audit.jsonl")
    _append_entries(store, provider, 2)

    assert "SYN-SEED-MATERIAL-MUST-NOT-LEAK" not in repr(provider)
    assert provider.current_key_id() in repr(provider)

    records = _records(store)
    signature = records[0]["signature"]
    records[0]["signature"] = "f" * 64
    _write_records(store, records)
    report = verify_chain(open_store(store.path), provider, tenant_id=TENANT_A)

    assert report.reason == "invalid_signature"
    assert signature not in repr(report)
    assert signature not in store.path.read_text(encoding="utf-8")
