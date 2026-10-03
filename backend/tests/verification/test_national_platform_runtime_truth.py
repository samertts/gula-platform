"""What the seven registered national platform routers actually do at runtime.

IA-057. All seven are registered in app/factory.py, all seven declare
SQLAlchemy repositories, and none of their 42 tables is created by any of the
102 migrations. That is where the previous cycle stopped. This executes them.

Two architectures, not one -- which is why "schema-latent" is the wrong single
label for all seven:

  A. rules_engine, document_platform, background_platform, observability,
     scheduling_platform
     Router-level dependencies=[Depends(require_permission("system:admin"))].
     Service built per-request from Depends(get_db), a sync Session.
     Zero `async with SessionLocal` sites. These reach SQL and fail only
     because the table is absent.

  B. task_engine, workflow_runtime
     No router-level dependency; get_current_user per route (29 and 22 times).
     Service built by `_get_service()` with NO database argument, from
     repositories that do `async with SessionLocal() as session:` and
     `await session.get(...)` -- 7 and 13 sites. app.database.SessionLocal is
     a sync `sessionmaker`; its Session has no __aenter__ and `get` is not a
     coroutine function. These fail BEFORE any SQL is emitted, so supplying
     the missing tables would not make them work.

Both files are byte-identical on claude/independent-audit-1 and
claude/autonomous-run-1.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

from tests.conftest import auth_headers

# (package, method, path, table the handler reads)
GROUP_A = [
    ("rules_engine",         "GET", "/national/rules/",                   "national_rules"),
    ("document_platform",    "GET", "/national/documents/",               "national_documents"),
    ("background_platform",  "GET", "/national/jobs/",                    "national_background_jobs"),
    ("observability",        "GET", "/national/observability/dashboards", "national_observability_dashboards"),
    ("scheduling_platform",  "GET", "/national/scheduling/appointments",  "national_scheduling_appointments"),
]

GROUP_B = [
    ("task_engine",      "GET", "/national/tasks/"),
    ("workflow_runtime", "GET", "/national/workflows/definitions"),
]


@pytest.fixture()
def admin(db, make_lab, make_lab_user, client):
    # role="master_admin": measured, not guessed. system:admin appears in
    # shared.rbac.permissions.EXTENDED_ALL_PERMISSIONS (a catalogue) and is
    # granted by exactly one of the 23 roles -- EXTENDED_ROLE_PERMISSIONS
    # ["master_admin"]. A lab "admin" gets 403 "Permission required:
    # system:admin", which is the authorization layer doing its job.
    """A real persisted admin. A synthetic token is rejected 401 by design --
    `get_current_user` resolves the subject against lab_users, which is the
    first thing this probe established and is why it seeds instead."""
    lab = make_lab()
    user = make_lab_user(lab_id=lab.id, role="master_admin")
    db.flush()
    return auth_headers(user_id=user.id, lab_id=lab.id, role="master_admin")


def _drop(session, table: str) -> None:
    """Drop on the request's own connection.

    A second connection via engine.begin() deadlocks the SQLite harness
    ("database is locked") because the savepoint connection holds the file.
    The savepoint rolls the DDL back when the test ends, so nothing leaks.
    """
    session.execute(text(f"DROP TABLE IF EXISTS {table}"))
    session.flush()


@pytest.mark.parametrize("package,method,path,table", GROUP_A, ids=[g[0] for g in GROUP_A])
def test_group_a_route_outcome_with_its_table_absent(client, db, admin, package, method, path, table):
    """Record the real status code when the table no migration creates is absent."""
    _drop(db, table)
    try:
        response = client.request(method, path, headers=admin)
    except Exception as exc:   # raise_server_exceptions=True surfaces the 500 as an exception
        print(f"\n{package:22s} {method} {path} -> raised {type(exc).__name__}: {str(exc)[:160]}")
        return
    print(f"\n{package:22s} {method} {path} -> {response.status_code} {response.text[:160]}")


@pytest.mark.parametrize("package,method,path", GROUP_B, ids=[g[0] for g in GROUP_B])
def test_group_b_route_outcome_with_its_table_present(client, admin, package, method, path):
    """Table present. Any failure here is the async/sync defect, not the schema."""
    try:
        response = client.request(method, path, headers=admin)
    except Exception as exc:
        print(f"\n{package:22s} {method} {path} -> raised {type(exc).__name__}: {str(exc)[:200]}")
        return
    print(f"\n{package:22s} {method} {path} -> {response.status_code} {response.text[:200]}")


def test_sessionlocal_is_sync_so_group_b_cannot_reach_sql():
    """The static half of the Group B claim, asserted rather than described."""
    from app.database import SessionLocal
    import inspect

    session = SessionLocal()
    try:
        assert not hasattr(session, "__aenter__"), (
            "SessionLocal now yields an async session; re-measure Group B"
        )
        assert hasattr(session, "__enter__")
        assert not inspect.iscoroutinefunction(session.get)
    finally:
        session.close()


def test_group_b_repositories_really_use_the_async_protocol_on_it():
    """If these sites were repaired, the Group B finding would be stale."""
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2] / "app" / "national"
    counts = {
        name: (root / name / "infrastructure" / "repository.py").read_text().count("async with SessionLocal")
        for name in ("task_engine", "workflow_runtime")
    }
    assert counts["task_engine"] > 0 and counts["workflow_runtime"] > 0, (
        f"the async-with-sync-sessionmaker sites are gone: {counts} -- re-run the runtime probe"
    )
    print(f"\nasync-with-SessionLocal sites: {counts}")
