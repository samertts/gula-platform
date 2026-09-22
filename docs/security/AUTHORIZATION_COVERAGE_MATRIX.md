# Authorization Coverage Matrix

Evidence-based, built from the actual mounted router graph (89 routers
in `app/factory.py`), not filenames. Full route-by-route coverage of
all 89 routers was **not** completed in this bounded pass — see
"Scope and honesty note" at the end. This matrix covers the domains
where real, per-route evidence already exists (from this session's own
vertical-slice audits and from pre-existing test suites independently
re-run this pass), plus the Platform Authority axis in full (small
enough to cover completely).

## Axis 1 — Platform Authority (4 capabilities, fully covered this pass)

| Route | Method | Capability | Mechanism | Tenant/Scope | Ownership | Audit | Idempotency | Transaction | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| `/certificates/issue` | POST | `certificates_manage` | `require_platform_capability` | platform (mixed-scope resource, see arch doc §1) | N/A (issuance, not object mutation) | via service | claim/replay pattern present | commit-on-success | `test_platform_authority_certificate_cluster.py` | **VERIFIED** |
| `/certificates/{id}/revoke` | POST | `certificates_manage` | same | same | resource_id resolved server-side | via service | N/A | never commits on not-found (tested) | same test file | **VERIFIED** |
| `/certificates/{id}/rotate` | POST | `certificates_manage` | same | same | same | via service | N/A | never commits on not-found (tested) | `test_rotate_certificate_*` (3 tests) | **VERIFIED** |
| `/certificates/authorities` (register_ca) | POST | `certificates_manage` | same | platform | N/A | via service, tested "succeeds and commits with audit" | N/A | tested | `test_register_ca_*` (4 tests) — also tests raw private key is never stored | **VERIFIED** |
| `/certificates/authorities/{id}/crl` (generate_crl) | POST | `certificates_manage` | same | platform | resource_id resolved server-side | tested | N/A | never commits on not-found (tested) | `test_generate_crl_*` (3 tests) | **VERIFIED** |
| `/certificates/api-keys` (generate_api_key) | POST | `certificates_manage` | same | organization (required, non-nullable `organization_id` on `APIKey`) | **tested**: rejects a spoofed `created_by` and a nonexistent organization explicitly | tested | N/A | tested | `test_generate_api_key_*` (4 tests) | **VERIFIED** |
| `/certificates/api-keys/{id}/revoke` | POST | `certificates_manage` | same | organization | resource_id resolved server-side | tested | N/A | never commits on not-found (tested) | `test_revoke_api_key_*` (3 tests) | **VERIFIED** |
| `/certificates/api-keys/{id}/rotate` | POST | `certificates_manage` | same | organization | same | tested | N/A | never commits on not-found (tested) | `test_rotate_api_key_*` (3 tests) | **VERIFIED** |
| `federation/routes.py` — 10 platform-authority-gated mutations | POST/PUT | `federation_manage` | `require_platform_capability` | platform | N/A | via service | not individually re-verified this pass | not individually re-verified this pass | closed in NIAM batch 6 this session (prior continuation) | **PARTIALLY VERIFIED** (gate confirmed present via grep; not re-run this pass) |
| `trust/routes.py` — 15 platform-authority-gated mutations | POST/PUT | `trust_manage` | same | platform | N/A | via service | not individually re-verified this pass | not individually re-verified this pass | gate confirmed present via grep this pass | **PARTIALLY VERIFIED** |
| `governance/routes.py` (`app/identity/governance/`) — 17 platform-authority-gated mutations | POST/PUT | `governance_manage` | same | platform | N/A | via service | not individually re-verified this pass | not individually re-verified this pass | closed in NIAM batches 7a/7b/7c this session | **PARTIALLY VERIFIED** |
| **Platform Authority grant/revoke itself** | — | — | **NOT EXPOSED VIA ANY HTTP ROUTE** | — | — | — | — | — | `app/identity/platform_authority/bootstrap.py`'s own docstring: "never exposed via any HTTP route, deployment/environment-controlled" — confirmed by grep (only 2 callers of `PlatformAuthorityService(`: `bootstrap.py` and `authorization.py`'s read-only `has_capability` check) | **NOT IMPLEMENTED (by design)** — self-escalation of platform authority is structurally impossible: there is no live route through which to attempt it |

