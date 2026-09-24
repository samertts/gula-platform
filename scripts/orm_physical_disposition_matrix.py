#!/usr/bin/env python3
"""Generate the ORM <-> physical PostgreSQL disposition matrix (NR-080).

Reproducible by anyone with a database at migration head:

    MIGRATION_DATABASE_URL=postgresql+psycopg2://... \
      python3 scripts/orm_physical_disposition_matrix.py --prefix radiology \
      --out docs/architecture/NR-080-radiology-disposition-matrix.json

Two sources are compared, and only two, because only two exist here:

  PHYSICAL  information_schema / pg_catalog on a database built by running
            `alembic upgrade head` against an empty database. It is therefore
            migration-derived; it is not independent of the migration files.
  ORM       the metadata objects `migrations/env.py` registers, loaded by
            replaying that file's imports (env.py runs the migration at module
            scope and cannot be imported).

A third, genuinely independent source -- a production database -- is not
reachable from this environment, and the matrix does not pretend otherwise.
Each row carries `sources` saying exactly what backed it.

Column classification follows the A-H scheme:

  A CANONICAL ORM COLUMN     B CANONICAL PHYSICAL COLUMN
  C LEGACY PHYSICAL COLUMN   D LEGACY ORM COLUMN
  E SHARED / CROSS-DOMAIN    F DERIVED
  G EXTERNAL COMPATIBILITY   H UNKNOWN

Classification here is deliberately conservative: it is assigned only where the
evidence decides it, and H/UNKNOWN otherwise. Guessing a disposition would make
the matrix look complete while making it wrong, and a wrong disposition is what
authorises a destructive migration.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (REPO, os.path.join(REPO, "backend")):
    if path not in sys.path:
        sys.path.insert(0, path)

import sqlalchemy as sa  # noqa: E402

#: Columns that carry protected data or an authoritative constraint. A physical
#: column matching one of these is never a DROP candidate, whatever the ORM says.
PROTECTED = (
    "lab_id", "patient_id", "national_id", "sndhs_health_id", "health_id",
    "person_id", "citizen_id", "organization_id", "facility_id", "tenant_id",
    "created_by", "updated_by", "audit", "consent", "version",
)

#: Physical columns the platform gives every tenant-scoped clinical table.
#: Their absence from a mapper is a tenant-isolation defect, not drift.
PLATFORM = {"lab_id", "sync_id", "created_by", "updated_by"}

_EQUIVALENT = {
    ("VARCHAR", "character varying"), ("VARCHAR", "text"), ("TEXT", "text"),
    ("INTEGER", "integer"), ("BIGINT", "bigint"), ("BOOLEAN", "boolean"),
    ("DATETIME", "timestamp with time zone"), ("DATE", "date"),
    ("TIME", "time without time zone"), ("FLOAT", "double precision"),
    ("NUMERIC", "numeric"), ("JSON", "json"), ("JSON", "jsonb"),
    ("JSONB", "jsonb"), ("UUID", "uuid"), ("SMALLINT", "smallint"),
}


def _base_type(rendered: str) -> str:
    return re.split(r"[(\s]", rendered)[0].upper()


def _protected(column: str) -> bool:
    return any(token in column for token in PROTECTED)


def _load_orm():
    from tests.test_alembic_metadata_registry import _load_registry

    tables, owners = {}, {}
    for label, metadata in _load_registry():
        for name, table in metadata.tables.items():
            if name not in tables:
                tables[name], owners[name] = table, label
    return tables, owners


def _load_physical(url: str):
    engine = sa.create_engine(url)
    columns: dict[str, dict[str, dict]] = {}
    fks: dict[str, dict[str, str]] = {}
    indexes: dict[str, list[str]] = {}
    with engine.connect() as connection:
        for row in connection.execute(sa.text(
            "SELECT table_name, column_name, data_type, is_nullable, "
            "column_default, character_maximum_length FROM information_schema.columns "
            "WHERE table_schema = 'public' ORDER BY table_name, ordinal_position",
        )):
            columns.setdefault(row[0], {})[row[1]] = {
                "type": row[2], "nullable": row[3] == "YES",
                "default": row[4], "length": row[5],
            }
        for row in connection.execute(sa.text("""
            SELECT tc.table_name, kcu.column_name, ccu.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
              ON tc.constraint_name = ccu.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        """)):
            fks.setdefault(row[0], {})[row[1]] = row[2]
        for row in connection.execute(sa.text(
            "SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public'",
        )):
            indexes.setdefault(row[0], []).append(row[1])
    engine.dispose()
    return columns, fks, indexes


def build(url: str, prefix: str) -> dict:
    orm_tables, orm_owners = _load_orm()
    phys_columns, phys_fks, phys_indexes = _load_physical(url)

    names = sorted(
        {t for t in phys_columns if t.startswith(prefix)}
        | {t for t in orm_tables if t.startswith(prefix)},
    )
    matrix = {}
    for name in names:
        physical = phys_columns.get(name, {})
        table = orm_tables.get(name)
        orm = {c.name: c for c in table.columns} if table is not None else {}

        rows = {}
        for column in sorted(set(physical) | set(orm)):
            p, o = physical.get(column), orm.get(column)
            row = {
                "in_physical": p is not None,
                "in_orm": o is not None,
                "physical_type": p["type"] if p else None,
                "orm_type": str(o.type) if o is not None else None,
                "physical_nullable": p["nullable"] if p else None,
                "orm_nullable": bool(o.nullable) if o is not None else None,
                "physical_default": p["default"] if p else None,
                "orm_server_default": (
                    str(o.server_default.arg)
                    if o is not None and o.server_default is not None else None),
                "primary_key": bool(o.primary_key) if o is not None else None,
                "physical_fk": phys_fks.get(name, {}).get(column),
                "orm_fk": sorted(str(fk.target_fullname) for fk in o.foreign_keys)
                          if o is not None else None,
                "protected": _protected(column),
            }
            row["type_mismatch"] = bool(
                p and o is not None
                and (_base_type(str(o.type)), p["type"]) not in _EQUIVALENT)
            row["nullability_mismatch"] = bool(
                p and o is not None and p["nullable"] != bool(o.nullable))
            row["fk_mismatch"] = bool(
                p and o is not None and bool(row["physical_fk"]) != bool(row["orm_fk"]))

            if p and o is None:
                row["classification"] = "B" if column in PLATFORM or row["protected"] else "H"
                row["disposition"] = "MAP" if row["classification"] == "B" else "UNKNOWN"
                row["safe_action"] = (
                    "Add this column to the mapper. It is physical, and for lab_id it is "
                    "the tenant-isolation column CLAUDE.md Security Invariant #1 requires."
                    if row["classification"] == "B" else
                    "Establish ownership and usage before acting. Do NOT drop it.")
                row["migration_required"] = False
                row["risk"] = "HIGH — autogenerate proposes DROP COLUMN for this" if row["protected"] else "MEDIUM"
            elif o is not None and p is None:
                row["classification"] = "H"
                row["disposition"] = "UNKNOWN"
                row["safe_action"] = (
                    "Decide against the physical schema: either RENAME the mapper field "
                    "onto the physical column that carries this information, or ADD the "
                    "column with an additive migration. Do NOT delete the mapper field "
                    "without proving the information is held elsewhere.")
                row["migration_required"] = None
                row["risk"] = "HIGH — every statement against this table fails with UndefinedColumn"
            else:
                conflict = row["type_mismatch"] or row["fk_mismatch"]
                row["classification"] = "H" if conflict else "E"
                row["disposition"] = "BLOCK" if conflict else "KEEP"
                row["safe_action"] = (
                    "Type or foreign key disagree. Resolve in favour of the physical "
                    "column: it is the one a constraint is built on."
                    if conflict else "Aligned. No action.")
                row["migration_required"] = False
                row["risk"] = "HIGH — identity type conflict" if row["type_mismatch"] and row["primary_key"] else (
                    "MEDIUM" if conflict else "NONE")
            rows[column] = row

        matrix[name] = {
            "domain": prefix,
            "physical_table": name if name in phys_columns else None,
            "orm_class": table.name if table is not None else None,
            "metadata_owner": orm_owners.get(name),
            "canonical_owner": "physical schema" if name in phys_columns else "UNKNOWN",
            "n_physical_columns": len(physical),
            "n_orm_columns": len(orm),
            "physical_only": sorted(set(physical) - set(orm)),
            "orm_only": sorted(set(orm) - set(physical)),
            "physical_indexes": sorted(phys_indexes.get(name, [])),
            "physical_foreign_keys": phys_fks.get(name, {}),
            "type_mismatches": sorted(c for c, r in rows.items() if r["type_mismatch"]),
            "nullability_mismatches": sorted(c for c, r in rows.items() if r["nullability_mismatch"]),
            "fk_mismatches": sorted(c for c, r in rows.items() if r["fk_mismatch"]),
            "protected_unmapped": sorted(
                c for c, r in rows.items()
                if r["protected"] and r["in_physical"] and not r["in_orm"]),
            "runtime_impact": (
                "FATAL — the mapper names a column the table does not have, so every "
                "statement including SELECT fails with UndefinedColumn"
                if set(orm) - set(physical) and name in phys_columns else
                "NO PHYSICAL TABLE — every statement fails with UndefinedTable"
                if name not in phys_columns else "none measured"),
            "verification_state": "EXECUTED — SELECT run against PostgreSQL at migration head",
            "sources": ["physical: information_schema (migration-derived)",
                        "orm: migrations/env.py target_metadata"],
            "columns": rows,
        }
    return matrix


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", default="radiology")
    parser.add_argument("--out", default="-")
    parser.add_argument("--url", default=os.environ.get("GULA_SCHEMA_DATABASE_URL")
                        or os.environ.get("MIGRATION_DATABASE_URL"))
    args = parser.parse_args()
    if not args.url:
        parser.error("set --url, GULA_SCHEMA_DATABASE_URL or MIGRATION_DATABASE_URL")

    matrix = build(args.url, args.prefix)
    payload = json.dumps(
        {"domain": args.prefix, "tables": len(matrix), "matrix": matrix},
        indent=1, default=str, ensure_ascii=False) + "\n"
    if args.out == "-":
        sys.stdout.write(payload)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
        sys.stderr.write(f"{len(matrix)} tables -> {args.out}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
