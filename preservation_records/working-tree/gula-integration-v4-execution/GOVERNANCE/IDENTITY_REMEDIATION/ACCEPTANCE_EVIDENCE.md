# Acceptance Evidence

> Evidence discipline: a command counts as evidence only when actually executed.
> `PENDING` entries are not claims. No test result is copied from the study.
> This file was backfilled after the P0 tranche was executed and verified.

## 1. Baseline commands (executed)

| Command | Exit | Result | Environment note |
|---|---|---|---|
| `git rev-parse --abbrev-ref HEAD` in `gula-integration` | 0 | `integration/gula-unification-v1` | — |
| `git rev-parse HEAD` in `gula-integration` | 0 | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | — |
| `git status --porcelain=v1 \| wc -l` (Phase 0) | 0 | `228` pre-existing entries + 1 new untracked dir (`229`) | preserved |
| `git status --porcelain=v1` in `gula-platform` | 0 | 0 entries; HEAD `f478676b…` | protected repo clean |
| `md5sum GOVERNANCE/FINAL_DECISION.md` | 0 | `effdfeaf10234678d83b2668c4489552` | HOLD unchanged |
| `PYTHONPATH=backend:. python3.11 -m pytest backend/tests/test_auth_infrastructure.py -q` | 1 | 30 collected, **30 setup errors** | Interpreter mismatch: PEP 695 syntax requires Python 3.12; not a code failure |
| `python3.12 -m pip install --user -r backend/requirements-lock.txt` | rejected | externally-managed environment | No project file changed |
| `python3.12 -m venv /tmp/opencode/gula-py312` + `pip install --timeout 120 --retries 8 -r backend/requirements-lock.txt` | 0 (`PIP_EXIT=0`) | isolated Python **3.12.13**, pytest 9.1.1, webauthn 3.0.0 | Environment-only; no repo dependency change |
| `pip install 'signxml>=4.2.0'` into isolated venv | 0 | installed | `signxml` is in `requirements.txt` but absent from `requirements-lock.txt` — **pre-existing lockfile gap, not modified** |

A separate pre-existing Python 3.12 environment was used read-only for two
intermediate runs; all final evidence below uses the isolated venv only.

## 2. Executed test evidence

```
UNIT: P0-A / P0-B / P0-C / P0-D / P0-E (combined final verification)
COMMAND: PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest
         backend/tests/unit/test_national_id_canonicalization.py
         backend/tests/unit/test_webauthn_hardening.py
         backend/tests/unit/test_session_revocation.py
         backend/tests/test_persisted_identity_governance.py
         backend/tests/test_mpi_merge_integrity.py
         backend/tests/test_auth_infrastructure.py
         -q --no-header --disable-warnings --tb=short
WORKDIR: /home/samertts/workspace/projects/gula-integration
EXIT CODE: 0
COLLECTED: 109   PASSED: 109   FAILED: 0   SKIPPED: 0   WARNINGS: 1
DURATION: 147.64s (0:02:27)
ENVIRONMENT: Python 3.12.13, SQLite in-memory/file test DBs, no operational DB
NOTES: 30 tests from test_auth_infrastructure.py (includes the updated JWKS test).
       No production/runtime/E2E claim.
```

Per-unit smallest-suite runs (all executed with the same isolated interpreter):

| Unit | Suite (exact file) | Exit | Collected / Passed | Notes |
|---|---|---|---|---|
| P0-A | `backend/tests/unit/test_national_id_canonicalization.py` | 0 | 17 / 17 | Arabic-Indic/Extended-Arab-Indic/Western parity, family-hash separation, legacy candidates, no raw NID at rest, duplicate across scripts |
| P0-A (related) | `backend/tests/test_persisted_identity_governance.py` | 0 | 35 / 35 | Full pre-existing suite; 4 initial failures caused by alphanumeric synthetic IDs were fixed by restricting canonicalization to digit-bearing, letter-free values |
| P0-B | `backend/tests/test_auth_infrastructure.py::test_oauth2_jwks` | 0 | 1 / 1 | Endpoint 503; no usable key set published |
| P0-C | `backend/tests/unit/test_webauthn_hardening.py` | 0 | 18 / 18 | invalid origin/RP config, base64url fidelity, missing/expired/replayed challenges, namespace separation, store errors, single-use |
| P0-D | `backend/tests/unit/test_session_revocation.py` | 0 | 3 / 3 | correct bump signature on change-password; reset revokes sessions; failed reset does not revoke |
| P0-E | `backend/tests/test_mpi_merge_integrity.py` | 0 | 6 / 6 | claim repoint + provenance, hash-chained audit, idempotency, self/cycle rejection, reason required, savepoint rollback |