**Self-escalation question (Phase 4, item 6) for the Platform Authority
axis: answered definitively, not UNKNOWN.** An authenticated actor,
however capable, cannot grant or modify a `PlatformAuthorityAssignment`
through any HTTP route, live or dead — the only path is an
environment-variable-controlled bootstrap script that runs outside the
request cycle entirely. This is the strongest possible answer to that
question: not "guarded," but "unreachable."

## Axis 2 — Legacy monolith tenant isolation (`require_permission` / `current_user.lab_id`)

Vertical-slice-audited this session, each with its own real-Postgres
concurrency+authorization proof (status docs cited):

| Domain | Live mutating routes | Mechanism | Tenant scope | Ownership | Audit | Status doc |
|---|---|---|---|---|---|---|
| Laboratory (orders/samples/results) | ~6 (spread across `routes/orders.py`, `routes/samples.py`, `routes/results.py`) | `require_permission` + `lab_id` | query-predicate, `lab_id` | order/sample owner validated server-side | `AuditLog` hash-chain | pre-existing repair queue rows `lab-slice-*` |
| Imaging/Radiology | 24 | same + `_RADIOLOGY_WRITE_ROLES`/`_REPORT_SIGNOFF_ROLES` tiers | same | `radiologist_id` validated against same-lab doctor/radiologist | same | pre-existing repair queue rows `imaging-slice-*` |
| EMS | 14 | same | same | — | same | pre-existing repair queue row `ems-*` |
| Nursing | 38 | same + `_NURSING_WRITE_ROLES` | same | `nurse_id` validated | same | pre-existing repair queue row `nursing-vertical-slice` |
| NHDW | 30 | same + `_NHDW_ADMISSION_WRITE_ROLES` | same, `Bed.lab_id` cross-check added | — | same | pre-existing repair queue row `nhdw-admission-vertical-slice` |
| Payments | 34 (8+4+7+9+6 across 5 route files) | `require_permission` + `assert_institution_access` | query-predicate, `institution_id` | — | `PaymentAuditEvent` | `docs/security/PAYMENTS_CAPTURE_REFUND_CAS_STATUS.md` |
| Devices | 15 | `require_institutional_permission` | `lab_id` | device/connector resolved server-side | `DeviceEvent`/outbox | `docs/security/DEVICES_OUTBOX_CAS_STATUS.md` |
| Biomedical | 11 | `require_permission("system:admin")` (router-level) | none needed — SYSTEM_CONTROLLED, admin-only, cross-lab by design | N/A | none observed beyond service logs | `docs/security/BIOMEDICAL_WORK_ORDER_CAS_STATUS.md` |
| Command Center | 6 | same | same (SYSTEM_CONTROLLED) | N/A | none observed | `docs/security/COMMAND_CENTER_CONCURRENCY_STATUS.md` |
| Public Health | 8 | same | same (SYSTEM_CONTROLLED) | N/A | none observed | `docs/security/PUBLIC_HEALTH_CONCURRENCY_STATUS.md` |
| Blood Bank | not individually counted (7-file test suite) | `require_permission("system:admin")` + `ClinicalCommandGuard` | `lab_id` + facility_id checks (tested: `test_http_idor_reservation_return_and_discard_are_facility_scoped`) | tested explicitly | `ClinicalCommandReceipt` + `log_action` | `tests/blood_bank/` (32/32 re-run this session) |
| Critical Care | not individually counted | same + `_safely`-suffixed hardened methods | `lab_id` | — | — | route-to-service call audit (this session) |

**Subtotal, legacy axis, routes with individually-verified evidence this
session: ~186** (6+24+14+38+30+34+15+11+6+8, Blood Bank/Critical Care
routes not separately counted here since their evidence is
suite-level, not route-enumerated).

### Batch 2 additions (this pass — 5 domains, 23 mutating routes traced)

