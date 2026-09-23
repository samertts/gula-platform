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
evidence that the remaining UNKNOWN bucket is clean.

## Batch 4 — combined Hospital + auth-adjacent (Accelerated Security & Authorization Closure)

### GAP-5 (found and CLOSED this pass) — `hospital-facility-no-role-check`

- **Severity**: P1 (patient-safety-adjacent: some affected routes are
  clinical operations, not merely administrative)
- **Routes**: 19 of 23 mutating routes in `app/routes/hospital.py` —
  facility/administrative creates (`create_building`, `create_floor`,
  `create_department`, `update_department`, `create_clinic`,
  `create_room`, `create_bed`, `create_unit`,
  `create_operation_theater`, `create_equipment`, `update_equipment`,
  `create_cost_center`, `update_campus`) and clinical patient-safety
  operations (`assign_bed`, `discharge_bed`, `transfer_bed`,
  `update_ot_status`, `complete_surgical_safety_checklist`,
  `create_appointment`)
- **Current mechanism (pre-fix)**: `Depends(get_current_user)` only —
  no role check of any kind
- **Missing control**: any authenticated `LabUser` of any role
  (including non-clinical staff) could create hospital facility
  structure, and critically could assign/discharge/transfer a real
  patient to a bed, change an operation theater's status, or complete
  a WHO-mandated surgical safety checklist
- **Context**: a prior session pass had already fixed 4 sibling routes
  in this same file (`create_hospital`/`update_hospital`/
  `deactivate_hospital`/`create_campus`) and its own test file
  (`test_hospital_update_security.py`) explicitly documented "the
  entire hospital.py route surface still has no role gates beyond
  these four" as deliberately deferred — this closes that deferral
- **Fix applied**: reused the same two role-set convention already
  established in this codebase — `_HOSPITAL_ADMIN_ROLES = {admin,
  master_admin}` (already present in this file) for facility structure,
  and a new `_HOSPITAL_CLINICAL_WRITE_ROLES = {admin, master_admin,
  doctor, nurse}` (verbatim copy of NHDW's `_NHDW_ADMISSION_WRITE_ROLES`
  / Nursing's `_NURSING_WRITE_ROLES`) for clinical operations — no new
  role vocabulary invented
- **Evidence**: real HTTP proof via `TestClient` — `staff` role denied
  (403) on all 19 routes; `admin`/`nurse`/`doctor` succeed on
  representative routes; cross-tenant target rejected (404) for
  `assign_bed` and `update_department`
- **Negative-proofed**: `git stash`/`git stash pop` with md5-verified
  byte-identical restoration — vulnerability reproduces on revert (24
  errors — see GAP-6, the fixture itself depends on GAP-6's fix — and
  once isolated, 403 checks fail as 200/201), fix holds on restore
- **Regression test**: `backend/tests/test_hospital_role_gate_completion.py`
  (25 tests: 19 role-denial checks, 3 correct-role success checks, 2
  cross-tenant denials, 1 unauthenticated-baseline check) — all pass
- **Regression sweep**: `test_hospital_update_security.py`,
  `test_hospital_service_log_action.py`, `test_security.py`,
  `test_tenant_isolation_matrix.py`, `test_rbac_tenant_scope.py`,
  `test_detect_missing_tenant_scope.py`, `test_feature_flags.py` — 209
  tests total, 0 failures
- **Status**: **CLOSED.**

### GAP-6 (found and CLOSED this pass, discovered while building GAP-5's test harness) — `hospital-get-entity-boolean-bug`

- **Severity**: P1 (data integrity / correctness, not authorization)
- **Location**: `app/services/hospital_service.py::_get_entity` — the
  shared nested-entity lookup helper used by 17 call sites across ~10
  routes (`update_campus`, `create_building`, `create_floor`,
  `create_department`'s parent check, `create_clinic`, `create_room`,
  `update_department`, `assign_bed`/`discharge_bed`/`transfer_bed`,
  `update_ot_status`/`complete_surgical_safety_checklist`,
  `update_equipment`, `bed_assignment_history`)
- **Bug**: `db.query(model).filter(model.id == entity_id, model.lab_id
  == lab_id, not model.is_deleted)` — the `not` is Python's boolean
  `not`, applied to the `InstrumentedAttribute` column object itself,
  not a SQL `NOT`. Confirmed directly: `bool(Model.column)` is always
  `True` (default object truthiness), so `not model.is_deleted`
  evaluates to the **literal Python `False`** at query-build time,
  before SQLAlchemy ever sees it. A standalone check confirmed
  `.filter(False)` compiles to `WHERE 0 = 1` — every call through this
  helper unconditionally matched zero rows, regardless of what data
  actually existed
- **Fix applied**: `~model.is_deleted` (SQLAlchemy's boolean-NOT
  operator), matching every other `is_deleted` filter already in this
  same file
- **Evidence**: reproduced directly in a Python REPL-style check
  (`bool(Foo.is_deleted)` → `True`; `not Foo.is_deleted` → `False`);
  reproduced via the test suite (24 fixture-setup errors, all
  `NotFoundError: hospital_campuses not found`, before the fix)
- **Negative-proofed**: `git stash`/`git stash pop`, md5-verified;
  vulnerability reproduces on revert, fix holds on restore
- **Status**: **CLOSED**, same commit/regression evidence as GAP-5
  (both fixes were needed together for the test harness to even run).
- **Systemic pattern — NOT fixed, registered for a future batch**: the
  identical `not X.is_deleted`/`not X.is_revoked`/`not X.is_active`
  shape recurs at 5 more call sites outside Hospital, confirmed by
  repo-wide grep: `app/radiology/pacs.py:365,375,388` (`ImageShare`
  lookups), `app/pharmacy/routes.py:504` (generic entity lookup),
  `app/routes/admin.py:257` (`Lab` listing). Each would need the same
  one-line `not` → `~` fix, but these are in different, unaudited
  domains outside this batch's bound — not fixed here.

### GAP-7 (found and CLOSED this pass, discovered while proving GAP-6's fix) — `hospital-missing-commit`

- **Severity**: P1 (transaction integrity / silent data loss — arguably
  the most severe finding of this batch)
- **Routes**: 18 of Hospital's mutating routes (all except the 5
  `ClinicalCommandGuard`-based ones, which already commit inside
  `_run_hospital_command`): `create_hospital`, `update_hospital`,
  `deactivate_hospital`, `create_campus`, `update_campus`,
  `create_building`, `create_floor`, `create_department`,
  `update_department`, `create_clinic`, `create_room`, `create_bed`,
  `create_unit`, `create_operation_theater`, `create_equipment`,
  `update_equipment`, `create_cost_center`, `create_appointment`
