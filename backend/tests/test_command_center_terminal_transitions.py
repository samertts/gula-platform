"""An emergency declaration resolves once, within its own tenant.

THE DEFECTS, all reproduced against real PostgreSQL before the repair.

`CommandCenterService.resolve_emergency` and `.fulfill_resource` both were:

    model = self.db.query(Model).filter_by(id=...).first()
    if not model:
        raise NotFoundError()
    model.status = "resolved"          # or "fulfilled"
    ...
    self.db.commit()

1. NO TENANT SCOPE. Reproduced: a caller acting for lab A resolved lab B's
   national emergency declaration and stamped `resolved_by` with its own string.
   The same hole existed on `fulfill_resource`. Both routes sit behind
   require_permission("system:admin"), but admin is a lab-scoped role in this
   platform — only master_admin and ministry_admin are cross-tenant — so this was
   a genuine cross-tenant mutation.

2. NO TERMINAL-STATE GUARD. Reproduced: an already-resolved emergency resolved
   again, overwriting `resolved_at` and `resolved_by` and appending a second
   "[RESOLVED] ..." line to `situation_summary`.

3. NO ROW LOCK, AND `version` NEVER MOVED. Reproduced with two real PostgreSQL
   sessions released from a barrier: both committed, and the surviving row was a
   BLEND — `resolved_by` from one transaction with the other transaction's note
   appended first. That is a corrupted after-action record for a level_3_major
   emergency, not merely a lost update. `version` stayed at 1 throughout even
   though both models carry the optimistic-lock column.

4. NOT FIXED HERE, DELIBERATELY: `resolved_by` is still caller-supplied free
   text, so the recorded resolver of a national emergency is whatever the client
   sends. Registered as NR-018 awaiting an owner decision, because both remedies
   change a contract — server-derive the field (API semantics) or add a distinct
   authenticated-actor column (schema). test_f pins the current behaviour so the
   decision is made deliberately rather than drifting.

`actor_lab_id` is keyword-only with no default: a caller that forgets it raises
TypeError rather than reaching across tenants.

EVIDENCE LEVEL. Real PostgreSQL required — defect 3 is row-lock behaviour under
genuine concurrent transactions. Skips, never passes, without CC_POSTGRES_URL.
"""

from __future__ import annotations

import inspect
import os
import threading
from datetime import UTC, datetime

import pytest
from app.command_center.application.service import CommandCenterService
from app.command_center.exceptions import (
    EmergencyAlreadyResolvedError,
    EmergencyNotFoundError,
    ResourceRequestNotFoundError,
)
from app.command_center.infrastructure.models import (
    EmergencyDeclarationModel,
    ResourceRequestModel,
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

POSTGRES_URL = os.getenv("CC_POSTGRES_URL", "")
pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="CC_POSTGRES_URL is not configured"
)

LAB_A, LAB_B = 9901, 9902


@pytest.fixture(scope="module")
def Session():
    engine = create_engine(POSTGRES_URL, future=True)
    for model in (EmergencyDeclarationModel, ResourceRequestModel):
        model.__table__.create(engine, checkfirst=True)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture()
def clean(Session):
    def _wipe():
        with Session() as s:
            s.execute(text("DELETE FROM cc_resource_requests"))
            s.execute(text("DELETE FROM cc_emergency_declarations"))
            s.commit()

    _wipe()
    yield
    _wipe()


def _emergency(Session, *, lab=LAB_A, status="active"):
    with Session() as s:
        m = EmergencyDeclarationModel(
            lab_id=lab, emergency_type="flood", region="Basra", status=status,
            level="level_3_major", declared_at=datetime.now(UTC),
            declared_by="ops-officer", situation_summary="initial",
        )
        s.add(m)
        s.flush()
        s.commit()
        return m.id


def _request(Session, emergency_id, *, lab=LAB_A):
    with Session() as s:
        m = ResourceRequestModel(
            lab_id=lab, emergency_id=emergency_id, resource_type="ambulance",
            quantity=5, requested_at=datetime.now(UTC), status="pending",
        )
        s.add(m)
        s.flush()
        s.commit()
        return m.id


def test_a_actor_lab_id_is_required_and_keyword_only():
    """Structural control, and the positive control for the module."""
    for fn in (CommandCenterService.resolve_emergency,
               CommandCenterService.fulfill_resource):
        params = inspect.signature(fn).parameters
        assert "actor_lab_id" in params, fn.__qualname__
        assert params["actor_lab_id"].kind is inspect.Parameter.KEYWORD_ONLY
        assert params["actor_lab_id"].default is inspect.Parameter.empty


