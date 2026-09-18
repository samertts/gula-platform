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
| 6 | Core clinical path | **NOT STARTED** | — |
| 7 | Frontend ↔ backend | **NOT STARTED** | — |
| — | Golden path (§24) | **NOT RUN** | Steps 1–6 hold in isolation; the sequence has not been run end to end. |
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
| NR-118 | P2 | 87 unit tests fail only when the suite runs together | **OPEN** — measured at HEAD and after: identical, so not a regression |
| NR-119 | P1 | Three clinical read endpoints 500 — `national_patients` is built by no migration | **OPEN** — the fix is a migration, which CLAUDE.md reserves |

## CRITICAL — do next, in this order

| ID | Action | Verification | Depends on |
|----|--------|--------------|------------|
| G6-a | Gate 6: login → org context → patient → check-in → queue → encounter → note → order → specimen/result → audit | real endpoints only; no parallel workflow built to make a demo pass | — |
| G7-a | Frontend ↔ backend: a real login and one real read from `frontend-v2` | browser or fetch against the running API | G6-a |
| NR-119 | Decide whether `national_patients` gets a migration or the three routes get retired | `alembic upgrade head` on a clean DB, then the three routes answer | human approval |

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
migrates to head, starts, bootstraps, and passes 43/43 runtime checks across
authentication, revocation, rate limiting, account lockout, authorization and
two-tenant isolation. Reproduce with the commands under *Verification* below.

It is not a production candidate: the core clinical path (gate 6) has not been
run end to end, the frontend has not been exercised against the API, and NR-114
is open.

**Deployment: BLOCKED.** Two reasons, both specific:
1. NR-114 — MFA is an enrolment checkbox, not a challenge, so a stolen password
   alone still yields a full privileged session.
2. Gate 6 unproven — no evidence yet that the clinical path works end to end.

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
python3 scripts/runtime_gates.py --base http://127.0.0.1:8000  # -> 43/43, exit 0

# the guards CI runs
cd backend && python3 -m pytest tests/test_runtime_activation_guards.py -q
```