- **Bug**: none of these routes, nor `HospitalService`'s corresponding
  methods, nor `log_action`, ever called `db.commit()`. `get_db()`
  (`app/database.py`) uses `sessionmaker(autocommit=False, ...)` and
  only calls `db.rollback()` on exception — a pending
  (flushed-but-uncommitted) transaction is implicitly discarded by
  SQLAlchemy's default `Session.close()` behavior when the request
  ends. Every one of these routes returned a 200/201 with what looked
  like a real created/updated record, but nothing was durably
  persisted
- **Why this was invisible to existing tests**: `tests/conftest.py`'s
  `client` fixture's `_override_get_db` yields the **same** `db`
  session object for every HTTP request within one test (`try: yield
  db; finally: pass` — never closes or rolls back between requests).
  A flush is visible to later queries on that same open
  session/transaction regardless of whether it was ever committed, so
  every pre-existing Hospital test (including the already-"FIXED —
  VERIFIED" `create_hospital`/`update_hospital`/`deactivate_hospital`/
  `create_campus` from a prior session) passed despite this bug
- **Evidence (pre-fix reproduction)**: a standalone proof script
  (not the shared-session test client) drove two genuinely
  independent connections against a real file-backed SQLite DB:
  `POST /hospital/` → `201` with `id=1`; the very next request,
  `POST /hospital/1/departments`, got **`404 Hospital not found`**
  (a fresh `SessionLocal()`, matching real production per-request
  behavior, found nothing); a third, fully independent session
  confirmed neither row existed
- **Fix applied**: `db.commit()` added immediately after each
  affected route's service call, matching the exact pattern the
  file's own `_run_hospital_command` helper already used for the 5
  `ClinicalCommandGuard` routes
- **Evidence (post-fix)**: same two-request proof — `POST
  /hospital/1/departments` now returns `201`; an independent
  third-session verification confirms both the hospital and
  department rows durably exist
- **Negative-proofed**: `git stash`/`git stash pop` with md5-verified
  byte-identical restoration; the proof script's "not durably
  committed" result reproduces on revert, "durably committed" holds on
  restore
- **Regression test**: `backend/tests/test_hospital_durable_commit.py`
  (3 tests, using a genuinely independent two-session fixture rather
  than the shared-session `client` fixture — confirmed to fail against
  the pre-fix code, pass against the fix) — all pass
- **Side effect worth noting**: `update_hospital`/`deactivate_hospital`
  use `.with_for_update()` (a real row lock). Without a commit, that
  lock would be held until connection close/rollback rather than
  released promptly — a lock-contention risk on top of the data-loss
  risk, once Hospital's schema exists in production
- **Status**: **CLOSED.**

### GAP-8 (found and CLOSED this pass) — `oauth2-register-no-role-check`

- **Severity**: P1 (security configuration)
- **Route**: `POST /oauth2/register`
- **Current mechanism (pre-fix)**: `Depends(get_current_user)` only
- **Missing control**: `OAuth2Client` (`app/models/oauth2_client.py`)
  is a platform-global registry — no `lab_id`/tenant column exists on
  the model at all, by design, not an omission. Any authenticated
  `LabUser` of any role could register an OAuth2 client with
  attacker-chosen `redirect_uris`, which then receives real users'
  access/refresh/id tokens the moment any user completes `/authorize`
  against it — a real open-redirect / token-exfiltration vector
- **Fix applied**: `_OAUTH2_CLIENT_ADMIN_ROLES = {admin, master_admin}`
  role gate, reusing the same convention as `service_accounts.py` and
  Hospital
- **Evidence**: real HTTP proof — unauthenticated → 401; `staff` role
  → 403; `admin` role → 200 with `client_id`/`client_secret` issued
- **Negative-proofed**: `git stash`/`git stash pop`, md5-verified;
  vulnerability reproduces on revert, fix holds on restore
- **Regression test**: `backend/tests/test_oauth2_register_authz.py`
  (3 tests) — all pass; existing `test_auth_infrastructure.py` oauth2
  coverage (discovery/jwks/token-no-auth) re-run unaffected
- **Status**: **CLOSED.**

### Checked and confirmed NOT a gap this pass — `app/routes/password_reset.py`

All 3 routes correctly scoped: `forgot_password`/`reset_password`
derive identity solely from the reset token itself (anti-enumeration
response for `forgot`, no client-supplied user id anywhere in either)
— the exact "identity A must never mutate/authenticate as identity B"
property holds because there is no identity parameter to spoof in the
first place. `change_password` requires `get_current_user` and only
ever reads/writes the caller's own `password_hash`, then calls
`bump_perm_version` to revoke other sessions. **VERIFIED.**

