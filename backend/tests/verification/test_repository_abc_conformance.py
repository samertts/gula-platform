"""Implementations the code treats as concrete that Python refuses to construct.

IA-059. Python computes ``__abstractmethods__`` itself, so this is not a
heuristic: a non-empty set on a class whose own factory calls ``Cls()`` means
that factory raises TypeError. Across 4,765 classes in backend/app, 253 inherit
an abstract interface and 5 left it unimplemented as first measured:

    app.national.task_engine...SQLAlchemyTaskAssignmentRepository   [FIXED]
        missing find_by_assignee
    app.national.task_engine...SQLAlchemyTaskSLARepository          [FIXED]
        missing find_by_category_and_priority, list
    app.reference.infrastructure.repositories.SQLResultRepository   [OPEN]
        missing list_by_patient_analyte
    app.document_intelligence.application.wiring.DefaultLayoutDetector [OPEN]
        missing detect_handwritten_text, detect_logos, detect_stamps
    app.document_intelligence.providers.base.OcrProviderBase
        missing 8 -- NOT a defect, see below

The two task_engine entries are repaired under IA-070, and the repair is not
the one this file originally implied. Their TypeErrors were the only thing in
front of 24 methods, in six classes in the same file, that persisted nothing
while reporting success -- the task audit log's ``save`` returned its argument
and wrote nothing. Simply implementing the three missing methods would have
unblocked ``_get_service()`` and exposed all of them. They are implemented as
refusals instead, so the classes construct and nothing silently discards.

That is the general lesson for the two still OPEN: an unconstructible class is
sometimes load-bearing. Check what its TypeError is holding back before making
it constructible.

Each was reproduced through the construction site production uses, and each
fails BEFORE any SQL:

    SQLResultRepository(session)            TypeError (abstract)
    get_result_service(session)             TypeError (abstract) -- the
                                            FastAPI dependency itself
    SQLAlchemyTaskSLARepository()           TypeError (abstract)
    DefaultLayoutDetector()                 TypeError (abstract)

OcrProviderBase is declared ``class OcrProviderBase(OcrProvider, ABC)``, is
never instantiated directly, and all three of its subclasses --
EasyOcrProvider, PaddleOcrProvider, TesseractProvider -- have
``__abstractmethods__ == frozenset()``. It is an intermediate abstract base
doing its job, and counting it would have been a false positive.

REACHABILITY DIFFERS, AND IT DECIDES THE SEVERITY.

Measured by request, not assumed:

    /national/tasks/                 registered -> TypeError (served)
    /document-intelligence/documents registered -> RuntimeError "Document
                                     Intelligence Platform not initialized."
                                     so the orchestrator holding
                                     DefaultLayoutDetector() is never built;
                                     the route fails closed with a clear
                                     message and the TypeError stays latent
    /reference/results/              404 NOT REGISTERED
    /reference/orders/               404
    /reference/patients/             404

So app.reference's break is latent, not served. It still matters: the method
that does not exist, ``list_by_patient_analyte``, is called by
app/reference/domain/safety.py:31 inside ``perform_delta_check`` -- a delta
check, which compares a result against the patient's previous results for the
same analyte to catch a suspicious change -- and that is reached from
ResultService at app/reference/services/result_service.py:34. The clinical
control cannot run, and no route currently asks it to.
"""
from __future__ import annotations

import asyncio
import inspect

import pytest


def _missing(cls) -> list[str]:
    return sorted(getattr(cls, "__abstractmethods__", frozenset()))


def test_task_engine_repositories_are_constructible_and_refuse_every_call():
    """IA-059 as first recorded, now superseded by IA-070.

    This asserted that the two classes could not be constructed --
    ``SQLAlchemyTaskAssignmentRepository`` was missing ``find_by_assignee`` and
    ``SQLAlchemyTaskSLARepository`` was missing ``find_by_category_and_priority``
    and ``list``, so both raised TypeError.

    That reading was incomplete in a way that mattered. Those two TypeErrors
    were the only thing standing in front of 24 methods, across six classes in
    the same file, that persisted nothing while reporting success -- including
    the task audit log, whose ``save`` returned its argument and wrote nothing.
    Implementing the three missing methods, the obvious repair for this test,
    would have unblocked ``_get_service()`` and exposed all of them.

    IA-070 implements them as refusals instead, along with every other method in
    those six classes, so the classes are constructible and nothing silently
    discards. The full ratchets live in test_task_engine_persistence_truth.py.
    """
    from app.national.task_engine.infrastructure.repository import (
        SQLAlchemyTaskAssignmentRepository,
        SQLAlchemyTaskSLARepository,
        TaskEngineRepositoryUnavailable,
    )

    assert _missing(SQLAlchemyTaskAssignmentRepository) == []
    assert _missing(SQLAlchemyTaskSLARepository) == []

    # constructible -- but only because every method now refuses
    with pytest.raises(TaskEngineRepositoryUnavailable, match="find_by_assignee"):
        asyncio.run(SQLAlchemyTaskAssignmentRepository().find_by_assignee("probe"))
    with pytest.raises(TaskEngineRepositoryUnavailable, match="find_by_category_and_priority"):
        asyncio.run(SQLAlchemyTaskSLARepository().find_by_category_and_priority("c", "p"))
    # and the one that used to report a write it never made
    from app.national.task_engine.infrastructure.repository import (
        SQLAlchemyTaskAuditLogRepository,
    )
    with pytest.raises(TaskEngineRepositoryUnavailable):
        asyncio.run(SQLAlchemyTaskAuditLogRepository().save({"task_id": "t-1"}))


