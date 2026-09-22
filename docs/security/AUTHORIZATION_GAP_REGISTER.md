# Authorization Gap Register

Findings only — dispositions, not blanket claims. Severity assigned by
concrete impact, not by domain name.

## Sampling method this pass

Rather than eyeballing every route, cross-referenced the count of
`@router.post/put/patch/delete` decorators against the count of
`require_platform_capability`/`require_permission`/`get_current_user`
call sites within the same function body, for the 4 Platform-Authority
domains (federation, trust, certificates, governance — small enough to
check exhaustively, 100 mutating routes total). This surfaced 2
candidates for manual review; both resolved as correctly-designed, not
gaps (below). Zero new findings from this specific check.

## GAP-1 (carried forward, not new) — `adaptive-auth-account-id-idor`

- **Severity**: P1 (candidate — broad IDOR shape, NEEDS_DECISION)
- **Route**: ~10 endpoints in `app/identity/adaptive_auth/routes.py`
  (`evaluate_risk`, `get_risk_history`, `create_mfa_challenge`,
  `verify_mfa_challenge`, `list_travel_events`,
  `get_active_session_count`, `detect_new_device`,
  `enforce_session_policy`, `check_session_expiry`, `is_session_valid`)
- **Current mechanism**: bare NIAM authentication only
- **Missing control**: no self-or-admin ownership check on a
  client-supplied `account_id`/`session_id`
- **Tenant impact**: none (this is account-scoped, not tenant-scoped)
- **Ownership impact**: any authenticated actor can evaluate/read/act on
  an arbitrary other account's risk/session state
