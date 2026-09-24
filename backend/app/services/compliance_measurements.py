"""Measured facts for the government compliance reports.

`/compliance/security-report` and `/compliance/system-status` describe
themselves as reports for government and ISO 27001 auditors. NR-090 found two
of their statements outright false. This module exists for the rest of them:
23 verdicts that were string literals no code computed, so nothing failed when
the system they described changed.

The classification, per §32-D of the operating brief. A verdict is one of:

``MEASURED_PASS`` / ``MEASURED_FAIL``
    The process checked the thing itself, now, and reports what it found.
``DERIVED_PASS``
    Read off configuration or code this process owns. Weaker than measured --
    it confirms intent, not effect.
``UNOBSERVABLE``
    True or false depending on nginx, the TLS terminator, the container runtime
    or the deployment. This process cannot see it. **Naming what would have to
    be checked is the honest answer; PASS is not.**
``ENFORCED_BY_GATE``
    A platform-wide invariant held by a CI guard rather than by a runtime
    check. The report says which guard, so an auditor can ask for its output
    instead of taking the sentence on trust.

The rule that matters: **UNOBSERVABLE never becomes PASS.** An auditor reading
"PASS - HTTPS/TLS via nginx" is being told this system verified something it
has no way to verify.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger("gula.compliance.measure")

#: Triggers that make audit_logs append-only. Named so the report can say which
#: are missing rather than only that something is.
_AUDIT_IMMUTABILITY_TRIGGERS = ("trg_audit_logs_no_update", "trg_audit_logs_no_delete")


def audit_immutability(db: Session) -> str:
    """Query the database for the triggers that block UPDATE and DELETE.

    This is the strongest verdict in either report: the claim is about a
    database object, and the database is asked. Previously it read
    "PASS - PostgreSQL trigger blocks UPDATE/DELETE" whether or not the
    triggers existed -- and on SQLite, where the report also runs, they cannot.
    """
    try:
        rows = db.execute(
            text(
                """
                SELECT t.tgname
                FROM pg_trigger t
                JOIN pg_class c ON c.oid = t.tgrelid
                WHERE c.relname = 'audit_logs' AND NOT t.tgisinternal
                """,
            ),
        ).fetchall()
    except Exception as exc:  # non-PostgreSQL, or no permission on the catalog
        logger.warning("[COMPLIANCE] could not read audit triggers: %s", exc)
        return (
            "UNOBSERVABLE - the audit trigger catalogue could not be read on "
            "this backend; verify on the PostgreSQL primary"
        )

    present = {row[0] for row in rows}
    missing = [name for name in _AUDIT_IMMUTABILITY_TRIGGERS if name not in present]
    if missing:
        return (
            f"MEASURED_FAIL - audit_logs is NOT append-only: {', '.join(missing)} "
            "absent. Rows can be updated or deleted."
        )
    return (
        "MEASURED_PASS - "
        f"{', '.join(sorted(present & set(_AUDIT_IMMUTABILITY_TRIGGERS)))} "
        "present on audit_logs"
    )


def middleware_verdict(app: Any, class_name: str, label: str) -> str:
    """Whether a middleware is actually in the running stack.

    `app.user_middleware` is what Starlette will build the chain from, so this
    reports the stack that exists rather than the one factory.py intends.
    """
    try:
        installed = {m.cls.__name__ for m in app.user_middleware}
    except Exception as exc:
        logger.warning("[COMPLIANCE] could not inspect middleware: %s", exc)
        return f"UNOBSERVABLE - middleware stack not inspectable ({label})"
    if class_name in installed:
        return f"MEASURED_PASS - {label} ({class_name} is in the running stack)"
    return f"MEASURED_FAIL - {class_name} is NOT installed, so {label} is not enforced"


def unobservable(control: str, where: str) -> str:
    """A control this process cannot see, named together with where it lives."""
    return f"UNOBSERVABLE - {control}; enforced in {where}, verify there"


def enforced_by_gate(invariant: str, guard: str) -> str:
    """A platform-wide invariant held by a CI guard rather than a runtime check.

    Deliberately not PASS. The guard runs in CI, not in this process, and it
    constrains the code rather than observing this request. An auditor should
    ask for the guard's output.
    """
    return f"ENFORCED_BY_GATE - {invariant}; held by {guard}, not verified at request time"
