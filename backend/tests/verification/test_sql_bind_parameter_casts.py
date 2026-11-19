"""An inline ``:param::type`` cast silently renames the bind parameter.

SQLAlchemy's ``text()`` parser consumes the last character of the parameter name
into the cast, so the value the caller supplies never reaches the statement.
Measured on every name the repository actually used::

    intended       SQLAlchemy binds
    caps        -> cap
    cfg         -> cf
    metrics     -> metric
    meta        -> met
    vec         -> ve
    filter_json -> filter_jso

Nothing raises at import time and nothing is flagged by a linter.  What happens
instead is that the statement arrives at PostgreSQL with a literal ``:`` in it
and fails at execution -- and in all three places this occurred the failure was
caught and logged at WARNING, so three AI subsystems were silently
non-functional:

* ``ai_model_registry``  -- 0 rows; the model registry had never once persisted
* ``ai_evaluations``     -- 0 rows; every evaluation record discarded
* ``ai_embeddings`` and ``ai_conversations`` -- writes discarded, and the vector
  similarity SELECTs affected too, since ``:vec::vector`` appears in the query
  path as well as the write path

``CAST(:param AS type)`` parses the name correctly and is portable.  This file
is the standing detector, because the defect is invisible by construction: it
cannot be found by reading the SQL, only by asking SQLAlchemy what it parsed.
"""

from __future__ import annotations

import pathlib
import re

from sqlalchemy import text

# Matches an inline PostgreSQL cast applied directly to a bind parameter.
_INLINE_CAST = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)::([a-zA-Z_][a-zA-Z0-9_]*)")

_ROOTS = (
    pathlib.Path(__file__).resolve().parents[2] / "app",
    pathlib.Path(__file__).resolve().parents[3] / "services",
    pathlib.Path(__file__).resolve().parents[3] / "scripts",
)


def _installed_sqlalchemy() -> tuple[int, int]:
    import sqlalchemy

    major, minor = sqlalchemy.__version__.split(".")[:2]
    return int(major), int(minor)


def _declared_floor() -> tuple[int, int]:
    """The oldest SQLAlchemy a deployment may legitimately install.

    Read from requirements.txt rather than assumed, because that is the file
    the production Dockerfile installs.
    """
    requirements = (
        pathlib.Path(__file__).resolve().parents[2] / "requirements.txt"
    ).read_text()
    match = re.search(r"^sqlalchemy(?:\[[^\]]*\])?\s*>=\s*(\d+)\.(\d+)", requirements, re.MULTILINE | re.IGNORECASE)
    assert match, "positive control: requirements.txt declares a sqlalchemy floor"
    return int(match.group(1)), int(match.group(2))


def test_the_premise_behind_the_ban_is_still_measured():
    """The positive control, and it had to be re-measured rather than asserted.

    As originally written this asserted unconditionally that
    ``text("SELECT :payload::jsonb")`` binds ``["payloa"]`` — SQLAlchemy
    consuming the first ``:`` of ``::`` and truncating the name. That was true
    and is the whole reason for the ban below.

    **SQLAlchemy 2.1 changed it.** Under 2.1.4 the same expression binds
    nothing at all, so the original assertion fails — correctly, which is what
    a premise check is for: it caught an upstream change instead of leaving a
    ban standing on a reason that had evaporated.

    The ban nevertheless stays, and unconditionally, because
    ``requirements.txt`` declares a *floor* (``sqlalchemy[asyncio]>=2.0.51``)
    and not a ceiling. A deployment is free to install 2.0.x, where the form
    silently loses its value. The same source must be correct on every version
    the project admits, so this test asserts the premise on versions where it
    holds and, on newer ones, asserts that the floor still admits a version
    where it does — which is what keeps the ban load-bearing.
    """
    installed = _installed_sqlalchemy()
    mangled = sorted(text("SELECT :payload::jsonb")._bindparams)

    if installed < (2, 1):
        assert mangled == ["payloa"], (
            f"SQLAlchemy {installed} no longer truncates an inline-cast "
            f"parameter name (got {mangled}) even below 2.1; re-read IA-084 "
            f"before relaxing anything."
        )
    else:
        assert mangled != ["payload"], (
            f"SQLAlchemy {installed} now binds the inline-cast form correctly "
            f"(got {mangled}). If that holds at the declared floor too, the "
            f"ban below is obsolete and should be retired deliberately."
        )
        floor = _declared_floor()
        assert floor < (2, 1), (
            f"the declared floor is now {floor}, at or above the version that "
            f"stopped mangling, so the ban's premise no longer applies to any "
            f"admitted version. Retire the ban deliberately, or keep it with a "
            f"new reason — do not leave this test asserting a dead premise."
        )

    # The replacement form is correct on every version. Unconditional.
    assert sorted(text("SELECT CAST(:payload AS jsonb)")._bindparams) == ["payload"]


def test_no_source_file_uses_an_inline_bind_parameter_cast():
    """The sweep. Any occurrence is a statement whose value never arrives."""
    offenders: list[str] = []
    scanned = 0
    for root in _ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            scanned += 1
            for lineno, line in enumerate(path.read_text().splitlines(), 1):
                for match in _INLINE_CAST.finditer(line):
                    intended = match.group(1)
                    parsed = sorted(text(f"SELECT :{intended}::{match.group(2)}")._bindparams)
                    offenders.append(
                        f"{path}:{lineno}: :{intended}::{match.group(2)} "
                        f"binds {parsed} instead of ['{intended}']"
                    )

    # Guard the guard: a sweep over nothing passes vacuously.
    assert scanned > 500, f"only {scanned} files scanned; the sweep is not covering the tree"
    assert offenders == [], (
        "inline bind-parameter casts found -- the supplied value never reaches "
        "the statement, and the failure is usually swallowed:\n  "
        + "\n  ".join(offenders)
    )
