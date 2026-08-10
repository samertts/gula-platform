"""A5 — Audit chain integrity verification for the identity hash-chained log.

Verification is read-only: it recomputes hashes and reports anomalies but never
rewrites or repairs entries. Tests cover intact chains, tampered hashes, broken
previous-hash links, unhashed gaps after the chain started (and legacy unhashed
entries before it), empty chains, and the report surface.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app._compat import UTC
from app.identity.models.audit import IdentityAuditEntry
from app.identity.services.audit_service import AuditService

START = datetime(2026, 8, 10, 12, 0, 0, tzinfo=UTC)


def _make_entry(
    service: AuditService,
    *,
    index: int,
    previous_hash: str | None,
    occurred_at: datetime,
    action: str = "login_succeeded",
    actor_id: str = "actor-1",
    target_type: str = "account",
    target_id: str = "acct-1",
    organization_id: str | None = None,
    outcome: str = "success",
) -> IdentityAuditEntry:
    entry = IdentityAuditEntry(
        id=f"ENTRY{index:06d}",
        uuid=f"00000000-0000-0000-0000-{index:012d}",
        action=action,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        occurred_at=occurred_at,
        outcome=outcome,
        organization_id=organization_id,
        previous_hash=previous_hash,
    )
    entry.entry_hash = service._compute_hash(
        entry_id=entry.id,
        uuid_str=entry.uuid,
        action=entry.action,
        actor_id=entry.actor_id,
        target_type=entry.target_type,
        target_id=entry.target_id,
        occurred_at=entry.occurred_at.isoformat(),
        outcome=entry.outcome,
        previous_hash=previous_hash,
        organization_id=organization_id,
    )
    return entry


def _build_chain(service: AuditService, count: int = 3) -> list[IdentityAuditEntry]:
    entries: list[IdentityAuditEntry] = []
    previous = None
    for i in range(count):
        entry = _make_entry(
            service,
            index=i + 1,
            previous_hash=previous,
            occurred_at=START + timedelta(seconds=i),
        )
        entries.append(entry)
        previous = entry.entry_hash
    return entries


def _service() -> AuditService:
    return AuditService(MagicMock())


class TestChainIntegrity:
    async def test_intact_chain_has_no_violations(self):
        service = _service()
        chain = _build_chain(service)
        assert await service.verify_chain_integrity(entries=chain) == []

    async def test_intact_chain_report_ok(self):
        service = _service()
        chain = _build_chain(service)
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: chain)))
        )
        report = await AuditService(session).verify_chain_report()
        assert report["total_entries"] == 3
        assert report["hashed_entries"] == 3
        assert report["unhashed_entries"] == 0
        assert report["anomalies"] == 0
        assert report["integrity_ok"] is True

    async def test_tampered_hash_detected(self):
        service = _service()
        chain = _build_chain(service)
        chain[1].entry_hash = "0" * 64
        violations = await service.verify_chain_integrity(entries=chain)
        assert any(v["reason"] == "hash_mismatch" and v["id"] == chain[1].id for v in violations)
        # A broken link also cascades to the next entry's previous-hash check.
        assert any(v["reason"] == "previous_hash_mismatch" for v in violations)

    async def test_broken_previous_link_detected(self):
        service = _service()
        chain = _build_chain(service)
        chain[2].previous_hash = "1" * 64
        violations = await service.verify_chain_integrity(entries=chain)
        assert any(
            v["reason"] == "previous_hash_mismatch" and v["id"] == chain[2].id for v in violations
        )

    async def test_verification_never_rewrites(self):
        service = _service()
        chain = _build_chain(service)
        snapshot = [(e.id, e.entry_hash, e.previous_hash) for e in chain]
        await service.verify_chain_integrity(entries=chain)
        assert [(e.id, e.entry_hash, e.previous_hash) for e in chain] == snapshot


class TestReportAnomalies:
    async def test_unhashed_entry_after_chain_start_flagged(self):
        service = _service()
        chain = _build_chain(service, count=2)
        gap = IdentityAuditEntry(
            id="GAP000001",
            uuid="00000000-0000-0000-0000-100000000000",
            action="legacy",
            occurred_at=START + timedelta(seconds=5),
            outcome="success",
            previous_hash=None,
            entry_hash=None,
        )
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=lambda: [chain[0], gap, chain[1]]))
            )
        )
        report = await AuditService(session).verify_chain_report()
        assert report["unhashed_entries"] == 1
        assert any(
            a["reason"] == "unhashed_entry_after_chain_start" for a in report["unhashed_anomalies"]
        )
        assert report["anomalies"] == 1
        assert report["integrity_ok"] is False

    async def test_legacy_unhashed_before_chain_not_flagged(self):
        service = _service()
        chain = _build_chain(service, count=1)
        legacy = IdentityAuditEntry(
            id="LEG000001",
            uuid="00000000-0000-0000-0000-200000000000",
            action="legacy",
            occurred_at=START - timedelta(days=1),
            outcome="success",
            previous_hash=None,
            entry_hash=None,
        )
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(
                scalars=MagicMock(return_value=MagicMock(all=lambda: [legacy, chain[0]]))
            )
        )
        report = await AuditService(session).verify_chain_report()
        assert report["unhashed_entries"] == 1
        assert report["unhashed_anomalies"] == []
        assert report["integrity_ok"] is True

    async def test_empty_chain_report(self):
        session = MagicMock()
        session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=list)))
        )
        report = await AuditService(session).verify_chain_report()
        assert report["total_entries"] == 0
        assert report["anomalies"] == 0
        assert report["integrity_ok"] is True

    async def test_verify_chain_integrity_queries_when_entries_not_given(self):
        service = _service()
        chain = _build_chain(service, count=2)
        service.session.execute = AsyncMock(
            return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=lambda: chain)))
        )
        violations = await service.verify_chain_integrity()
        assert violations == []
        service.session.execute.assert_awaited_once()
