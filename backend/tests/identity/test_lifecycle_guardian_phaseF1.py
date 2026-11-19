"""NIAM Lifecycle Category-F closure, class 1 of 5: GuardianService.

Regression guard for the authorization boundary added alongside the
sync/async conversion (see docs/security/NIAM_SYNC_ASYNC_LIFECYCLE_F1_GUARDIAN_STATUS.md).
Follows this repo's established pattern for this layer (fake session/actor,
no real async engine -- see test_platform_authority_phase10.py's own
docstring for why) rather than a real DB TestClient.

These tests exist so that if the ownership/fail-closed checks are ever
removed or weakened, CI catches it -- the real HTTP+PostgreSQL negative
proof (removing the gate flips 403->200) was run once by hand during this
class's closure and is documented in the status report, not re-run here.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app.identity.lifecycle import routes as lifecycle_routes
from fastapi import HTTPException


def _actor(identity_id="IDENTITY-P1"):
    return SimpleNamespace(account=SimpleNamespace(id="ACCOUNT-P1", identity_id=identity_id))


class _FakeDb:
    def __init__(self, person_id_for_identity):
        self._person_id = person_id_for_identity

    async def scalar(self, _stmt):
        return self._person_id


# ── _require_self_person: the reusable primitive under all 6 routes ──


def test_require_self_person_passes_when_actor_matches_target():
    lifecycle_routes._require_self_person("PERSON-A", "PERSON-A")


def test_require_self_person_blocks_when_actor_differs_from_target():
    with pytest.raises(HTTPException) as exc:
        lifecycle_routes._require_self_person("PERSON-A", "PERSON-B")
    assert exc.value.status_code == 403


def test_require_self_person_blocks_when_actor_person_unresolved():
    with pytest.raises(HTTPException) as exc:
        lifecycle_routes._require_self_person(None, "PERSON-B")
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_resolve_actor_person_id_returns_scalar_result():
    db = _FakeDb(person_id_for_identity="PERSON-A")
    result = await lifecycle_routes._resolve_actor_person_id(db, _actor())
    assert result == "PERSON-A"


# ── create_guardianship: self-owned, guardian_person_id must equal actor's own person ──


@pytest.mark.asyncio
async def test_create_guardianship_blocks_impersonation_of_another_persons_guardian_claim(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "GuardianService", lambda _db: SimpleNamespace(
        create_guardianship=AsyncMock(side_effect=AssertionError("must not reach service when gate blocks")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.create_guardianship(
            guardian_id="g1",
            guardian_person_id="PERSON-VICTIM",  # not the actor's own person
            dependent_person_id="PERSON-DEP",
            relationship="parent",
            guardian_type="legal",
            db=db,
            actor=_actor(),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_guardianship_allows_self_claim(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    db.commit = AsyncMock()
    fake_svc = SimpleNamespace(
        create_guardianship=AsyncMock(return_value=SimpleNamespace(guardian_id="g1")),
    )
    monkeypatch.setattr(lifecycle_routes, "GuardianService", lambda _db: fake_svc)
    result = await lifecycle_routes.create_guardianship(
        guardian_id="g1",
        guardian_person_id="PERSON-ACTOR",  # actor claiming to be the guardian themselves
        dependent_person_id="PERSON-DEP",
        relationship="parent",
        guardian_type="legal",
        db=db,
        actor=_actor(),
    )
    assert result == {"guardian_id": "g1"}
    fake_svc.create_guardianship.assert_awaited_once()
    db.commit.assert_awaited_once()


# ── verify_guardianship: fails closed for EVERYONE, including the guardian themselves ──


@pytest.mark.asyncio
async def test_verify_guardianship_fails_closed_even_for_the_guardian_of_record(monkeypatch):
    db = _FakeDb(person_id_for_identity="PERSON-ACTOR")
    monkeypatch.setattr(lifecycle_routes, "GuardianService", lambda _db: SimpleNamespace(
        verify_guardianship=AsyncMock(side_effect=AssertionError("must never reach the service")),
    ))
    with pytest.raises(HTTPException) as exc:
        await lifecycle_routes.verify_guardianship(
            guardian_id="g1", verified_by="anyone", db=db, actor=_actor(),
        )
    assert exc.value.status_code == 403
    assert "administrative authority" in exc.value.detail
