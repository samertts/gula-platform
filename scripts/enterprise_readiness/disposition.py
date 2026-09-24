"""Per-table evidence for the canonical disposition matrix (BATCH-2).

Reuses the GULA Intelligent Core detectors for discovery rather than
re-implementing them: `_load_orm_metadata` supplies every declarative base and
`_registered_metadata_ids` supplies alembic's view. This script only joins that
against the physical schema, the reachable route surface and static usage, then
applies deterministic rules.

    GULA_INTEL_DATABASE_URL=... python3 scripts/enterprise_readiness/disposition.py
"""

from __future__ import annotations

import collections
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
SCAN = pathlib.Path(os.getenv("GULA_SCAN_DIR", "/tmp/gula-scan"))
SCAN.mkdir(parents=True, exist_ok=True)
for extra in (str(REPO), str(REPO / "backend"), str(REPO / "tools")):
    if extra not in sys.path:
        sys.path.insert(0, extra)

from gula_intel import detectors  # noqa: E402

APP = REPO / "backend" / "app"
TESTS = REPO / "backend" / "tests"


def _text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def collect() -> list[dict[str, object]]:
    import sqlalchemy

    url = os.environ["GULA_INTEL_DATABASE_URL"]
    engine = sqlalchemy.create_engine(url)
    inspector = sqlalchemy.inspect(engine)
    physical = set(inspector.get_table_names())

    bases = detectors._load_orm_metadata()
    registered, _ = detectors._registered_metadata_ids()

    # class -> table, and table -> owning bases (duplicates matter: two bases
    # mapping one table name is a MERGE candidate, not two independent entities)
    table_bases: dict[str, list[str]] = collections.defaultdict(list)
    for label, metadata in bases:
        for name in metadata.tables:
            table_bases[name].append(label)

    class_table = detectors._mapped_classes()
    table_class = {t: c for c, (t, _d) in class_table.items()}

    # Static usage: which source files mention each model class name.
    app_hits: collections.Counter[str] = collections.Counter()
    test_hits: collections.Counter[str] = collections.Counter()
    service_hits: collections.Counter[str] = collections.Counter()
    for root, counter in ((APP, app_hits), (TESTS, test_hits)):
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            body = _text(path)
            for cls, (table, _dom) in class_table.items():
                if cls in body:
                    counter[table] += 1
                    if root is APP and ("service" in path.name or "routes" in path.name):
                        service_hits[table] += 1

    # Reachable operations per table, from the booted-app route survey if present.
    reachable: collections.Counter[str] = collections.Counter()
    backing = SCAN / "endpoint_backing_exact.json"
    if backing.exists():
        for row in json.loads(_text(backing)):
            for table in row.get("tables", []):
                reachable[table] += row.get("ops", 0)

    # Migration mentions: a table named in the alembic chain has a migration
    # history even if it is absent now (dropped, or conditionally created).
    migration_mentions: set[str] = set()
    versions = REPO / "backend" / "migrations" / "versions"
    if versions.exists():
        blob = "\n".join(_text(p) for p in versions.glob("*.py"))
        for name in table_bases:
            if f'"{name}"' in blob or f"'{name}'" in blob:
                migration_mentions.add(name)

    # Column-level drift, from GULA-SCHEMA-002 itself rather than a reimplementation.
    drift = detectors.detect_orm_schema_drift(url)
    drifted = {a.split(".")[0] for f in drift.findings for a in f.affected}

    rows: list[dict[str, object]] = []
    for label, metadata in bases:
        domain = detectors._domain_of(label)
        base_registered = id(metadata) in registered
        for name, table in sorted(metadata.tables.items()):
            columns = {c.name: c for c in table.columns}
            pk = [c.name for c in table.primary_key.columns]
            pk_types = {str(columns[c].type).split("(")[0].upper() for c in pk if c in columns}
            # target_fullname is the declared string, so an FK whose target is
            # not in this base's metadata is recorded rather than raising. Those
            # cross-base references are themselves evidence: SQLAlchemy cannot
            # build them, so the relationship exists only on paper.
            fks, unresolved_fks = set(), set()
            for column in table.columns:
                for fk in column.foreign_keys:
                    target = str(fk.target_fullname).rsplit(".", 1)[0]
                    fks.add(target)
                    if target not in metadata.tables:
                        unresolved_fks.add(target)
            scope = (
                "TENANT" if "lab_id" in columns
                else "FACILITY" if "facility_id" in columns
                else "PATIENT" if "patient_id" in columns and "lab_id" not in columns
                else "USER" if "user_id" in columns and "lab_id" not in columns
                else "GLOBAL"
            )
            public_ids = sorted(
                c for c in columns
                if c.endswith("_id") and "UUID" in str(columns[c].type).upper()
            )
            rows.append({
                "domain": domain,
                "declarative_base": label,
                "base_in_target_metadata": base_registered,
                "model": table_class.get(name, ""),
                "table": name,
                "physical": name in physical,
                "duplicate_bases": table_bases[name] if len(table_bases[name]) > 1 else [],
                "primary_key": pk,
                "pk_types": sorted(pk_types),
                "public_uuid_columns": public_ids,
                "scope": scope,
                "foreign_keys_to": sorted(fks),
                "foreign_keys_outside_base": sorted(unresolved_fks),
                "app_references": app_hits[name],
                "service_or_route_references": service_hits[name],
                "test_references": test_hits[name],
                "reachable_operations": reachable[name],
                "named_in_migrations": name in migration_mentions,
                "column_drift": name in drifted,
            })
    return rows