| Domain | Live mutating routes | Mechanism | Tenant scope | Ownership | Audit | Status |
|---|---|---|---|---|---|---|
| Billing (`app/billing/routes.py`) | 5 (`create_invoice`, `simulate_settlement`, `advance_claim`, `create_coverage`, `verify_coverage_local`) | `require_permission("payments:write"/"payments:read")` | `lab_id=current_user.lab_id` on every query | — | none observed beyond service logs | **VERIFIED** (authorization); P2/P3 concurrency findings documented, not authorization gaps — see gap register |
| Lifecycle Platform (`app/lifecycle_platform/api/routes.py`) | 7 (`register_component`, `update_component_stage`, `create_release`, `approve_release`, `record_compatibility`, `create_upgrade_path`, `issue_deprecation`) | `require_permission("system:admin")` (router-level) — **P0 fixed this pass, was previously zero auth** | none needed — SYSTEM_CONTROLLED, platform-global registry, admin-only by design | N/A | none observed | **FULLY VERIFIED** (`register_component`: full FIND→TRACE→PROVE→FIX→NEGATIVE PROOF→REGRESSION cycle); other 6 routes **VERIFIED** (same router-level gate, not individually re-proven) |
| Pilot Platform (`app/pilot_platform/api/routes.py`) | 6 (`create_pilot`, `advance_phase`, `enroll_facility`, `assess_readiness`, `decide_gate`, `record_deployment`) | `require_permission("system:admin")` (router-level) — fixed in a prior session, **re-verified still in place this pass** | same (SYSTEM_CONTROLLED) | N/A | none observed | **VERIFIED** (re-confirmed, not re-proven from scratch) |
| `services/mpi/api.py` | 3 (`resolve`, `manual_merge`, `decide_pending_review`) | `get_current_user`+`require_own_lab` (resolve); `require_role(master_admin, ministry_admin[, province_admin])` (the other two) | `resolve`: `lab_id` via ABAC; merge/decide: intentionally cross-lab (national identity adjudication) | N/A | `MergeAudit`/hash-chained `mpi_merge_audit` | **VERIFIED** |
| `capabilities/fhir_interoperability/routes.py` (the one LIVE sub-router of `app/capabilities/`) | 2 (`convert_hl7_to_fhir`, `create_fhir_resource`) | `require_institutional_permission("lab:manage")` | `actor.lab_id` | `IntegrityError`→409 on `(id,version,institution)` unique constraint (atomic-claim pattern) | via service | **VERIFIED** |

**Batch 2 subtotal: 23 routes**, all with explicit authorization
confirmed; 1 P0 found and closed (lifecycle_platform); 2 concurrency
findings documented (billing, P2/P3, not authorization gaps — see
`docs/security/AUTHORIZATION_GAP_REGISTER.md`).

### Batch 3 additions (this pass — 5 domains, 17 mutating routes traced, 0 findings)

Selected from the `LIVE / NO-OWNED-MODELS` bucket in
`docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md` (routers mounted, real
persistence via shared models, not yet individually confirmed). All 5
resolved to **VERIFIED** — zero P0/P1/P2/P3 findings this batch, a
genuine result of the domains selected, not evidence that the whole
UNKNOWN bucket is clean.

| Domain | Live mutating routes | Mechanism | Tenant scope | Ownership | Audit | Evidence |
|---|---|---|---|---|---|---|
| Healthcare Consent (`app/routes/consent.py`) | 2 (`grant`, `revoke`) | `get_current_user` + self-or-admin ownership (`_user_owns_gpid`: caller must be the citizen subject, or `master_admin`/`ministry_admin`) | subject-scoped (`gpid` = citizen_ulid) | explicit ownership check, not role-only | via `consent_service` audit trail | `tests/test_consent.py` (9 tests, re-run green) |
| Patient Card (`app/routes/patient_card.py`) | 1 (`/scan`; reads also HMAC-verified) | `get_current_user` + `lab_id` tenant filter + HMAC token verify + cross-lab token rejection | `current_user.lab_id`, token bound to issuing lab | N/A (token-based, not account-based) | every view/scan/history/print writes `log_action` | `tests/test_patient_card.py` (15 tests, re-run green) — matches CLAUDE.md's own Patient Card invariant |
| Canonical Patient / MPI (`app/routes/canonical_patient.py`) | 4 (create, `/merge`, `/link-patient`, `/link-citizen`) | `require_national_scope`/`require_own_patient`/`provenance_lab_id` (`app/services/mpi/scope.py`) — **a prior fix, "NR-148", already closed before this session**; re-verified, not assumed | national-scope permission (`platform:view_stats`) for cross-lab ops; server-derived provenance for lab-scoped create | `visible_canonical` returns 404 (not 403) to avoid an existence oracle | via MPI link/merge services | `tests/test_canonical_patient_scope.py` (24 tests) + `tests/test_canonical_patient_lab_id_authority.py` (2 tests) + `tests/test_auth_infrastructure.py` cross-tenant merge proof (403 same-lab, 200 national), all re-run green |
| Service Accounts (`app/routes/service_accounts.py`) | 3 (create, `DELETE /{id}`, `/{id}/rotate`) | role check (`master_admin`/`admin`) + `lab_id` scope enforced inside `revoke_service_account`/`rotate_api_key` (query filters by `lab_id` unless caller is `master_admin`) | `current_user.lab_id`, real DB-level filter (confirmed by code read, not assumed) | N/A | — | **New test file this pass**: `tests/test_service_accounts_authz.py` (6 tests — non-admin role denied, foreign `lab_id` in body denied, cross-lab rotate/revoke denied 404, master_admin cross-lab success, unauthenticated 401) — closes a real evidence gap (prior test coverage only exercised the single-lab admin happy path) |
| MFA (`app/routes/mfa.py`) | 7 (TOTP setup/verify, WebAuthn register/authenticate begin+complete, device delete) | `get_current_user`; every mutation scoped to `current_user.id` server-side — **no client-supplied account/session identifier anywhere in this router**, unlike the carried-forward `adaptive-auth-account-id-idor` P1 | self only (device ownership: `remove_device` filters `MFADevice.id == device_id AND user_id == user_id`) | N/A | — | `tests/test_auth_infrastructure.py` MFA section (401 unauthenticated for 4 endpoints, own-device add/remove/404-for-others-device roundtrip), re-run green |

