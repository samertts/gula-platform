"""SQLAlchemy must be able to configure every mapper the application registers.

``configure_mappers()`` is all-or-nothing. One unresolvable ``relationship()``
string makes it raise, and it raises again on *every* later attempt, so the first
bad declaration takes down every endpoint that touches the ORM afterwards — not
only the module that owns it.

``app/nhdw/models.py`` declared 22 relationships to classes owned by other
declarative bases: ``Patient`` (on the main ``Base``) and ``HospitalMaster``,
``HospitalDepartment``, ``Room``, ``Bed`` and ``Clinic`` (on the hospital base).
A relationship() string is resolved inside the declaring class's own registry, so
none of them could ever resolve. They were removed rather than rewritten: nothing
read the attributes, and ``app/nhdw/services.py`` and ``kpi.py`` already import
and query those models directly, which is the pattern that works across bases.

The second test is the durable guard — it is what stops the next cross-base
relationship from being added, since the failure is invisible until something
calls into the ORM.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

APP = pathlib.Path(__file__).resolve().parents[2] / "app"


def test_configure_mappers_succeeds() -> None:
    """The whole mapped surface must configure, or nothing using the ORM works."""
    import app.main  # registers every mapped class
    from sqlalchemy.orm import configure_mappers

    try:
        configure_mappers()
    except Exception as exc:  # pragma: no cover - the assertion message is the point
        pytest.fail(f"configure_mappers() failed, so every ORM endpoint is broken: {exc}")


def _declared_classes(module: pathlib.Path) -> set[str]:
    try:
        tree = ast.parse(module.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    return {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}


# Modules that own a declarative base of their own. A relationship() inside one of
# these may only name a class the same module declares; anything else is resolved
# in the wrong registry and cannot be found.
OWN_BASE_MODULES = (
    "nhdw/models.py",
    "radiology/models.py",
    "nursing/models.py",
)


def test_no_relationship_names_a_class_from_another_declarative_base() -> None:
    offences: list[str] = []
    for relative in OWN_BASE_MODULES:
        module = APP / relative
        if not module.exists():
            continue
        local = _declared_classes(module)
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            for stmt in cls.body:
                if not (isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call)):
                    continue
                fn = stmt.value.func
                name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
                if name != "relationship" or not stmt.value.args:
                    continue
                target = stmt.value.args[0]
                if (
                    isinstance(target, ast.Constant)
                    and isinstance(target.value, str)
                    and target.value not in local
                ):
                    attr = getattr(stmt.targets[0], "id", "?")
                    offences.append(
                        f"app/{relative}:{stmt.lineno} {cls.name}.{attr} -> "
                        f"'{target.value}' is not declared in this module's registry"
                    )
    assert not offences, (
        "relationship() cannot resolve a class from another declarative base; these make "
        "configure_mappers() fail, which breaks every ORM endpoint:\n  "
        + "\n  ".join(offences)
    )