### Checked and confirmed NOT a gap (but functionally incomplete) — `app/routes/saml.py`

`POST /auth/saml/acs` validates the SAML response's signature, issuer,
audience, and assertion cryptographically — but never issues a
session, JWT, or writes to the database (the `db: Session =
Depends(get_db)` parameter is declared but unused in the function
body). There is no privileged effect to authorize because the route
grants no session at all yet; this is an incomplete SSO
implementation (a feature-completeness gap), not an authentication
bypass. **VERIFIED, not exploitable, not fixed (feature completion is
out of this audit's scope).**

### OAuth2 protocol-conformance notes — documented, not fixed (P2/P3)

Traced but out of this batch's fix scope, per Phase 5's "do not
redesign authentication protocols" instruction:

- **`GET /oauth2/authorize` has no explicit user-consent screen** — it
  issues an authorization code bound to `current_user.id` immediately.
  Not a proven IDOR (no client-supplied identity is ever used — the
  code is always bound to whoever is currently authenticated), but a
  deviation from typical OAuth2 UX/security practice. P3.
- **`POST /oauth2/introspect` and `POST /oauth2/revoke` require no
  client authentication** — a deviation from RFC 7662's convention
  that introspection/revocation endpoints authenticate the caller.
  Not practically exploitable without already possessing the real
  token value (the lookup key is `hash_token(data.token)`, not a
  guessable identifier), so this is a protocol-conformance hardening
  note, not a proven vulnerability. P3.
- **`_handle_refresh_token_grant`'s `user_id`/`client_id` come from
  the refresh token's own server-signed JWT payload** (verified via
  `decode_oauth2_refresh_token` → `decode_access_token`, which
  validates the signature and raises `JWTError` on tamper) — **checked
  and confirmed NOT an IDOR risk.**

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
| `hospital-facility-no-role-check` | P1 | **CLOSED** (Batch 4 — fixed, proven, tested) |
| `hospital-get-entity-boolean-bug` | P1 | **CLOSED** (Batch 4 — fixed, proven, tested) |
| `hospital-missing-commit` | P1 | **CLOSED** (Batch 4 — fixed, proven, tested) |
| `oauth2-register-no-role-check` | P1 | **CLOSED** (Batch 4 — fixed, proven, tested) |
| `not`-vs-`~` boolean-filter (radiology/pharmacy/admin) | P1 | DOCUMENTED (Batch 4), not fixed |
| `password_reset` | — | VERIFIED (Batch 4), not a gap |
| `saml` ACS | — | VERIFIED (Batch 4), not exploitable, functionally incomplete |
| oauth2 `/authorize` no consent screen | P3 | DOCUMENTED (Batch 4), not fixed |
| oauth2 `/introspect`, `/revoke` no client auth | P3 | DOCUMENTED (Batch 4), not fixed |

**Batch 4 found and closed 4 real P1 findings** (1 authorization gap
with patient-safety impact, 1 data-integrity bug, 1 transaction-
integrity bug affecting silent data loss, 1 security-configuration
authorization gap) — the most severe single batch this program has
run since the lifecycle_platform P0. This reflects the 2 domains
actually traced in depth this batch (Hospital fully, OAuth2's
highest-risk route), not a claim that the remaining UNKNOWN-bucket
routers are gap-free.

## Batch 5 — systemic boolean-filter closure (28 sites, 1 detector, 1 accounting correction)

### GAP-9 (found and CLOSED this pass) — `not-vs-tilde-boolean-filter` (repo-wide, all instances)

- **Severity**: P1 (data-integrity/correctness; opposite failure mode
  from most security bugs — fails closed/empty, not open)
- **Discovery method**: a deterministic AST-based detector
  (`scripts/security/boolean_not_filter_guard.py`, built this pass) —
  per this batch's own "do not assume exact files or line numbers"
  instruction, not a grep of the 5 sites the directive assumed going
  in. The detector found **28 total occurrences**, 23 more than
  assumed.
- **Root cause** (identical across all 28): `not Model.field` inside a
  `.filter()`/`.filter_by()` call. Python evaluates `not
  <InstrumentedAttribute>` immediately at query-build time; a bare
  column has no `__bool__` override, so `bool(Model.column)` is always
  `True` and `not Model.column` is the literal Python `False`.
  `.filter(False)` compiles to `WHERE 0 = 1` — unconditionally zero
  rows, regardless of real data.
