"""Regression guard for the public_health outbreak-alert concurrency fix.

update_alert_status previously accepted any client-supplied string with no
enum validation, no row lock, and no terminal-state guard -- the same
TOCTOU shape already fixed this session in payments, devices, biomedical,
and command_center. Proven separately against a real disposable
PostgreSQL 16 database that two concurrent transitions to "declared_over"
on the same outbreak alert both succeeded pre-fix. SQLite (this suite's
default) cannot reproduce the race itself, so this test pins the
guarantees that make the guard real.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.national.base import NationalBase
from app.public_health.application.service import PublicHealthService
from app.public_health.exceptions import (
    InvalidOutbreakStatusError,
    OutbreakAlreadyDeclaredOverError,
)
from app.public_health.infrastructure.models import OutbreakAlertModel

LAB_ID = 3131


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    NationalBase.metadata.create_all(engine, tables=[OutbreakAlertModel.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed(db) -> str:
    now = datetime.now(timezone.utc)
    alert = OutbreakAlertModel(lab_id=LAB_ID, disease="measles", region="Erbil", status="investigating", first_detected=now)
    db.add(alert)
    db.commit()
    return alert.id


def test_invalid_status_is_rejected(db):
    alert_id = _seed(db)
    service = PublicHealthService(db)
    with pytest.raises(InvalidOutbreakStatusError):
        service.update_alert_status(alert_id, "not_a_real_status")


def test_transition_locks_and_increments_version(db):
    alert_id = _seed(db)
    service = PublicHealthService(db)
    updated = service.update_alert_status(alert_id, "confirmed", notes="lab confirmed")
    assert updated.id == alert_id

    refreshed = db.query(OutbreakAlertModel).filter_by(id=alert_id).one()
    assert refreshed.status == "confirmed"
    assert refreshed.version == 2


def test_declared_over_is_terminal_and_rejects_further_transitions(db):
    alert_id = _seed(db)
    service = PublicHealthService(db)
    service.update_alert_status(alert_id, "declared_over", notes="outbreak resolved")

    with pytest.raises(OutbreakAlreadyDeclaredOverError):
        service.update_alert_status(alert_id, "monitoring", notes="reopening attempt")

    refreshed = db.query(OutbreakAlertModel).filter_by(id=alert_id).one()
    assert refreshed.status == "declared_over"
    assert refreshed.investigation_notes.count("outbreak resolved") == 1
    assert "reopening attempt" not in refreshed.investigation_notes


def test_update_alert_status_query_is_row_locked(db, monkeypatch):
    from sqlalchemy.orm import Query as SAQuery

    alert_id = _seed(db)
    calls = []
    original = SAQuery.with_for_update

    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(SAQuery, "with_for_update", spy)

    service = PublicHealthService(db)
    service.update_alert_status(alert_id, "confirmed")

    assert calls, "update_alert_status must call Query.with_for_update()"