def dispose(row: dict[str, object]) -> tuple[str, str, str]:
    """(disposition, risk, decision_required) from evidence alone.

    Order matters: a table mapped by two bases is an ownership question before
    it is anything else, and a physical table that drifts is RECONCILE rather
    than KEEP -- calling it KEEP is how 1,677 findings stayed invisible.
    """
    physical = row["physical"]
    ops = row["reachable_operations"]
    svc = row["service_or_route_references"]
    refs = row["app_references"]
    dup = row["duplicate_bases"]
    outside = row["foreign_keys_outside_base"]

    if dup:
        return ("MERGE", "P1",
                f"one table mapped by {len(dup)} declarative bases: {', '.join(dup)}")
    if physical:
        if row["column_drift"]:
            return ("RECONCILE", "P1", "")
        return ("KEEP", "P3", "")

    # Not physical from here down.
    if outside:
        # It cannot be created in isolation: its foreign keys name tables owned
        # by another base, so the owning domain must be settled first.
        return ("CROSS_DOMAIN_OWNER", "P0" if ops else "P1",
                "foreign keys target tables outside this base ("
                + ", ".join(outside) + "); the owning domain must be decided first")
    if ops:
        return ("CREATE_PHYSICAL", "P0",
                "reachable API operations query a table that does not exist")
    if svc:
        return ("CREATE_PHYSICAL", "P1",
                "referenced by a service or route module but not reachable through a registered router")
    if row["named_in_migrations"]:
        return ("BLOCKED", "P1",
                "named in the migration chain yet absent from the built schema; "
                "dropped, conditionally created, or never applied?")
    if refs > 1:
        return ("DEFER", "P2", "")
    return ("RETIRE", "P2",
            "no physical table, no reachable operation, no service reference and no "
            "migration history: confirm the capability was never shipped")


def main() -> int:
    rows = collect()
    for row in rows:
        disposition, risk, decision = dispose(row)
        row["disposition"] = disposition
        row["risk"] = risk
        row["decision_required"] = decision
    (SCAN / "disposition_rows.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    counts = collections.Counter(r["disposition"] for r in rows)
    print(json.dumps({
        "tables": len(rows),
        "physical": sum(1 for r in rows if r["physical"]),
        "missing": sum(1 for r in rows if not r["physical"]),
        "dispositions": dict(counts.most_common()),
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
