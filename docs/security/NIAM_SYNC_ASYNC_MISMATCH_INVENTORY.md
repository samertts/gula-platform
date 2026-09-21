# NIAM Sync/Async Mismatch Inventory

Phase 11 of the "P1 DATA-INTEGRITY + IDEMPOTENCY CLOSURE" workstream.
**Classification only — nothing in this document was repaired.** Per
this workstream's own explicit instruction: no mass conversion, no new
async engine, no second DB pool, no repository-wide rewrite.

## Method

For each of the 8 remaining NIAM route modules (`certificates` and the
`TrustFramework`-specific surface of `trust` are already fixed and
excluded from these counts), inspected:

1. `grep -c "Depends(get_db)"` on `routes.py` — the raw occurrence count.
2. Whether the module's `services.py`/`engine.py` classes declare
   `def __init__(self, session: AsyncSession)` and use
   `await self.session.execute(...)`/`.flush()` (the pattern already
   proven, three times now, to crash under the sync `get_db()`
   dependency — `TypeError: object ... can't be used in 'await'
   expression`).
3. A spot-check of the actual route→service call shape, since one
   module (`lifecycle`) turned out to have a materially different, and
   worse, defect shape than the rest.

## Classification key

- **A** — DB operation incorrectly awaited (the proven shape: sync
  `Depends(get_db)` + `await session.execute(...)`/`.flush()` inside an
  async-styled service — crashes on any real invocation).
- **B** — genuine async I/O (unrelated to the DB mismatch).
- **C** — sync DB operation correctly used (no `await` on the sync
  session anywhere in the call path).
- **D** — dead/unreachable (module not mounted, or a route with no
  working entry point at all).
- **E** — false positive (grep matched, but not actually this defect
  shape).
- **F** — requires architectural conversion (broken in a way a simple
  `get_db` → `get_niam_db` swap cannot fix).

## Per-module results

