"""NR-061 — a practitioner is a Person with a licence and a post, not a second person registry.

Seventeen ORM classes in this repository model something called practitioner,
provider, staff, employee, healthcare worker or person. **Four are built**, and
three of those four are homonyms: `fin_providers` is a financial service
provider, `pay_providers` a payment processor, `niam_fed_providers` an OIDC/SAML
identity provider. Exactly one built table represents a natural person:
`niam_persons`.

Everything clinical is unbuilt -- `national_practitioners` (88 foreign-key
references, the single most-depended-on table in the repository),
`national_providers`, `national_employees`, `gov_healthcare_workers`.

The temptation NR-022 creates is to close that gap by building
`national_practitioners`. That would be a mistake, and these tests exist to make
it a loud one. The Identity Platform already models a practitioner, relationally
and fully built:

    niam_persons        who they are
    niam_licenses       ProfessionalLicense -- number, authority, expiry, board
    niam_employments    Employment -- person -> organization, position, dates
    niam_assignments    Assignment -- where they are posted
    niam_role_assignments  what they are permitted to do

`national_practitioners` flattens all of that into one row and carries PII
directly (full_name, date_of_birth, phone, email, national_id_hash), outside the
proofing, assurance and verification governance that surrounds `niam_persons`.

CLAUDE.md states the rule these tests hold: the Identity Platform is the single
trusted identity provider, and no subsystem implements its own.
"""

from __future__ import annotations

import json
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
MIGRATIONS = BACKEND / "migrations" / "versions"

#: The composition that *is* the canonical practitioner. Each must stay built.
CANONICAL_PRACTITIONER_COMPOSITION = {
    "niam_persons": "the natural person",
    "niam_licenses": "professional licence and board certification",
    "niam_employments": "person to organization, with position and dates",
    "niam_assignments": "posting",
    "niam_role_assignments": "what the person may do",
}

#: Person-like tables that must NOT become a second person registry. They may be
#: retired; they may not be built while the composition above is canonical.
#: This ledger may shrink. It may never grow.
DECLARED_RIVAL_PERSON_REGISTRIES = frozenset({
    "national_practitioners",
    "national_providers",
    "national_employees",
    "gov_healthcare_workers",
})


def _created_tables() -> dict[str, list[str]]:
    """Every table built by `op.create_table`, from the committed evidence file.

    Derived by AST from the migration chain — not by searching for the table
    name, which also matches foreign-key references inside migrations and
    reports unbuilt tables as built.
    """
    evidence = BACKEND.parent / "docs" / "architecture" / "evidence-created-tables.json"
    return json.loads(evidence.read_text(encoding="utf-8"))


def test_the_created_table_evidence_is_present_and_plausible() -> None:
    """Guard the guard: a missing or empty evidence file would pass everything."""
    created = _created_tables()
    assert len(created) >= 400, (
        f"only {len(created)} created tables found; the evidence file has drifted "
        "from the migration chain"
    )


def test_the_canonical_practitioner_composition_is_built() -> None:
    """The decision rests on this being real rather than aspirational.

    If any part of the composition stops being migration-backed, "use the
    Identity Platform" stops being an answer and this finding has to be
    re-derived rather than assumed.
    """
    created = _created_tables()
    missing = sorted(t for t in CANONICAL_PRACTITIONER_COMPOSITION if t not in created)
    assert missing == [], (
        "the canonical practitioner composition is no longer fully built, so the "
        f"NR-061 decision no longer stands on its own evidence: {missing}"
    )


def test_no_rival_person_registry_has_been_built() -> None:
    """The one that matters.

    NR-022 records that the most-depended-on tables do not exist. The obvious
    way to "fix" that is to build them. For `national_practitioners` and its
    siblings that would create a second registry of natural persons, with its
    own copy of name, date of birth, phone, email and national ID hash, outside
    the identity governance that covers `niam_persons`.

    Retiring these is fine. Building one is a decision about where personal data
    lives, and it fails here rather than arriving in a migration.
    """
    created = _created_tables()
    built_rivals = sorted(t for t in DECLARED_RIVAL_PERSON_REGISTRIES if t in created)
    assert built_rivals == [], (
        "a rival registry of natural persons has been built. A practitioner is a "
        "Person (niam_persons) holding a ProfessionalLicense (niam_licenses) and "
        "an Employment (niam_employments); building these duplicates personal "
        f"data outside identity governance: {built_rivals}"
    )