Broader regression set (executed, same interpreter):

```
COMMAND: PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest
         backend/tests/test_identity_authentication_security.py backend/tests/identity/
         backend/tests/test_routes_register.py backend/tests/test_routes_labs.py
         backend/tests/test_wave3_identity_mapping.py -q --no-header --disable-warnings --tb=short
EXIT CODE: 0
COLLECTED: 235   PASSED: 231   SKIPPED: 4   FAILED: 0
DURATION: 37.61s
NOTES: 4 skips are pre-existing migration-dependent tests (to be recorded as skips, never as passes).
```

### Evidence corrections made during execution (honest record)

- The first JWKS assertion checked the response `detail` text. The application's
  global 5xx handler sanitizes 5xx bodies, so the assertion failed even though
  the endpoint correctly returned 503. The **test assertion** was narrowed to
  status 503 plus absence of a `keys` field; production fail-closed behavior was
  not weakened.
- The governance-service hash initially canonicalized alphanumeric synthetic
  IDs (e.g. `NID-B`) to an empty string, breaking 4 pre-existing tests. Fixed by
  canonicalizing only digit-bearing, letter-free identifiers; all 35 pass.
- MyPy found a real defect in the new WebAuthn adapter: webauthn 3.x
  `VerifiedRegistration` has no `transports` field. Fixed with `getattr` plus
  typed `PublicKeyCredentialDescriptor` construction; suite re-run green.

## 3. Static-analysis evidence

```
COMMAND: ruff check --output-format=concise <all changed/new Python files>
EXIT CODE: 0 (after fixes)
OUTPUT: 1 remaining finding — backend/app/routes/register.py:305 RUF001 (EN DASH)
        This is PRE-EXISTING (confirmed against HEAD via git show); not introduced
        by this tranche and not altered.

COMMAND: mypy --config-file pyproject.toml --no-pretty --no-error-summary shared/auth/webauthn.py
EXIT CODE: 0   OUTPUT: clean (no errors)

COMMAND: mypy --config-file pyproject.toml <all changed backend modules>
EXIT CODE: 2   LIMITATION: repo-wide strict MyPy baseline has pre-existing errors
        in untouched modules (governance/base.py, models/clinical_scope.py,
        governance/services/*, etc.). No error was attributed to a line added
        by this tranche. MyPy is therefore reported as "where practical", not
        as a clean repo-wide gate.
```

Ruff baseline comparison used `git show HEAD:<file>` copies inside the repo so
import-resolution/isort behaved identically; pre-existing findings in
`identity.py`, `resolver.py` docstrings and `register.py:305` were left untouched.

## 4. Diff-inspection evidence

```
COMMAND: git diff --name-only  (+ git status --porcelain=v1)
CHANGED (tracked, this tranche):
  backend/app/services/identity.py
  backend/app/routes/register.py
  backend/app/governance/services/identity_persistence_service.py
  backend/app/routes/identity.py
  backend/app/security/oauth2_provider.py
  backend/app/routes/oauth2.py
  backend/app/security/mfa_service.py
  backend/app/routes/mfa.py
  backend/app/routes/password_reset.py
  backend/app/services/mpi/resolver.py
  shared/auth/webauthn.py
  backend/tests/test_auth_infrastructure.py
NEW (untracked, this tranche):
  backend/tests/unit/test_national_id_canonicalization.py
  backend/tests/unit/test_webauthn_hardening.py
  backend/tests/unit/test_session_revocation.py
  backend/tests/test_mpi_merge_integrity.py
  GOVERNANCE/IDENTITY_REMEDIATION/  (governance documents, incl. this file)
UNAUTHORIZED CHANGES: none observed
PRE-EXISTING USER ENTRIES: 228 preserved (incl. deferred files
  backend/app/health_data/mdm/matching.py, backend/app/health_data/mdm/service.py,
  backend/app/security/dependencies.py, backend/migrations/env.py)
```