- **All 28 sites, fixed, with reachability**:
  - `app/lims/routes.py` — **20 sites, all LIVE**: `Instrument`(×2),
    `InstrumentModel`, `Specimen`(×2), `Order`, `Panel`, `Result`,
    `Reagent`, `Consumable`, `Lot`, `ReferenceRangeDef`,
    `AutoValidationRule`, `LabReport`, `QCProgram`, `Supplier`,
    `Storage`, `DeltaCheckRule`, `Department`, `Manufacturer`. Every
    one is a real, mounted, `_lab_id(current_user)`-tenant-scoped
    list/get/dashboard-count route. This is `lims_routes.router`, a
    genuinely distinct router from the legacy `routes/labs.py`/
    `routes/samples.py`/`routes/results.py` files already covered by
    this register's "Laboratory" entries — **never before
    individually audited**. The entire LIMS listing/lookup/dashboard
    surface was silently non-functional (every affected call returned
    empty/zero) until this fix.
  - `app/pharmacy/inventory.py` — 2 sites (`auto_quarantine_expired`,
    `get_cold_chain_drugs`), both **DEAD** (zero callers anywhere in
    the tree).
  - `app/pharmacy/routes.py:504` — 1 site (`_get_or_404`), **DEAD**
    (zero callers).
  - `app/pharmacy/services.py:198` — 1 site (`get_expiring_batches`),
    **LIVE** — backs `GET /pharmacy/dashboard/expiry-alerts`
    (confirmed reachable and fixed by real HTTP proof) and `GET
    /pharmacy/batches/expiring` (same fixed method, but that specific
    route is itself shadowed by an earlier-registered
    `/batches/{batch_id}` path — a **separate, pre-existing
    route-ordering bug**, confirmed by reading the registration order,
    NOT fixed here, out of this batch's bound). Tenant-scoped via
    `self.lab_id`, server-derived from `user.lab_id` in
    `_get_pharmacy_service`, never client-supplied.
  - `app/radiology/pacs.py` — 3 sites: `revoke_share` (**LIVE**, via
    `DELETE /radiology/sharing/{share_id}`, ownership-scoped via
    `_study_for_user` before the buggy method is even reached — the
    bug broke the revoke *action* itself, not the authorization
    boundary in front of it); `access_share`, `list_shares` (**DEAD**,
    zero callers).
  - `app/routes/admin.py:257` — 1 site (`list_pending_labs`), **LIVE**
    — `GET /admin/labs/pending`, gated by
    `require_permission("platform:manage_users")`, additionally
    province-scoped for `province_admin`.
- **False positive checked and excluded**: `app/routes/demo.py:96`'s
  `elif not user.is_active or user.lab_id != lab.id or ...` — `not` on
  an already-fetched ORM *instance's* real runtime boolean value,
  inside a plain `if`/`elif`, not inside a `.filter()` call at all.
  Confirmed a completely different and correct usage; excluded from
  the detector by construction (it only flags `not <attribute>` as a
  direct argument to `.filter()`/`.filter_by()`).
- **Fix applied**: `not X.field` → `~X.field` at all 28 sites (20 via
  a verified, uniform `sed` substitution in `lims/routes.py` after
  confirming exact occurrence-count match and uniform semantics via 2
  spot checks; the remaining 8 via individual edits).
- **Evidence**: real HTTP/service-level proof for all 4 LIVE-reachable
  representative sites — LIMS (`POST`+`GET /lims/departments`, a
  created department is now found), pharmacy (`GET
  /pharmacy/dashboard/expiry-alerts` finds a real expiring batch),
  radiology (`ImageSharingService.revoke_share` returns `True` for a
  real share), admin (`GET /admin/labs/pending` lists a real inactive
  lab) — `backend/tests/test_boolean_not_filter_regression.py`, 5
  tests, all passing.
- **Negative-proofed**: `git stash`/`git stash pop` across all 6
  affected files, md5-verified byte-identical restoration; the
  detector and all 5 new tests reproduce the vulnerability (28 hits;
  5 test failures) on the reverted state and confirm the fix (0 hits;
  5 passes) after restore.
- **Regression sweep**: 151 tests across LIMS/pharmacy/radiology
  domain suites plus security/tenant-isolation/rbac — 0 failures.
- **Status**: **CLOSED — 28 of 28 known-shape sites fixed.** Not a
  claim that no other boolean-filter mistake of any shape exists
  anywhere in the codebase — only that this specific, precisely
  AST-detectable shape has zero remaining instances as of this scan.

### Mounted-router accounting correction (not a gap — a counting-methodology fix)

Every prior batch counted mounted routers via `grep -c
"app.include_router("` against `app/factory.py`, reporting 89. This
batch's mandatory Phase 11 recalculation found that one line
(`app/factory.py:578-579`, a `for` loop over 6 concatenated lists)
registers **29 routers** in a single loop iteration that a textual
line-count only counts as 1. **Corrected total: 117 mounted routers**
(89 − 1 + 29). Full detail and the complete list of the 25 newly
surfaced UNKNOWN routers in
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`'s Batch 5 section.
This is a correction to how this session has been counting, not new
mounting activity or a regression in prior work.

## Summary (additions this pass)

| ID | Severity | Status |
|---|---|---|
| `not-vs-tilde-boolean-filter` (repo-wide, 28 sites) | P1 | **CLOSED** (Batch 5 — 28/28 fixed, proven, tested; 23 of the 28 newly discovered by this pass's own detector, not the 5 originally assumed) |
| `lims_routes.router` | — | **VERIFIED this pass** — genuinely new coverage (was UNKNOWN, 20 LIVE routes traced) |
| `pharmacy_router` | — | **PARTIALLY VERIFIED this pass** — genuinely new coverage (was UNKNOWN, 2 LIVE routes traced) |
| `app/routes/admin.py` router | — | PARTIALLY VERIFIED this pass (1 of ~15+ routes traced) |
| `radiology_router` | — | RE-VERIFIED (already audited prior pass), 1 regression found+fixed |
| pharmacy `/batches/expiring` route-shadowing bug | P3 | DOCUMENTED this pass, not fixed (pre-existing, unrelated to the boolean-filter defect) |

**Batch 5 found and closed 1 systemic P1 pattern across 28 sites** (the
largest single-pattern closure this program has run) and corrected a
mounted-router accounting error that had understated the true UNKNOWN
denominator in every prior batch. This does not mean "all boolean-
filter defects are gone" (only this precise AST-detectable shape was
scanned for) or "authorization complete" — ~86 of the corrected 117
mounted routers remain UNKNOWN.

## Batch 6 — Runtime Surface Reconciliation + Security Triage Acceleration

Scope: the 25 routers newly surfaced by Batch 5's router-count
correction. Traced as one combined discovery/triage pass, not 25
independent projects.

### GAP-2 (new, this pass, CLOSED) — "missing `require_permission` on a
`get_current_user`-only mutation/PII-read" — confirmed systemic, 4th–5th
instance of the pattern

**Shape**: a route depends only on `Depends(get_current_user)` (proves
authentication) with no `require_permission(...)` call anywhere in the
function (proves authorization). Tenant isolation (`lab_id ==
current_user.lab_id`) is present and correct in every instance below —
only the role/permission layer is missing. Confirmed exploitable via
direct RBAC query (`app/security/rbac.py::get_permissions_for_role`)
against all 10 roles: `cashier`, `citizen`, `finance_auditor`,
`finance_controller`, `finance_operator`, `reconciler`,
`refund_reviewer` lack `patients:read` entirely; those plus `doctor`,
`ministry_admin`, `province_admin`, `technician` lack `patients:write`;
`cashier`, `citizen`, `finance_*`, `reconciler`, `refund_reviewer` also
lack `results:read`.

- **Severity**: P1 (real patient PII / clinical-identity mutation
  reachable by authenticated actors outside the intended role)
- **Routes fixed** (7 total, 4 files):
  - `app/routes/identity.py::link_national_id` (`POST /identity/link`)
    — mutates `patient.national_id_hash` with zero permission check,
    while its sibling read route (`lookup_by_national_id`) in the same
    file already correctly requires `patients:read`. **Fix**: added
    `Depends(require_permission("patients:write"))`.
  - `app/routes/patients.py` — **all 6 routes** in the canonical
    patient-management router (`list`, `create`, `family/{family_id}`,
    `{patient_id}/children`, `get {patient_id}`, `update
    {patient_id}`) had zero permission checks; confirmed the service
    layer (`app/services/patient_service.py`) also performs no
    permission check (`grep` for
    `require_permission|patients:read|patients:write|current_user.role`
    → no matches). This was the single largest-blast-radius finding
    this pass — the entire patient PII surface (full_name, phone,
    birth_date, gender, email, national_id, family_id) was reachable
    by any authenticated LabUser regardless of role. **Fix**: added
    `Depends(require_permission("patients:read"))` to the 4 reads,
    `Depends(require_permission("patients:write"))` to the 2
    mutations.
  - `app/routes/test_results.py::create_test_result` (`POST
    /test-results/`) — same shape; sibling routes in the same file
    (`get_test_result`, `verify_test_result`) are already correctly
    role/state-gated (see "positive examples" below). **Fix**: added
    `Depends(require_permission("results:write"))`. Also extended to
    `list_citizen_results` and `citizen_timeline` (`GET
    /test-results/citizen/{health_id}[/timeline]`) — read-only but
    return full clinical result history; gated with
    `Depends(require_permission("results:read"))` for consistency with
    the same-file write-side fix.
  - `app/routes/compliance.py` — 4 HL7 FHIR export routes
    (`get_fhir_patient`, `get_fhir_observations`,
    `get_fhir_diagnostic_report`, `get_fhir_service_request`) return
    real patient PII (full_name, phone, email, birth_date, gender) and
    clinical result data with zero permission check, unlike the file's
    other admin-gated routes (`system_info`, `audit_integrity`,
    `security_report`, `system_status`, all correctly role-checked).
    **Fix**: `get_fhir_patient` → `require_permission("patients:read")`;
    the 3 order/result-centric routes →
    `require_permission("results:read")`. `audit-summary` and
    `dhis2/aggregate` in the same file were checked and are **not**
    gaps — both return counts/aggregates only, no patient PII (the
    dhis2 route's own docstring and `log_action` call explicitly assert
    `contains_patient_pii: False`, confirmed correct by inspection).
- **Positive examples confirmed in the same sweep (NOT gaps)**:
  `test_results.py::verify_test_result` (explicit role gate +
  atomic `UPDATE ... WHERE locked_at IS NULL` CAS + `enforce_transition`
  state-machine check — exemplary), `test_results.py::get_test_result`
  (role-filtered query, `citizen` role hits `sa.false()`), `login.py`,
  `register.py`, `verification.py`, `id_scan.py`, `qr.py` (intentional
  capability-URL design, `secrets.token_urlsafe(32)` + SHA-256 hash +
  expiry, matches `patient_card.py` precedent), `cds_hooks.py`,
  `admin_log_level.py`, `setup.py` — all traced in full, all VERIFIED
  SAFE, no fix needed.
- **Evidence**: `backend/tests/test_batch6_permission_gates.py` (10
  tests) — 7 negative-proof cases (a role confirmed via direct RBAC
  query to lack the relevant permission gets 403 post-fix) + 3 sanity
  cases (a role that legitimately holds the permission is still
  allowed, 200/201).
- **Negative-proofed**: `git stash push --` on all 4 files, reproduced
  every one of the 7 findings live (200/201 where 403 is expected,
  confirmed by running the new test file against the reverted state),
  `git stash pop`, md5-verified byte-identical restoration of all 4
  files, re-ran the same test file to confirm all 10 pass post-restore.
- **Regression sweep**: 163 tests across
  `test_chaos_survival.py`, `test_compliance_integrity.py`,
  `test_elite_improvements.py`, `test_observability_invariants.py`,
  `test_public_demo_security.py`, `test_security_regression.py`,
  `test_tenant_isolation_matrix.py`, plus 58 tests across
  `test_canonical_patient_lab_id_authority.py`,
  `test_canonical_patient_scope.py`,
  `test_clinical_authorization_context.py`,
  `test_clinical_authorization_policy.py`, `test_rbac_tenant_scope.py`,
  `test_patient_card.py` — 0 failures.
- **Status**: **CLOSED** for the 7 routes listed. Not a claim that
  `identity.py`/`patients.py`/`test_results.py`/`compliance.py` have no
  other findings — only these specific missing-permission-check sites.

### GAP-3 (Batch 6 stub, REFINED this pass — Batch 7) —
`app/routes/ehr.py` (86 routes) + `app/routes/ehr_fhir.py` (29 routes):
canonical-ownership analysis complete, family-level classification
replaces the earlier blanket "115 routes, all BLOCKED" statement

Batch 6 left this as a single undifferentiated 115-route P1 candidate.
Batch 7's mandate ("resolve the authorization taxonomy decision... do
NOT directly patch all 115 routes, first establish the authorization
model") required determining canonical ownership before classifying
further. Full route-family inventory, canonical-ownership analysis,
and the resulting architecture decision are now recorded in
`docs/national/ADR.md`'s **ADR-009** (new this pass) — this entry
summarizes the disposition; see the ADR for full evidence and the
3-option decision it puts to a domain owner.

**Canonical ownership finding (the key discovery this pass)**: EHR's
clinical resources (`app/ehr/models/*` — ClinicalNote, Allergy,
Medication*, CarePlan*, Condition, Diagnosis, FamilyHistory,
SocialHistory, RiskFactor, Immunization, Attachment) are genuinely
EHR-owned, first-party canonical data — NOT a projection/facade over
the legacy monolith's `Patient`/`LabResult` (confirmed via ADR-001).
They key off `app.national.domain.patient.Patient` (table
`national_patients`), the National platform's own canonical patient
identity — a structurally distinct table from the legacy `patients`
table that `patients:read`/`patients:write` were built to guard.
Tenant isolation is sound across this boundary (both share the same
`lab_id` value space via `TenantMixin`), but role/permission
authorization is a separate question, and that's where the real gap
is.

**The National domain already has its own dormant, more sophisticated
authorization layer** (`app/national/security/{rbac,abac,
consent_enforcement,break_glass}.py` — 16-role × 42-permission ABAC/RBAC
+ consent + break-glass, documented as built in
`app/national/DOMAIN_AUDIT_REPORT.md`) that is confirmed, by grep,
**never called by any live route** (`app/national/api/routes/security.py`
and `consent.py` are not mounted in `app/factory.py`; `ehr.py`/
`ehr_fhir.py`/`ehr_service.py` never import from
`app.national.security.*`). Its `NationalRole` enum does not map onto
`LabUser.role` (the legacy 10-role space actually issued in JWTs) — no
mapping function exists anywhere in the codebase.

**Family-level breakdown of the 115 routes** (see ADR-009 for full
route lists):

| Family | Routes | Canonical owner | Disposition |
|---|---|---|---|
| EHR clinical sub-resource CRUD (`ehr.py`) | 82 | EHR-native (`app/ehr/models`) via `NationalPatient` | **G — BLOCKED**, pending ADR-009's taxonomy decision |
| Patient timeline/summary aggregation (`ehr.py`) | 3 | Same as above (aggregates the same family) | **G — BLOCKED** |
| Cross-facility verified clinical read (`ehr.py::get_clinical_note_for_verified_facility`) | 1 | Same, but already has its own gate | **VERIFIED** — `ClinicalEhrReadGate` already authorizes this route; not a gap |
| FHIR read/search over EHR-native + National resources (`ehr_fhir.py`: Patient, Encounter, Condition, MedicationRequest, MedicationStatement, CarePlan, Procedure, AllergyIntolerance, Immunization, DocumentReference, Composition, $everything, Bundle) | 20 | Same as row 1 | **G — BLOCKED** |
| Generic FHIR create/update/delete/batch dispatcher (`ehr_fhir.py`) | 4 | Dispatches to the same EHR-native/National models (never `LabResult`/`Patient`) | **G — BLOCKED** |
| FHIR Observation read + search (`ehr_fhir.py`) | 2 | Legacy `LabResult`/`LabOrder` (already owns `results:read`/`results:write`) | **FIXED this pass** — `require_permission("results:read")` |
| FHIR Provenance search (`ehr_fhir.py`) | 1 | `AuditLog` (already owns `audit:read`, reused identically in `app/routes/admin.py`) | **FIXED this pass** — `require_permission("audit:read")` |
| FHIR population-summary analytics (`ehr_fhir.py`) | 1 | Aggregate counts only, no PII (matches the already-accepted `dhis2/aggregate` precedent) | **VERIFIED, not a gap** |
| FHIR metadata/CapabilityStatement (`ehr_fhir.py`) | 1 | Static server metadata, no patient data | **VERIFIED SAFE** |

Totals: **109 of 115 routes BLOCKED** (pending ADR-009), **3 of 115
FIXED this pass**, **3 of 115 VERIFIED SAFE / not a gap**.

- **Fix applied this pass**: `ehr_fhir.py`'s `fhir_read_observation`,
  `fhir_search_observation` → `require_permission("results:read")`;
  `fhir_search_provenance` → `require_permission("audit:read")`.
- **Evidence**: `backend/tests/test_batch7_ehr_fhir_permission_gates.py`
  (5 tests — 3 negative-proof + 2 sanity).
- **Negative-proofed**: `git stash`/`pop` on `ehr_fhir.py`, md5-verified
  byte-identical restoration; all 3 negative-proof cases reproduced
  live (200 where 403 expected) pre-fix, confirmed fixed post-restore.
- **Status**: 3 routes **CLOSED**. 109 routes **OPEN — BLOCKED on
  ADR-009's taxonomy decision**, explicitly not guessed. 3 routes
  **VERIFIED, not a gap**.

### GAP-4 (new, this pass — Batch 7) — 3 more instances of the same
missing-permission-check pattern, found while sweeping the remaining
9 small routers

Phase 8's sweep of `demo`, `metrics`, `dashboard`, `app_updates`,
`device_results`, `quality_control`, `critical_alerts`, `batch`,
`mobile` (the last 9 of the 25 routers Batch 5's accounting correction
surfaced) found 3 more confirmed instances of the same
`Depends(get_current_user)`-only pattern, each with an unambiguous,
already-established, precise-fit permission:

- **`app/routes/device_results.py::receive_device_results`** (`POST
  /device/results`) — creates `LabResult` rows from a lab analyzer
  device submission; tenant-scoped correctly (`LabOrder.lab_id ==
  current_user.lab_id`), excellent CAS/state-machine concurrency
  handling already in place, but zero permission check on a mutation
  of the same canonical resource `test_results.py::create_test_result`
  was gated with in Batch 6. **Fix**: `require_permission("results:write")`.
- **`app/routes/critical_alerts.py`** — both routes
  (`get_critical_alerts`, `alert_statistics`) return real patient names
  and critical `LabResult` values (`get_critical_alerts` eager-loads
  `LabResult.order.patient`), tenant-scoped correctly, zero permission
  check. **Fix**: both → `require_permission("results:read")`.
- **`app/routes/batch.py::create_batch_orders`** (`POST /batch/orders`)
  — bulk-creates `LabOrder` + `LabResult` rows, tenant-scoped correctly
  (patient IDs pre-validated against `current_user.lab_id`), zero
  permission check on the same canonical resource `orders:write`
  already governs. **Fix**: `require_permission("orders:write")`.
- **Evidence**: `backend/tests/test_batch7_small_router_permission_gates.py`
  (7 tests — 4 negative-proof + 3 sanity).
- **Negative-proofed**: `git stash`/`pop` on all 3 files, md5-verified
  byte-identical restoration; all 4 negative-proof cases reproduced
  live pre-fix (200/201 where 403 expected — including
  `device_results.py` reaching real business logic and 404ing on an
  unknown barcode, proving the gate is a real authorization check and
  not merely masking an unrelated 404), confirmed fixed post-restore.
- **Regression sweep**: 3099 tests across the full backend suite
  (excluding the 2 pre-existing, unrelated failures already confirmed
  identical on unmodified HEAD in Batch 6) — 0 new failures.
- **Status**: **CLOSED** — 4 routes across 3 files.

### GAP-5 (new, this pass — Batch 7, OPEN — documented, not fixed,
P2/P3) — `app/routes/quality_control.py`, 4 routes, same pattern, no
precise-fit permission exists

`submit_qc`, `submit_qc_batch` (mutations creating `QualityControl`
rows — instrument calibration/Westgard-rule records) and `list_qc`,
`qc_summary` (reads) all depend only on `Depends(get_current_user)`,
tenant-scoped correctly (`QualityControl.lab_id == current_user.lab_id`),
no permission check. Unlike GAP-4's 3 fixes, `QualityControl` is not
the same canonical resource as any existing permission
(`patients:*`/`results:*`/`orders:*` all govern different tables) —
reusing one would be an imprecise fit, and inventing a new
`qc:read`/`qc:write` pair would mean editing the central RBAC matrix,
which this batch's scope discipline reserves for explicit
authorization (same reasoning as GAP-3, at much smaller scale: no
patient PII is exposed, and lab quality-control records don't carry
the same clinical-safety weight as a patient's own result — this is a
data-integrity/operational-hygiene concern, not a patient-privacy or
mis-diagnosis risk).

- **Severity**: P2/P3 (tenant-isolated, no PII, no patient-safety
  bypass — any authenticated lab staff member recording or viewing
  instrument QC data is a much lower-impact exposure than the P1s
  fixed elsewhere this batch).
- **Status**: **OPEN — documented, not fixed.** A future batch should
  decide whether QC data belongs under a new permission pair or should
  simply require `staff:manage` (the closest existing "lab operations"
  permission) before gating it.

### Observation (not triaged this pass — out of this batch's mandate)
— `scripts/setattr_mass_assignment_guard.py` flags 17 unguarded
`for key, value in data.items(): setattr(record, key, value)` sites in
`app/services/ehr_service.py` (one per `update_*` function). Checked
whether these are exploitable through the live route surface: every
`ehr.py` `*Update` Pydantic model (e.g. `ClinicalNoteUpdate`) declares
only safe fields and none override `model_config`/`class Config` to
allow extra fields, so FastAPI's default `extra="ignore"` behavior
means a client cannot inject `patient_id`/`lab_id`/`id` through the
live route today. Recorded as a defense-in-depth observation, not a
live finding — the service layer isn't independently safe if a future
caller passes a less-constrained dict. Not investigated further or
fixed this pass; this batch's mandate was authorization taxonomy, not
mass-assignment.

### Carried forward, unchanged this pass

- GAP-1 `adaptive-auth-account-id-idor` — still **BLOCKED —
  NEEDS_DECISION**, not re-investigated.
- Hospital schema blocker (13/14 tables lack Alembic migrations) —
  unchanged.
- External CI runner blocker — unchanged, re-verified after this
  pass's push.
- Pharmacy `/batches/expiring` route-shadowing bug (P3) — still
  documented, not fixed (out of this batch's scope, P3).

## Summary (additions this pass)

| ID | Severity | Status |
|---|---|---|
| `identity.py::link_national_id` missing `patients:write` | P1 | **CLOSED** |
| `patients.py` — 6 routes missing `patients:read`/`patients:write` | P1 | **CLOSED** |
| `test_results.py::create_test_result` missing `results:write` | P1 | **CLOSED** |
| `test_results.py` citizen-results reads missing `results:read` | P2 (systemic, low-risk, fixed alongside the write-side fix in the same file) | **CLOSED** |
| `compliance.py` — 4 FHIR routes missing `patients:read`/`results:read` | P1 | **CLOSED** |
| `ehr.py` (86 routes) + `ehr_fhir.py` (29 routes) — same pattern, no existing permission string | P1 (candidate) | **OPEN — BLOCKED, next batch** |
| `security.py::/security/status` cross-tenant aggregate counts for `admin`/`master_admin` | P3 | DOCUMENTED, not fixed (SYSTEM_CONTROLLED platform-scope allowance) |

**Batch 6 closed 12 routes across 4 files (7 P1 + 1 systemic P2), all
fully negative-proofed and regression-tested (10 new + 221 adjacent
existing tests, 0 failures), and documented — but explicitly did not
fix — a 115-route sibling finding (`ehr.py`/`ehr_fhir.py`) whose
correct fix requires a permission-taxonomy decision first. This is not
"authorization complete," "security complete," or "production ready" —
per the recalculated accounting below, most of the 117 mounted routers
remain outside this pass's exhaustive-trace scope.

## Batch 7 — EHR Authorization Taxonomy + Remaining Small Router Sweep

### Carried forward, unchanged this pass

- GAP-1 `adaptive-auth-account-id-idor` — still **BLOCKED —
  NEEDS_DECISION**, not re-investigated.
- Hospital schema blocker (13/14 tables lack Alembic migrations) —
  unchanged.
- External CI runner blocker — unchanged, re-verified after this
  pass's push.
- Pharmacy `/batches/expiring` route-shadowing bug (P3) — still
  documented, not fixed (out of this batch's scope, P3).
- GAP-5 (`quality_control.py`, this pass's own new P2/P3 finding) —
  documented above, not fixed, carried into the next batch.

## Summary (additions this pass — Batch 7)

| ID | Severity | Status |
|---|---|---|
| GAP-3 refinement: `ehr.py`+`ehr_fhir.py` canonical-ownership analysis, 115 routes classified into families | — | 109 **OPEN — BLOCKED on ADR-009**, 3 **CLOSED** (Observation×2 + Provenance), 3 **VERIFIED, not a gap** |
| `ehr_fhir.py::fhir_read_observation`/`fhir_search_observation` missing `results:read` | P1 | **CLOSED** |
| `ehr_fhir.py::fhir_search_provenance` missing `audit:read` | P1 | **CLOSED** |
| `device_results.py::receive_device_results` missing `results:write` | P1 | **CLOSED** |
| `critical_alerts.py` — both routes missing `results:read` | P1 | **CLOSED** |
| `batch.py::create_batch_orders` missing `orders:write` | P1 | **CLOSED** |
| GAP-5: `quality_control.py` — 4 routes, no precise-fit permission | P2/P3 | DOCUMENTED, not fixed |
| `demo.py`, `metrics.py`, `dashboard.py`, `app_updates.py`, `mobile.py` (11 routes total) | — | **VERIFIED SAFE** — no gap found |

**Batch 7 resolved the EHR/FHIR authorization-taxonomy question Batch 6
left open — not by guessing a permission, but by establishing canonical
ownership first (ADR-009) and discovering the real shape of the
problem: 109 of 115 routes are genuinely EHR/National-owned and
BLOCKED on a real architectural decision (reuse the legacy flat RBAC vs.
wire in the National domain's own dormant, more sophisticated ABAC/RBAC/
consent/break-glass layer), while 3 routes turned out to be
mislabeled — they project the already-permissioned legacy
`LabResult`/`AuditLog` resources and are now fixed. Separately, Batch 7
completed the small-router sweep Batch 6 deferred: of the 9 remaining
routers from Batch 5's accounting correction, 5 are fully safe, 3 had
the same missing-permission-check P1 (all closed with existing, precise-fit
permissions), and 1 (`quality_control.py`) is a new, low-severity,
documented-not-fixed finding pending its own permission decision.**

**Recalculated UNKNOWN (exact, from the 117 baseline, per this
program's router-level convention that a router "resolves" out of
UNKNOWN once it has real evidence — whether VERIFIED, PARTIALLY
VERIFIED, or BLOCKED with a documented reason — not only when every
finding within it is closed)**: Batch 6 ended at 70 of 117. This pass
examined all 9 of the 25 Batch-5-surfaced routers that Batch 6 had not
yet reached (`demo, metrics, dashboard, app_updates, device_results,
quality_control, critical_alerts, batch, mobile`) — every one of them
now has real evidence (5 VERIFIED SAFE, 3 fixed/CLOSED, 1 BLOCKED with
a documented reason). **70 − 9 = 61 of 117 mounted routers remain
UNKNOWN.** This completes examination of all 25 routers Batch 5's
router-count correction originally surfaced (16 in Batch 6 + 9 in
Batch 7 = 25). `ehr`/`ehr_fhir` themselves were already counted as
resolved (PARTIALLY VERIFIED) in Batch 6's tally and are not
double-counted here — this pass refined their internal classification
without changing the router-level UNKNOWN count.

This is not "authorization complete," "security complete," "production
ready," or "national scale ready." 61 of 117 mounted routers remain
genuinely untraced, GAP-3's 109 EHR/FHIR routes remain open pending a
human architecture decision (ADR-009), and the carried-forward items
above remain exactly as open as before.
