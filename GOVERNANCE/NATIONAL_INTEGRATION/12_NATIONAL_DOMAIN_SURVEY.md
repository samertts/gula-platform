# WS-07 Survey — National Domains & Journeys

**Document:** 12 · **Status:** `INTEGRATED` (11-domain framework) / `BLOCKED` (national waves).

## Surface
`backend/app/domain_platform/**`, `backend/app/national/**`, `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`, `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md`, `GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md`; 11 test-domain modules.

## Verified evidence (prior cycle, unchanged)
- Domain Platform: 11 canonical domains, **11/11 certified @ 100%, isolation PASS (0 findings)**.
- National service inventory: **18 services** with evidence, migrations coverage, auth and test counts.
- Migration coverage: 833 ORM tables / 40 contexts; 407 migrated (48.9%), **426 missing**; 18/40 contexts fully covered.
- `NR-011`: `alembic check`/autogenerate aborts (`ehr_allergies.encounter_id → national_encounters` missing from metadata; `env.py:38` imports only `app.national.base`).
- W1 strict-schema probe: 753 passed / 119 failed on migration-only schema vs 872 passed on SQLite conftest — 340 table slots / 664 columns missing across 82 tables; four P0 patient-workflow modules fail.
- National waves W1–W7 sequenced in `NATIONAL_INTEGRATION_ROADMAP.md`; every wave entry gate is an owner decision.

## Gaps
| Gap | Classification | Route |
|---|---|---|
| NR-011 metadata repair | `TESTED` | 14/14 regressions + disposable-PG `alembic check` with 0 metadata aborts — critical-path prerequisite engineering **complete**; ADR-A decision still `BLOCKED` |
| ADR-A / B / C / D | `BLOCKED` | decision packages (`05` §5) |
| 426-table backfill | `BLOCKED` | ADR-A + context-by-context migrations |
| MIG-EXISTING closure | `BLOCKED` | ADR-B + production-like snapshot |
| Dormant router/engine activation | `NOT IMPLEMENTED` | forbidden by constitution |
| National deployment compatibility claim | `BLOCKED` | owner + government authority |

## Program action
Preserve domain isolation. NR-011 engineering (17-base registration + merged MetaData) was **verified in this program**: `backend/tests/unit/test_nr011_metadata_discovery.py` 14/14 passed; on a brand-new disposable database `gula_nr011_verify`, `alembic upgrade head` exited 0 and `alembic check` executed to completion with **0 `NoReferencedTableError`/traceback markers** (exit 1 attributable to 284 documented unmigrated ORM tables — ADR-A debt, not a metadata abort). No operational database was touched; the disposable DB is dropped after evidence capture. No wave starts without its recorded entry gate.