Final exact status is recorded in `IMPLEMENTATION_PROGRESS.md` §6.

## 5. Non-claims (must remain true)

- No E2E, runtime, production, RPO, RTO or security-certification claim.
- No claim that passkey/OIDC/OCR/national services are ready for use.
- No claim that D-020 or D-021 was satisfied.
- No claim that `FINAL_DECISION.md` changed from HOLD.
- No claim that a database migration was executed or validated against an
  operational database.
- Test passes on synthetic fixtures are **unit/integration evidence only**.

## 6. Second tranche — session/device/MPI/NHID readiness (this session)

All commands executed with the same isolated interpreter:
`/tmp/opencode/gula-py312/bin/python` = **Python 3.12.13**, pytest 9.1.1,
SQLAlchemy 2.0.51, FastAPI 0.139.2, webauthn 3.0.0. Workdir
`/home/samertts/workspace/projects/gula-integration`. No project dependency file
changed; no operational DB connection; no migration/DDL.

| # | Exact command | Env | Exit | Collected / Passed / Failed / Skipped | Warnings | Duration |
|---|---|---|---|---|---|---|
| 1 | `ENV=test PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest backend/tests/unit/test_session_revocation.py -q` | ENV=test | 0 | 22 / 22 / 0 / 0 | 1 (Starlette httpx deprecation, unrelated) | 0.40s |
| 2 | `ENV=test PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest backend/tests/unit/test_nhid_readiness.py -q --tb=short` | ENV=test | 0 | 23 / 23 / 0 / 0 | 1 (same unrelated deprecation) | 0.16s |
| 3 | Combined P0 regression: `...pytest backend/tests/unit/test_national_id_canonicalization.py backend/tests/unit/test_webauthn_hardening.py backend/tests/unit/test_session_revocation.py backend/tests/test_persisted_identity_governance.py backend/tests/test_mpi_merge_integrity.py backend/tests/test_auth_infrastructure.py -q --no-header --disable-warnings --tb=short` | ENV=test | 0 | 128 / 128 / 0 / 0 | 1 | 98.99s |
| 4 | `ruff check backend/app/security/session.py backend/tests/unit/test_session_revocation.py backend/tests/unit/test_nhid_readiness.py` | — | 0 | All checks passed | — | — |

Notes:
- Run 1 is the smallest suite (session-store fail-closed). The file grew from 3
  → 22 tests (19 new Phase A regressions).
- Run 2 is the NHID synthetic compatibility suite (23 new tests). Two tests are
  explicitly labelled `KNOWN_RISK`/characterization — they pin current behaviour
  and do not endorse it; no identifier changed and no canonical NHID implemented.
- Run 3 re-ran all prior P0 suites plus the expanded session suite (109 → 128);
  0 failures, 0 skips. Prior broader 231-passed set was not re-run this tranche
  (no change to those files) and remains recorded in §2 above.
- Run 4 was executed after `ruff check --fix` on `test_nhid_readiness.py`
  (import ordering + 2 unused-noqa directives only; no behavioural change).
- MyPy: not re-run this tranche. `session.py`'s only new logic is int coercion and
  store I/O; repo-wide strict MyPy remains non-clean for pre-existing reasons
  (§3). "Where practical" — no new typing defect introduced.
- Environment limitations: in-memory SQLite fixtures only; process-local in-memory
  fallback applies in dev/test (`IS_PRODUCTION` false); no Redis outage was
  induced against a real production-profile service — outage/timeout paths were
  exercised with fault-injected fakes in unit tests.

### Files changed this tranche (all uncommitted)
- **Code:** `backend/app/security/session.py` (clean before edit; converted raw
  cache → fail-closed `security_store`, stale/malformed handling).
- **Tests:** `backend/tests/unit/test_session_revocation.py` (extended 3 → 22),
  `backend/tests/unit/test_nhid_readiness.py` (new, 23).
- **Governance (new):** `SESSION_SECURITY_REMEDIATION_REPORT.md`,
  `DEVICE_IDENTITY_AND_REVOCATION_REPORT.md`,
  `MPI_CROSS_DOMAIN_INTEGRITY_REPORT.md`, `NHID_CANONICALIZATION_READINESS.md`.