**Batch 3 subtotal: 17 routes**, all VERIFIED, 0 findings. **Zero
production code changed this batch** — one new test file
(`backend/tests/test_service_accounts_authz.py`) closing an evidence
gap identified during tracing.

## Axis 3 — NIAM Organization RBAC (`AuthorizationDecisionService`)

Closed this session, prior continuation (NIAM sync/async closure,
Directive 4): `workflows` (8), `notifications` (11), `compliance` (8),
`admin` (12), `adaptive_auth` (16, +P0 authz fix), `federation` (15,
+`federation_manage` capability), `governance` sub-batches 7a/7b/7c
(24, +`governance_manage` capability), lifecycle `GuardianService` (6),
`EnterpriseRegistrationService` (6), `WorkforceService` (9, all
fail-closed), `GovernmentHRService` (9, all fail-closed),
`CitizenService` (11, mixed self/admin). **135 routes total**, each
individually proven with real HTTP 401/403/cross-tenant/self-escalation
negative proofs at the time (`docs/security/NIAM_SYNC_ASYNC_CLOSURE_FINAL_REPORT.md`).
Not re-verified in this bounded pass (no code changed since); cited as
existing evidence.

## Dead / latent authorization surface — explicitly excluded from live coverage

| Package | Classification | Note |
|---|---|---|
| `app/capabilities/clinical_foundation`, `document_management`, `encounter_management`, `healthcare_consent`, `provider_management`, `reporting_service`, `search_service`, `storage_service`, `workflow_engine` (9 of 10 sub-packages, 46 command files) | **DEAD** | Zero references anywhere outside their own package; not mounted in `app/factory.py`. If any were activated in the future, each would need its own authorization audit before going live — none is pre-verified by virtue of existing as code. |
| 7 schema-latent domains (`command_intelligence`, `document_intelligence`, `health_data`, `knowledge_graph`, `research_platform`, `roadmap`, `simulation`) | **LIVE (routed) / SCHEMA-BLOCKED** | Router is mounted (so technically "LIVE" per a router-only definition) but every mutating endpoint 500s with `UndefinedTable` — not exploitable, not usable, excluded from authorization coverage counting since there is no reachable mutation to authorize. |
| `governance` (top-level `app/governance/`, distinct from `app/identity/governance/`) | **LIVE (routed) / SCHEMA-BLOCKED** | 58/64 tables missing — same reasoning. |
| `national` (11 routers) | **LIVE (routed) / SCHEMA-BLOCKED** | 103/114 tables missing — same reasoning. |
| `app/core/idempotency.py` | **DORMANT** (not an authorization mechanism, cross-referenced from the prior idempotency pass) | No live route uses it; not counted anywhere in this matrix. |

## Phase 8 — Live mutation coverage summary

