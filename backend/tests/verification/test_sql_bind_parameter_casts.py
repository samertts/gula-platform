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


def test_sqlalchemy_really_does_mangle_the_inline_form():
    """The positive control.

    Without this, the sweep below could pass because the pattern never occurs
    OR because the premise is wrong. This asserts the premise directly, so a
    future SQLAlchemy that fixes the parse makes THIS test fail rather than
    leaving a now-pointless ban in place.
    """
    mangled = sorted(text("SELECT :payload::jsonb")._bindparams)
    assert mangled == ["payloa"], (
        "SQLAlchemy no longer truncates an inline-cast parameter name "
        f"(got {mangled}); re-evaluate whether this ban is still needed"
    )
    # And the replacement form is correct.
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