- **Governance (updated):** this file, `IMPLEMENTATION_BACKLOG.md`,
  `IMPLEMENTATION_PROGRESS.md`, `DEPENDENCY_GRAPH.md`, `CHANGE_RISK_REGISTER.md`,
  `NEXT_PHASE_AUTHORIZATION_REQUEST.md`.
- **Deferred / user-modified files NOT touched:** `security/redis_client.py`,
  `security/dependencies.py`, `security/auth.py`, `security/rate_limit.py`,
  `security/mfa_service.py`, `security/platform_access.py`, `routes/password_reset.py`,
  `backend/migrations/env.py` (+49/-0 preserved), root `SECURITY_REMEDIATION_REPORT.md`.

## 7. MPI integrity & concurrency tranche (this session)

All commands executed from `/home/samertts/workspace/projects/gula-integration` with
`/tmp/opencode/gula-py312/bin/python` = Python 3.12.13. Env
`ENV=test PYTHONPATH=backend:. DATABASE_URL=sqlite:///:memory:`. SQLite temp-file fixture;
no operational DB connection, no DDL, no migration.

| # | Exact command (suffix) | Exit | Collected / Passed / Failed / Skipped | Warnings | Duration |
|---|---|---|---|---|---|
| 1 | `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py -q --disable-warnings` (pre-edit baseline) | 0 | 41 / 41 / 0 / 0 | 1 | 81.16s |
| 2 | `… -m pytest backend/tests/test_mpi_hash_chain_integrity.py -q --no-header --tb=short` (first pass) | 0 | 7 / 7 / 0 / 0 | 1 | 81.74s |
| 3 | same (final 11-test file) | 0 | 11 / 11 / 0 / 0 | 1 | 82.79s |
| 4 | `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py backend/tests/test_mpi_hash_chain_integrity.py -q --no-header --tb=short` | 0 | 52 / 52 / 0 / 0 | 1 | 80.12s |
| 5 | `… -m pytest backend/tests/test_citizen_relationship_workflow.py backend/tests/test_security_merge_regression_synthetic.py -q --no-header --tb=short` | 0 | 13 / 13 / 0 / 0 | 1 | 0.75s |
| 6 | **final combined** `… -m pytest backend/tests/test_mpi_merge_integrity.py backend/tests/test_mpi_matcher.py backend/tests/test_mpi_hash_chain_integrity.py backend/tests/test_citizen_relationship_workflow.py backend/tests/test_security_merge_regression_synthetic.py -q --no-header --tb=short` | **0** | **65 / 65 / 0 / 0** | 1 | **85.53s** |

Warning (all runs): `StarletteDeprecationWarning` from FastAPI's own `testclient.py`; pre-existing.
No test was deleted, weakened, skipped or had expectations altered to obtain a pass.

Static analysis:
- `ruff check backend/app/services/mpi/resolver.py backend/tests/test_mpi_hash_chain_integrity.py --output-format=concise` → EXIT 1, one **pre-existing** `RUF002` at `resolver.py:13` (EN DASH in `0.70–0.90`, confirmed at HEAD); 0 new findings.
- `mypy --config-file backend/pyproject.toml --follow-imports=skip --no-pretty --no-error-summary backend/app/services/mpi/resolver.py` → EXIT 0 (system mypy; isolated venv has no mypy).

Not verified (explicit non-claims): PostgreSQL row-lock contention, deadlock detection, concurrent
audit-fork reproduction, any runtime/E2E/production behaviour, RPO/RTO. Read-only PG catalog
probe only; no PG writes. Full detail in `MPI_INTEGRITY_CONCURRENCY_REMEDIATION_REPORT.md`.

## 8. MPI PostgreSQL concurrency tranche (this session)

**Gate failed before any test was run.** No `pytest`, Ruff or MyPy execution this tranche because
no application source file was modified; the §7 numbers above are prior-tranche evidence and are
not re-claimed. Full detail in `MPI_POSTGRESQL_CONCURRENCY_REMEDIATION_REPORT.md` §15.

All commands executed from `/home/samertts/workspace/projects/gula-integration`; local interpreter
`/tmp/opencode/gula-py312/bin/python` = Python 3.12.13. **No database connection, no DDL, no
migration, no credential read** (secret env values were omitted from every `docker inspect` format).

