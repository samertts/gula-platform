# Database & Migration Readiness Report — P0 Tranche

> Readiness/boundary record. **No migration was authored, modified, executed,
> or validated against any database in this tranche.** No connection to an
> operational, staging, or production database was opened. Synthetic SQLite
> test databases were used by the test harness only.

## 1. Verdict

| Dimension | Status |
|---|---|
| Migrations executed | **NONE** |
| DDL / schema change | **NONE** |
| `backend/migrations/env.py` delta | **`+49 / -0`, preserved** (pre-existing user work, not edited) |
| F-085 (NR-011 full metadata completeness) | **OPEN — not authorized** |
| RPO / RTO | **UNMEASURED / NOT VERIFIED** |
| Production / runtime readiness claim | **NONE** — HOLD unchanged |

## 2. Invariants verified at end of tranche

```
git diff --numstat -- backend/migrations/env.py   -> 49  0   backend/migrations/env.py
md5sum GOVERNANCE/FINAL_DECISION.md               -> effdfeaf10234678d83b2668c4489552  (HOLD)
gula-platform: branch remediate-security-001, HEAD f478676b…, 0 status entries
gula-integration: branch integration/gula-unification-v1, HEAD 2827c1ff…
```

- The protected `env.py +49/-0` delta was left exactly as found. Registering
  `DocIntelBase` / `InsBase` to close F-085 would alter this protected delta
  and was therefore **not done**.
- No file under `backend/migrations/` was created or edited. The six
  `20261114_000*` unifier migration files visible in Git status are
  **pre-existing user work** and were not touched.
- No Alembic command (`upgrade`, `downgrade`, `check`, `revision`,
  `autogenerate`) was executed against any database.

## 3. Code changes in this tranche — schema impact assessment

All P0 code changes were application-layer and required **no schema change**:

| Change | Schema impact |
|---|---|
| Canonical NID/HMAC helpers (`services/identity.py`) | None — pure functions |
| Registration hash parity (`routes/register.py`) | None — existing columns only |
| No raw NID at rest (`identity_persistence_service.py`) | None — existing `documents_json` column |
| POST NID lookup (`routes/identity.py`) | None — new route, no table |
| JWKS fail-closed (`oauth2_provider.py`, `routes/oauth2.py`) | None |
| WebAuthn config/challenge lifecycle (`shared/auth/webauthn.py`, `mfa_service.py`, `routes/mfa.py`) | None — challenges in existing cache store, no new table |
| Password reset session revocation (`routes/password_reset.py`) | None — existing `perm_version` mechanism |
| MPI merge integrity (`services/mpi/resolver.py`) | None — existing `citizens`, `identity_claims`, `mpi_merge_audit` tables; uses nested SAVEPOINT only |

The MPI merge uses `db.begin_nested()` (SAVEPOINT) for atomicity; this is a
transaction-control construct within the existing transaction and does not
create or alter schema.

## 4. Migrations that remain out of scope

- **F-085 / NR-011** — full Alembic metadata completeness (registering all
  bases including `DocIntelBase` / `InsBase`). Registering them would change
  the protected `+49/-0` delta and is **not authorized** in this program.
  Recorded as P2-01 `NEEDS_OWNER_DECISION`.
- The broader program's unmigrated-ORM-table backlog (ADR-A / D-001) was
  explicitly not advanced.
- No production database snapshot, restore, or DR drill was performed;
  RPO/RTO remain `UNMEASURED`.

## 5. Test-environment note (honest)

Tests ran against temporary SQLite databases created by the test harness
(`conftest.py`), with in-memory/file stores — never an operational database.
The interpreter was Python 3.12.13 from an isolated venv; `signxml` was
installed into that venv because it is in `requirements.txt` but absent from
`requirements-lock.txt` (a **pre-existing lockfile gap**, not modified).

## 6. Non-claims

- No claim that any migration applies cleanly to PostgreSQL or any target DB.
- No claim that F-085 is closed or that strict-schema checks pass.
- No claim about RPO, RTO, backup/restore, or disaster recovery.
- No claim of production/runtime schema readiness. HOLD unchanged.
