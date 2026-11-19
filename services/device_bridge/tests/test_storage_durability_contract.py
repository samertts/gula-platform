"""The contract any device-bridge store must satisfy, executable today.

IA-040 — preparatory work for a NEEDS_DECISION. The decision itself (which
engine, and how PHI is encrypted at rest in it) is in
docs/DURABILITY_DECISION_PACK.md and is not made here.

This suite is parameterised over a *store factory*. `InMemoryDB` is registered
as the first implementation, and `_PERSISTENT_FACTORIES` records which factories
claim to survive a restart -- currently none, which is the finding.

The persistence cases assert the *measured* behaviour of a store that makes no
such claim: everything is gone after a restart. So they are green today by
recording the loss, and they fail the moment a store stops losing it, with a
message saying to register the factory. That turns every case in this file into
a hard assertion, and a durable implementation is validated by running this same
file rather than by rewriting it.

An earlier draft used an imperative `pytest.xfail()` for those cases. That was
wrong in a way worth recording: `pytest.xfail()` reports xfail unconditionally,
so it would have reported xfail even once a store had started persisting -- it
could never have announced the fix, which is the opposite of what this file is
for.

What "restart" means here: a new store object built by the same factory, which
is exactly what a new process gets. For the in-memory store that is empty by
construction; for a file- or database-backed store it must find what the
previous instance wrote. The runtime proof over real HTTP and a real uvicorn
restart is in the decision pack.
"""
from __future__ import annotations

from collections.abc import Callable

import pytest
from app.storage.db import InMemoryDB
from app.storage.result_repository import LogRepository, ResultRepository

# A factory takes a handle (what a durable store would use as its path or DSN)
# and returns a store. The handle is ignored by the in-memory implementation,
# which is itself the finding: there is nowhere for it to point.
StoreFactory = Callable[[str], InMemoryDB]

_FACTORIES: dict[str, StoreFactory] = {
    "in-memory": lambda handle: InMemoryDB(),
}

_PERSISTENT_FACTORIES: frozenset[str] = frozenset()
"""Names in _FACTORIES that claim to survive a restart. Empty: that is IA-040."""


@pytest.fixture(params=sorted(_FACTORIES))
def factory(request) -> tuple[str, StoreFactory]:
    return request.param, _FACTORIES[request.param]


def _persistence_expected(name: str) -> bool:
    return name in _PERSISTENT_FACTORIES


def _write_one_of_everything(store: InMemoryDB) -> None:
    """Exercise every collection through the repositories, not by poking lists."""
    from app.pipeline.normalizer import Normalizer
    from app.pipeline.parser_engine import ParsedResult

    repo = ResultRepository(store)
    logs = LogRepository(store)

    normalized = Normalizer().transform(
        ParsedResult(test_code="HEMOGLOBIN", value=13.5, unit="g/dL"),
        patient_id="12345",
        device_id="CBC-01",
    )
    repo.save_results([normalized])          # results + an audit event
    repo.save_log(device_id="CBC-01", raw_data="<frame>", status="received")
    logs.save({"device_id": "CBC-01", "raw_data": "<frame>", "status": "processed"})
    repo.enqueue_offline({"device_id": "CBC-01", "results": ["HEMOGLOBIN"]})


def _counts(store: InMemoryDB) -> dict[str, int]:
    return {
        "results": len(store.results),
        "logs": len(store.logs),
        "audit_trail": len(store.audit_trail),
        "offline_queue": len(store.offline_queue),
    }


# ── the part every store already satisfies ──────────────────────────────────


def test_a_write_is_readable_through_the_repositories(factory, tmp_path):
    name, build = factory
    store = build(str(tmp_path / f"{name}.store"))
    _write_one_of_everything(store)

    repo = ResultRepository(store)
    assert len(repo.list_results()) == 1
    assert repo.list_results()[0]["test_code"] == "HEMOGLOBIN"
    assert len(repo.list_logs()) == 2
    assert [row["status"] for row in repo.list_logs()] == ["received", "processed"]
    # Two events, not one: save_results emits result_saved and enqueue_offline
    # emits offline_enqueued. The restart case below asserts the same two.
    assert len(repo.list_audit_trail()) == 2
    assert [row["event_type"] for row in repo.list_audit_trail()] == [
        "result_saved",
        "offline_enqueued",
    ]
    assert len(repo.list_offline_queue()) == 1


def test_appends_keep_their_order(factory, tmp_path):
    """Ordering is part of the contract: a log is a sequence of what happened,
    and a store that reorders it cannot be used to reconstruct an incident."""
    name, build = factory
    store = build(str(tmp_path / f"{name}.store"))
    repo = ResultRepository(store)
    for index in range(5):
        repo.save_log(device_id="CBC-01", raw_data=f"frame-{index}", status=f"s{index}")
    assert [row["status"] for row in repo.list_logs()] == ["s0", "s1", "s2", "s3", "s4"]