```
TOTAL LIVE MUTATING ROUTES WITH INDIVIDUALLY-VERIFIED EVIDENCE (cumulative through Batch 3)
----------------------------------------------------------------------------
~186 (legacy axis) + 51 (Platform Authority call sites, 4 domains) + 135
(NIAM organization RBAC, prior continuation) + 23 (Batch 2: billing,
lifecycle_platform, pilot_platform, mpi, fhir_interoperability) + 17
(Batch 3: consent, patient_card, canonical_patient, service_accounts,
mfa) = ~412

WITH EXPLICIT AUTHORIZATION
---------------------------
~412 (all of the above — none of these routes were found unguarded at
the end of their respective passes; lifecycle_platform's 7 routes had
ZERO authorization until Batch 2's fix — see gap register GAP-2 — and
are counted here only post-fix)

WITH TENANT ISOLATION
---------------------
~333 (legacy axis's tenant-scoped rows + NIAM organization-scoped rows +
Batch 2's tenant-scoped additions: billing 5, fhir_interoperability 2,
mpi's `resolve` 1 + Batch 3's tenant/subject-scoped additions:
patient_card 1, service_accounts 3, consent's subject-ownership model 2
(not lab-scoped, but an equivalent per-subject boundary); excludes the
SYSTEM_CONTROLLED admin-only domains where tenant scope is deliberately
not applicable — biomedical/command_center/public_health/blood_bank/
critical_care/pilot_platform/lifecycle_platform, mpi's cross-lab admin
adjudication routes `manual_merge`/`decide_pending_review`, canonical_patient's
national-scope operations by design, and mfa's account-scoped-not-tenant-scoped
routes)

WITH OBJECT OWNERSHIP CHECK
---------------------------
~13 individually-documented ownership validations (radiologist_id,
nurse_id, device/connector resolution, facility-scoped reservation
IDOR test, certificate api-key spoofed-created_by rejection, Batch 3's
consent subject-ownership check, patient-card HMAC-token-to-lab
binding, MFA device-to-user ownership filter, service-account
lab-scope filter) — this is a count of *documented instances*, not a
claim that every route needing one has it; most routes in the matrix
do not require object-ownership validation by their nature
(platform-wide admin operations, INSERT-only creates)

WITH AUDIT
----------
~412 minus the SYSTEM_CONTROLLED domains where no dedicated audit
table was observed (biomedical/command_center/public_health/
pilot_platform/lifecycle_platform -- they log via standard application
logs, not a dedicated AuditLog/PaymentAuditEvent row; not verified as a
gap, just not confirmed present) minus service_accounts/mfa (no
dedicated audit trail observed for these two specifically; not
verified as a gap, just not confirmed present)

WITH IDEMPOTENCY WHERE REQUIRED
-------------------------------
Clinical commands (Laboratory/Imaging/EMS/Blood Bank via
ClinicalCommandGuard): confirmed. Payments (PaymentIntent): confirmed.
Devices (DeviceOutboxMessage): confirmed. FHIR resource creation
(`create_fhir_resource`): confirmed — real `(id,version,institution)`
unique constraint + `IntegrityError`→409, atomic-claim pattern.
Billing `create_invoice`: partially confirmed — backed by a real
unique constraint (no silent double-create possible) but the route
does not catch `IntegrityError`, so a race produces an unhandled 500
rather than a clean 409 (documented as GAP-4, P3, not fixed). Everything
else: NOT INDIVIDUALLY VERIFIED this pass -- most of the ~412 routes
above are not inherently idempotency-sensitive (reads, or creates where
a duplicate POST is an acceptable user-facing retry, not a
clinical/financial duplicate-effect risk).

WITH EXPLICIT TRANSACTION CONTRACT
-----------------------------------
ClinicalCommandGuard's claim/complete contract is explicit and
documented at the source. Payments/Devices/Biomedical/Command
Center/Public Health CAS fixes each individually proved commit/rollback
correctness as part of their own real-Postgres proof. Billing's
`simulate_settlement`/`advance_claim` lack row locking (documented as
GAP-3, P2, not fixed — both racers converge on the same correct final
status per the state-transition map, so no incorrect end state results,
only a possible duplicate audit write). Not independently re-verified
as a standalone Phase-3-style trace for the remaining routes in this
pass.

FULLY VERIFIED
---------------
Platform Authority certificates cluster (8 routes, 64 tests, re-run
green this pass) + the 6 CAS-fixed domains' specific fixed routes (6
routes) + lifecycle_platform's `register_component` (Batch 2's P0 fix,
full cycle) = 15 routes with the complete FIND→TRACE→PROVE→FIX→
NEGATIVE PROOF→REGRESSION lifecycle demonstrably closed.

PARTIALLY VERIFIED
------------------
~397 (everything else counted above — real evidence exists, from this
session or a prior one, but was not independently re-proven inside
*that specific bounded pass* with the full negative-proof cycle;
includes lifecycle_platform's other 6 routes, all of billing/
pilot_platform/mpi/fhir_interoperability's routes, and Batch 3's 17
routes — VERIFIED via direct code read + existing/new test evidence,
not a from-scratch negative-proof cycle per route)

AUTHORIZATION GAP
-----------------
0 remaining open authorization gaps found through Batch 3. One P0 was
found (`lifecycle-platform-no-auth`, Batch 2, zero auth on 7 mutating
routes) and CLOSED within that same batch (fixed, proven,
negative-proofed, tested, zero regressions). Batch 3 found 0 new
findings of any severity. See docs/security/AUTHORIZATION_GAP_REGISTER.md
for full evidence, plus the one item carried forward from a prior
pass — `adaptive-auth-account-id-idor`, still NEEDS_DECISION, not
newly discovered — and two non-authorization concurrency findings in
billing (P2/P3, documented not fixed, Batch 2, out of bounded scope).

BLOCKED
-------
0 authorization findings blocked (the governance/national schema gaps
are BLOCKED for a different reason -- persistence, not authorization --
and are excluded from this count since there is no reachable route to
authorize)

UNKNOWN
-------
The remaining ~68 of the 89 mounted routers not named above (the
schema-latent 7, the `NO-OWNED-MODELS` bucket minus Batch 3's 5 newly
resolved routers, `national`'s 11 routers, `governance`'s 1 router, and
every router no pass has vertical-slice-audited) — their route-level
authorization mechanism was NOT traced. Recorded as UNKNOWN, not
silently assumed either safe or unsafe. (Was ~78 before Batch 2, ~73
before Batch 3, now ~68 — derived from the actual mounted router graph
in `app/factory.py`, re-confirmed at 89 routers this pass, not by
blindly subtracting 5.)
```