- **Exploitability**: real, but the correct semantics are genuinely
  ambiguous without deeper context on NIAM's login/step-up-auth call
  graph (some of these endpoints plausibly need to be system-invoked
  mid-login, before the acting account's own session exists)
- **Evidence**: originally found and documented in
  `docs/engineering/MUSTAFA_ACTIVE_REPAIR_QUEUE.md`
  (`adaptive-auth-account-id-idor` row), prior session
- **Recommended control**: a domain owner must state, per endpoint,
  whether the caller is (a) the account itself, (b) an
  unauthenticated-at-that-point login-internal caller, or (c) a
  legitimate cross-account admin/security caller
- **Status**: **BLOCKED — NEEDS_DECISION.** Not re-investigated this
  pass (no new evidence); carried forward as-is per this pass's
  explicit "reconcile, don't repeat" instruction.

## Checked and confirmed NOT a gap this pass

### `POST /federation/sessions`, `POST /federation/sessions/{id}/terminate`

Initial automated scan flagged these as lacking a
`require_platform_capability` call (unlike their 10 sibling mutations
in the same file). Manual read: both are correctly self-service —
`create_federated_session` calls `_require_self(actor, account_id)`;
`terminate_federated_session` resolves the target session's owning
`account_id` server-side *before* calling `_require_self` on it (with
an explicit code comment recording the reasoning: "a client can never
terminate another account's federated session merely by
guessing/obtaining its session_id"). Platform capability would be the
wrong control here — a user managing their own federated login session
should not need platform-admin rights. **Disposition: VERIFIED, not a
gap.**

## Platform Authority grant/revoke — confirmed NOT_IMPLEMENTED (not a gap)

Per `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`: there is no HTTP
route anywhere that grants or revokes a `PlatformAuthorityAssignment`.
The only path is `app/identity/platform_authority/bootstrap.py`, which
its own docstring states is "never exposed via any HTTP route,
deployment/environment-controlled." This is recorded as **NOT
IMPLEMENTED (by design)**, not a gap — per this directive's own
instruction not to fabricate a route that doesn't exist, and not to
treat "operation doesn't exist" as equivalent to "operation exists but
is unguarded."

## Batch 2 — 5 domains traced (`billing`, `lifecycle_platform`, `pilot_platform`, `services/mpi`, `capabilities/fhir_interoperability`)

### GAP-2 (found and CLOSED this pass) — `lifecycle-platform-no-auth`

- **Severity**: P0 (was — now CLOSED)
- **Route**: all 14 routes in `app/lifecycle_platform/api/routes.py`
  (component registry, releases, compatibility matrix, upgrade paths,
  deprecation notices — `register_component`, `create_release`,
  `approve_release`, `record_compatibility`, `create_upgrade_path`,
  `issue_deprecation`, plus 8 read routes)
- **Current mechanism (pre-fix)**: none whatsoever — `grep -c
  "Depends(get_current_user)\|Depends(require_permission...\|
  Depends(require_platform_capability...\|dependencies=\["` on the file
  returned 0
- **Missing control**: any auth dependency at all
- **Tenant impact**: none (platform-global resource registry, not
  per-lab — `ComponentRegistryModel` correctly has no `TenantMixin`),
  but that makes an open write surface a platform-wide integrity risk,
  not merely a single tenant's
- **Exploitability**: real, proven live — `POST /lifecycle/components`
  with zero `Authorization` header returned `201 Created` with a real
  generated `id` and persisted row
- **Evidence (pre-fix reproduction)**: real `TestClient` HTTP request,
  no auth header, anonymous → `201`
- **Fix applied**: router-level
  `dependencies=[Depends(require_permission("system:admin"))]`, the
  same convention already used by every sibling "National X Platform"
  domain (biomedical/command_center/public_health/critical_care/pilot_platform)
- **Evidence (post-fix)**: same request → `401
  {"code":"AUTHENTICATION_REQUIRED",...}`; full matrix proven via
  `app.dependency_overrides[get_current_user]`: no override → 401,
  `role="lab_tech"` → 403, `role="master_admin"` → 201
- **Negative-proofed**: `git stash push -- routes.py` (md5
  `28ecbe8b965596acccbfdd6b6272566c`) → re-ran proof → 201 reproduced →
  `git stash pop` (md5 `a209bdd042a1c2e819c22f527be89cf3`, byte-identical
  to fixed copy) → re-ran proof → 401 confirmed
- **Regression test**: `backend/tests/test_lifecycle_platform_auth.py`
  (3 tests: unauthenticated → 401, wrong role → 403, `master_admin` →
  201) — all 3 pass
- **Regression sweep**: `test_security.py`, `test_feature_flags.py`,
  `test_tenant_isolation_matrix.py`, `tests/blood_bank/`,
  `test_biomedical_work_order_cas.py`, `test_command_center_emergency_cas.py`,
  `test_device_outbox.py`, `test_outbox_service.py`,
  `test_payment_orchestration.py`, `test_payments_foundation.py`,
  `test_payments_route_registration.py`, `test_public_health_outbreak_cas.py`
  — 178 passed, 23 skipped (pre-existing Postgres-fixture skips,
  unrelated to this change), 0 failed
- **Status**: **CLOSED.**

### GAP-3 (found, NOT fixed — documented per P2/P3 disposition) — `billing-settlement-no-lock`

- **Severity**: P2
- **Routes**: `POST /billing/claims/{id}/advance`,
  `POST /billing/settlements/simulate` (via
  `app/billing/service.py::BillingService.simulate_settlement` and
  `advance_claim`)
- **Same systemic pattern** as previously fixed in
  payments/devices/biomedical/command_center/public_health (see
  `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md`): unlocked
  `SELECT` + status-transition check + write, no `.with_for_update()`,
  and `BillingInvoice`/`Claim`/`InsuranceCoverage` use plain `Base` (no
  `OptimisticLockMixin`/version column)
- **Why P2, not P0/P1**: `app/billing/` is explicitly a demo-safe
  projection layer (module docstring: "Business rules for the
  demo-safe billing and insurance projection"), distinct from the real
  financial infrastructure in `app/payments/` (already hardened). A
  duplicate-write race here produces at worst a duplicate
  `BillingPayment` audit row or a redundant claim-status write — both
  racers compute the same next status from the same state-transition
  map (`draft→validated→submitted→accepted→paid`,
  `rejected→submitted`), so the final persisted state is still correct;
  it is not a silent-corruption or double-charge class of bug
- **Tenant impact**: none — all queries correctly filter
  `lab_id=current_user.lab_id`
- **Recommended fix** (not applied — out of this batch's bounded
  scope): add `.with_for_update()` to the invoice/claim SELECT and a
  terminal-state guard, matching the pattern already applied elsewhere
- **Status**: **DOCUMENTED, not fixed** (per this directive's P2/P3
  disposition: record and continue, do not stop the inventory to fix).

### GAP-4 (found, NOT fixed — P3) — `billing-idempotency-key-unhandled-race`

- **Severity**: P3
- **Route**: `POST /billing/invoices` (`create_invoice`)
- **Finding**: `create_invoice` checks for an existing
  `idempotency_key` via an unlocked `SELECT` before inserting. The
  table has a real `UniqueConstraint("lab_id", "idempotency_key")`, so
  a concurrent duplicate-key race cannot silently double-create a
  row — but the route only catches `ValueError`, not `IntegrityError`,
  so a genuine race produces an unhandled `500`, not a clean `409`
- **Contrast with the DORMANT `app/core/idempotency.py` module**: that
  module's identical-shaped `INSERT ... ON CONFLICT DO NOTHING` race
  has zero live callers anywhere in the repo (previously documented as
  P3/no-live-exploit); this billing route IS live and reachable, so the
  race is reachable, just not silently corrupting — the failure mode is
  an ugly error response, not a data-integrity break
- **Recommended fix** (not applied): catch `IntegrityError` in
  `create_invoice` and return `409` with the existing invoice, mirroring
  the atomic-claim pattern already used by `ClinicalCommandGuard`
- **Status**: **DOCUMENTED, not fixed** (P3, out of bounded scope).

### Re-verified this pass — `pilot_platform` (prior P0 fix, CONFIRMED STILL IN PLACE)

`app/pilot_platform/api/routes.py` — router-level
`dependencies=[Depends(require_permission("system:admin"))]`,
fixed in an earlier session (in-code comment documents the original
finding and fix). Re-read in full this pass rather than assumed safe.
**VERIFIED, no regression, no new gap.**

### Checked and confirmed NOT a gap this pass — `services/mpi/api.py`

3 mutating routes (`resolve`, `manual_merge`,
`decide_pending_review`). `resolve` uses `get_current_user` +
`require_own_lab` (ABAC — a user may only resolve patients in their
own lab; platform admins may cross labs). `manual_merge` and
`decide_pending_review` use `require_role(master_admin,
ministry_admin[, province_admin])` — correct for a cross-lab national
identity-adjudication function. **VERIFIED, not a gap.**

### Checked and confirmed NOT a gap this pass — `capabilities/fhir_interoperability/routes.py`

The one LIVE sub-router of the otherwise-dead `app/capabilities/`
package (mounted in `app/factory.py`; the other 9 sub-packages have
zero references anywhere and are not routable). 2 mutating routes:
`convert_hl7_to_fhir` (stateless conversion, no DB write) and
`create_fhir_resource` (real DB write). Both gated via
`require_institutional_permission("lab:manage")`, which chains through
`require_institutional_user` (rejects non-`LabUser`/no-`lab_id`
accounts) → role-permission check. `create_fhir_resource` scopes by
`actor.lab_id` and catches `IntegrityError` on the real
`(id, version, institution)` unique constraint, returning a clean
`409` — the same atomic-claim-via-DB-constraint pattern as
`ClinicalCommandGuard`, not a check-then-insert race. **VERIFIED, not
a gap.**

## Batch 3 — 5 domains traced (`consent`, `patient_card`, `canonical_patient`, `service_accounts`, `mfa`), 0 findings

Selected from the `LIVE / NO-OWNED-MODELS` bucket per Batch 3's own
Phase 1 priority (identity/patient-data/security-configuration
relevance). All 5 read as correctly authorized on direct code trace;
no P0/P1/P2/P3 discovered.

### Checked and confirmed NOT a gap — `app/routes/consent.py`

`grant`/`revoke` require `get_current_user` plus `_user_owns_gpid`
(caller must be the citizen subject: `role == "citizen" and
citizen_ulid == gpid`) OR `role in {master_admin, ministry_admin}`. A
real self-or-admin ownership check, not a role-only gate. **VERIFIED.**

### Checked and confirmed NOT a gap — `app/routes/patient_card.py`

Every route (`get_patient_card`, `qr.png`, `/scan`, `/history`,
`/print`) requires `get_current_user`, filters by
`current_user.lab_id` via `lookup_patient_for_lab`, and `/scan`
additionally verifies an HMAC-signed token bound to the issuing lab —
a token from Lab A is explicitly rejected (403, logged as
`scan_cross_lab_blocked`) when redeemed by a Lab B user. Every action
writes to the audit log. Matches CLAUDE.md's own stated invariant for
this file exactly. **VERIFIED.**

### Checked and confirmed NOT a gap — `app/routes/canonical_patient.py`

Gated by `app/services/mpi/scope.py`'s `require_national_scope` /
`require_own_patient` / `provenance_lab_id` — **a pre-existing fix
("NR-148") already closed before this session**, re-verified this
pass rather than assumed still correct. `create_canonical` derives
`lab_id` server-side (the historic bug this fix closed: the client
could set `lab_id` directly via `**data.model_dump()`). `merge`,
`search`, `by-citizen`, and `link-citizen` require national scope
(`platform:view_stats` permission — held only by
master_admin/ministry_admin/province_admin). `link-patient` requires
the caller own the target patient. `visible_canonical` returns 404
(not 403) on an unauthorized read, preventing an existence-oracle
side channel. **VERIFIED, and a good example of a correctly-designed
cross-tenant-by-design domain** (the MPI is deliberately national in
scope; the fix was about *which* callers may act nationally, not about
eliminating cross-tenant reads entirely).

### Checked and confirmed NOT a gap — `app/routes/service_accounts.py`

Role check (`master_admin`/`admin` only) plus real DB-level `lab_id`
scoping inside `app/security/service_accounts.py`'s
`revoke_service_account`/`rotate_api_key` (both filter the target row
by `lab_id` unless the caller is `master_admin` — confirmed by reading
the query construction, not assumed from the route's role check
alone). **New test evidence added this pass** (no prior test proved
the cross-lab-denial or non-admin-denial cases —
`backend/tests/test_service_accounts_authz.py`, 6 tests, all passing):
non-admin role → 403, foreign `lab_id` in creation body → 403, Lab A
admin rotating/revoking Lab B's service account → 404, master_admin
cross-lab rotate → 200, unauthenticated → 401 on all 4 mutating
routes. **VERIFIED.**

### Checked and confirmed NOT a gap — `app/routes/mfa.py`

Every mutation (`totp/setup`, `totp/verify`, `webauthn/*`,
`devices/{id}` DELETE) is scoped to `current_user.id` server-side —
**no route in this file accepts a client-supplied account/session
identifier**, the exact shape the carried-forward P1
(`adaptive-auth-account-id-idor`) is about. `remove_device` filters
`MFADevice.id == device_id AND user_id == current_user.id` before
deleting — a client cannot delete another user's MFA device by
guessing its id (404, not a silent cross-account deletion).
**VERIFIED**, and a useful contrast case: this is what the
adaptive_auth P1's endpoints would need to look like to be closed.

## Summary

| ID | Severity | Status |
|---|---|---|
| `adaptive-auth-account-id-idor` | P1 | BLOCKED — NEEDS_DECISION (carried forward) |
| federation self-service session routes | — | VERIFIED (checked prior pass, not a gap) |
| Platform Authority grant/revoke | — | NOT IMPLEMENTED (by design, not a gap) |
| `lifecycle-platform-no-auth` | P0 | **CLOSED** (Batch 2 — fixed, proven, tested) |
| `billing-settlement-no-lock` | P2 | DOCUMENTED (Batch 2), not fixed |
| `billing-idempotency-key-unhandled-race` | P3 | DOCUMENTED (Batch 2), not fixed |
| `pilot_platform` router auth | — | RE-VERIFIED (Batch 2), still in place |
| `services/mpi/api.py` | — | VERIFIED (Batch 2), not a gap |
| `capabilities/fhir_interoperability` | — | VERIFIED (Batch 2), not a gap |
| `consent` | — | VERIFIED (Batch 3), not a gap |
| `patient_card` | — | VERIFIED (Batch 3), not a gap |
| `canonical_patient` (MPI) | — | VERIFIED (Batch 3), prior fix re-confirmed |
| `service_accounts` | — | VERIFIED (Batch 3), new test evidence added |
| `mfa` | — | VERIFIED (Batch 3), not a gap |

**Batch 3 found zero new findings of any severity** — a genuine result
of the 5 domains selected (all already correctly designed), not
evidence that the remaining UNKNOWN bucket is clean. Cumulative: one
P0 found and closed (Batch 2, lifecycle_platform); two lower-severity
concurrency findings in billing documented, not fixed (Batch 2); zero
findings in Batch 3. This reflects the 10 domains actually traced
across both batches (40 routes total), not a claim that the remaining
UNKNOWN-bucket routers (see
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`) are gap-free.
