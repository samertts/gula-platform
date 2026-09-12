"""NR-022 — the Stable Core is five built concepts, and nothing depends downward.

The Stable Core map recommends a deliberately small Core: Account, Person,
Organization, Facility, Tenant. Small because every rule in that map has to hold
for everything in it, and a Core that grows is not a Core.

Two of its claims are mechanical and are held here rather than left as prose.

**Every Core concept is built.** The Core is the built one on purpose. The whole
of NR-022 is that the platform runs on one Core while 263 foreign keys name
another; a Core concept that stopped being migration-backed would put the
recommendation on the wrong side of its own finding.

**Nothing in the Core depends on a domain.** Domains reference Core; Core never
references a domain. `labs`, `niam_persons` and `national_facilities` declare no
outbound foreign key at all. `niam_accounts` references `niam_identities` and
`niam_organizations` references itself -- both inside the Identity Platform,
which is the substrate the Core sits on, not a domain above it. That distinction
is the rule, and it is why this file allows `niam_*` rather than demanding zero.

What is deliberately NOT here: Patient, Citizen, Practitioner and Encounter. The
approved NR-022 decision rejects a universal data subject -- Person is the
canonical national subject and Patient and Citizen are contextual roles -- and
NR-061 showed a practitioner composes from Person plus a licence plus a post
rather than needing a table. None of them belongs in a five-concept identity
Core, and `test_subject_reference_semantics.py` holds their classification.
"""

from __future__ import annotations

import ast
import pathlib

# NR-069. `built_tables()` derives from the migration chain. Reading
# `evidence-created-tables.json` directly is how three tables created through a
# migration helper were treated as unbuilt; one source of truth, derived.
from tests.orm_resolution import built_tables

BACKEND = pathlib.Path(__file__).resolve().parents[1]
APP = BACKEND / "app"

#: The Stable Core: table -> the module that owns it. Both halves are asserted,
#: because a Core concept quietly re-homed is as much a drift as one dropped.
STABLE_CORE = {
    "niam_accounts": "app/identity/models/account.py",
    "niam_persons": "app/identity/models/person.py",
    "niam_organizations": "app/identity/models/niam_organization.py",
    "national_facilities": "app/models/clinical_scope.py",
    "labs": "app/models/lab.py",
}

#: The Identity Platform substrate. A Core table may reference these; they are
#: not domains. Anything else referenced from the Core inverts the dependency.
_SUBSTRATE_PREFIX = "niam_"


def _core_owners() -> dict[str, list[tuple[str, list[str]]]]:
    """Core table -> [(owning module, outbound FK target tables)] for every owner."""
    found: dict[str, list[tuple[str, list[str]]]] = {t: [] for t in STABLE_CORE}
    for path in APP.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        module = str(path.relative_to(BACKEND))
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            table = None
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            table = stmt.value.value
            if table not in STABLE_CORE:
                continue
            targets = [
                node.args[0].value.split(".")[0]
                for node in ast.walk(cls)
                if isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "ForeignKey"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
            ]
            found[table].append((module, sorted(set(targets))))
    return found


def test_every_stable_core_table_is_built() -> None:
    """The Core is the built one, which is the entire point of choosing it."""
    built = set(built_tables())
    missing = sorted(t for t in STABLE_CORE if t not in built)
    assert missing == [], (
        "these Stable Core tables are no longer created by any migration, so the "
        "Core would be as unbuilt as the National Core it was chosen over: "
        f"{missing}"
    )


def test_each_core_concept_has_exactly_one_orm_owner() -> None:
    """Two owners of a Core table is two answers to who a person is."""
    owners = _core_owners()
    wrong = {
        table: [m for m, _ in found]
        for table, found in owners.items()
        if len(found) != 1
    }
    assert wrong == {}, (
        "every Stable Core table must be mapped by exactly one ORM class. "
        f"These are mapped zero times or more than once: {wrong}"
    )


def test_the_core_owner_modules_are_where_the_map_says() -> None:
    """A Core concept re-homed silently makes the map describe another repo."""
    owners = _core_owners()
    moved = {
        table: (declared, found[0][0])
        for table, declared in STABLE_CORE.items()
        if (found := owners[table]) and found[0][0] != declared
    }
    assert moved == {}, (
        f"Stable Core owners moved (declared -> now): {moved}"
    )


def test_the_core_never_depends_on_a_domain_table() -> None:
    """Domains reference Core. Core never references a domain.

    A Core table with a foreign key into a domain would make the domain a
    precondition for identity, which is the inversion the map exists to prevent.
    References within the Core, and into the Identity Platform substrate it sits
    on, are not that.
    """
    inverted = sorted(
        (table, module, target)
        for table, found in _core_owners().items()
        for module, targets in found
        for target in targets
        if target not in STABLE_CORE and not target.startswith(_SUBSTRATE_PREFIX)
    )
    assert inverted == [], (
        "these Stable Core tables reference a table outside the Core and outside "
        "the Identity Platform, inverting the dependency direction "
        f"(core table, module, target): {inverted}"
    )
