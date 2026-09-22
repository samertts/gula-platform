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
