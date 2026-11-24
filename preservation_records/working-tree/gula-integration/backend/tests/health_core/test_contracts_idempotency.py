"""Contract tests: idempotency key shape, replay semantics and conflict code."""

from __future__ import annotations

import pytest
from app.health_core.common import DuplicateEntityError, new_synthetic_id
from app.health_core.contracts.idempotency import (
    IDEMPOTENCY_CONFLICT_CODE,
    IDEMPOTENCY_CONFLICT_STATUS,
    IDEMPOTENCY_HEADER,
    IDEMPOTENCY_SEMANTICS,
    IDEMPOTENCY_TTL_SECONDS,
    IdempotencyScope,
    ReplaySemantics,
    new_idempotency_key,
    validate_idempotency_key,
)


def test_generated_key_is_synthetic_and_validates() -> None:
    key = new_idempotency_key()
    assert key.startswith("SYN-IDK-")
    assert validate_idempotency_key(key) == key


@pytest.mark.parametrize("bad_key", ["", "   ", "123456789012", "ABCD123456789", "IDK-0001", 42])
def test_invalid_keys_are_rejected(bad_key: object) -> None:
    with pytest.raises(ValueError):
        validate_idempotency_key(bad_key)


def test_header_and_ttl_match_national_conventions() -> None:
    assert IDEMPOTENCY_HEADER == "Idempotency-Key"
    assert IDEMPOTENCY_TTL_SECONDS == 86_400


def test_conflict_code_uses_shared_duplicate_error() -> None:
    assert DuplicateEntityError.code == IDEMPOTENCY_CONFLICT_CODE
    assert IDEMPOTENCY_CONFLICT_STATUS == DuplicateEntityError.status_code == 409


def test_replay_semantics_are_documented_for_every_outcome() -> None:
    assert set(IDEMPOTENCY_SEMANTICS) == set(ReplaySemantics)
    assert "stored response" in IDEMPOTENCY_SEMANTICS[ReplaySemantics.REPLAY_STORED_RESPONSE]
    assert IDEMPOTENCY_CONFLICT_CODE in IDEMPOTENCY_SEMANTICS[ReplaySemantics.CONFLICT]
    assert "process once" in IDEMPOTENCY_SEMANTICS[ReplaySemantics.CREATE_NEW]


def test_idempotency_scope_binds_key_to_tenant_and_operation() -> None:
    scope = IdempotencyScope(
        tenant_id=new_synthetic_id("LAB"),
        idempotency_key=new_idempotency_key(),
        operation="lab_result.create",
    )
    assert scope.tenant_id.startswith("SYN-")
    assert scope.idempotency_key.startswith("SYN-")
    assert scope.operation == "lab_result.create"


def test_scope_rejects_invalid_key() -> None:
    with pytest.raises(ValueError):
        IdempotencyScope(
            tenant_id=new_synthetic_id("LAB"),
            idempotency_key="123456789012",
            operation="lab_result.create",
        )


def test_scope_rejects_empty_operation() -> None:
    with pytest.raises(ValueError, match="operation"):
        IdempotencyScope(
            tenant_id=new_synthetic_id("LAB"),
            idempotency_key=new_idempotency_key(),
            operation="",
        )
