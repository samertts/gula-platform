"""Guards for the BATCH-2.5 identity findings.

These do not fix anything. They pin measured facts so a regression — or a
silent resolution nobody recorded — fails loudly instead of drifting.

Full evidence: docs/enterprise-readiness/GULA_NATIONAL_CORE_IDENTITY_CONTRACT.md
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP = REPO_ROOT / "backend" / "app"
MIGRATIONS = REPO_ROOT / "backend" / "migrations" / "versions"

# The two different bodies that share the name `_ulid()` in this repository.
_TRUNCATED_UUID4 = "return str(uuid.uuid4()).replace('-', '').upper()[:26]"
_REAL_ULID_MARKER = "_CROCKFORD"


def _python_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _ulid_definitions() -> dict[str, str]:
    found: dict[str, str] = {}
    for path in _python_files(REPO_ROOT / "backend"):
        source = path.read_text(encoding="utf-8", errors="ignore")
        if "def _ulid" not in source:
            continue
        for node in ast.walk(ast.parse(source, filename=str(path))):
            if isinstance(node, ast.FunctionDef) and node.name == "_ulid":
                found[f"{path.relative_to(REPO_ROOT)}:{node.lineno}"] = ast.unparse(node)
    return found


# --- NR-025: one name, two incompatible identifier schemes -------------------


def test_two_incompatible_implementations_share_the_name_ulid() -> None:
    """NR-025.

    Fifteen functions are called `_ulid()` and they do two different things:

    * 13 return ``str(uuid.uuid4()).replace('-', '').upper()[:26]`` — the first
      26 hex characters of a random UUID4. Not a ULID: no timestamp prefix, no
      Crockford base32, no time ordering. Full 26-byte key cost, none of the
      benefit.
    * 2 are genuine ULIDs — 48-bit millisecond timestamp plus 80 random bits,
      Crockford base32, time-sortable.

    So identifiers generated under one name are not mutually ordered, and a call
    site does not reveal which scheme it gets. Every declarative base — the ones
    that actually mint primary keys — uses the *fake* one; the real one is
    confined to two services.
    """
    definitions = _ulid_definitions()
    truncated = {k for k, v in definitions.items() if _TRUNCATED_UUID4 in v}
    genuine = {k for k, v in definitions.items() if _REAL_ULID_MARKER in v}

    assert truncated | genuine == set(definitions), (
        "an _ulid() appeared that is neither of the two known implementations: "
        f"{sorted(set(definitions) - truncated - genuine)}"
    )
    assert len(truncated) == 13, (
        f"{len(truncated)} truncated-UUID4 _ulid() definitions (was 13). "
        "Update NR-025 rather than the number."
    )
    assert len(genuine) == 2, (
        f"{len(genuine)} genuine ULID _ulid() definitions (was 2). "
        "Update NR-025 rather than the number."
    )


def test_every_declarative_base_mints_keys_with_the_fake_ulid() -> None:
    """The half of NR-025 that reaches the data model.

    This is why the national core is keyed on INTEGER/BIGINT in the identity
    contract rather than copying the VARCHAR shape: the String(26) primary keys
    across the tree are random, not time-ordered, so they buy page splits and
    26-byte index entries and nothing else.
    """
    bases = [
        "care_continuum", "citizen_platform", "clinical", "ehr", "identity",
        "national", "nursing",
    ]
    for package in bases:
        source = (APP / package / "base.py").read_text(encoding="utf-8")
        assert _TRUNCATED_UUID4.removeprefix("return ") in source.replace('"', "'"), (
            f"app/{package}/base.py no longer mints keys with the truncated UUID4; "
            "if it adopted a real ULID, update NR-025"
        )


# --- NR-026: nursing ORM contradicts its own physical schema -----------------


def _nursing_migration_source() -> str:
    path = MIGRATIONS / "20260716_0002_nursing_platform.py"
    assert path.exists(), "the nursing platform migration was renamed or removed"
    return path.read_text(encoding="utf-8")


def test_the_nursing_migration_keys_every_actor_column_on_integer() -> None:
    """NR-026, physical half — read from migration source, not a live database."""
    source = _nursing_migration_source()
    actor_columns = re.findall(
        r'sa\.Column\(\s*"([a-z_]+)",\s*sa\.(\w+)\(\),\s*sa\.ForeignKey\("lab_users\.id"',
        source,
    )
    assert actor_columns, "no lab_users foreign keys found in the nursing migration"
    non_integer = [(name, typ) for name, typ in actor_columns if typ != "Integer"]
    assert not non_integer, (
        f"the deployed nursing schema is no longer all-Integer on lab_users: {non_integer}"
    )


def test_the_nursing_orm_still_contradicts_the_deployed_schema() -> None:
    """NR-026, ORM half.

    Asserts the defect, not its absence. When Nursing is reconciled this test
    fails, which is the signal to close NR-026 and delete the guard — not to
    weaken it.
    """
    models = (APP / "nursing" / "models.py").read_text(encoding="utf-8")

    string_fks_to_lab_users = len(
        re.findall(r'Column\(String\(26\), ForeignKey\("lab_users\.id"', models)
    )
    encounter_columns = len(
        re.findall(r'encounter_id = Column\(String\(26\), ForeignKey\("national_encounters', models)
    )

    assert string_fks_to_lab_users == 23, (
        f"NR-026 changed: {string_fks_to_lab_users} String(26) foreign keys to the "
        "Integer lab_users.id (was 23). If Nursing was reconciled, close NR-026."
    )
    assert encounter_columns == 12, (
        f"NR-026 changed: {encounter_columns} encounter_id columns declared in the ORM "
        "(was 12). If Nursing was reconciled, close NR-026."
    )
    assert "encounter_id" not in _nursing_migration_source(), (
        "the nursing migration now creates an encounter_id column; NR-026's second "
        "half is resolved and this guard should be updated"
    )


# --- Encounter references in the deployed schema -----------------------------


def test_the_legacy_encounter_references_keep_their_three_widths() -> None:
    """The physical evidence behind the Encounter ownership decision.

    Three deployed tables reference an encounter as an unconstrained string in
    three different widths, with no foreign key. They must not be retyped until
    the canonical Encounter is chosen (BLOCKED — CLINICAL OWNER REQUIRED).
    """
    expected = {
        "20260814_0009_billing_insurance_projection.py": ("encounter_ref", "128"),
        "20260901_0001_blood_bank_phase2_operational.py": ("encounter_id", "100"),
        "20260815_0022_pharmacy_pos_sales.py": ("encounter_id", "26"),
    }
    for filename, (column, width) in expected.items():
        source = (MIGRATIONS / filename).read_text(encoding="utf-8")
        pattern = rf'sa\.Column\("{column}", sa\.String\((?:length=)?{width}\)'
        assert re.search(pattern, source), (
            f"{filename} no longer declares {column} as String({width}); the Encounter "
            "ownership decision rests on these three widths differing"
        )
        assert 'ForeignKey("national_encounters' not in source, (
            f"{filename} gained a foreign key to national_encounters, which is a "
            "PROJECTION and may never be a foreign-key target"
        )
