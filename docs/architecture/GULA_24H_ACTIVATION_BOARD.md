# GULA — 24-hour activation board

Recalculated from execution, not from prior status. Every state here was
produced by running the thing it describes; nothing is inherited from an
earlier report.

- **Runtime proved against:** PostgreSQL 16 (`gula_run`, created empty),
  Redis 7, uvicorn serving `app.main:app` on 127.0.0.1:8000.
  No SQLite substitution — PostgreSQL is the production target, so PostgreSQL
  is what the gates ran on.
- **Branch:** `claude/p0-2-pharmacy-reconciliation` (PR #258).

## Gate status

| # | Gate | State | Evidence |
|---|------|-------|----------|
| 1 | System startup | **VERIFIED** | Kernel booted, startup guard passed in 1124–1915 ms across 7 consecutive cold boots. `system_ready: true`; `/health`, `/health/ready` 200 with a live DB pool; 1794 paths served in the OpenAPI contract. |
| 2 | Database | **VERIFIED** | `alembic upgrade head` from an empty database → 423 tables, head `20260916_0001`, exit 0. Migration → startup → query → write → read all exercised by the gates below. |
| 3 | Authentication | **VERIFIED** | 21/21 checks, every one with a positive control. Valid credential accepted; wrong password, unknown account, no credential, malformed token, expired token, unapproved lab all rejected; refresh issues a working token; logout revokes; a login burst is rate limited; a locked account is refused *with the right password* and works again once unlocked. `scripts/runtime_gates.py` gates 3, 3b, 3c, 3d. |
| 4 | Authorization | **VERIFIED** | 11/11. A lab admin reads its own session, its own patients and its own lab profile, and is refused another lab's profile, the pending queue, lab creation, lab approval and lab deactivation. An expired token is refused a tenant read. Its audit view contains no other tenant's rows. |
| 5 | Tenant isolation | **VERIFIED** | 11/11. Beta cannot read, update, list, search or id-guess Alpha's patient. Three alternate EHR routes answer 500 for *everyone* including the owner — classified UNAVAILABLE (NR-119), not scored as isolation, because a route broken for every caller leaks nothing tenant-specific. |
| 6 | Core clinical path | **VERIFIED, with two steps UNAVAILABLE** | 14/14. Organization context → patient → order → specimen (barcoded) → result entry → read-back → audit. The optimistic lock is driven, not routed around: no `If-Match` → 428, stale `If-Match` → 409, observed version → 200, and the value reads back. The audit chain carries ('create', patient), ('create', lab_order) and ('create', sample). CHECK-IN and CLINICAL NOTE answer 500 for everyone and are reported UNAVAILABLE (NR-119, NR-121), not skipped. |
| 7 | Frontend ↔ backend | **PARTIALLY VERIFIED (contract only)** | frontend-v3 calls 434 distinct backend paths; 367 are served, 67 are not. One backend fix (NR-122) took that from 83 to 67 by removing a doubled `/niam/niam/` prefix on 60 routes. 21 of the remaining 67 are malformed on the frontend side (NR-123). No browser run yet — this is contract alignment, not a rendered login. |
| — | Golden path (§24) | **VERIFIED to step 13** | Infrastructure → database → migrations → backend → login → organization context → authorization → patient access → clinical workflow → mutation → audit → logout all run in one sequence from a dropped database. Steps 5 (frontend) and 14–15 (restart, coherence after restart) are not yet included. |
| — | Clean-start test (§25) | **VERIFIED through gate 5** | Empty database → 423 tables → server start → bootstrap → MFA enrolment → login → 43/43 gates, run three times from a dropped database and a flushed Redis. The clinical path beyond patient creation is not yet included. |

## Findings closed today

| ID | Sev | Title | State |
|----|-----|-------|-------|
| NR-111 | P0 | A fresh deployment could not be administered at all | **CLOSED** — out-of-band enrolment, proven live, CI-gated |
| NR-112 | P1 | The documented master-admin recovery script crashed before it did anything | **CLOSED** — 8 undefined names in `scripts/` → 0 |
| NR-113 | P1 | Twenty-six SQL filters compiled to `WHERE false` | **CLOSED** — 26 → 0, approval queue 0 → 2 labs |
| NR-114 | P1 | MFA is enforced as an enrolment checkbox, never as a challenge | **OPEN** — fix changes `/login`'s response shape, which CLAUDE.md reserves |
| NR-115 | P0 | Logout was a no-op for every non-browser client | **CLOSED** — both revocation layers now run for bearer sessions |
| NR-116 | P0 | Any lab admin could approve, create and switch off other laboratories | **CLOSED** — five handlers gained the platform-scope check |
| NR-117 | P0 | `POST /patients` answered 500 for every request on PostgreSQL | **CLOSED** — health_id and gender both overflowed their columns |
| NR-118 | P2 | 87 unit tests fail only when the suite runs together | **CLOSED** — single root cause found (NR-126). 87 → **0** failures, 3021 → 3126 passes |
| NR-124 | P2 | A test imported through the shadow package root two findings exist to prevent | **CLOSED** — import corrected, guard widened from `app/engineering/` to all of `backend/` |
| NR-125 | P3 | Two startup-guard tests set an env var the code had already frozen into a constant | **DIAGNOSIS CORRECTED** — a symptom of NR-126, not a cause; the change stays as hardening |
| NR-126 | P1 | A config-isolation helper evicted `app.config` from `sys.modules` and never put it back — 86 tests answered 503 | **CLOSED** — three-file minimal reproducer, 4/4 negative proofs, suite 84 → 0 |
| NR-119 | P1 | Four clinical endpoints 500 — `national_patients` is built by no migration | **OPEN** — the fix is a migration, which CLAUDE.md reserves |
| NR-120 | P2 | Clinical audit rows carry a NULL `lab_id` | **OPEN** — nothing leaks today; any query keyed on `lab_id` misses them |
| NR-121 | P1 | Patient check-in 500s — `nhdw_queue_entries.encounter_id` is in the ORM, not the table | **OPEN** — the fix is a migration, which CLAUDE.md reserves |
| NR-122 | P1 | Sixty identity routes served at `/niam/niam/…`, which no client calls | **CLOSED** — 24 frontend calls now reach a real endpoint |
| NR-123 | P2 | 21 frontend calls request a path with an empty segment — and the contract guard skipped exactly those | **OPEN** — declared in a shrink-only ledger; the guard no longer skips them |

## CRITICAL — do next, in this order

| ID | Action | Verification | Depends on |
|----|--------|--------------|------------|
| G6-a | Gate 6: login → org context → patient → check-in → queue → encounter → note → order → specimen/result → audit | real endpoints only; no parallel workflow built to make a demo pass | — |
| G7-a | Frontend ↔ backend: a real login and one real read from `frontend-v2` | browser or fetch against the running API | G6-a |
| NR-119 | Decide whether `national_patients` gets a migration or the four routes get retired | `alembic upgrade head` on a clean DB, then the three routes answer | human approval |

## HIGH

| ID | Action | Depends on |
|----|--------|------------|
| NR-114 | Make MFA a challenge, not a checkbox. Needs a decision on `/login`'s response shape for privileged accounts. | human approval |
| G7-a | Frontend ↔ backend: prove a real login and one real read from `frontend-v2`. | G3-a |
| DEMO | §19 demo mode: synthetic, clearly marked, isolated. `generate_demo_data.py` runs again now that NR-112 is closed, but has not been executed end to end. | G6-a |

## DEFERRED (explicitly, with reason)

| Item | Reason |
|------|--------|
| Ghidra integration | §28 — out of scope for this window |
| Financial Engine business logic | CLAUDE.md: Phase A is schema-only, changes need approval |
| Migration-backed fixes for NR-110's two unbuilt audit tables | CLAUDE.md reserves DB schema changes |
| CI workflow edits to extend the F821 gate over `scripts/` | CLAUDE.md reserves `.github/workflows/`; the guard was put in pytest instead, which CI already runs |
| Cosmetic and architectural refactors | §27 — nothing that does not contribute to running or securing the system |

## Platform readiness (§35)

**C — RUNNABLE, CORE VERIFIED.** On a clean PostgreSQL database the system
migrates to head, starts, bootstraps, and passes 57/57 runtime checks across
authentication, revocation, rate limiting, account lockout, authorization,
two-tenant isolation and the core clinical path. Reproduce with the commands
under *Verification* below.

It is not a production candidate: the frontend has not been exercised against
the API, check-in and clinical notes are unavailable (NR-119, NR-121), and
NR-114 is open.

**Deployment: BLOCKED.** Three reasons, all specific:
1. NR-114 — MFA is an enrolment checkbox, not a challenge, so a stolen password
   alone still yields a full privileged session.
2. NR-119 and NR-121 — check-in, queue and clinical notes answer 500 on a
   migration-built schema. Both fixes are migrations, which CLAUDE.md reserves.
3. No frontend evidence — the API is proven, the product is not.

## Verification — the exact commands

```bash
# clean slate
redis-cli -n 0 FLUSHDB
psql -c "DROP DATABASE IF EXISTS gula_run;" -c "CREATE DATABASE gula_run;"
(cd backend && alembic upgrade head)          # -> 423 tables, head 20260916_0001

# start the real server, then bootstrap the one account that exists
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000   # in backend/
python3 scripts/enroll_mfa.py --role master_admin              # NR-111

# the gates
python3 scripts/runtime_gates.py --base http://127.0.0.1:8000  # -> 57/57, exit 0

# the guards CI runs
cd backend && python3 -m pytest tests/test_runtime_activation_guards.py -q
```
