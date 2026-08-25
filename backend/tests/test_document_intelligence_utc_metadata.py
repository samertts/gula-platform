from __future__ import annotations

from datetime import UTC, datetime

import pytest
from app.document_intelligence.observability import AlertManager, HealthChecker
from app.document_intelligence.security import AuditLogger, IntegrityChecker


def _assert_utc_iso8601(value: str) -> None:
    assert datetime.fromisoformat(value).tzinfo == UTC


@pytest.mark.asyncio
async def test_observability_metadata_uses_aware_utc_timestamps() -> None:
    checker = HealthChecker()

    async def healthy_check() -> dict[str, bool]:
        return {"ok": True}

    checker.register("synthetic", healthy_check)
    health = await checker.run_all()
    _assert_utc_iso8601(health["timestamp"])

    alerts = AlertManager()

    async def always_trigger(_: dict[str, object]) -> bool:
        return True

    alerts.add_rule("synthetic", always_trigger)
    triggered = await alerts.evaluate({})
    _assert_utc_iso8601(triggered[0]["timestamp"])


@pytest.mark.asyncio
async def test_security_metadata_uses_aware_utc_timestamps_and_keeps_integrity() -> None:
    audit = AuditLogger()
    entry = await audit.log("read", "document", "synthetic-id", "synthetic-actor")
    _assert_utc_iso8601(entry["timestamp"])

    integrity = IntegrityChecker()
    record = await integrity.add_entry({"event": "synthetic"})
    _assert_utc_iso8601(record["timestamp"])
    assert integrity.verify_chain()