def test_b_an_emergency_resolves_for_its_own_tenant(Session, clean):
    """Positive control. A method that refused everything would satisfy the
    denial assertions below while being useless."""
    eid = _emergency(Session)
    with Session() as s:
        result = CommandCenterService(s).resolve_emergency(
            eid, "Incident Commander", "all clear", actor_lab_id=LAB_A,
        )
    assert result.status == "resolved"
    with Session() as s:
        m = s.get(EmergencyDeclarationModel, eid)
        assert m.status == "resolved"
        assert m.version == 2, "the optimistic-lock column must advance"
        assert m.resolved_at is not None


def test_c_another_tenants_emergency_is_not_reachable(Session, clean):
    """Defect 1 on resolve_emergency."""
    eid = _emergency(Session, lab=LAB_B)
    with Session() as s, pytest.raises(EmergencyNotFoundError):
        CommandCenterService(s).resolve_emergency(
            eid, "attacker", "closed by wrong tenant", actor_lab_id=LAB_A,
        )
    with Session() as s:
        m = s.get(EmergencyDeclarationModel, eid)
        assert m.status == "active"
        assert m.resolved_by is None
        assert m.situation_summary == "initial", "lab A altered lab B's record"


def test_d_another_tenants_resource_request_is_not_reachable(Session, clean):
    """Defect 1 on fulfill_resource — the identical hole next door."""
    eid = _emergency(Session, lab=LAB_B)
    rid = _request(Session, eid, lab=LAB_B)
    with Session() as s, pytest.raises(ResourceRequestNotFoundError):
        CommandCenterService(s).fulfill_resource(
            rid, {"fulfilled_quantity": 5, "fulfilled_by": "wrong tenant"},
            actor_lab_id=LAB_A,
        )
    with Session() as s:
        r = s.get(ResourceRequestModel, rid)
        assert r.status == "pending"
        assert r.fulfilled_by is None


def test_e_a_resolved_emergency_cannot_be_resolved_again(Session, clean):
    """Defect 2 — the terminal-state guard, and that the record survives."""
    eid = _emergency(Session)
    with Session() as s:
        CommandCenterService(s).resolve_emergency(
            eid, "Dr First", "first", actor_lab_id=LAB_A,
        )
    with Session() as s, pytest.raises(EmergencyAlreadyResolvedError):
        CommandCenterService(s).resolve_emergency(
            eid, "Someone Else Entirely", "second", actor_lab_id=LAB_A,
        )
    with Session() as s:
        m = s.get(EmergencyDeclarationModel, eid)
        assert m.resolved_by == "Dr First", "the refused repeat overwrote the resolver"
        assert m.situation_summary.count("[RESOLVED]") == 1, (
            f"the summary was appended more than once: {m.situation_summary!r}"
        )


def test_f_resolved_by_is_still_caller_supplied(Session, clean):
    """Defect 4, PINNED rather than fixed.

    This asserts today's behaviour on purpose: `resolved_by` is whatever the
    caller passes, so the recorded resolver of a national emergency is not
    server-derived. NR-018 carries the decision. When that decision lands and
    the field becomes server-derived, THIS TEST MUST FAIL and be rewritten — it
    is a tripwire, not an endorsement.
    """
    eid = _emergency(Session)
    with Session() as s:
        CommandCenterService(s).resolve_emergency(
            eid, "a name the client invented", "", actor_lab_id=LAB_A,
        )
    with Session() as s:
        assert s.get(EmergencyDeclarationModel, eid).resolved_by == (
            "a name the client invented"
        )


def test_g_two_concurrent_resolutions_commit_exactly_once(Session, clean):
    """Defect 3 — the reason this module needs PostgreSQL.

    Before the repair both transactions committed and the surviving row blended
    them: one transaction's resolved_by with the other's note appended first.
    """
    eid = _emergency(Session)
    barrier = threading.Barrier(2)
    outcomes: list[tuple[str, str]] = []
    lock = threading.Lock()

    def attempt(tag: str) -> None:
        with Session() as s:
            service = CommandCenterService(s)
            barrier.wait(timeout=10)
            try:
                service.resolve_emergency(eid, tag, f"note from {tag}", actor_lab_id=LAB_A)
                verdict = "committed"
            except EmergencyAlreadyResolvedError:
                verdict = "refused"
            with lock:
                outcomes.append((tag, verdict))

    threads = [threading.Thread(target=attempt, args=(t,)) for t in ("T1", "T2")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    committed = [t for t, v in outcomes if v == "committed"]
    assert len(committed) == 1, f"resolved {len(committed)} times: {outcomes}"
    assert len([t for t, v in outcomes if v == "refused"]) == 1, outcomes

    with Session() as s:
        m = s.get(EmergencyDeclarationModel, eid)
        assert m.version == 2
        winner = committed[0]
        assert m.resolved_by == winner
        # The record must belong to the winner alone, not be a blend of both.
        assert m.situation_summary.count("[RESOLVED]") == 1
        assert f"note from {winner}" in m.situation_summary
        loser = "T2" if winner == "T1" else "T1"
        assert f"note from {loser}" not in m.situation_summary