| Module | `Depends(get_db)` count | Classification | Risk | Live/dead | Recommended treatment |
|---|---|---|---|---|---|
| `governance` | 24 | **A** (confirmed: `def __init__(self, session: AsyncSession)`, `await self.session.execute` throughout `services.py`) | P1 — every mutating route crashes 500 on real use (authenticated, reachable, but non-functional); read routes crash identically | Live (mounted, `_AUTH_REQUIRED` applies) but functionally dead on any DB touch | Same proven fix as `certificates`/`TrustFramework`: swap `get_db`→`get_niam_db`, add `require_platform_capability` + audit + commit where a mutation exists |
| `federation` | 15 (2 of an original ~17 already fixed: `register_provider`, `update_provider`) | **A** | P1 | Live, functionally dead on DB touch | Same fix |
| `lifecycle` | 42 | **F** — distinct and deeper: `services.py`'s five service classes (`EnterpriseRegistrationService`, `WorkforceService`, `GovernmentHRService`, `CitizenService`, `GuardianService`) have **no `__init__`** at all and their methods are plain **synchronous** functions taking `db: Session` as an explicit *parameter* (`def start_registration(self, db: Session, org_id: str, submitted_by: str)`) — yet every route does `svc = EnterpriseRegistrationService(db)` (passing `db` to a constructor with no parameters — `TypeError`) and then `await svc.start_registration(organization_id, submitted_by)` (awaiting a **non-async** method, and never passing `db` to it at all — a second, independent `TypeError`/`AttributeError`). Confirmed identical across all 42 routes via `grep "await svc\."`. This is not a dependency-injection mismatch fixable by swapping one `Depends(...)`; the service layer itself needs to be rewritten to the `def __init__(self, session)` + `await self.session.execute` convention every other module already uses, or the routes need to stop awaiting synchronous calls and pass `db` correctly — either way, a real service-layer rewrite, not a mechanical swap | P1 (correctness — currently 100% non-functional, not merely slow/insecure) | Live (mounted) but **guaranteed to crash on every single route**, not just on DB-touching ones — even `get_enterprise_status` (a read) is broken the same way | Do not apply the certificates/trust pattern here. Needs its own dedicated workstream: decide whether to convert the service layer to the async-session convention (matching the rest of NIAM) or leave it synchronous and fix the routes to call it correctly and use `Depends(get_db)` (still sync) without `await` |
| `workflows` | 8 | **A** (`engine.py`'s `WorkflowEngine.__init__(self, session: AsyncSession)`, `await self.session.execute`/`.flush()` throughout) | P1 | Live, functionally dead on DB touch | Same fix as `certificates`/`TrustFramework` |
| `notifications` | 11 | **A** (`def __init__(self, session: AsyncSession)` confirmed) | P1 | Live, functionally dead on DB touch | Same fix |
| `adaptive_auth` | 16 | **A** (two service classes, both `def __init__(self, session: AsyncSession)` confirmed) | P1 | Live, functionally dead on DB touch | Same fix |
| `admin` | 12 | **A** (`def __init__(self, session: AsyncSession)` confirmed) | P1 | Live, functionally dead on DB touch | Same fix |
| `compliance` | 8 | **A** (`def __init__(self, session: AsyncSession)` confirmed) | P1 | Live, functionally dead on DB touch | Same fix |
| `trust` (remaining, non-`TrustFramework` surface) | 23 (`AssuranceService`, `TrustAnchorService`, `FederationTrustService`, `IdentityProofingService`, `TrustEvaluationService` — all still on `get_db`; `TrustFrameworkService`'s own three routes were fixed this session) | **A** (all five remaining service classes use `def __init__(self, session: AsyncSession)` / `await self.session.execute`, confirmed in the full file read during the prior TrustFramework work) | P1 | Live, functionally dead on DB touch | Same fix |

**Totals:** 162 total `Depends(get_db)` occurrences across these 8
modules (`24+15+42+8+11+16+12+8+26` from the raw grep, of which 3 in
`trust` were fixed this session, leaving 159 open + the 3 already
closed = matches the previously-reported "162+" figure). **120 of these
(governance/federation/workflows/notifications/adaptive_auth/admin/
compliance/trust) are category A** — the identical, already-proven,
mechanical fix pattern. **42 (100% of `lifecycle`) are category F** —
a materially different, deeper defect requiring an actual service-layer
rewrite decision, not a mechanical swap. **Zero D or E found** in this
pass — every module is mounted and reachable, and every occurrence
checked really is this defect shape (no false positives encountered).
**Zero B found** — no genuine non-DB async I/O confused with the DB
mismatch in any of the 8 modules.

## Live risk, in plain terms

None of this is exploitable in the sense of "an attacker bypasses
security" — quite the opposite: every one of these routes currently
**crashes before doing anything**, authorized or not. The real risk is
**correctness/availability**: these are advertised, mounted, documented
NIAM features (governance authorities beyond `create_authority`,
federation provider management beyond the two already fixed, the
entire enterprise/workforce/citizen/guardian lifecycle surface,
workflow definitions, notifications, adaptive auth, admin operations,
compliance checks, and five of `trust`'s six domains) that are **100%
non-functional today** for any caller, not a security gap being
actively exploited. Closing `niam-cert-router-gap` and the
`TrustFramework` gap did not change this — those were the two areas
that had already been identified and separately bounded; this inventory
is the first time the other 8 modules have been counted and classified
as a whole.

## Recommended next dedicated workstream

Two separate workstreams, not one:

1. **The 120 category-A occurrences** (governance/federation/workflows/
   notifications/adaptive_auth/admin/compliance/trust's remaining
   surface): mechanically identical to the fix already proven three
   times (`certificates`, `TrustFramework`, and the original Workstream
   1 five operations) — swap `get_db`→`get_niam_db`, add
   `require_platform_capability`/tenant-appropriate authorization +
   `CanonicalAuditService` + route-level commit per mutating route,
   fix the read routes' broken engine only. Large in occurrence count
   but low in design risk since the pattern is proven; should be its
   own workstream purely because of its size, not its difficulty.
2. **The 42 category-F `lifecycle` occurrences**: needs a design
   decision first (rewrite the service layer to the async convention,
   vs. fix the routes to correctly call synchronous services) before
   any code changes — explicitly out of scope for a mechanical-fix
   workstream.

Neither is attempted here, per this workstream's own explicit
instruction.
