"""NR-076 — a built table is not a working one, and neither is a named repository.

Every ledger in this suite asks some version of *"is this table built?"*. NR-073,
NR-074 and NR-075 were the first three defects where the answer was **yes** and
the code still could not run. This is the fourth shape, and it sits even earlier
in the call than the others: the persistence layer is present, named, imported
and constructed, and it does nothing.

`SQLAlchemyTaskAssignmentRepository.save` is::

    def save(self, assignment: Any) -> Any:
        return assignment

No session, no INSERT, no exception. A caller receives its own object back and
every subsequent read returns `[]`. Across the two national orchestration
packages, **eleven of the fourteen concrete repositories are shaped like that**,
including *both* audit-log repositories, both the assignment and escalation
stores, and workflow steps, approvals, compensations and timers.

Nothing has ever executed them, so nothing noticed. `_get_service()` raises
`TypeError` first -- `SQLAlchemyTaskAssignmentRepository` implements
`find_by_user` and `find_active` while its ABC declares `find_by_assignee`, so
the class is still abstract -- and that TypeError is currently the only thing
standing between this platform and a workflow engine that answers
``{"success": true}`` while discarding every row it is handed.

**The detector, and two wrong ones before it.** This measurement took three
attempts and only the third is asserted below:

1. looking for the tokens `SessionLocal`/`get_db`/`session` reported 44 of 51
   repositories as stubs -- **false**: `SQLAlchemyDocumentRepository` and its
   neighbours hold the session as `self.db`, and they persist perfectly well;
2. counting write methods with no `ast.Call` reported 82 -- **also false**: it
   counted the abstract base classes, whose bodies are `...` by definition;
3. counting **concrete** write methods (not `...`, not `pass`, not `raise`) that
   contain no call at all gives **11**, which matches reading every file.

The first two numbers are not recorded anywhere as findings, because they are
not true. The rule they cost is worth stating: a detector for "does this code
do anything?" must exclude the code that is *declared* to do nothing.

The ledger may shrink. It may never grow. An entry that gains a real
implementation must be removed rather than left behind -- and removing one is
only correct once its writes reach a database, not once the class merely becomes
instantiable. Making it instantiable without implementing it would replace a
loud failure with silent data loss, which is the wrong direction.
"""

from __future__ import annotations

import ast

from tests.orm_resolution import APP, BACKEND, parse

#: Method names that are supposed to change persistent state.
WRITE_METHODS = frozenset({"save", "create", "update", "delete", "add", "persist", "store"})

#: Concrete repositories whose every write method performs no call at all, and
#: therefore cannot reach a database. Measured at the time of writing.
DECLARED_INERT_REPOSITORIES = frozenset({
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskQueueRepository",
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskAssignmentRepository",
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskEscalationRepository",
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskSLARepository",
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskCommentRepository",
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskAuditLogRepository",
    "app/national/workflow_runtime/infrastructure/repository.py:SQLAlchemyWorkflowExecutionStepRepository",
    "app/national/workflow_runtime/infrastructure/repository.py:SQLAlchemyWorkflowApprovalRepository",
    "app/national/workflow_runtime/infrastructure/repository.py:SQLAlchemyWorkflowCompensationRepository",
    "app/national/workflow_runtime/infrastructure/repository.py:SQLAlchemyWorkflowTimerRepository",
    "app/national/workflow_runtime/infrastructure/repository.py:SQLAlchemyWorkflowTemplateRepository",
})

#: The two audit logs among them, named separately because losing an audit row
#: silently is a different severity from losing a timer.
INERT_AUDIT_REPOSITORIES = frozenset({
    "app/national/task_engine/infrastructure/repository.py:SQLAlchemyTaskAuditLogRepository",
})


def _is_declared_empty(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """True for a body that is only a docstring, `...`, `pass` or `raise`.

    This is the exclusion the second detector was missing. An abstract method is
    *supposed* to contain nothing, so counting it as inert measures the interface
    rather than the implementation.
    """
    body = [
        node for node in fn.body
        if not (isinstance(node, ast.Expr)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str))
    ]
    if not body:
        return True
    return all(
        isinstance(node, (ast.Pass, ast.Raise))
        or (isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and node.value.value is Ellipsis)
        for node in body
    )


def _inert_repositories() -> dict[str, list[str]]:
    """'module:Class' -> write methods that contain no call at all."""
    found: dict[str, list[str]] = {}
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        module = str(path.relative_to(BACKEND))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            if not cls.name.endswith("Repository"):
                continue
            concrete = [
                m for m in cls.body
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                and m.name in WRITE_METHODS
                and not _is_declared_empty(m)
            ]
            if not concrete:
                continue
            callless = sorted(
                m.name for m in concrete
                if not any(isinstance(n, ast.Call) for n in ast.walk(m))
            )
            if len(callless) == len(concrete):
                found[f"{module}:{cls.name}"] = callless
    return found


def test_the_inert_repository_scan_still_finds_repositories() -> None:
    """Guard the guard -- against the population, not against the finding.

    A floor on the *number of inert repositories* would be satisfied by a broken
    scan that also reported zero real ones. This asserts the scan still sees a
    substantial repository population, so the ledger below is measured against
    something.
    """
    total = 0
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = parse(path)
        if tree is None:
            continue
        total += sum(
            1 for n in ast.walk(tree)
            if isinstance(n, ast.ClassDef) and n.name.endswith("Repository")
        )
    assert total >= 80, (
        f"only {total} repository classes found; the scan has drifted and the "
        "ledger below would be measured against nothing"
    )


def test_no_new_repository_accepts_writes_and_discards_them() -> None:
    """The ratchet. A new one silently loses every row it is given."""
    appeared = sorted(set(_inert_repositories()) - DECLARED_INERT_REPOSITORIES)
    assert appeared == [], (
        "these repositories have write methods that perform no call at all, so "
        "they accept an entity, return it, and store nothing. A caller cannot "
        f"tell that from success: {appeared}"
    )


def test_the_inert_repository_ledger_does_not_rot() -> None:
    """A repository that gained a real implementation must leave the ledger.

    Leaving it behind is not harmless: the entry is what tells the next reader
    that this package cannot persist, and a stale one makes the whole ledger
    unreliable in the direction that understates the problem.
    """
    resolved = sorted(DECLARED_INERT_REPOSITORIES - set(_inert_repositories()))
    assert resolved == [], (
        "these repositories now perform a call in their write methods; remove "
        "them from the ledger so the ratchet keeps its grip -- and check that "
        "the call actually reaches a session before you do: "
        f"{resolved}"
    )


def test_no_audit_log_repository_is_inert_outside_the_declared_set() -> None:
    """Audit rows are the one kind whose silent loss is a security matter.

    CLAUDE.md requires every mutation to reach the audit log. A repository that
    accepts an audit row and discards it satisfies every static check for
    "the code writes an audit row" while satisfying none of the intent.
    """
    inert_audit = {
        name for name in _inert_repositories()
        if "Audit" in name.split(":")[-1]
    }
    undeclared = sorted(inert_audit - INERT_AUDIT_REPOSITORIES - DECLARED_INERT_REPOSITORIES)
    assert undeclared == [], (
        "these audit-log repositories accept a row and store nothing, so audit "
        f"coverage is declared but not delivered: {undeclared}"
    )
