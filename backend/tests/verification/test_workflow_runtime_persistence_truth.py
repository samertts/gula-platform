"""A served workflow write no longer reports success while storing nothing.

IA-071. Found by sweeping for the IA-070 pattern platform-wide. Five of the
seven repository classes in
``app/national/workflow_runtime/infrastructure/repository.py`` contained no
SQLAlchemy at all. Measured by AST: ``SQLAlchemyWorkflowDefinitionRepository``
(7 db-touching methods of 10) and ``SQLAlchemyWorkflowExecutionRepository``
(6 of 9) are real; the other five had 20 methods and 0 that issue a query.

UNLIKE IA-070, THIS ONE WAS LIVE. ``task_engine`` was shielded by a TypeError
at construction. ``workflow_runtime``'s ``_get_service()`` constructs fine, so
the stubs were reachable through served, authenticated routes. Measured over
HTTP before the repair, as an admin:

    POST /national/workflows/templates
      -> 200 {"success":true,"id":"b4ebd8c9-4a67-440b-bb85-8173b19695a6"}
    GET  /national/workflows/templates
      -> 200 {"items":[],"total":0}

The endpoint reported success and minted an id the client could keep, while
storing nothing. ``SQLAlchemyWorkflowTemplateRepository.delete`` returned
``True`` — a deletion that never happened, indistinguishable from a real one.
``find_pending_for_user`` returned ``[]`` unconditionally, so an approval could
be recorded as saved and never appear in the queue that governs it.

The repair refuses rather than writing queries: no migration creates any of the
subsystem's eight tables, so real SQLAlchemy would raise ``no such table``.
That is also honest, but refusing says why.
"""
from __future__ import annotations

import ast
import asyncio
import inspect
import pathlib

import pytest

from tests.conftest import auth_headers

REPOSITORY_FILE = (
    pathlib.Path(__file__).resolve().parents[2]
    / "app" / "national" / "workflow_runtime" / "infrastructure" / "repository.py"
)

#: The five that never persisted. The two real ones are excluded deliberately.
UNAVAILABLE_REPOSITORIES = (
    "SQLAlchemyWorkflowExecutionStepRepository",
    "SQLAlchemyWorkflowApprovalRepository",
    "SQLAlchemyWorkflowCompensationRepository",
    "SQLAlchemyWorkflowTimerRepository",
    "SQLAlchemyWorkflowTemplateRepository",
)

REAL_REPOSITORIES = (
    "SQLAlchemyWorkflowDefinitionRepository",
    "SQLAlchemyWorkflowExecutionRepository",
)


def _repo(name):
    from app.national.workflow_runtime.infrastructure import repository

    return getattr(repository, name)


def test_the_served_template_write_no_longer_claims_success(client, db, make_lab, make_lab_user):
    """The defect, at the boundary a client actually sees.

    Before: 200 with success:true and a minted id, then an empty list.
    After: the request fails. A 500 is not pretty, but a write that reports
    success and stores nothing is worse than a write that fails loudly.
    """
    from app.national.workflow_runtime.infrastructure.repository import (
        WorkflowRepositoryUnavailable,
    )

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    headers = auth_headers(user_id=user.id, lab_id=lab.id, role="admin")

    with pytest.raises(WorkflowRepositoryUnavailable, match="no persistence"):
        client.post(
            "/national/workflows/templates",
            json={"name": "IA071", "definition": {}},
            headers=headers,
        )


def test_the_served_reads_do_not_answer_an_empty_list(client, db, make_lab, make_lab_user):
    """An empty list is indistinguishable from "nothing matches"."""
    from app.national.workflow_runtime.infrastructure.repository import (
        WorkflowRepositoryUnavailable,
    )

    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="admin")
    headers = auth_headers(user_id=user.id, lab_id=lab.id, role="admin")

    for path in ("/national/workflows/templates", "/national/workflows/approvals/pending"):
        with pytest.raises(WorkflowRepositoryUnavailable):
            client.get(path, headers=headers)


def test_delete_does_not_report_a_deletion_it_did_not_perform():
    """`delete` returned True. That is the hardest shape to notice."""
    from app.national.workflow_runtime.infrastructure.repository import (
        SQLAlchemyWorkflowTemplateRepository,
        WorkflowRepositoryUnavailable,
    )

    with pytest.raises(WorkflowRepositoryUnavailable, match="delete"):
        asyncio.run(SQLAlchemyWorkflowTemplateRepository().delete("tpl-1"))


def test_every_method_of_every_unavailable_repository_refuses():
    from app.national.workflow_runtime.infrastructure.repository import (
        WorkflowRepositoryUnavailable,
    )

    checked = 0
    for class_name in UNAVAILABLE_REPOSITORIES:
        cls = _repo(class_name)
        instance = cls()
        for method_name, _method in inspect.getmembers(cls, inspect.isfunction):
            if method_name.startswith("_"):
                continue
            bound = getattr(instance, method_name)
            args = [
                "probe" for p in inspect.signature(bound).parameters.values()
                if p.default is inspect.Parameter.empty
                and p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            ]
            with pytest.raises(WorkflowRepositoryUnavailable) as caught:
                result = bound(*args)
                if inspect.isawaitable(result):
                    asyncio.run(result)
            assert class_name in str(caught.value)
            assert method_name in str(caught.value)
            checked += 1

    # 20 methods were measured across the five classes
    assert checked >= 20, f"only {checked} methods exercised; the walk has gone blind"


def test_the_two_real_repositories_were_not_touched():
    """The repair must not have broken or hollowed out the working ones."""
    source = REPOSITORY_FILE.read_text()
    tree = ast.parse(source)
    db_markers = ("SessionLocal", "session", "query", "execute", "select")

    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name not in REAL_REPOSITORIES:
            continue
        body = ast.get_source_segment(source, node) or ""
        assert any(m in body for m in db_markers), (
            f"{node.name} no longer touches the database; it was one of the two real ones"
        )
        assert "_refuse" not in body, f"{node.name} was converted to a refusal by mistake"


def test_no_method_in_the_stub_classes_returns_a_success_shaped_value():
    """The ratchet. `return []` or `return True` is how this comes back."""
    source = REPOSITORY_FILE.read_text()
    tree = ast.parse(source)
    db_markers = ("SessionLocal", "session", "query", "execute", "select")

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
            returns = [n for n in ast.walk(method) if isinstance(n, ast.Return) and n.value is not None]
            if returns and not any(m in body for m in db_markers):
                offenders.append(f"{node.name}.{method.name} returns a value without querying")

    assert scanned >= 20, f"only {scanned} methods scanned; the scan has gone blind"
    assert not offenders, "\n".join(offenders)


def test_refusals_do_not_absorb_a_future_contract_change():
    from app.national.workflow_runtime.infrastructure import repository

    for class_name in UNAVAILABLE_REPOSITORIES:
        assert "__getattr__" not in vars(getattr(repository, class_name))
    assert "__getattr__" not in vars(repository._UnavailableWorkflowRepository)
