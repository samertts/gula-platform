"""requirements-lock.txt must be able to build a working environment (NR-008).

The lock file is what a reproducible deploy installs. When it is missing a
package that requirements.txt declares, a lock-only environment imports a
module that is not there -- and the failure surfaces at request time, in the
one path nobody exercises locally.

MEASURED, and the register's count was wrong. NR-008 recorded one gap,
signxml. There were two, with different dispositions, and signxml's own
transitive lxml was missing as well, so locking signxml alone would not have
fixed it:

  signxml  DECLARED, UNLOCKED, AND IMPORTED. app/security/saml_service.py
           imports signxml.algorithms, signxml.exceptions and signxml.verifier
           at module level, so a lock-only environment cannot import that
           module at all -- and POST /auth/saml/acs is one of the twenty-one
           endpoints NR-108 declared reachable without a credential. Fixed:
           signxml==5.1.0 and its unlocked runtime dependency lxml==6.1.3.

  psycopg  DECLARED, UNLOCKED, AND NEVER IMPORTED. requirements.txt asks for
           psycopg[binary]>=3.3.4,<4.0.0, but nothing in app/ imports psycopg,
           and no configuration anywhere uses the postgresql+psycopg:// URL
           scheme -- psycopg2-binary is the real driver, and it is both
           declared and locked. Locking an unused driver would add a binary
           wheel to every image to satisfy a declaration that is probably the
           actual mistake. Which of the two to remove is a dependency
           decision, so it is DECLARED here rather than guessed at.

Two further runtime dependencies were unlocked and unrelated to either --
annotated-doc (fastapi) and typing-inspection (fastapi, pydantic,
pydantic-settings). Both are now pinned. They were found by the transitive
check below, not by the top-level one, which is the point of having it.
"""
from __future__ import annotations

import importlib.metadata as md
import re
from pathlib import Path

import pytest
from packaging.requirements import Requirement

_BACKEND = Path(__file__).resolve().parents[1]
_DECLARED = _BACKEND / "requirements.txt"
_LOCKED = _BACKEND / "requirements-lock.txt"

#: Declared but deliberately NOT locked. SHRINK-ONLY: an entry leaves when the
#: dependency decision is made, in either direction. A new unlocked
#: declaration is NR-008 again and fails the test below.
DECLARED_UNLOCKED: dict[str, str] = {
    "psycopg": (
        "psycopg[binary]>=3.3.4,<4.0.0 is declared and never imported: no "
        "`import psycopg` anywhere in app/, and no postgresql+psycopg:// URL "
        "in any config. psycopg2-binary is the driver actually in use and is "
        "both declared and locked. Locking this would ship a binary wheel to "
        "satisfy a declaration that is more likely the error. Removing a "
        "declared dependency is a call for a human."
    ),
}

_UNLOCKED_CEILING = 1

#: Floors, so a parser that stops parsing cannot pass by finding nothing.
_MINIMUM_DECLARED = 25
_MINIMUM_LOCKED = 70


def _parse(path: Path) -> dict[str, str]:
    """Distribution name -> the line that declared it."""
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        match = re.match(r"^([A-Za-z0-9._-]+)", line)
        if match:
            out[match.group(1).lower().replace("_", "-")] = raw.strip()
    return out


def test_the_parser_still_reads_both_files() -> None:
    """Guard the guard, in both directions."""
    declared, locked = _parse(_DECLARED), _parse(_LOCKED)
    assert len(declared) >= _MINIMUM_DECLARED, (
        f"only {len(declared)} requirements parsed from requirements.txt; the "
        f"parser has drifted from the file format and every assertion below "
        f"is vacuous"
    )
    assert len(locked) >= _MINIMUM_LOCKED, (
        f"only {len(locked)} pins parsed from requirements-lock.txt; same "
        f"problem, in the direction that makes everything look unlocked"
    )
    assert all("==" in line for line in locked.values()), (
        "a lock entry is not pinned with ==, so the lock does not lock"
    )


def test_every_declared_requirement_is_locked() -> None:
    declared, locked = _parse(_DECLARED), _parse(_LOCKED)
    missing = sorted(set(declared) - set(locked) - set(DECLARED_UNLOCKED))
    assert not missing, (
        "these packages are declared in requirements.txt and absent from "
        "requirements-lock.txt, so a lock-only environment cannot import "
        "whatever uses them:\n"
        + "\n".join(f"  {name}: {declared[name]}" for name in missing)
    )


def test_the_lock_contains_the_runtime_closure() -> None:
    """A lock that pins a package but not what it imports is not a lock.

    This is what caught lxml: signxml was the visible gap, and pinning it
    alone would still have produced an environment that could not install.
    Environment markers are evaluated, so Windows-only and old-Python
    conditionals do not count as gaps.
    """
    declared, locked = _parse(_DECLARED), _parse(_LOCKED)
    checked = 0
    missing: dict[str, list[str]] = {}
    for name in sorted(set(declared) | set(locked)):
        try:
            dist = md.distribution(name)
        except md.PackageNotFoundError:
            continue        # not installed in this environment; cannot judge
        checked += 1
        for spec in dist.requires or []:
            try:
                requirement = Requirement(spec)
            except Exception:
                continue
            if requirement.marker is not None and not requirement.marker.evaluate(
                {"extra": ""},
            ):
                continue    # optional extra, or false on this platform
            dep = requirement.name.lower().replace("_", "-")
            if dep not in locked and dep not in DECLARED_UNLOCKED:
                missing.setdefault(dep, []).append(name)
    assert checked >= _MINIMUM_DECLARED, (
        f"only {checked} of the declared and locked packages are installed "
        f"here, so this check saw almost nothing and proves almost nothing"
    )
    assert not missing, (
        "these are runtime dependencies of locked packages and are themselves "
        "unlocked, so the lock cannot reproduce the environment:\n"
        + "\n".join(f"  {dep} <- required by {sorted(set(parents))}"
                    for dep, parents in sorted(missing.items()))
    )


def test_the_unlocked_ledger_cannot_grow() -> None:
    assert len(DECLARED_UNLOCKED) <= _UNLOCKED_CEILING, (
        f"DECLARED_UNLOCKED has {len(DECLARED_UNLOCKED)} entries, above the "
        f"ceiling of {_UNLOCKED_CEILING}. It may only shrink: a newly "
        f"unlocked declaration is the defect, not a new exemption."
    )


def test_the_unlocked_ledger_has_not_rotted() -> None:
    declared, locked = _parse(_DECLARED), _parse(_LOCKED)
    gone = sorted(name for name in DECLARED_UNLOCKED if name not in declared)
    assert not gone, (
        f"these are in DECLARED_UNLOCKED but no longer declared in "
        f"requirements.txt: {gone}. The decision was made -- remove them."
    )
    now_locked = sorted(name for name in DECLARED_UNLOCKED if name in locked)
    assert not now_locked, (
        f"these are in DECLARED_UNLOCKED but now appear in the lock: "
        f"{now_locked}. The decision was made the other way -- remove them."
    )


def test_the_saml_module_imports(monkeypatch: pytest.MonkeyPatch) -> None:
    """The consequence NR-008 actually had, asserted directly.

    app/security/saml_service.py imports signxml at module level. With signxml
    absent this raises ImportError and every route in that module is dead.
    """
    import importlib

    module = importlib.import_module("app.security.saml_service")
    assert module is not None
    # And the dependency it needs is genuinely resolvable, not merely named.
    assert md.version("signxml")
    assert md.version("lxml")