def test_the_reference_result_dependency_raises_before_any_sql(db):
    """get_result_service is a FastAPI dependency; it raises on construction."""
    from app.reference.infrastructure.dependencies import get_result_service
    from app.reference.infrastructure.repositories import SQLResultRepository

    assert _missing(SQLResultRepository) == ["list_by_patient_analyte"]
    with pytest.raises(TypeError, match="list_by_patient_analyte"):
        get_result_service(db)


def test_the_missing_method_is_the_one_the_delta_check_calls():
    """Not an unused interface method -- a clinical control depends on it."""
    from app.reference.domain import safety

    source = inspect.getsource(safety)
    assert "list_by_patient_analyte" in source
    assert "perform_delta_check" in source


def test_the_document_intelligence_layout_detector_cannot_be_constructed():
    from app.document_intelligence.application.wiring import DefaultLayoutDetector

    assert _missing(DefaultLayoutDetector) == [
        "detect_handwritten_text",
        "detect_logos",
        "detect_stamps",
    ]
    with pytest.raises(TypeError, match="detect_handwritten_text"):
        DefaultLayoutDetector()


def test_ocr_provider_base_is_abstract_on_purpose_and_its_subclasses_are_complete():
    """The one of the five that is not a defect, asserted so it stays that way."""
    import importlib
    import pkgutil

    import app.document_intelligence.providers as providers
    from app.document_intelligence.providers.base import OcrProviderBase

    assert inspect.isabstract(OcrProviderBase)

    concrete = []
    for info in pkgutil.iter_modules(providers.__path__, prefix=providers.__name__ + "."):
        try:
            module = importlib.import_module(info.name)
        except Exception:
            continue
        for value in vars(module).values():
            if (
                inspect.isclass(value)
                and issubclass(value, OcrProviderBase)
                and value is not OcrProviderBase
                and value.__module__ == module.__name__
            ):
                concrete.append(value)

    assert len(concrete) >= 3, [c.__qualname__ for c in concrete]
    for cls in concrete:
        assert _missing(cls) == [], f"{cls.__qualname__} is incomplete: {_missing(cls)}"


# ── IA-060: awaiting a sync Session ─────────────────────────────────────────
#
# app.database.get_db yields a sync Session. 227 route parameters annotate it
# as AsyncSession, which FastAPI does not enforce, so the annotation is simply
# untrue and nothing complains. For 221 of them that is only misleading: they
# use the session synchronously. Six files go further and await it:
#
#   identity/admin/routes.py          5 awaited session calls
#   identity/api/memberships.py       5
#   identity/adaptive_auth/routes.py  4
#   identity/api/roles.py             3
#   identity/api/workspaces.py        2
#   identity/api/security.py          2
#
# This is a different defect from the 20 `async with SessionLocal` sites in
# national/task_engine and national/workflow_runtime, which fail on
# __aenter__. Here the call returns a plain value and the await is applied to
# it, so the failure is "object X can't be used in 'await' expression".


def test_awaiting_the_injected_session_fails(db):
    """The exact expression at app/identity/api/roles.py:172."""
    import asyncio

    from app.identity.models import Membership

    assert not inspect.iscoroutinefunction(db.get)

    async def as_written():
        return await db.get(Membership, "01JJJJJJJJJJJJJJJJJJJJJJJJ")

    with pytest.raises(TypeError, match="can't be used in 'await' expression"):
        asyncio.run(as_written())

    # the same call without await returns a plain result
    assert db.get(Membership, "01JJJJJJJJJJJJJJJJJJJJJJJJ") is None


def test_the_awaited_session_sites_are_where_this_finding_says_they_are():
    import pathlib
    import re

    root = pathlib.Path(__file__).resolve().parents[2] / "app"
    pattern = re.compile(r"await (?:db|session|_db)\.(?:execute|get|commit|scalar|refresh|flush)")
    counts = {}
    for rel in (
        "identity/admin/routes.py",
        "identity/api/memberships.py",
        "identity/adaptive_auth/routes.py",
        "identity/api/roles.py",
        "identity/api/workspaces.py",
        "identity/api/security.py",
    ):
        path = root / rel
        counts[rel] = len(pattern.findall(path.read_text())) if path.exists() else -1

    assert all(n > 0 for n in counts.values()), counts
    print(f"\nawaited-session call sites: {counts}")