def test_every_collection_starts_empty(factory, tmp_path):
    """Positive control: a store that returned a fixed non-empty listing would
    pass the persistence cases below for the wrong reason."""
    name, build = factory
    store = build(str(tmp_path / f"{name}-fresh.store"))
    assert _counts(store) == {
        "results": 0,
        "logs": 0,
        "audit_trail": 0,
        "offline_queue": 0,
    }


def test_two_handles_do_not_share_state(factory, tmp_path):
    """Isolation, so the persistence cases cannot pass by every store being one
    global singleton."""
    _name, build = factory
    first = build(str(tmp_path / "a.store"))
    second = build(str(tmp_path / "b.store"))
    _write_one_of_everything(first)
    assert _counts(second)["results"] == 0


# ── the part no store satisfies yet: IA-040 ─────────────────────────────────


def test_everything_written_survives_a_restart(factory, tmp_path):
    """The requirement. A new store from the same factory and the same handle is
    what a new process gets.

    Measured over real HTTP and a real uvicorn restart, before any of this:
        before restart: results=1 logs=4 audit=2 offline-queue=1
        after  restart: results=0 logs=0 audit=0 offline-queue=0
    """
    name, build = factory
    handle = str(tmp_path / f"{name}-restart.store")

    before = build(handle)
    _write_one_of_everything(before)
    expected = _counts(before)
    assert expected == {
        "results": 1,
        "logs": 2,
        "audit_trail": 2,  # result_saved + offline_enqueued
        "offline_queue": 1,
    }
    del before  # the process ends here

    after = build(handle)
    if _persistence_expected(name):
        assert _counts(after) == expected
        return
    # IA-040, asserted as the measured reality rather than marked xfail. An
    # imperative pytest.xfail() here would report xfail even if the store had
    # started persisting, so it could never announce the fix -- the opposite of
    # what this file claims to do.
    assert _counts(after) == {
        "results": 0,
        "logs": 0,
        "audit_trail": 0,
        "offline_queue": 0,
    }, (
        f"{name} now survives a restart. Add it to _PERSISTENT_FACTORIES, which "
        "turns every case in this file into a hard assertion, and close IA-040 "
        "with a runtime restart proof over HTTP."
    )


def test_a_queued_result_survives_a_restart(factory, tmp_path):
    """The narrowest and most consequential case, called out on its own because
    the offline queue is the path a result takes *when GULA is unreachable* --
    and a restart is one of the likeliest events during an outage."""
    name, build = factory
    handle = str(tmp_path / f"{name}-queue.store")

    before = build(handle)
    ResultRepository(before).enqueue_offline(
        {"device_id": "CBC-01", "results": ["HEMOGLOBIN"], "reason": "send_failed"},
    )
    assert len(before.offline_queue) == 1
    del before

    after = build(handle)
    queued = ResultRepository(after).list_offline_queue()
    if _persistence_expected(name):
        assert len(queued) == 1
        assert queued[0]["results"] == ["HEMOGLOBIN"]
        return
    assert queued == [], (
        f"{name} now keeps the offline queue across a restart -- register it in "
        "_PERSISTENT_FACTORIES"
    )


def test_the_audit_trail_survives_a_restart(factory, tmp_path):
    """Recorded separately: CLAUDE.md forbids reducing audit coverage, and an
    audit trail that a restart erases provides none."""
    name, build = factory
    handle = str(tmp_path / f"{name}-audit.store")

    before = build(handle)
    ResultRepository(before).add_audit_event(
        event_type="result_saved", payload={"device_id": "CBC-01"},
    )
    assert len(before.audit_trail) == 1
    del before

    after = build(handle)
    trail = ResultRepository(after).list_audit_trail()
    if _persistence_expected(name):
        assert len(trail) == 1
        return
    assert trail == [], (
        f"{name} now keeps the audit trail across a restart -- register it in "
        "_PERSISTENT_FACTORIES"
    )


# ── the gap is declared, not hidden ─────────────────────────────────────────


def test_no_store_currently_claims_persistence():
    """The honest ledger. This file is green *with the persistence requirement
    declared as a known failure*; that is a record of the gap, not its
    resolution. When a durable store is registered this test fails, which is the
    cue to re-read docs/DURABILITY_DECISION_PACK.md §7 and close IA-040
    properly."""
    assert frozenset() == _PERSISTENT_FACTORIES, (
        "a store now claims to persist; the xfail(strict) markers above must "
        "become hard assertions and IA-040 can be closed with a runtime restart "
        "proof over HTTP, not just this suite"
    )


def test_the_decision_pack_is_recorded():
    import pathlib

    pack = pathlib.Path(__file__).resolve().parents[1] / "docs" / "DURABILITY_DECISION_PACK.md"
    text = pack.read_text()
    assert "NEEDS_DECISION" in text
    assert "## 5. The decision required" in text
    assert "edge_agent" in text, "the existing precedent must stay cited"
    assert "PHI at rest" in text, "the encryption half of the decision must stay stated"
