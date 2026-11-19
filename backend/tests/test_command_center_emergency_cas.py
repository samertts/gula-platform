"""Regression guard for the command_center concurrency fix.

resolve_emergency and fulfill_resource previously read a row with a plain
unlocked SELECT before mutating it, despite both models already inheriting
OptimisticLockMixin (version column present, unused) -- the same TOCTOU
shape already fixed this session in payments, devices, and biomedical.
Proven separately against a real disposable PostgreSQL 16 database that
two concurrent resolve_emergency calls on the same emergency both
succeeded pre-fix, appending duplicate "[RESOLVED]" notes and never
incrementing version. SQLite (this suite's default) cannot reproduce the
race itself, so this test pins the two guarantees that make the guard
real: a locked query is issued, and a second transition attempt is
rejected rather than silently re-applied.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.command_center.application.service import CommandCenterService
from app.command_center.exceptions import (
    EmergencyAlreadyResolvedError,
    ResourceRequestAlreadyFulfilledError,
)
from app.command_center.infrastructure.models import EmergencyDeclarationModel, ResourceRequestModel
from app.national.base import NationalBase

LAB_ID = 5151


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    NationalBase.metadata.create_all(engine, tables=[EmergencyDeclarationModel.__table__, ResourceRequestModel.__table__])
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _seed_emergency(db) -> str:
    now = datetime.now(timezone.utc)
    emergency = EmergencyDeclarationModel(
        lab_id=LAB_ID, emergency_type="flood", status="active",
        region="Basra", declared_at=now, declared_by="dispatcher",
    )
    db.add(emergency)
    db.commit()
    return emergency.id


def _seed_resource(db, emergency_id: str) -> str:
    now = datetime.now(timezone.utc)
    resource = ResourceRequestModel(
        lab_id=LAB_ID, emergency_id=emergency_id, resource_type="ambulance",
        quantity=2, priority="high", status="pending", requested_at=now, requested_by="ic-1",
    )
    db.add(resource)
    db.commit()
    return resource.id


def test_resolve_emergency_locks_and_increments_version(db):
    emergency_id = _seed_emergency(db)
    service = CommandCenterService(db)
    resolved = service.resolve_emergency(emergency_id, resolved_by="ic-1", notes="contained")
    assert resolved.id == emergency_id

    refreshed = db.query(EmergencyDeclarationModel).filter_by(id=emergency_id).one()
    assert refreshed.status == "resolved"
    assert refreshed.version == 2  # started at 1, incremented once


def test_second_resolution_is_rejected_not_reapplied(db):
    emergency_id = _seed_emergency(db)
    service = CommandCenterService(db)
    service.resolve_emergency(emergency_id, resolved_by="ic-1", notes="first close")

    with pytest.raises(EmergencyAlreadyResolvedError):
        service.resolve_emergency(emergency_id, resolved_by="ic-2", notes="second close")

    refreshed = db.query(EmergencyDeclarationModel).filter_by(id=emergency_id).one()
    assert refreshed.version == 2
    assert refreshed.situation_summary.count("[RESOLVED]") == 1
    assert refreshed.resolved_by == "ic-1"


def test_fulfill_resource_locks_and_rejects_second_fulfillment(db):
    emergency_id = _seed_emergency(db)
    resource_id = _seed_resource(db, emergency_id)
    service = CommandCenterService(db)

    fulfilled = service.fulfill_resource(resource_id, {"fulfilled_quantity": 2, "fulfilled_by": "depot-1"})
    assert fulfilled.id == resource_id

    with pytest.raises(ResourceRequestAlreadyFulfilledError):
        service.fulfill_resource(resource_id, {"fulfilled_quantity": 999, "fulfilled_by": "depot-2"})

    refreshed = db.query(ResourceRequestModel).filter_by(id=resource_id).one()
    assert refreshed.fulfilled_quantity == 2
    assert refreshed.fulfilled_by == "depot-1"
    assert refreshed.version == 2


def test_resolve_emergency_query_is_row_locked(db, monkeypatch):
    from sqlalchemy.orm import Query as SAQuery

    emergency_id = _seed_emergency(db)
    calls = []
    original = SAQuery.with_for_update

    def spy(self, *args, **kwargs):
        calls.append(kwargs)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(SAQuery, "with_for_update", spy)

    service = CommandCenterService(db)
    service.resolve_emergency(emergency_id, resolved_by="ic-1")

    assert calls, "resolve_emergency must call Query.with_for_update()"
