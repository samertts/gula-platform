# NIAM Sync/Async Closure Engine — Lifecycle Category-F: Consolidated Status

Consolidates the 5 lifecycle class closures (`docs/security/
NIAM_SYNC_ASYNC_LIFECYCLE_F1_GUARDIAN_STATUS.md` through `..._F5_CITIZEN_STATUS.md`)
into one summary. This is the final piece of the overall 135-occurrence
NIAM sync/async closure workstream (Batches 1–7 covered the other 94).

## Why lifecycle was different from every prior batch

Batches 1–7 (workflows, notifications, compliance, admin, adaptive_auth,
federation, governance) were uniformly **Category A**: a route declared
`db: AsyncSession = Depends(get_db)` against an already-async service, and
`get_db` actually yields a plain sync `Session` — a dependency-typing
mismatch, fixed by swapping to `get_niam_db`.

Lifecycle's 5 service classes were **Category F**: real service-layer
defects, not just a dependency swap —

| Class | Defect shape |
|---|---|
| `GuardianService` | No `__init__`, methods took explicit `db: Session`, legacy `db.query()` API. |
| `EnterpriseRegistrationService` | `__init__` already converted (prior session's one representative repair), but 6 remaining methods still sync — a real **arity mismatch** (routes called them as if `db` were bound) plus a missed `await` on the now-async `_add_step`. |
| `WorkforceService` | No `__init__` at all — construction-time `TypeError` (`WorkforceService(db)` against a class with no constructor), before the method call is even attempted. |
| `GovernmentHRService` | Identical shape to `WorkforceService`. |
| `CitizenService` | Identical shape to `WorkforceService`/`GovernmentHRService`. |

Each required a genuine service-layer rewrite (constructor, session
storage, `select()`-based async queries, audit calls) — never a
mechanical find-replace, per the explicit rule that structurally
different code must not receive the same mechanical transformation.

## Authorization outcomes by class

| Class | Routes | Outcome |
|---|---|---|
| `GuardianService` | 6 | 5 self-owned (actor's own person must match guardian/dependent), 1 fails closed (`verify_guardianship` — no capability models a real-world verifying authority). |
| `EnterpriseRegistrationService` | 6 (+1 pre-existing) | All 5 mutations gated by `governance_manage` — direct reuse of the capability already established by this same class's `start_registration`. 1 read, authenticated-only. |
| `WorkforceService` | 9 | All 8 mutations fail closed (zero self-service angle, no fitting capability). 1 read, authenticated-only. |
| `GovernmentHRService` | 9 | All 9 fail closed (zero self-service angle, no read route at all). |
| `CitizenService` | 11 | Genuine mixed model: 7 self-owned (5 on the citizen's own person, `link_guardian` self-checked on the **guardian** side instead), 3 fail closed (`verify_identity`, `issue_health_id`, `record_death` — the last inherently third-party). |

**No capability was ever invented.** Every fail-closed route got a
deterministic `403` via `_require_admin_authority_unavailable()`
(mirroring the established `_POLICY_AUTHORITY_UNAVAILABLE` precedent from
`adaptive_auth`), documented as a real, human-reviewable authorization
gap rather than silently left authenticated-only or papered over with a
misapplied capability.

## Pre-existing, unrelated bugs found and fixed (in-scope — inside methods being converted)

1. **`EnterpriseRegistrationStep.uuid=step_name`** (class 2): global
   uniqueness collision across ANY two registrations system-wide reaching
   the same step — fixed with a real `uuid4()`.
2. **Audit `action` column schema drift** (class 2): deployed
   `niam_audit_entries.action` is `varchar(50)`, not the ORM model's
   `String(120)` — one new action string shortened to fit; documented as
   a pre-existing, unrelated schema/model drift, not migrated in this
   batch.
3. **`GuardianAccount.uuid` composite too long** (class 5, `CitizenService.
   link_guardian`): same defect shape as #1 — fixed with a real `uuid4()`.

**Related, deliberately left untouched**: `GuardianService.
create_guardianship` (class 1, already `VERIFIED`) has the identical
latent `uuid` risk for long caller-supplied `guardian_id` values — not
triggered by that class's own proof, and not reopened here to avoid
unreviewed scope creep into an already-closed class.

**Also documented, not fixed** (orthogonal to sync/async and
authorization, pre-existing, file-wide): none of `lifecycle/routes.py`'s
routes catch the service layer's `ValueError` "not found" exceptions,
producing `500` instead of a clean `404` — confirmed on nonexistent
`guardian_id`/`reg_id`/`citizen_id` across classes 1, 2, and 5.

## Proof summary across all 5 classes

Every class received: compile check, a real HTTP + real PostgreSQL proof
(full matrix per its authorization model — self/other/no-token for
self-owned routes; blocked-for-everyone for fail-closed routes, split
into an HTTP-level proof plus a direct service-layer proof against real
PostgreSQL bypassing the gate, for classes 3 and 4 where the gate blocks
100% of mutations), a commit/flush-failure injection with fresh-session
rollback verification, a negative proof (temporarily removing the
authorization check, confirming the exact expected 403→200 flip, then
restoring the file and verifying byte-identical via `md5sum`), permanent
regression tests, and a full identity+migration suite run.

| Class | New regression tests | Suite total after |
|---|---|---|
| `GuardianService` | 7 | 262 passed, 4 skipped |
| `EnterpriseRegistrationService` | 4 | 266 passed, 4 skipped |
| `WorkforceService` | 9 | 275 passed, 4 skipped |
| `GovernmentHRService` | 9 | 284 passed, 4 skipped |
| `CitizenService` | 11 | 295 passed, 4 skipped |

Zero regressions at any point across all 5 classes (baseline before
lifecycle work: 255 passed, 4 skipped).

## RESULT — Lifecycle Category-F: **COMPLETE, all 5 classes VERIFIED**

41/41 occurrences closed (`GuardianService` 6, `EnterpriseRegistrationService`
6, `WorkforceService` 9, `GovernmentHRService` 9, `CitizenService` 11).
Combined with Batches 1–7's 94 occurrences, this closes all **135/135**
sync/async defects in the original inventory. See
`docs/security/NIAM_SYNC_ASYNC_CLOSURE_FINAL_REPORT.md` for the
directive-level consolidated report across the entire workstream.
