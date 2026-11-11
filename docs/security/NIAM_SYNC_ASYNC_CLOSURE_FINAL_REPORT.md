# NIAM Sync/Async Closure Engine — Directive 4 Final Report

**REAL P0/P1 CLOSURE — BOUNDED BATCHES WITH AUTOMATIC GATES.** All 135
originally-inventoried sync/async defects (`docs/security/
NIAM_SYNC_ASYNC_MISMATCH_INVENTORY.md`) are closed. Every batch passed
through DISCOVER→CLASSIFY→REPAIR→COMPILE→REAL HTTP→REAL POSTGRESQL→
AUDIT→TRANSACTION→FAILURE INJECTION→NEGATIVE PROOF→REGRESSION→COMMIT
before the next batch began.

## REAL CLOSURES table

| # | Batch | Module(s) | Occurrences closed | Commit |
|---|---|---|---|---|
| 1 | 1 | `workflows` | 8 | `98a6a6a9` |
| 2 | 2 | `notifications` | 11 | `420bd5aa` |
| 3 | 3 | `compliance` | 8 | `c52d28d0` |
| 4 | 4 | `admin` | 12 | `f1ccad51` |
| 5 | 5 | `adaptive_auth` | 16 | `c9658d49` |
| 6 | 6 | `federation` | 15 | `ea5be86d` |
| 7a | 7a | `governance` (authorities/councils/review-boards) | 8 | `29694642` |
| 7b | 7b | `governance` (policy-approvals/appeals) | 8 | `42327d93` |
| 7c | 7c | `governance` (suspensions/registry) | 8 | `cdc0c8aa` |
| F1 | lifecycle | `GuardianService` | 6 | `7355e8cf` |
| F2 | lifecycle | `EnterpriseRegistrationService` | 6 | `456183d3` |
| F3 | lifecycle | `WorkforceService` | 9 | `d0464d73` |
| F4 | lifecycle | `GovernmentHRService` | 9 | `b2877358` |
| F5 | lifecycle | `CitizenService` | 11 | `5f984d51` |
| | | **Total** | **135** | |

## SYNC/ASYNC DELTA

```
135 → 127 → 116 → 108 → 96 → 80 → 65 → 57 → 49 → 41 → 35 → 29 → 20 → 11 → 0
```

Batches 1–7 (Category A: `Depends(get_db)` yielding a sync `Session`
awaited as async) closed 94 occurrences (135→41). Lifecycle Category-F
(genuine service-layer defects — no `__init__`, or a partially-converted
one, requiring a full async rewrite, not a dependency swap) closed the
remaining 41 (41→0).

## Per-module status (final)

