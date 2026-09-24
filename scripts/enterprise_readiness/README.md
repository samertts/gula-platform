# Enterprise readiness scan

The scripts behind `docs/enterprise-readiness/GULA_MASTER_COMPLETION_MAP.md`.
Re-run them after a batch instead of re-deriving the numbers by hand — that is
the whole point of keeping them.

They are a measurement harness, not a new validation framework: the standing
regression mechanisms remain `GULA-SCHEMA-002`, the Intelligent Core detectors,
the migration gates and `scripts/quality_changed_files_gate.py`.

## Order

```bash
export GULA_SCAN_DIR=/tmp/gula-scan          # defaults to this if unset
export PYTHONPATH=/path/to/gula-platform:/path/to/gula-platform/backend

# 1. inventory: domains, endpoints, models, migrations, tests, CI, docs
python3 scripts/enterprise_readiness/scan.py > "$GULA_SCAN_DIR/inventory.json"

# 2. physical truth — a database migrated to alembic head, not migration source
psql -h 127.0.0.1 -U postgres -d <migrated_db> -tAc \
  "select table_name from information_schema.tables
   where table_schema='public' and table_type='BASE TABLE' order by 1" \
  > "$GULA_SCAN_DIR/physical_tables.txt"
python3 scripts/enterprise_readiness/delta.py

# 3. reachable routes — BOOTS the app; do not count decorators (see below)
ENV=development RUNTIME_MODE=test DATABASE_URL=postgresql+psycopg2://... \
  python3 scripts/enterprise_readiness/routes_reachable.py

# 4. exact endpoint -> table attribution
python3 scripts/enterprise_readiness/reach2.py

# 5. per-domain join
python3 scripts/enterprise_readiness/join.py
```

## Two traps these scripts exist to avoid

**Counting decorators overstates the API.** 2,406 `@router.get`-style decorators
exist; 2,102 operations are actually reachable. Reachability must come from a
booted app, walking FastAPI's lazy `_IncludedRouter` wrappers — a plain
`app.routes` walk returns 4 routes on this FastAPI version.

**Transitive import closure over-attributes tables.** A depth-3 closure blamed
Pharmacy for tables it never touches, contradicting its verified 27/27 state.
`reach2.py` resolves only classes a route module names directly, plus those
named by modules it imports from within its own domain package.
