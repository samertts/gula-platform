"""No task-engine repository reports a write it did not perform.

IA-070. Six of the seven classes named ``SQLAlchemy*Repository`` in
``app/national/task_engine/infrastructure/repository.py`` contained no
SQLAlchemy at all. ``save`` returned its argument without writing, ``get``
returned ``None``, every finder returned ``[]``. Measured by AST over the file:
of 7 repository classes only ``SQLAlchemyNationalTaskRepository`` touches the
database; the other 6 had 24 methods between them and 0 that issue a query.

``save`` returning the entity is the dangerous shape -- the caller gets its
object back and has every reason to believe it was stored. One of the six is
``SQLAlchemyTaskAuditLogRepository``, so the audit log discarded every write
while reporting success, against CLAUDE.md security invariant 2.

WHY THIS WAS URGENT EVEN THOUGH NOTHING REACHED IT. All 29 routes call
``_get_service()``, which constructs all seven and raised::

    TypeError: Can't instantiate abstract class
    SQLAlchemyTaskAssignmentRepository without an implementation for
    abstract method 'find_by_assignee'

The two classes with unimplemented abstract methods (IA-059) were an accidental
circuit breaker in front of the other 24 silent methods. The obvious repair for
that TypeError -- implement the three missing methods so the classes
instantiate -- would have unblocked construction and exposed all of them,
converting a loud failure into silent data loss across the whole task engine.

So the repair goes the other way: every method refuses, the missing ones
included. These tests exist to keep the discard from coming back, because the
tempting edit remains "just return [] so it works".
"""
from __future__ import annotations

import ast
import asyncio
import inspect
import pathlib

import pytest

REPOSITORY_FILE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "national" / "task_engine" / "infrastructure" / "repository.py"
)

#: The six that never persisted. ``SQLAlchemyNationalTaskRepository`` is absent
#: on purpose: it does issue queries, and is not part of this finding.
UNAVAILABLE_REPOSITORIES = (
    "SQLAlchemyTaskQueueRepository",
    "SQLAlchemyTaskAssignmentRepository",
    "SQLAlchemyTaskEscalationRepository",
    "SQLAlchemyTaskSLARepository",
    "SQLAlchemyTaskCommentRepository",
    "SQLAlchemyTaskAuditLogRepository",
)


def _repository(name):
    from app.national.task_engine.infrastructure import repository

    return getattr(repository, name)


def test_every_method_of_every_unavailable_repository_refuses():
    from app.national.task_engine.infrastructure.repository import (
        TaskEngineRepositoryUnavailable,
    )

    checked = 0
    for class_name in UNAVAILABLE_REPOSITORIES:
        cls = _repository(class_name)
        instance = cls()  # constructible now -- that is part of the repair
        for method_name, method in inspect.getmembers(cls, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            bound = getattr(instance, method_name)
            signature = inspect.signature(bound)
            args = [
                "probe" for p in signature.parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            with pytest.raises(TaskEngineRepositoryUnavailable) as caught:
                result = bound(*args)
                if inspect.isawaitable(result):
                    asyncio.run(result)
            assert class_name in str(caught.value)
            assert method_name in str(caught.value)
            checked += 1

    # positive control: 24 methods were measured across the six classes, so a
    # collapse to a handful means the walk stopped finding them
    assert checked >= 24, f"only {checked} methods exercised; the walk has gone blind"


def test_the_audit_log_repository_does_not_report_a_write_it_did_not_make():
    """Called out separately. This one is a security invariant, not a feature."""
    from app.national.task_engine.infrastructure.repository import (
        SQLAlchemyTaskAuditLogRepository,
        TaskEngineRepositoryUnavailable,
    )

    entry = {"task_id": "t-1", "action": "probe"}
    with pytest.raises(TaskEngineRepositoryUnavailable):
        asyncio.run(SQLAlchemyTaskAuditLogRepository().save(entry))


def test_no_method_in_the_file_returns_a_success_shaped_value_without_touching_the_db():
    """The ratchet. The tempting edit is `return []` to make something work.

    Any method that returns ``[]``, ``None``, or its own argument while issuing
    no query is reporting an outcome it did not produce. Only
    ``SQLAlchemyNationalTaskRepository`` is exempt, because it does query.
    """
    tree = ast.parse(REPOSITORY_FILE.read_text())
    db_markers = ("SessionLocal", "session", "query", "execute", "select", "add", "commit")
    source = REPOSITORY_FILE.read_text()

    offenders, scanned = [], 0
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in UNAVAILABLE_REPOSITORIES:
            continue
        for method in node.body:
            if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if method.name.startswith("_"):
                continue
            scanned += 1
            body = ast.get_source_segment(source, method) or ""
            touches_db = any(marker in body for marker in db_markers)
            returns = [n for n in ast.walk(method) if isinstance(n, ast.Return) and n.value is not None]
            if returns and not touches_db:
                offenders.append(f"{node.name}.{method.name} returns a value without querying")

    assert scanned >= 24, f"only {scanned} methods scanned; the scan has gone blind"
    assert not offenders, "\n".join(offenders)


def test_the_classes_are_constructible_so_the_circuit_breaker_is_no_longer_needed():
    """Construction succeeding is safe *because* every method refuses.

    Before the repair, ``_get_service()`` raised TypeError and that TypeError
    was the only thing preventing 24 silent discards. Asserting constructibility
    alone would be dangerous; it is asserted here together with the refusals
    above, and this test says so explicitly so the pair is not separated.
    """
    for class_name in UNAVAILABLE_REPOSITORIES:
        _repository(class_name)()  # must not raise TypeError

    from app.national.task_engine.api.routes import _get_service

    service = _get_service()
    assert service is not None


def test_refusals_do_not_absorb_a_future_contract_change():
    """A catch-all __getattr__ would hide a method added to an ABC later.

    The unavailable repositories list their methods explicitly, so a new
    abstract method appears as a normal TypeError at instantiation rather than
    being silently answered by a refusal. A refusal must not become the thing
    that conceals a contract change.
    """
    from app.national.task_engine.infrastructure import repository

    for class_name in UNAVAILABLE_REPOSITORIES:
        cls = getattr(repository, class_name)
        assert "__getattr__" not in vars(cls), f"{class_name} defines __getattr__"
        assert "__getattr__" not in vars(repository._UnavailableRepository)
