"""Runtime isolation guards.

Centralises the rules that distinguish API / worker / test / CLI processes:

  * `assert_worker_runtime()` — used by code paths (e.g. edge_* table access)
    that must NEVER execute inside an API request handler.
  * `is_edge_table(name)`     — predicate that classifies a table name as
    "edge data" (anything beginning with ``edge_``). All such access must
    happen from the worker runtime.
  * `install_edge_access_guard(engine)` — attaches a SQLAlchemy ``before_execute``
    hook that raises ``RuntimeIsolationError`` if an API/test/CLI process tries
    to query an edge_* table.

Edge tables are typically queues, distributed-state, replication outboxes,
or AI-pipeline scratch space — their access pattern is high-frequency and
should not block an HTTP request. Raising loudly when an API process touches
them surfaces accidental coupling immediately instead of silently degrading
request latency.
"""

from __future__ import annotations

import logging
import re

from ..config import IS_WORKER_RUNTIME, RUNTIME_MODE

logger = logging.getLogger("gula.runtime_guard")


class RuntimeIsolationError(RuntimeError):
    """Raised when a process accesses a resource outside its runtime role."""


_EDGE_TABLE_RE = re.compile(r"\bedge_[a-z0-9_]+\b", re.IGNORECASE)


def is_edge_table(name: str) -> bool:
    """Return True if ``name`` is an edge_* table identifier."""
    return bool(name) and name.lower().startswith("edge_")


def assert_worker_runtime(reason: str) -> None:
    """Raise unless the current process is the dedicated worker runtime."""
    if not IS_WORKER_RUNTIME:
        raise RuntimeIsolationError(
            f"{reason} — only allowed from RUNTIME_MODE=worker "
            f"(current RUNTIME_MODE={RUNTIME_MODE!r})",
        )


def _statement_touches_edge_table(sql: str) -> str | None:
    """Return the offending edge_* identifier or None.

    A simple regex scan is sufficient because edge_* tables follow a strict
    naming convention. False positives are not a concern: the API runtime
    has zero legitimate reason to mention ``edge_`` in any query.
    """
    if not sql:
        return None
    match = _EDGE_TABLE_RE.search(sql)
    return match.group(0) if match else None


def install_edge_access_guard(engine) -> None:
    """Attach a SQLAlchemy event hook that blocks edge_* access outside worker.

    Idempotent — re-installing the guard on the same engine is a no-op.
    """
    if IS_WORKER_RUNTIME:
        return  # worker runtime is allowed to access edge_* tables freely

    from sqlalchemy import event

    if getattr(engine, "_gula_edge_guard_installed", False):
        return

    @event.listens_for(engine, "before_cursor_execute")
    def _block_edge_access(conn, cursor, statement, parameters, context, executemany):
        offender = _statement_touches_edge_table(statement)
        if offender is None:
            return
        logger.error(
            "Runtime isolation violation: %s touched in RUNTIME_MODE=%s — statement=%r",
            offender,
            RUNTIME_MODE,
            statement[:200],
        )
        raise RuntimeIsolationError(
            f"Access to {offender} is forbidden outside the worker runtime "
            f"(current RUNTIME_MODE={RUNTIME_MODE!r}). Move the call site "
            "into a worker job or relay the data through an API-safe view.",
        )

    engine._gula_edge_guard_installed = True
    logger.info("Edge-table access guard installed (RUNTIME_MODE=%s)", RUNTIME_MODE)