| # | Exact command | Exit | Evidence | DB backend |
|---|---|---|---|---|
| 1 | `git rev-parse --show-toplevel` / `git branch --show-current` / `git rev-parse HEAD` / `git status --short` | 0 | HEAD `2827c1ff…`; 244 entries (104 M / 120 ?? / 20 R ) | none |
| 2 | `md5sum GOVERNANCE/FINAL_DECISION.md` | 0 | `effdfeaf10234678d83b2668c4489552` | none |
| 3 | `env \| grep -iE 'postgres\|database_url\|…' \| cut -d= -f1 \| sort -u` | 0 | no DB-related env var names | none |
| 4 | `docker info --format '{{.ServerVersion}}'` | 0 | `29.1.3` | none |
| 5 | `command -v psql pg_isready initdb pg_ctl postgres` | 0 | psql/pg_isready present; no server binaries | none |
| 6 | `ss -ltn \| grep -E ':5432\|:5433'` | 1 | no local listener | none |
| 7 | `docker ps -a --format …` | 0 | `gula-postgres` up 30 h; others exited | none |
| 8 | `docker inspect gula-postgres --format …` (no secret values) | 0 | network `gula-platform_default`; volume `pgdata`; `POSTGRES_*` keys | none |
| 9 | `docker volume ls` / `docker network ls` | 0 | `pgdata`, `gula-platform_default` | none |
| 10 | repo grep for `*_TEST_POSTGRES_URL` / test DB env names (values masked) | 0 | no `MPI_TEST_POSTGRES_URL` | none |
| 11 | `grep -nE 'sqlite\|DATABASE_URL\|create_engine…' backend/tests/conftest.py` | 0 | line 28 forces `sqlite:///:memory:` | none |
| 12 | `/tmp/opencode/gula-py312/bin/python -c 'import sys, sqlalchemy, psycopg2; …'` | 0 | 3.12.13 / 2.0.51 / 2.9.12 | none |

Exit 1 on #6 means "no match", not a failure of discovery. Classification: all rows
`VERIFIED_IN_SOURCE`; no `RUNTIME_VERIFIED`, `E2E_VERIFIED` or `PRODUCTION_VERIFIED` row exists.

Prior-tranche test counts (65 passed / 0 failed, EXIT 0, 85.53s) are **reference only**. No
throughput, lock-wait, deadlock or serialization-failure number was produced. No test was added,
deleted, skipped or weakened; no expectation altered to obtain a pass.

### Post-evaluation evidence addendum (2026-11-18)

`MPI_POSTGRESQL_CONCURRENCY_TEST_REPORT.md` (22 sections) records the executed isolated evaluation.
New **TEST_VERIFIED** evidence (out-of-repo harness, schema `mpi_concurrency_test`, synthetic data
only; `DATABASE_IDENTITY: VERIFIED`, PostgreSQL 16.14, 10/10 safety conditions PASS):

| Metric | Result |
|---|---|
| Suite | 65 passed / 0 failed / 0 skipped, EXIT 0, 87.61 s |
| Naive audit-tail fork groups (2/5/10/20 workers, 100 ops) | 50 / 20 / 10 / 5 |
| Naive lost increments (2/5/10/20 workers) | 1 / 4 / 9 / 19 |
| Sentinel / advisory genesis (20 workers) | 0 forks, valid chain — PASS |
| SERIALIZABLE genesis | fork reproduced in controlled diagnostics despite full retry — NOT GUARANTEED |
| Atomic SQL / `FOR UPDATE` / optimistic lost updates | 0 |
| Deadlock: opposite lock order / ascending order | `40P01` observed / 0 |
| Lock timeout | `55P03` at 1.008 s |
| Median throughput (naive/sentinel/advisory/serializable/atomic) | 123.88 / 75.53 / 84.47 / 82.17 / 105.54 ops/s |
| Median p95 (same order, ms) | 101.504 / 137.097 / 142.349 / 366.881 / 130.586 |
| Secrets scan | 33,115 files / 0 hits |
| Source / migration / Git / credentials | 0 changed / 0 created / NONE / not exposed |

Honesty baseline preserved: 0 PRODUCTION_VERIFIED, 0 RUNTIME_VERIFIED, 0 E2E_VERIFIED; no
production-readiness claim. HOLD `effdfeaf…`, D-020/D-021 `PENDING_APPROVAL`, D-MPI-1
`NEEDS_OWNER_DECISION`. **STOP.**