| Module | Status | Authorization outcome |
|---|---|---|
| `workflows` | SYNC/ASYNC CLOSED | Pre-existing (untouched this workstream) |
| `notifications` | SYNC/ASYNC CLOSED | Pre-existing (untouched) |
| `compliance` | SYNC/ASYNC CLOSED | Pre-existing (untouched); 1 pre-existing unrelated bug documented (`func.case` misuse in `get_org_compliance_status`), not fixed |
| `admin` | SYNC/ASYNC CLOSED | Pre-existing (untouched); 1 pre-existing unrelated bug documented (`add_department` business-key/internal-id FK mismatch), not fixed |
| `adaptive_auth` | SYNC/ASYNC + AUTHORIZATION CLOSED | Self-ownership (`account_id == actor.account.id`) added to account/session-scoped routes; 2 pre-existing unrelated bugs found, 1 fixed (FK target correction, zero schema risk), 1 documented (`account_type` referenced but column doesn't exist), not fixed |
| `federation` | SYNC/ASYNC + AUTHORIZATION CLOSED | `federation_manage` capability + self-checks added |
| `governance` (7a/7b/7c) | SYNC/ASYNC + AUTHORIZATION CLOSED | `governance_manage` capability added to all mutations; 1 ambiguity documented (`submit_appeal` self-submission), 1 pre-existing unrelated bug documented (`certify_identity`'s `or ""` FK fallback), neither fixed |
| `lifecycle.GuardianService` | SYNC/ASYNC + AUTHORIZATION CLOSED | 5 self-owned, 1 fails closed (`verify_guardianship`) |
| `lifecycle.EnterpriseRegistrationService` | SYNC/ASYNC + AUTHORIZATION CLOSED | All mutations gated by `governance_manage` (direct reuse); 2 in-scope bugs fixed (`_add_step` uuid collision, audit action-string schema drift) |
| `lifecycle.WorkforceService` | SYNC/ASYNC + AUTHORIZATION CLOSED | All 8 mutations fail closed (no capability fits, zero self-service angle) |
| `lifecycle.GovernmentHRService` | SYNC/ASYNC + AUTHORIZATION CLOSED | All 9 fail closed (same reasoning, no read route) |
| `lifecycle.CitizenService` | SYNC/ASYNC + AUTHORIZATION CLOSED | Mixed: 7 self-owned (2 different ownership directions), 3 fail closed; 1 in-scope bug fixed (`GuardianAccount.uuid` composite too long) |

**REAL SECURITY CLOSURE ONLY**: no module above is counted as closed
merely because its async crash disappeared. Every module with a
mutating, newly-reachable route received an explicit authorization
decision — capability reuse where semantics genuinely fit
(`governance_manage`, `federation_manage`), self-ownership checks where
the resource is actor-scoped, or a deterministic fail-closed 403 where no
legitimate authority exists yet, never a silent bare-authentication
default.

## SECURITY PROOFS

Every authorization boundary added this workstream was proven with a real
HTTP request matrix (401 no-token / 403 wrong-actor-or-capability / 200
valid-access where applicable) **and** a negative proof: the check was
temporarily removed, the expected 403→200 flip was confirmed via a real
request, and the file was restored from a pre-change backup with
`md5sum`-verified byte-identical restoration before continuing. This
was done independently for every batch (13 negative proofs total across
batches 5, 6, 7a/b/c, and lifecycle F1–F5; batches 1–4 added no new
authorization surface, only dependency fixes).

## DATABASE PROOFS

Every batch's mutations were proven against a real, disposable local
PostgreSQL 16 cluster (`gula_certproof` database) with fresh-session
persistence checks (a separate connection/session confirming what was
actually committed, not just what the request handler returned) and a
commit/flush-failure injection (via `unittest.mock.patch.object` on
`AsyncSession.commit`/`.flush`) confirming clean rollback with no partial
or orphaned writes.

## REGRESSION

Every batch ran the identity + migration test suite
(`pytest tests/identity/ tests/test_migrations.py
tests/test_migration_resilience.py`) before and after its changes, with
zero regressions at any point:

```
Batch 1–7 baseline (pre-lifecycle): 255 passed, 4 skipped
F1 (GuardianService):                262 passed, 4 skipped  (+7 tests)
F2 (EnterpriseRegistrationService):  266 passed, 4 skipped  (+4 tests)
F3 (WorkforceService):               275 passed, 4 skipped  (+9 tests)
F4 (GovernmentHRService):            284 passed, 4 skipped  (+9 tests)
F5 (CitizenService):                 295 passed, 4 skipped  (+11 tests)
```

40 new permanent regression tests added across the 5 lifecycle classes,
each proving the specific authorization boundary added (self-ownership
pass/fail, fail-closed-for-everyone, capability-gate pass/fail).

## AUTONOMOUS ENGINEERING

**NOT STARTED.** No autonomous-engineering batch (independent findings
sweep with a forced-rollback demonstration) was run in this continuation.
This is listed as an open item below, not fabricated.

## ARCHITECTURE

No architecture regression check was run in this continuation beyond the
per-batch identity+migration suite. The lifecycle work stayed entirely
within the existing NIAM async DB boundary (`get_niam_db`/
`open_niam_session`, a second connection pool bound to the same database,
established in a prior session) — no new engine, pool, or DB dependency
was introduced. `CLAUDE.md`'s pool-budget formula is unaffected (this
workstream added zero new pool configuration).

## PRODUCTION READINESS

`docs/architecture/PRODUCTION_READINESS_DELTA.md` was **not updated** in
this continuation. This is an explicit gap — the file should be updated
to reflect that all 135 NIAM sync/async defects (and the authorization
gaps discovered alongside 3 of them: `adaptive_auth`, `federation`,
`governance`) are now closed, before this work is considered fully
integrated into the platform's production-readiness record.

## REMAINING P0/P1/P2

**P1 (documented, not fixed — each independently pre-existing and orthogonal to sync/async):**
1. `compliance.get_org_compliance_status`: `func.case(...)` misuse.
2. `admin.add_department`: passes business `facility_id` instead of
   internal id to a NOT-NULL FK.
3. `adaptive_auth.AdaptiveMFASession.session_id`: FK referenced a
   nonexistent table (this one **was fixed** — zero-schema-risk
   correction; listed here for completeness of the discovery, not as
   outstanding).
4. `adaptive_auth`: `UserSession.account_type` referenced by
   `is_session_valid`/`check_session_expiry` but the column doesn't exist.
5. `governance.certify_identity`: `certifying_authority_id or ""` against
   a NOT NULL FK.
6. `lifecycle` (file-wide, all 5 classes): no route catches the service
   layer's `ValueError` "not found" exceptions — produces `500` instead
   of a clean `404`. Confirmed on nonexistent `guardian_id`/`reg_id`/
   `citizen_id`.
7. `GuardianService.create_guardianship` (already `VERIFIED`): latent
   `uuid=guardian_id` length risk for caller-supplied `guardian_id`
   values over 36 chars — same defect shape as two bugs fixed elsewhere
   this workstream, not yet triggered, not yet fixed.

**P2 (design ambiguity, documented, not resolved):**
8. `governance.submit_appeal`: unclear whether appeal self-submission
   should be self-service or administrative — left authenticated-only
   pending a human decision.

**Zero P0s remain open.** The one real P0 found this workstream
(`adaptive_auth`'s missing authorization on account/session-scoped
routes, item 3's sibling finding) was closed in Batch 5, with the user's
explicit authorization.

## BEFORE → AFTER

| | Before this workstream | After this workstream |
|---|---|---|
| Sync/async defects | 135 | **0** |
| NIAM routes with a silent, unreviewed authorization gap | Unknown (undiscovered until each batch's routes became reachable) | 0 — every mutating route has an explicit, documented decision |
| Lifecycle service classes with a working constructor | 0 of 5 (`EnterpriseRegistrationService` partially) | **5 of 5** |
| Permanent regression tests for NIAM authorization boundaries (this workstream) | 0 | **40** (lifecycle alone; batches 5–7 also added their own, tracked in their respective status docs) |
| Known, documented, unfixed pre-existing bugs (orthogonal to this workstream) | 0 documented | 8 documented (7 P1, 1 P2) |

## EXACT NEXT ACTION

This continuation's scope (finish lifecycle Category-F with full proof
rigor) is complete. The following were referenced as later phases of the
broader directive but were **not started** in this continuation and
should be explicitly scoped and confirmed before beginning:

1. Detector improvements (referenced as a later phase; no detailed spec
   available in this continuation's context to execute against).
2. An autonomous engineering batch (≤5 findings, at least one forced
   rollback) — not run.
3. An architecture regression check beyond the per-batch identity suite —
   not run.
4. A decision on running the full (non-identity-scoped) test suite — not
   made.
5. A final P0/P1/P2 sweep across the whole codebase (beyond the 8 items
   documented above, which are limited to what surfaced incidentally
   during this workstream) — not run.
6. `docs/architecture/PRODUCTION_READINESS_DELTA.md` — not updated.

Per the directive's own closing instruction: **STOP after this report.
Do not automatically launch another workstream.**
