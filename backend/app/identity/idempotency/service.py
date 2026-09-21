"""Canonical NIAM idempotency mechanism -- one implementation reused by
every operation that needs it (`generate_api_key`, `issue_certificate`,
`rotate_certificate`, `rotate_api_key`), not four separate ones.

Reuses `CitizenRelationshipWorkflow`'s exact HMAC-SHA256 key/fingerprint
algorithm (`app/identity/services/citizen_relationship_service.py`), not
reimplemented differently. Concurrency is handled the same way real
PostgreSQL already handles it for that workflow: a unique index
(`operation`, `actor_account_id`, `key_hash`) plus a `SAVEPOINT` around
the claiming `INSERT` so a losing concurrent transaction recovers
gracefully (without aborting the whole request's transaction) and
re-reads the winner's already-committed result -- proven against real
concurrent PostgreSQL connections in this workstream's proof harness
before this module was written.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import uuid as uuid_module
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.config import AUDIT_ANCHOR_KEY
from app.identity.idempotency.models import NiamIdempotencyKey


class IdempotencyKeyInvalid(ValueError):
    """The client-supplied Idempotency-Key fails the length contract."""


class IdempotencyConflict(ValueError):
    """The same (operation, actor, key) was already claimed for a
    different request -- never a silent replay of the wrong result."""


@dataclass
class IdempotencyOutcome:
    replay: bool
    row: NiamIdempotencyKey


def _idempotency_hmac_key() -> bytes:
    key = os.getenv("GULA_CERT_IDEMPOTENCY_KEY") or AUDIT_ANCHOR_KEY
    if not key or len(key) < 32:
        raise RuntimeError(
            "GULA_CERT_IDEMPOTENCY_KEY or AUDIT_ANCHOR_KEY must be at least 32 characters"
        )
    return key.encode("utf-8")


def _digest(value: str) -> str:
    return hmac.new(_idempotency_hmac_key(), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _key_hash(raw_key: str) -> str:
    return _digest(f"idempotency:{raw_key}")


def _fingerprint(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return _digest(f"request:{serialized}")


class IdempotencyService:
    """One canonical durable mechanism. `begin_or_replay()` either
    returns a completed prior result (safe replay -- perform no
    mutation) or a fresh, claimed `pending` row (the caller must perform
    the business mutation, then call `complete()`). Everything happens
    within the caller's existing session/transaction -- no separate
    commit here, matching this codebase's established route-commits-once
    convention: the idempotency claim, the business mutation, and
    marking the claim completed all land in the SAME transaction the
    route commits once at the end."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def begin_or_replay(
        self,
        operation: str,
        actor_account_id: str,
        raw_key: str,
        payload: dict[str, Any],
        ttl_hours: int = 24,
    ) -> IdempotencyOutcome:
        if not (16 <= len(raw_key) <= 128):
            raise IdempotencyKeyInvalid("Idempotency-Key must be 16 to 128 characters")

        kh = _key_hash(raw_key)
        fp = _fingerprint(payload)

        existing = await self._find(operation, actor_account_id, kh)
        if existing is not None:
            return self._resolve_existing(existing, fp)

        new_row = NiamIdempotencyKey(
            uuid=str(uuid_module.uuid4()),
            operation=operation,
            actor_account_id=actor_account_id,
            key_hash=kh,
            request_fingerprint=fp,
            status="pending",
            expires_at=datetime.now(UTC) + timedelta(hours=ttl_hours),
        )
        self.session.add(new_row)
        try:
            async with self.session.begin_nested():
                await self.session.flush()
        except IntegrityError:
            # Lost the race: a concurrent transaction claimed the same
            # (operation, actor_account_id, key_hash) first and has
            # already committed (Postgres serializes concurrent inserts
            # on a unique index -- this INSERT blocked until the winner's
            # transaction ended, then failed with exactly this error).
            # The SAVEPOINT rollback above recovers this request's own
            # transaction without aborting it; re-read the winner.
            self.session.expunge(new_row)
            winner = await self._find(operation, actor_account_id, kh)
            if winner is None or winner.status != "completed":
                raise RuntimeError(
                    "idempotency unique violation but no completed winner row found "
                    "-- violates the commit-once invariant this mechanism depends on",
                ) from None
            return self._resolve_existing(winner, fp)

        return IdempotencyOutcome(replay=False, row=new_row)

    async def complete(self, row: NiamIdempotencyKey, result_type: str, result_id: str) -> None:
        row.status = "completed"
        row.result_type = result_type
        row.result_id = result_id
        await self.session.flush()

    async def _find(self, operation: str, actor_account_id: str, key_hash: str) -> NiamIdempotencyKey | None:
        stmt = select(NiamIdempotencyKey).where(
            NiamIdempotencyKey.operation == operation,
            NiamIdempotencyKey.actor_account_id == actor_account_id,
            NiamIdempotencyKey.key_hash == key_hash,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _resolve_existing(row: NiamIdempotencyKey, fingerprint: str) -> IdempotencyOutcome:
        if row.request_fingerprint != fingerprint:
            raise IdempotencyConflict("Idempotency-Key was reused for a different request")
        if row.status == "completed":
            return IdempotencyOutcome(replay=True, row=row)
        # status == "pending" from a still-in-flight concurrent request
        # that hasn't committed yet is unreachable under commit-once
        # (nothing is visible to another transaction before it commits,
        # and by then it is "completed") -- surfaced loudly rather than
        # silently treated as a replay of an incomplete result.
        raise RuntimeError(
            f"idempotency row found in unexpected status {row.status!r} -- "
            "violates the commit-once invariant this mechanism depends on",
        )
