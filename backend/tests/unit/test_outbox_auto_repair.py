"""Tests for the outbox backlog auto-repair action (PROGRAM-011 WARN burn-down).

Covers:
    - Dynamic poll interval in app/services/outbox_service.py
    - RepairEngine._repair_outbox_backlog (speeds up poll on backlog spike)
    - RepairEngine._normalize_outbox_poll (restores default once cleared)
    - Policy gating via guard_repair
"""

from unittest.mock import patch

from app.core.auto_repair import _QUEUE_CRITICAL, _QUEUE_WARN, RepairAction, RepairEngine
from app.services import outbox_service


def _engine() -> RepairEngine:
    engine = RepairEngine()
    engine._register(RepairAction("outbox_poll", "x", "warn", cooldown_s=60))
    return engine


# ─── outbox_service dynamic poll interval ─────────────────────────────────────


def test_default_poll_interval_is_10s():
    assert outbox_service.get_poll_interval() == outbox_service._POLL_SECS


def test_set_poll_interval_lowers():
    outbox_service.set_poll_interval(2)
    assert outbox_service.get_poll_interval() == 2
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


def test_set_poll_interval_clamps_to_minimum_1s():
    outbox_service.set_poll_interval(0)
    assert outbox_service.get_poll_interval() == 1
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


def test_set_poll_interval_restores_default():
    outbox_service.set_poll_interval(2)
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)
    assert outbox_service.get_poll_interval() == outbox_service._POLL_SECS


# ─── RepairEngine: backlog spike → speed up ───────────────────────────────────


def test_backlog_spike_speeds_up_poll(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", outbox_service._POLL_SECS)

    with patch("app.core.auto_repair._guard_repair", return_value=True):
        ok = engine._repair_outbox_backlog(_QUEUE_CRITICAL + 1)

    assert ok
    assert outbox_service.get_poll_interval() == 2
    assert engine._repair_log[-1]["success"] is True
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


def test_backlog_repair_is_idempotent(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", 2)

    with patch("app.core.auto_repair._guard_repair", return_value=True):
        ok = engine._repair_outbox_backlog(_QUEUE_CRITICAL + 1)

    assert ok
    assert outbox_service.get_poll_interval() == 2
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


def test_backlog_repair_respects_policy(monkeypatch):
    engine = _engine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", outbox_service._POLL_SECS)

    with patch("app.core.auto_repair._guard_repair", return_value=False):
        ok = engine._repair_outbox_backlog(_QUEUE_CRITICAL + 1)

    assert ok is False
    assert outbox_service.get_poll_interval() == outbox_service._POLL_SECS


def test_backlog_repair_records_failure_on_exception(monkeypatch):
    engine = _engine()

    with patch("app.core.auto_repair._guard_repair", return_value=True), patch(
        "app.services.outbox_service.set_poll_interval", side_effect=RuntimeError("boom"),
    ):
        ok = engine._repair_outbox_backlog(999)

    assert ok is False
    assert engine._repair_log[-1]["success"] is False
    assert "boom" in engine._repair_log[-1]["details"]


# ─── RepairEngine: normalize back to default ──────────────────────────────────


def test_normalize_restores_default_when_queue_cleared(monkeypatch):
    engine = RepairEngine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", 2)

    with patch("app.core.auto_repair._guard_repair", return_value=True):
        engine._normalize_outbox_poll(0)

    assert outbox_service.get_poll_interval() == outbox_service._POLL_SECS
    assert engine._repair_log[-1]["action"] == "outbox_poll"
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


def test_normalize_keeps_default_interval_when_queue_cleared(monkeypatch):
    engine = RepairEngine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", outbox_service._POLL_SECS)

    with patch("app.core.auto_repair._guard_repair", return_value=True):
        engine._normalize_outbox_poll(0)

    assert outbox_service.get_poll_interval() == outbox_service._POLL_SECS
    assert engine._repair_log == []  # nothing recorded — no change needed


def test_normalize_keeps_fast_poll_while_backlog_persists(monkeypatch):
    engine = RepairEngine()
    monkeypatch.setattr(outbox_service, "_poll_interval_s", 2)

    engine._normalize_outbox_poll(_QUEUE_WARN + 5)

    assert outbox_service.get_poll_interval() == 2
    assert engine._repair_log == []
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)


# ─── Main check cycle wiring ──────────────────────────────────────────────────


async def test_check_and_repair_triggers_outbox_action():
    engine = _engine()

    def fake_rss():
        return 100.0

    def fake_db():
        return 10.0

    def fake_redis():
        return 1.0

    def fake_queue():
        return _QUEUE_CRITICAL + 10

    with patch("app.core.auto_repair._guard_repair", return_value=True), \
            patch.object(engine, "_rss_mb", fake_rss), \
            patch.object(engine, "_db_latency_ms", fake_db), \
            patch.object(engine, "_redis_latency_ms", fake_redis), \
            patch.object(engine, "_queue_depth", fake_queue), \
            patch.object(engine, "_normalize_outbox_poll") as mock_normalize:
        await engine._check_and_repair()

    assert engine.stats()["outbox_poll"]["triggered"] == 1
    mock_normalize.assert_not_called()
    assert outbox_service.get_poll_interval() == 2
    outbox_service.set_poll_interval(outbox_service._POLL_SECS)
