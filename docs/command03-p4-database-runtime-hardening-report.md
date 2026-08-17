# P4 Command 03 — Database, Migration, and Runtime Infrastructure Hardening

**Repository:** `samertts/gula-platform`
**Branch:** `chore/security-ddos-hardening-clean`
**Pull request:** [#226](https://github.com/samertts/gula-platform/pull/226)
**Baseline commit:** `25d0f0deafbefcfde76743223d90544bf63151d6`
**Base:** `origin/main` at `1e07b8d677c5f7c94d0fb387937eff959af9589d`
**Execution date:** 2026-08-17
**Status:** Final local and read-only external re-evaluation before commit/push

> **Safety boundary:** No production database connection, DDL, data mutation, migration execution against production, deployment, automatic merge, or P5/Command 04 work was performed.

## 1. Executive Decision

P4 Command 03 is **`INFRASTRUCTURE_PARTIAL`**. The Alembic graph is structurally healthy with one canonical head and no missing parents. Local migration, disaster-recovery, tenant-isolation, security, performance, runtime-import, full-backend, and compose-YAML checks pass within the available environment. Three confirmed active compose defects were repaired with minimal changes: the backend build context was aligned with `backend/Dockerfile`, the compose API port was aligned with the healthchecks and Nginx upstream, and production `BASE_URL` fallback was removed from the active compose paths.

The result cannot be classified as fully remediated because Docker is unavailable in the sandbox, no local PostgreSQL/Redis service is running, the live migration upgrade/downgrade path was not executed against a disposable PostgreSQL database, Railway has no configured connector and is therefore unverified, and the current Vercel deployment is externally **BLOCKED** by account configuration before a build is produced. Production database state and full production alignment therefore remain unverified.

## 2. Authoritative Baseline

The baseline was captured from the current repository rather than older reports. The working tree was clean at baseline commit `25d0f0deafbefcfde76743223d90544bf63151d6`; the current Command 03 worktree contains only the remediation files and the two final reports pending commit.

| Dimension | Evidence |
|---|---|
| Current baseline commit | `25d0f0deafbefcfde76743223d90544bf63151d6` |
| Branch | `chore/security-ddos-hardening-clean` |
| `origin/main` | `1e07b8d677c5f7c94d0fb387937eff959af9589d` |
| Python / Node / npm / pnpm | 3.12.3 / 22.13.0 / 10.9.2 / 11.20.0 |
| Alembic | 1.19.1 |
| Docker CLI | Not available in sandbox |
| Local Postgres/Redis listeners | None detected on 5432/6379 |
| `DATABASE_URL`, `GULA_DATABASE_URL`, `REDIS_URL` | Unset in the sandbox shell |
| Railway connector | No matching connector configured |
| Vercel connector | Enabled and read-only inspection performed |

The repository's backend CI workflow uses Python 3.12 and Node 22, while the quality-gate workflow uses Python 3.14 and the backend Dockerfiles use Python 3.14. This is a documented environment-version drift that did not justify an unreviewed workflow or runtime major-version change during this command.

## 3. Alembic Integrity

The Alembic graph was inspected with the repository's configured `ScriptDirectory`, independently of a database connection. The result is a single canonical head with resolved historical branches and no missing parents.

| Invariant | Result |
|---|---:|
| Revision count | 88 |
| Base revision | `20250322_0000` |
| Canonical head | `20260816_0023` |
| Number of heads | 1 |
| Missing parent revisions | 0 |
| Branch points | `20260814_0011`, `20260815_0002` |
| Merge points | `20260815_0003`, `20260815_0015` |
| Graph status | **PASS** |

The branch points are resolved by explicit merge revisions and are not unresolved multiple heads. No historical revision was deleted, renamed, or rewritten.

## 4. Migration Risk and Destructive Operations

A static scan found historical migration operations that drop columns, tables, indexes, constraints, or PostgreSQL triggers during downgrade paths. These are historical rollback behaviors, not operations executed by this command. Any change to those paths requires explicit review for data preservation, reversibility, and production rollback semantics.

| Finding | Classification | Action |
|---|---|---|
| Historical `drop_column`/`drop_table`/`drop_constraint` operations | High-risk rollback surface | Documented; no execution or rewrite |
| Historical raw `op.execute` SQL | Review required by dialect and revision | Documented; no broad refactor |
| Multiple unresolved heads | Not found | No merge migration added |
| Missing parent revisions | Not found | No migration repair required |
| Production schema drift | Not testable without authorized read-only production access | `UNVERIFIED` |

No empty merge migration was created merely to satisfy a checker, and no historical migration was removed.

## 5. Confirmed Runtime/Compose Defects and Fixes

The active compose files used `context: ./backend` while `backend/Dockerfile` explicitly copies `backend/requirements.txt`, `backend/app`, `backend/migrations`, and `shared`, which require the repository root as build context. The same configuration also allowed the Railway-style entrypoint to default to port 10000 while compose healthchecks and the internal Nginx upstream expected port 8000. The main compose API also had an HTTP localhost fallback for `BASE_URL` despite production mode requiring HTTPS.

The minimum safe fix was applied only to active compose files. No historical archive compose file was changed.

| File | Change | Risk disposition |
|---|---|---|
| `docker-compose.yml` | API and worker use `context: .` with `dockerfile: backend/Dockerfile`; API receives `PORT: 8000`; production `BASE_URL` is required; worker receives the same required `BASE_URL` | Low; aligns existing declarations |
| `docker-compose.demo.yml` | Demo API uses root context and `backend/Dockerfile`; explicit `PORT: 8000` retained with its existing HTTPS `BASE_URL` | Low; no data/runtime feature change |
| `docker-compose.full.yml` | Backend uses root context and `backend/Dockerfile`; explicit `PORT: 8000`; required production `BASE_URL` | Low; aligns healthcheck/upstream |

A local PyYAML validator parsed all three active files and asserted the context, Dockerfile, port, and secure/required `BASE_URL` contracts. All three returned `YAML_STATUS=PASS`. Docker build execution remains unavailable because the sandbox has no Docker CLI.

## 6. Schema Consistency

The application and migration code load successfully in the repository's test configuration, and the existing migration/schema tests pass. The local test fixture builds SQLAlchemy metadata against SQLite and covers model relationships and schema assumptions used by the application. However, no disposable PostgreSQL server was available, so a live comparison of SQLAlchemy metadata against a fully upgraded PostgreSQL schema was not possible.

| Schema comparison | Status | Evidence boundary |
|---|---|---|
| Static migration revision and dependency consistency | **PASS** | 88-revision graph inspection and migration tests |
| SQLAlchemy model importability | **PASS** | Runtime import probe and full backend suite |
| SQLite fixture metadata/relationship behavior | **PASS** | Existing tests and 2,719-test regression |
| Fresh PostgreSQL schema vs models | **UNVERIFIED** | No local Postgres/Docker |
| Existing production schema vs models | **UNVERIFIED** | No production DB access was attempted |
| Enum/default/index/nullable drift in live DB | **UNVERIFIED** | Requires disposable or authorized read-only PostgreSQL |

## 7. Migration Testing

The structural migration suites passed: `tests/test_migrations.py` reported **9 passed**, and `tests/test_migration_resilience.py` reported **10 passed**. The disaster-recovery suite also passed as part of the targeted Command 03 run. The four live schema tests for workspace, membership, security audit, and clinical gateway correctly skipped because `MIGRATION_DATABASE_URL`/a PostgreSQL database was not provided.

An additional offline SQL-generation probe was attempted using the correct repository/backend `PYTHONPATH` and a non-production PostgreSQL URL. It progressed through the base revision but stopped at historical revision `20250322_0001` because that migration calls `inspect(op.get_bind())` against Alembic's offline `MockConnection`, producing `sqlalchemy.exc.NoInspectionAvailable`. This is classified as an **offline-mode compatibility limitation**, not silently treated as a successful full migration run. The same introspection pattern exists in many historical migrations; a broad offline refactor was not safe to perform in this command.

## 8. Transaction Safety and Rollback

The repository's local migration-resilience tests verify revision reachability, required upgrade/downgrade functions, unsafe nullable additions, dialect-awareness patterns, and selected schema-consumer assumptions. The full backend suite and targeted DR tests pass. No online upgrade, downgrade, rollback-after-failure, or transaction recovery rehearsal was executed because PostgreSQL and Docker are unavailable locally.

| Rollback criterion | Status |
|---|---|
| Every reachable revision exposes upgrade/downgrade functions | **PASS** locally |
| Static migration resilience checks | **PASS**: 19 migration tests |
| Online `upgrade head` on disposable PostgreSQL | **UNVERIFIED** |
| Online `downgrade -1` and re-upgrade | **UNVERIFIED** |
| Failure simulation and recovery integrity | **PARTIAL**: synthetic DR tests pass; live rehearsal unavailable |
| Production rollback | **BLOCKED** by safety boundary and missing authorized environment |

## 9. Tenant Isolation

The targeted tenant-isolation matrix and security regression tests passed. The full backend regression also passed all included tenant-isolation and authorization coverage. No cross-tenant leakage was observed in local tests, and no change in this command modifies tenant predicates, session context, or authorization semantics.

This is a **PASS for the executed local application-level evidence**. It is not a claim of database-level row-level-security proof or live production isolation, both of which remain unverified without an authorized PostgreSQL environment.

## 10. Query and Index Performance

The performance, concurrency, and queue-backpressure suites reported **36 passed, 2 warnings**. The full backend regression reported **2,719 passed, 4 skipped, 172 warnings** in 320.56 seconds after the current source changes. No new query, cache, retry, or serialization layer was introduced by the remediation. The compose changes only correct build/runtime wiring.

| Performance dimension | Status |
|---|---|
| Local query/performance budget tests | **PASS** |
| Local concurrency/backpressure tests | **PASS** |
| N+1 regression observed | **Not observed in executed scope** |
| PostgreSQL query latency and pool saturation | **UNVERIFIED** |
| Production API latency | **UNVERIFIED** |
| Memory/load behavior under deployment runtime | **UNVERIFIED** |

The existing pool contract is explicit: the backend derives total connection capacity from worker count, pool size, and overflow, and applies PostgreSQL statement and idle-transaction timeouts where supported. No pool values were changed in this command.

## 11. Runtime Configuration and Startup Reliability

The runtime import probe passed with `RUNTIME_MODE=test` and `FEATURE_BACKGROUND_TASKS=false`; the application imported without starting background loops. The startup-guard tests passed, including database/migration readiness contracts, timeout behavior, and runtime isolation. The startup guard requires `alembic_version`, a populated revision row, and required tables before normal readiness, while Redis degradation is explicitly distinguished from critical database failure.

The local probe also demonstrated that an un-migrated in-memory database produces a non-fatal model-sync warning during import. This was not treated as migration success. The full startup guard and migration tests remain the authoritative local checks for readiness behavior.

## 12. Railway Status

**`RAILWAY_UNVERIFIED`**. No Railway connector is configured in the current session, no Railway service/deployment/health/log access was available, and no Railway environment variable values were read or printed. The repository contains a Railway-compatible startup script and probe, but repository files alone are not evidence of a live Railway deployment, commit, health state, migration revision, restart behavior, or database connection.

No attempt was made to create or enable a Railway connector, and no deployment action was performed.

## 13. Vercel Status

The enabled Vercel connector was used only for read-only inspection. The team contained one project named `gula-platform`, and the latest observed deployment for commit `25d0f0deafbefcfde76743223d90544bf63151d6` had state **`BLOCKED`**, target `null`, and an account-configuration error link. The Vercel build-log query returned **no error/stderr/exit events**, indicating that the deployment was blocked before a normal build failure was produced.

| Vercel evidence | Result |
|---|---|
| Project | `gula-platform` |
| Latest inspected commit | `25d0f0deafbefcfde76743223d90544bf63151d6` |
| Deployment state | **BLOCKED** |
| Target | `null` |
| Build errors | None recorded; build did not proceed normally |
| Interpretation | External account/project configuration blocker |

The Vercel state is therefore **BLOCKED**, not PASS. No redeploy, project setting change, deployment-protection change, or domain change was performed.

## 14. Production Database Status

**`UNVERIFIED`**. The command did not connect to, inspect, mutate, migrate, reset, truncate, or otherwise access a production database. No production migration revision, schema version, connectivity, health, or integrity assertion is made.

This is intentional. A production read-only verification would require an explicitly authorized and correctly scoped database connector/environment; its absence cannot be converted into PASS.

## 15. Backup and Recovery

The local disaster-recovery tests passed **10 tests** within the targeted suite and cover deterministic audit-chain restoration, mixed-tenant restore boundaries, anchor HMAC tamper detection, startup readiness protection, and migration rollback-shape invariants. These tests demonstrate application-level recovery properties but do not prove that a production backup can be restored.

No backup file was treated as evidence of restore capability. Retention, RPO, RTO, restore rehearsal, and production backup permissions remain **UNVERIFIED**.

## 16. Security

The security status is **PASS for the executed local scope** and **PARTIAL overall**. The full backend regression, targeted security regression, tenant-isolation matrix, startup-guard, and authorization-related tests passed. No credentials, connection strings, tokens, passwords, or session secrets were printed. No client-controlled verification/session/workspace state, public registration, National Identity activation, OCR/NFC/biometrics, or government integration was enabled.

The Vercel and Railway inspections were read-only. No production DB or deployment operation occurred. Any future production/runtime access must preserve least privilege, secret redaction, fail-closed migration checks, and explicit human approval.

## 17. Test Results

| Test surface | Result |
|---|---:|
| Full backend regression after current changes | **2,719 passed, 4 skipped, 172 warnings** in 320.56s |
| Targeted DR/startup/tenant/security/live-schema suite | **100 passed, 4 skipped, 3 warnings** in 69.86s |
| Migration and migration-resilience suites | **19 passed, 1 warning** in 0.57s |
| Performance/concurrency/backpressure suites | **36 passed, 2 warnings** in 27.06s |
| N806 targeted startup/document/security suite | **111 passed, 53 warnings** in 54.10s |
| Frontend Vitest from Command 02 evidence | **68 passed** |
| Frontend Playwright from Command 02 evidence | **55 passed** |
| Frontend typecheck/lint/build from Command 02 evidence | **PASS** |
| Compose YAML/config assertions | **PASS** for 3 active compose files |
| `git diff --check` | **PASS** |

The four live schema tests skipped for the explicitly missing migration database environment. They remain `UNVERIFIED`, not PASS.

## 18. CI Parity and Deployment Alignment

The repository CI workflow uses PostgreSQL 17 and Redis 7 service containers, Python 3.12, and Node 22 for its main backend path. The quality-gate workflow uses Python 3.14, and backend Dockerfiles use Python 3.14. This is a version-drift observation requiring governance/compatibility review rather than an automatic major-version change.

The local environment passed the relevant suites. Remote GitHub Actions for the prior source commit were blocked externally before runner steps, and the latest Vercel deployment was blocked by account configuration before build events. Railway and production database alignment were not verifiable.

| Alignment item | Status |
|---|---|
| Local source/test environment | **PASS** for executed scope |
| Main CI version contract | **PARTIAL** due 3.12 vs quality-gate/Docker 3.14 drift |
| Railway commit/runtime/database revision | **UNVERIFIED** |
| Vercel deployment for current baseline | **BLOCKED** |
| Production DB revision/schema | **UNVERIFIED** |
| Overall production alignment | **UNVERIFIED** |

## 19. Remaining Blockers

The remaining blockers are environmental and governance-sensitive rather than silently ignored code failures. Docker and PostgreSQL are unavailable in the sandbox, so live migration round-trip, schema comparison, pool measurement, and rollback rehearsal cannot be completed locally. Railway has no configured connector. Vercel is blocked by external account configuration. The offline SQL path has historical introspection incompatibilities beginning at revision `20250322_0001`; resolving every historical offline guard would be a broad migration refactor and is not safe without a dedicated migration architecture review.

The broad quality debt from Command 02 also remains open: legacy import-order/naming/style rules and SQLAlchemy MyPy plugin limitations. The selected dead-code and N806 scopes are closed without gate suppression.

## 20. Human Approval Required

Human approval is required before any destructive or high-risk migration change, SQLAlchemy/dependency major-version migration, architecture restructuring, production database read access, Railway connector configuration, Vercel account/project configuration change, deployment, rollback, branch-protection change, merge, or P5 transition. A production migration must remain explicitly reviewed, reversible where technically possible, and tested against a known-good backup in a non-production rehearsal first.

## 21. Final P4 Gate

| Gate item | Classification | Evidence/limitation |
|---|---|---|
| Database integrity | **PARTIAL** | Local schema/DR tests pass; live PostgreSQL unavailable |
| Migration integrity | **PASS** structurally / **PARTIAL** operationally | Single head, no missing parents; no online round-trip |
| Schema consistency | **PARTIAL** | Application fixtures pass; live PostgreSQL comparison unavailable |
| Tenant isolation | **PASS** locally / **PARTIAL** overall | Local matrix passes; live DB proof unavailable |
| Query performance | **PARTIAL** | Local performance tests pass; no PostgreSQL load measurement |
| Railway status | **UNVERIFIED** | No connector/access |
| Production DB status | **UNVERIFIED** | Intentionally not accessed |
| Runtime configuration | **PASS** statically / **PARTIAL** deployed | Compose assertions pass; Docker/Railway runtime unavailable |
| Backup/recovery | **PARTIAL** | Synthetic DR evidence; no restore rehearsal |
| Rollback | **PARTIAL** | Static downgrade contracts; no online rollback |
| Security | **PASS** local scope / **PARTIAL** deployment scope | Security suites pass; external runtime unverified |
| Tests | **PASS** local | Full and targeted suites pass with documented skips/warnings |
| Production alignment | **UNVERIFIED** | Railway/DB unavailable; Vercel blocked |
| Remaining blockers | **BLOCKED** | External infrastructure and governance prerequisites remain |

## 22. Final Status and Protection

**Infrastructure status:** `INFRASTRUCTURE_PARTIAL`
**P4 status:** `P4_PARTIAL`
**P5 gate:** `P5_BLOCKED_BY_PREREQUISITE`

P5, P5.1, government integrations, National Identity activation, OCR/NFC/biometrics, production migration, production deployment, automatic merge, and Command 04 execution remain prohibited in this task. No status was promoted from PARTIAL or UNVERIFIED to PASS.

## 23. Exact Next Command

**`P4 Command 04` only after the human governance decision resolves the live PostgreSQL/Docker/Railway/Vercel evidence prerequisites; do not start it automatically.** Until then, the safe state is to review this report, restore the authorized non-production infrastructure, and rerun only the missing live checks in an isolated environment.

## References

[1]: ../backend/alembic.ini "GULA Alembic configuration"
[2]: ../backend/migrations/env.py "GULA Alembic environment"
[3]: ../backend/tests/test_migrations.py "Migration chain integrity tests"
[4]: ../backend/tests/test_migration_resilience.py "Migration resilience tests"
[5]: ../backend/tests/test_disaster_recovery.py "Disaster recovery and tenant-boundary tests"
[6]: ../backend/app/core/startup_guard.py "Runtime startup and migration readiness guard"
[7]: ../backend/app/database.py "Database pool, timeout, and connectivity configuration"
[8]: ../docker-compose.yml "Primary compose runtime"
[9]: ../docker-compose.demo.yml "Demo compose runtime"
[10]: ../docker-compose.full.yml "Full compose runtime"
[11]: https://vercel.com/docs/deployments/troubleshoot-project-collaboration "Vercel account/project collaboration troubleshooting"
