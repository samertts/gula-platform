"""NIAM Lifecycle Category-F closure, class 5 of 5 (final): CitizenService.

The one class with a genuine mixed self-service/admin model:
  - register_citizen, send_otp, verify_otp, record_consent, deactivate,
    get_citizen_status: self-owned (actor's own person == citizen's
    person_id).
  - link_family_member: self-owned on the CITIZEN side (adding a
    relative/emergency contact confers no authority).
  - link_guardian: self-owned on the GUARDIAN side, not the citizen side
    (matches GuardianService.create_guardianship's precedent -- a person
    may only register *themselves* as a guardian).
  - verify_identity, issue_health_id, record_death: fail closed for
    everyone (record_death inherently so -- a deceased person cannot
    call this API).

See docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F5_CITIZEN_STATUS.md.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.lifecycle import routes as lifecycle_routes
from fastapi import HTTPException


def _actor(identity_id="IDENTITY-ACTOR"):
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-ACTOR", identity_id=identity_id))


class _FakeDb:
    def __init__(self, person_id_for_identity):
        self._person_id = person_id_for_identity

    async def scalar(self, _stmt):
        return self._person_id


# ── register_citizen: self-owned on the person_id itself ──


@pytest.mark.asyncio
async def test_register_citizen_blocks_registering_another_persons_citizenship(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        register_citizen=AsyncMock(side_effect=AssertionError("must not reach service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.register_citizen(person_id="PERSON-OTHER", db=db, actor=_actor())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_register_citizen_allows_self(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    db.commit = AsyncMock()
    fake_svc = SimpleNamespace(register_citizen=AsyncMock(return_value=SimpleNamespace(citizen_id="c1")))
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: fake_svc)
    result = await lifecycle_routes.register_citizen(person_id="PERSON-ACTOR", db=db, actor=_actor())
    assert result == {"citizen_id": "c1"}
    db.commit.assert_awaited_once()


# ── send_otp: pre-fetch-and-check pattern (Guardian precedent) ──


@pytest.mark.asyncio
async def test_send_otp_blocks_other_actor(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    fake_svc = SimpleNamespace(
        get_citizen=AsyncMock(return_value=SimpleNamespace(person_id="PERSON-OTHER")),
        send_otp=AsyncMock(side_effect=AssertionError("must not reach mutation")),
    )
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: fake_svc)
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.send_citizen_otp(citizen_id="c1", db=db, actor=_actor())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_send_otp_allows_self(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    db.commit = AsyncMock()
    fake_svc = SimpleNamespace(
        get_citizen=AsyncMock(return_value=SimpleNamespace(person_id="PERSON-ACTOR")),
        send_otp=AsyncMock(return_value=SimpleNamespace(citizen_id="c1", status="otp_sent")),
    )
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: fake_svc)
    result = await lifecycle_routes.send_citizen_otp(citizen_id="c1", db=db, actor=_actor())
    assert result == {"citizen_id": "c1", "status": "otp_sent"}


# ── link_guardian: self-owned on the GUARDIAN side, not the citizen side ──


@pytest.mark.asyncio
async def test_link_guardian_blocks_citizen_appointing_arbitrary_guardian(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-CITIZEN")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        link_guardian=AsyncMock(side_effect=AssertionError("must not reach service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.link_citizen_guardian(
            citizen_id="c1", guardian_person_id="PERSON-VICTIM", relationship="parent", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_link_guardian_allows_prospective_guardian_self(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-GUARDIAN")
    db.commit = AsyncMock()
    fake_svc = SimpleNamespace(link_guardian=AsyncMock(return_value=SimpleNamespace(guardian_id="g1")))
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: fake_svc)
    result = await lifecycle_routes.link_citizen_guardian(
        citizen_id="c1", guardian_person_id="PERSON-GUARDIAN", relationship="parent", db=db, actor=_actor(),
    )
    assert result == {"guardian_id": "g1"}


# ── link_family_member: self-owned on the CITIZEN side (opposite of link_guardian) ──


@pytest.mark.asyncio
async def test_link_family_blocks_non_owning_actor(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-OTHER")
    fake_svc = SimpleNamespace(
        get_citizen=AsyncMock(return_value=SimpleNamespace(person_id="PERSON-CITIZEN")),
        link_family_member=AsyncMock(side_effect=AssertionError("must not reach mutation")),
    )
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: fake_svc)
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.link_citizen_family(
            citizen_id="c1", relative_id="r1", relationship="sibling", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403


# ── verify_identity / issue_health_id / record_death: fail closed for everyone ──


@pytest.mark.asyncio
async def test_verify_identity_fails_closed_even_for_citizen_self(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        verify_identity=AsyncMock(side_effect=AssertionError("must never reach the service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.verify_citizen_identity(citizen_id="c1", verified_by="anyone", db=db, actor=_actor())
    assert exc.value.status_code == 403
    assert "administrative authority" in exc.value.detail


@pytest.mark.asyncio
async def test_issue_health_id_fails_closed(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        issue_health_id=AsyncMock(side_effect=AssertionError("must never reach the service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.issue_health_id(citizen_id="c1", health_id="HID-1", db=db, actor=_actor())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_record_death_fails_closed_inherently_third_party(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        record_death=AsyncMock(side_effect=AssertionError("must never reach the service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.record_citizen_death(
            citizen_id="c1", death_date="2026-01-01T00:00:00Z", death_certificate_id="DC-1", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403


# ── get_citizen_status: self-owned read ──


@pytest.mark.asyncio
async def test_get_citizen_status_blocks_reading_another_persons_record(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "CitizenService", lambda _db: SimpleNamespace(
        get_citizen_status=AsyncMock(side_effect=AssertionError("must not reach service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.get_citizen_status(person_id="PERSON-OTHER", db=db, actor=_actor())
    assert exc.value.status_code == 403
