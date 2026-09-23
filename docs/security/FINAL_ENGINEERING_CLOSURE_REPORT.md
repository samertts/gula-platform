# Final Engineering Closure Report — This Continuation

Scope note first: this directive's 14 phases are, collectively, a
multi-week program. This continuation performed Phase 0 (baseline) in
full and Phase 2 (idempotency) as a bounded, real investigation. Phases
1, 3, 4 (beyond what was already closed before this continuation began),
5 (partially, via the `capabilities` correction), 6–13 were **not**
attempted this pass. Per this directive's own success condition
("Minimum Resources → Maximum Verified Result... do not broaden scope
simply because additional defects are discovered"), no code was changed
this pass — both real findings (the dormant idempotency module, the dead
`capabilities` routers) had no live, reachable defect to fix, so fixing
them would itself have been unjustified scope expansion. Every phase not
covered is marked NOT STARTED below, not silently dropped.

## 1. HEAD commit
`3c04462acc1bc39ebf09697fab37869add725d83` (unchanged this pass — no commit made, since no code changed)

## 2. Branch
`claude/mustafa-parallel-engineering`

## 3. Baseline test counts
320 passed, 4 skipped (focused regression tier, at start of this continuation)

## 4. Tests added
0 (no code defect found this pass required a fix)

## 5. Tests passed
320 passed, 13 skipped (the +9 skips are `tests/blood_bank/test_failure_injection_postgres.py`'s env-gated Postgres tests, skipped when `BLOOD_BANK_POSTGRES_URL` isn't set for a plain run — already independently re-verified 32/32 green against a real Postgres 16 database earlier this session)

## 6. Tests failed
0

## 7. Migrations added
0

## 8. Migrations changed
0

## 9. P0
Closed: 0 new this pass (0 P0s were found — both new findings are P2/documentation-only). Open: 0 known. Blocked: 0. Unknown: 0.

## 10. P1
Closed: 0 new this pass. Open: 0 known beyond what's already tracked (governance/national schema gaps are P1-shaped but architecturally BLOCKED, not open work items). Blocked: 2 (governance schema, national schema — unchanged, pre-existing).

## 11. Authorization coverage
**NOT STARTED this pass.** No repo-wide route→capability→scope machine-readable inventory exists yet. Existing coverage: NIAM identity governance (`app/identity/governance/`) hardened in a prior pass (batches 7a/7b/7c); the 9 already-closed vertical-slice domains (Laboratory, Imaging, EMS, Nursing, NHDW, Payments, Devices, Biomedical, Command Center, Public Health) each individually verified their own role-gate/tenant-scope coverage as part of their CAS audits, but that is not the same as the repo-wide capability-taxonomy inventory Phase 1 asks for.

## 12. Idempotency coverage
**PARTIALLY VERIFIED this pass** — see `docs/security/IDEMPOTENCY_CLOSURE_STATUS.md`. 7 mechanisms inventoried and classified: 4 VERIFIED SAFE / ACTIVE (`ClinicalCommandGuard`, payments, devices outbox, canonical outbox_service), 1 DORMANT with a documented latent race (`app/core/idempotency.py`), 2 DEAD (`kernel/event_bus/outbox.py`, and 9 of 10 `app/capabilities/*` routers — the latter newly discovered this pass). A full per-endpoint idempotency-necessity questionnaire across every LIVE domain was **not** performed.

## 13. Transaction integrity coverage
**NOT STARTED as a dedicated pass this pass.** Incidentally verified as part of each of the 6 already-closed CAS fixes this session (each proved its own commit/rollback correctness), and `ClinicalCommandGuard`'s claim/complete contract is explicitly documented at the source. No repo-wide trace of every LIVE mutation's transaction boundary was performed.

## 14. Concurrency coverage
6 real defects closed this session total (payments, devices, biomedical, command_center, public_health — 5 domains), 2 domains independently re-verified already-safe (blood_bank, critical_care). Systemic pattern registered after the 3rd instance. No new concurrency defect found or fixed this specific continuation.

## 15. Schema blockers
Unchanged: governance (58/64 tables missing), national (103/114 missing), plus 7 smaller schema-latent domains — all BLOCKED, human-approval required, none touched this pass (per explicit instruction not to fabricate migrations).

## 16. CI status
**BLOCKED / UNKNOWN — external infrastructure**, unchanged. Reproduced identically (`runner_id=0`, ~0ms execution, no runner dispatch) on every commit pushed this session, including the most recent (`3c04462a`). Documented once; not re-litigated on each new push per this session's own standing rule, consistent with this directive's Phase 11 instruction.

## 17. Autonomous engineering evidence
No autonomous self-audit-agent run was invoked this pass (Phase 9 not exercised). The existing hardened mechanism (`scripts/self_audit_agent.py`, hardened in a prior session with path allow-list/change-budget/exact-scope-rollback/impact-aware verification) was not re-run — no autonomous fix cycle was needed since this pass's findings had no live defect to autonomously patch.

## 18. Production readiness matrix
Not rebuilt this pass. `docs/architecture/PRODUCTION_READINESS_DELTA.md` (pre-existing) was not updated — no new evidence from this pass changes its categories beyond what `docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md` and `docs/security/NEXT_CLOSURE_BASELINE.md` already record. Rebuilding the full 38-category matrix from evidence (Phase 12) is explicitly deferred, not fabricated.

## 19. Remaining blockers
- Governance schema (58/64 tables) — human-approved migration + domain-owner scoping required.
- National schema (103/114 tables) — same.
- CI — external account/org-level GitHub Actions block, outside this repo's control.
- Full Authorization Expansion registry — not started.
- Full Transaction Integrity trace — not started.
- Full per-endpoint Idempotency-necessity audit — not started (mechanism inventory done; per-endpoint requirement analysis is not).
- Certificates/Trust/Federation re-audit — not started this pass.
- AI/Clinical safety re-check — not started this pass.
- Production Readiness matrix rebuild — not started this pass.

## 20. Exact next highest-value action

Two candidates, evidence-ranked:

1. **Wire up the fix for `app/core/idempotency.py`'s latent race before anyone activates it on a real route** — cheap, already fully diagnosed, zero schema risk (add a `rowcount` check after the `ON CONFLICT DO NOTHING` insert). Not done this pass because there is no live route to prove it against yet; doing it now would be a speculative fix to dead code, which this directive explicitly discourages. Correct trigger: the moment any PR proposes wiring `idempotency_check` into a real route, this fix must land first.
2. **Begin the Authorization Expansion capability inventory (Phase 1) as its own bounded pass**, starting from the routes already vertical-slice-audited this session (their role-gates are already known and correct) and extending outward — this is the largest genuinely-not-started phase of this directive and the one most directly requested (Sections A and Phase 1 both name it first).

Neither was started this pass beyond the groundwork above, to keep this
continuation's change set matched to what was actually verified, per
this directive's own success condition.

---

## Addendum — Authorization Coverage Batch 2 (reconciling §11 above, not overwriting it)

§11 above ("Authorization coverage — NOT STARTED this pass") is a
historical snapshot from the pass that wrote it, predating the
Authorization Expansion / Capability Inventory work that followed.
Reconciling forward: the capability inventory has since progressed
through several bounded batches (`docs/security/
AUTHORIZATION_COVERAGE_MATRIX.md`, `docs/security/
AUTHORIZATION_GAP_REGISTER.md`), most recently "Batch 2" (this pass):

- **5 domains traced**: billing, lifecycle_platform, pilot_platform,
  `services/mpi`, `capabilities/fhir_interoperability` — 23 mutating
  routes.
- **1 P0 found and CLOSED**: `lifecycle-platform-no-auth` — zero
  authentication on all 19 routes of `app/lifecycle_platform/api/routes.py`,
  proven live (unauthenticated `POST /lifecycle/components` → 201),
  fixed with a router-level `require_permission("system:admin")` gate,
  proven post-fix (401/403/201 matrix), negative-proofed via
  `git stash`/`git stash pop` with md5-verified byte-identical
  restoration, covered by a new permanent regression test
  (`backend/tests/test_lifecycle_platform_auth.py`, 3/3 passing), zero
  collateral regressions across a 178-test focused sweep
  (identity/tenant-isolation/feature-flags/blood_bank/biomedical/
  command_center/device-outbox/payments/public_health).
- **2 non-authorization concurrency findings documented, not fixed**
  (P2/P3, in scope only to record per this batch's own disposition
  rule): billing's `simulate_settlement`/`advance_claim` share the
  session's registered systemic concurrency pattern (no row lock);
  `create_invoice` doesn't catch `IntegrityError` on its idempotency-key
  race.
- **3 domains re-verified/confirmed clean**: `pilot_platform` (a prior
  session's P0 fix, still in place), `services/mpi/api.py`,
  `capabilities/fhir_interoperability/routes.py`.

Cumulative coverage-matrix totals after Batch 2: ~395 live mutating
routes now have route-level authorization evidence (up from ~372); the
UNKNOWN bucket is ~73 of 89 mounted routers (down from ~78). **This is
still not "authorization complete" or "all routes protected."** ~73
routers remain untraced. See the coverage matrix's own "Scope and
honesty note" for the full remainder and the explicit do-not-repeat
list for the next bounded batch.

---

## Addendum 2 — Authorization Coverage Batch 3 (reconciling §11/Addendum 1)

Continuing forward from Addendum 1 (Batch 2): **Batch 3** traced 5 more
domains from the `LIVE / NO-OWNED-MODELS` bucket —
`consent`, `patient_card`, `canonical_patient`, `service_accounts`,
`mfa` — 17 mutating routes total.

- **0 P0/P1/P2/P3 findings.** All 5 domains read as correctly
  authorized: `consent` (self-or-admin ownership check),
  `patient_card` (lab-scoped + HMAC token binding + audit-logged, per
  its own CLAUDE.md invariant), `canonical_patient` (a pre-existing
  fix, "NR-148", re-verified rather than assumed), `service_accounts`
  (role check + real DB-level `lab_id` scoping), `mfa` (every mutation
  self-scoped to `current_user.id`, no client-supplied account
  identifier anywhere — the opposite shape of the still-open
  `adaptive-auth-account-id-idor` P1).
- **1 test-evidence gap closed, 0 production code changed**: no prior
  test proved `service_accounts`' cross-lab-denial or
  non-admin-denial cases. New file `backend/tests/
  test_service_accounts_authz.py` (6 tests) closes it.
- **88 tests re-run green** (82 pre-existing + 6 new), reusing
  substantial existing evidence rather than reinventing proofs
  already on file.

Cumulative coverage-matrix totals after Batch 3: ~412 live mutating
routes now have route-level authorization evidence (up from ~395 after
Batch 2, ~372 before Batch 2). The UNKNOWN bucket is ~68 of 89 mounted
routers (down from ~73 after Batch 2, ~78 originally). **Still not
"authorization complete" or "all routes protected."** ~68 routers
remain untraced. Next bounded-batch candidates named in the coverage
matrix's honesty note: the authentication-adjacent trio
(`password_reset`/`oauth2`/`saml`) and `hospital` (23 mutating routes,
would need its own batch given the 35-route cap).

---

## Addendum 3 — Accelerated Security & Authorization Closure Batch 4

Combined pass covering Hospital (23 mutating routes) + auth-adjacent
(password_reset/oauth2/saml). **Four real P1 findings found and
CLOSED**, each with the complete FIND→TRACE→REPRODUCE→FIX→NEGATIVE
PROOF→REGRESSION cycle:

1. `hospital-facility-no-role-check` — 19 mutating routes (including
   clinical patient-safety operations: bed assign/discharge/transfer,
   OT status, surgical safety checklist) had zero role check. Fixed
   reusing this codebase's own existing role-set conventions.
2. `hospital-get-entity-boolean-bug` — a Python `not` vs SQLAlchemy `~`
   typo in a shared 17-call-site helper made every nested-entity
   lookup unconditionally return "not found." Fixed; 5 more instances
   of the identical bug registered (not fixed) in radiology/pharmacy/
   admin.
3. `hospital-missing-commit` — 18 routes never called `db.commit()`
   anywhere, silently discarding every write despite returning a
   200/201. Proven with two genuinely independent DB sessions against
   a real file-backed SQLite DB (the standard shared-session test
   client masks this entirely). Fixed.
4. `oauth2-register-no-role-check` — any authenticated user could
   register a platform-global OAuth2 client with attacker-chosen
   redirect URIs. Fixed.

Schema caveat (re-confirmed, not new): Hospital remains SCHEMA-BLOCKED
on a real Postgres deployment (13 of 14 tables have no migration; the
14th's migration is itself already-blocked in the alembic chain on a
missing FK target) — these fixes are real and proven via this repo's
own SQLite test harness, but none of Hospital's routes are reachable
on a genuine migration-driven deployment today.

Cumulative coverage-matrix totals after Batch 4: ~436 live mutating
routes now have route-level authorization evidence (up from ~412
after Batch 3). The UNKNOWN bucket is ~64 of 89 mounted routers (down
from ~68). 209 regression tests re-run across all affected files, 0
failures. **Still not "authorization complete," "system secure," or
"production ready"** — ~64 routers remain untraced, Hospital remains
schema-blocked, 5 more instances of the boolean-filter bug remain open
in other domains, and the carried-forward `adaptive-auth-account-id-
idor` P1 remains BLOCKED — NEEDS_DECISION.

---

## Addendum 4 — Accelerated Batch 5: Systemic Boolean-Filter Closure + Router-Count Correction

Objective: close 5 known `not X.field`-vs-`~X.field` boolean-filter
defects via one systemic investigation. Discovery (a new AST-based
detector, `scripts/security/boolean_not_filter_guard.py`) found **28
total sites**, 23 more than assumed. **All 28 fixed** — 20 in
`app/lims/routes.py` (a router never before individually audited; the
entire LIMS listing surface was silently non-functional), 4 in
pharmacy (2 dead, 1 dead, 1 live — the live one backs a real dashboard
route plus a route shadowed by a separate, documented, unfixed
routing bug), 3 in radiology (1 live — `revoke_share`, 2 dead), 1 in
admin (`list_pending_labs`, live). Every fix independently negative-
proofed via `git stash`/`pop` with md5-verified restoration. 5 new
regression tests, 151 total tests re-run, 0 failures.

**Significant correction**: Phase 11's mandatory router-recalculation
found every prior batch's "89 mounted routers" was wrong — a `for`
loop in `app/factory.py` registers 29 routers that a textual
`app.include_router(` count only counted as 1. **Corrected total: 117
mounted routers.** 25 of the 28 net-new routers this surfaces were
never individually accounted for by any prior batch — genuinely
newly-honest UNKNOWN, not a regression. Corrected UNKNOWN: ~86 of 117
(up from ~64 of 89, because the denominator was wrong, not because
coverage regressed). `lims_routes.router` moves from UNKNOWN to
VERIFIED (genuine new coverage, 20 routes traced); `pharmacy_router`
to PARTIALLY VERIFIED (2 routes traced); `admin`'s router gains 1
route's evidence.

**Still not claimed**: "all boolean-filter defects" (only this
AST-detectable shape was scanned for), "authorization complete," or
"production ready." Hospital remains schema-blocked, ~86 routers
remain untraced, the carried-forward `adaptive-auth-account-id-idor`
P1 remains open, and the pharmacy route-shadowing bug found this pass
remains open (documented, not fixed).

## Addendum 5 — Batch 6: Runtime Surface Reconciliation + Security Triage Acceleration

Objective: use the 25 routers Batch 5's router-count correction
surfaced to reduce UNKNOWN coverage while performing route-level
security triage, as one combined pass. Traced 16 of the 25 (`login,
register, verification, identity, id_scan, qr, cds_hooks, security,
patients, test_results, notifications, compliance, admin_log_level,
setup` fully; `ehr, ehr_fhir` sampled/structurally confirmed given
their combined 115-route scope).

**7 P1 authorization findings closed** (12 routes across 4 files),
all the same systemic shape confirmed a 4th and 5th time this session:
a route depending only on `Depends(get_current_user)` — proving
authentication, not authorization — with zero `require_permission(...)`
call anywhere in the function, while tenant isolation
(`current_user.lab_id`) was already correctly enforced. Confirmed
exploitable via direct RBAC query against all 10 roles. Fixed:
`identity.py::link_national_id` (`patients:write`), all 6 routes in
`patients.py` (`patients:read`/`patients:write` — the entire canonical
patient-management surface was previously reachable by any
authenticated role), `test_results.py::create_test_result`
(`results:write`, plus 2 read routes gated with `results:read`
alongside it), and 4 FHIR export routes in `compliance.py`
(`patients:read`/`results:read`) that returned real patient PII
(name, phone, email, birth date) with no permission check.

Every fix negative-proofed via `git stash`/`git stash pop` with
md5-verified byte-identical restoration; a new permanent regression
test (`backend/tests/test_batch6_permission_gates.py`, 10 tests)
reproduces all 7 findings against the reverted state and confirms the
fix; 221 adjacent existing tests re-run, 0 failures. The boolean-filter
detector (`scripts/security/boolean_not_filter_guard.py`) was re-run
as required — 0 hits, no regression.

**1 new P1-candidate systemic gap documented, not fixed**:
`ehr.py` (86 routes) + `ehr_fhir.py` (29 routes) show the identical
missing-permission-check shape (confirmed via `grep -c
require_permission` = 0 in both files plus representative sampling),
but no existing RBAC permission string fits without a taxonomy
decision (`ehr:read`/`ehr:write` do not exist; reusing `patients:*`
would be a judgment call, not the precise fit it was for the 4 files
above). Documented as GAP-3, recommended as the next batch's primary
target — not fixed here, consistent with this batch's own scope
discipline against exploding a 115-route sibling finding into this
pass.

**UNKNOWN accounting, recalculated exactly from the 117 baseline**:
86 (Batch 5's figure) − 16 (routers moved to VERIFIED/PARTIALLY
VERIFIED this pass) = **70 of 117 mounted routers remain UNKNOWN.**
9 of the 25 Batch-5-surfaced routers were not examined this pass:
`demo, metrics, dashboard, app_updates, device_results,
quality_control, critical_alerts, batch, mobile`.

**Still not claimed**: "authorization complete," "security complete,"
"production ready," or "national scale ready." Carried forward,
unchanged: `adaptive-auth-account-id-idor` (P1, BLOCKED —
NEEDS_DECISION), Hospital schema blocker, external CI runner blocker,
pharmacy `/batches/expiring` route-shadowing bug (P3, still
documented, not fixed), and the newly-opened `ehr`/`ehr_fhir` gap
(P1-candidate, BLOCKED on a permission-taxonomy decision).