## Scope and honesty note

This matrix consolidates **real, already-gathered evidence** across
multiple bounded passes, most recently Batch 3 (consent, patient_card,
canonical_patient, service_accounts, mfa — 5 domains, 17 mutating
routes, 0 new findings) following Batch 2 (billing, lifecycle_platform,
pilot_platform, `services/mpi`, `capabilities/fhir_interoperability` —
5 domains, 23 mutating routes, 1 P0 found and closed with full proof
rigor). It is not a fresh route-by-route trace of all 89 mounted
routers — that would be a multi-day undertaking on its own, explicitly
out of scope for any of these "discovery + proof only, minimum
resources" bounded passes. The ~68 routers marked UNKNOWN above are the
honest remainder as of Batch 3 (down from ~78 before Batch 2, ~73
before Batch 3). **Already-audited domains — do not repeat in the next
bounded batch**: Platform Authority (certificates/federation/
trust/governance), Laboratory, Imaging/Radiology, EMS, Nursing, NHDW,
Payments, Devices, Biomedical, Command Center, Public Health, Blood
Bank, Critical Care, the 12 NIAM-axis domains (workflows/notifications/
compliance/admin/adaptive_auth/federation/governance/lifecycle
sub-services), billing, lifecycle_platform, pilot_platform,
`services/mpi`, `capabilities/fhir_interoperability`, consent,
patient_card, canonical_patient, service_accounts, mfa.

**Next bounded batch candidates (from the `LIVE / NO-OWNED-MODELS`
bucket in `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`, still
UNKNOWN after Batch 3)**: `password_reset`, `oauth2`, `saml`
(authentication-adjacent, similar risk class to `mfa`), `hospital`
(23 mutating routes — largest single remaining candidate), `edge`
(14 mutating routes), `ai_fabric` (23 mutating routes), `control_plane`
(10 mutating routes), `integrations`/`advanced_integrations`,
`chronic_care`, `certification`, `citizen_platform`, `contracts`,
`ai_telemetry`, `hospital`/`kernel`/`clinical_gateway`, and the generic
`routes/` package's remaining untraced files (`claims`, `ai`,
`optimizer`, `stats`, `user_preferences`, `national_data`,
`national_streaming`, `care_continuum`, `clinical*`). Each still needs
its own "what does this router actually persist, and where" check
before being called LIVE with confidence.
