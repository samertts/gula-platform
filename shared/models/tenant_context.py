"""NR-147 — the server's tenant for the current request, and the guard on it.

WHY THIS EXISTS
---------------
NR-146's audit of one service module found 41 functions shaped
`create_x(db, data) -> X(**data)`, where `data` is the request body and X
carries `lab_id`. Repairing 41 call sites one at a time is the change the next
`create_*` function silently undoes, because nothing would stop it. So the
tenant is defended where every one of them passes: the mixin that declares the
column.

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
This is DEFENCE IN DEPTH, not authorization. It answers exactly one question --
"is a request trying to write a row into a laboratory other than the
authenticated caller's?" -- and refuses when the answer is yes. It does not
decide whether the caller may act at all; that stays with the route's
permission checks and the service layer's scope rules, which remain the actual
control. A base guard treated as the whole answer would be the weaker system,
not the stronger one.

THE ESCAPE IS EXPLICIT, AND THAT IS THE POINT
---------------------------------------------
Legitimate cross-tenant writers exist: a ministry-level import, a background
reconciliation, a migration backfill. They say so:

    with cross_tenant("nightly national reconciliation"):
        session.add(Model(lab_id=other_lab))

An exception you have to name is one a reviewer can find. A silent bypass is
not.

WHEN NO TENANT IS ESTABLISHED, THIS IS INERT
--------------------------------------------
Workers, migrations, CLI tasks and tests run with no request tenant set, and
the guard allows everything -- it cannot police a value it has no truth for.
That is deliberate: this layer exists to catch a request body contradicting an
authenticated caller, and outside a request there is no such contradiction to
catch. It also means the guard must never be the only control, which is the
paragraph above.
"""
from __future__ import annotations

import contextvars
from collections.abc import Iterator
from contextlib import contextmanager

#: The authenticated caller's laboratory for this request.
#:
#: Set in exactly one place -- `get_current_user` in
#: backend/app/security/dependencies.py -- from the authenticated user's own
#: record, never from anything the client sent. `backend/app/database.py`
#: imports this rather than declaring its own, so there is one variable and not
#: two that drift.
current_lab_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "lab_id", default=None,
)

#: True while an explicitly declared cross-tenant operation is in progress.
_cross_tenant_reason: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "cross_tenant_reason", default=None,
)


class CrossTenantWriteRefused(PermissionError):
    """A request tried to write a row belonging to another laboratory."""

    def __init__(self, model: str, attempted: object, actual: object) -> None:
        super().__init__(
            f"{model}.lab_id={attempted!r} does not match the authenticated "
            f"caller's laboratory ({actual!r}). If this is a legitimate "
            f"cross-tenant operation, declare it with cross_tenant(reason); "
            f"if it is not, the tenant must come from the server, not the "
            f"request body (NR-147)."
        )
        self.model = model
        self.attempted = attempted
        self.actual = actual


@contextmanager
def cross_tenant(reason: str) -> Iterator[None]:
    """Declare that the code inside legitimately writes across laboratories.

    The reason is required and is not decoration: it is what a reviewer reads
    when deciding whether the exception is still justified.
    """
    if not reason or not reason.strip():
        raise ValueError("cross_tenant() requires a reason")
    token = _cross_tenant_reason.set(reason)
    try:
        yield
    finally:
        _cross_tenant_reason.reset(token)


def cross_tenant_reason() -> str | None:
    """The declared reason, when inside a cross_tenant block."""
    return _cross_tenant_reason.get()


def check_tenant_write(model: str, value: object) -> object:
    """Refuse a tenant the current request has no business writing.

    Returns the value unchanged when it is allowed, so it can be used directly
    from a SQLAlchemy validator.
    """
    if value is None:
        return value
    if _cross_tenant_reason.get() is not None:
        return value

    actual = current_lab_id.get()
    if actual is None:
        # No request tenant established: a worker, a migration, a test. There
        # is nothing to contradict, so there is nothing to refuse.
        return value

    if value != actual:
        raise CrossTenantWriteRefused(model, value, actual)
    return value