def test_the_rival_ledger_does_not_rot() -> None:
    """An entry that no longer names a real ORM table should be deleted.

    Otherwise the ledger becomes a list of things that used to be true, and the
    test above starts guarding nothing.
    """
    import ast

    declared_in_orm: set[str] = set()
    for path in (BACKEND / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for stmt in node.body:
                if not isinstance(stmt, ast.Assign):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target, ast.Name)
                        and target.id == "__tablename__"
                        and isinstance(stmt.value, ast.Constant)
                        and stmt.value.value in DECLARED_RIVAL_PERSON_REGISTRIES
                    ):
                        declared_in_orm.add(stmt.value.value)

    stale = sorted(DECLARED_RIVAL_PERSON_REGISTRIES - declared_in_orm)
    assert stale == [], (
        f"these ledger entries no longer name an ORM table; remove them: {stale}"
    )


# ---------------------------------------------------------------------------
# Unit 2 — the composition proved column by column.
#
# "Compose from Person" is only an answer if the composition actually holds what
# the rival table holds. So every column of `national_practitioners` is mapped
# to a real column of a real built composition table, or declared a gap. Mapped
# by hand rather than by name similarity: `date_of_birth` lives as `birth_date`,
# `qualification` as `degree_name`, `role` as an assignment's `role_id`. A
# name-matching heuristic would have called those four gaps and this one
# coverage, and both errors change the decision.
# ---------------------------------------------------------------------------

#: national_practitioners column -> (composition table, column that holds it).
PRACTITIONER_COLUMN_HOMES = {
    "role": ("niam_assignments", "role_id"),
    "full_name": ("niam_persons", "family_name"),
    "full_name_ar": ("niam_persons", "full_name_ar"),
    "date_of_birth": ("niam_persons", "birth_date"),
    "gender": ("niam_persons", "gender"),
    "nationality": ("niam_persons", "nationality"),
    "national_id_hash": ("niam_persons", "national_id_hash"),
    "phone": ("niam_persons", "phone"),
    "email": ("niam_persons", "email"),
    "is_active": ("niam_persons", "is_active"),
    "license_number": ("niam_licenses", "license_number"),
    "qualification": ("niam_licenses", "degree_name"),
    "is_verified": ("niam_licenses", "verified"),
    "organization_id": ("niam_employments", "organization_id"),
    "facility_id": ("niam_assignments", "facility_id"),
}

#: Columns the composition genuinely does not hold. Each is additive to an
#: existing table -- none of them needs a new registry of natural persons, which
#: is the whole point. This ledger may shrink. It may never grow.
DECLARED_COMPOSITION_GAPS = {
    "specialty": "clinical scope of practice; belongs on niam_licenses",
    "sub_specialty": "as above",
    "health_profession_number": "profession-registry identifier; belongs on niam_licenses",
    "available_for_telehealth": "a practice attribute, needed only once a "
                               "practitioner-facing feature is reachable",
    "signature_url": "the clinical signature; belongs with the licence it signs under",
    "photo_url": "person-scoped, not practitioner-scoped",
}


def _table_columns() -> dict[str, set[str]]:
    """table name -> declared Column attribute names, by AST."""
    import ast

    columns: dict[str, set[str]] = {}
    for path in (BACKEND / "app").rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for cls in (n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)):
            table = None
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            table = stmt.value.value
            if table is None:
                continue
            for stmt in cls.body:
                if (
                    isinstance(stmt, ast.Assign)
                    and isinstance(stmt.value, ast.Call)
                    and getattr(stmt.value.func, "id", None) == "Column"
                ):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name):
                            columns.setdefault(table, set()).add(target.id)
    return columns


def test_every_practitioner_column_is_mapped_or_declared_a_gap() -> None:
    """No column may quietly have nowhere to go.

    An unmapped column is the argument for building `national_practitioners`
    arriving by the back door: "the composition does not hold X, so we need the
    table." Either it maps, or it is named as a gap with the table it is
    additive to.
    """
    columns = _table_columns()
    practitioner = columns.get("national_practitioners", set())
    assert practitioner, "national_practitioners no longer declares any columns"
    unmapped = sorted(
        practitioner - set(PRACTITIONER_COLUMN_HOMES) - set(DECLARED_COMPOSITION_GAPS)
    )
    assert unmapped == [], (
        "these national_practitioners columns have no home in the canonical "
        "composition and are not declared gaps. Map each to a composition "
        f"column or declare it, rather than building the table: {unmapped}"
    )


def test_every_mapped_home_still_exists_in_the_composition() -> None:
    """The mapping is evidence only while its targets are real.

    A renamed or dropped NIAM column would silently turn coverage into a gap,
    and the decision would keep citing a table that no longer holds the data.
    """
    columns = _table_columns()
    broken = sorted(
        (source, table, column)
        for source, (table, column) in PRACTITIONER_COLUMN_HOMES.items()
        if column not in columns.get(table, set())
    )
    assert broken == [], (
        "these mappings name a composition column that no longer exists "
        f"(practitioner column, table, missing column): {broken}"
    )
