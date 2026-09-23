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

### Batch 4 additions (this pass — combined Hospital + auth-adjacent, 24 mutating routes traced, 3 real findings closed)

| Domain | Live mutating routes | Findings | Status |
|---|---|---|---|
| Hospital (`app/routes/hospital.py`) | 23 (4 already gated from a prior pass: `create_hospital`/`update_hospital`/`deactivate_hospital`/`create_campus`; 19 newly traced this batch) | **P0/P1 #1 (authorization)**: 19 of 23 mutating routes had zero role check beyond bare authentication — facility/administrative creates (buildings/floors/departments/clinics/rooms/beds/units/OTs/equipment/cost-centers) and, critically, clinical patient-safety operations (bed assign/discharge/transfer, OT status change, surgical safety checklist completion) were reachable by any authenticated LabUser of any role. **P1 #2 (data-integrity, found while building the fix's test harness)**: `HospitalService._get_entity`'s `not model.is_deleted` is a Python `not` applied to the column attribute itself (evaluates to a literal `False` at query-build time — confirmed directly), so every nested-entity lookup through it unconditionally matched zero rows; this is a shared helper used by 17 call sites across ~10 routes. **P1 #3 (transaction integrity, found while proving #2's fix)**: 18 of Hospital's mutating routes never called `db.commit()` anywhere (not the route, not the service, not `log_action`) — `get_db()` uses `autocommit=False` and only rolls back on exception, so every one of these routes returned a 200/201 showing an apparently-created/updated record that was never durably persisted; proven with two genuinely independent DB sessions against a real file-backed SQLite DB (the shared-session `client` test fixture masks this entirely). | **All three CLOSED**: role gates added (reusing this session's `_HOSPITAL_ADMIN_ROLES`/NHDW's `_NHDW_ADMISSION_WRITE_ROLES` conventions, no new role vocabulary); `_get_entity` fixed (`~model.is_deleted`); `db.commit()` added to all 18 affected routes. Full FIND→REPRODUCE→FIX→NEGATIVE PROOF→REGRESSION cycle for all three, `git stash`/`pop` md5-verified. 25 + 3 new tests, 209 total regression tests re-run, all green. |
| OAuth2 (`app/routes/oauth2.py`) | 1 selected (`POST /oauth2/register`; the rest of the OAuth2 surface traced but not fixed — see notes below) | `OAuth2Client` is a platform-global registry (no lab_id/tenant column on the model at all, by design). `register_client` had only `get_current_user` — any authenticated LabUser of any role could register a client with attacker-chosen `redirect_uris`, which then receives real users' access/refresh/id tokens the moment any user completes `/authorize` against it. | **CLOSED**: role-gated with the same `{admin, master_admin}` convention used elsewhere this session (`service_accounts.py`, Hospital). 3 new tests, full negative-proof cycle. |
| Password Reset (`app/routes/password_reset.py`) | 3 (`forgot-password`, `reset-password`, `change-password`) | All correctly scoped: `forgot`/`reset` derive identity solely from the token (anti-enumeration response, no client-supplied user id anywhere); `change-password` requires `get_current_user` and only ever mutates the caller's own row, then bumps `perm_version` to revoke other sessions. | **VERIFIED, no gap.** |
| SAML (`app/routes/saml.py`) | 1 mutating-shaped route (`POST /auth/saml/acs`) | Validates signature/issuer/audience/assertion cryptographically but **never issues a session, JWT, or writes to the DB** — the `db` parameter is declared but unused. Not a live authentication bypass because it grants no privileged effect; it is an incomplete SSO implementation (a functional gap, not a security gap). | **VERIFIED, not exploitable — documented as functionally incomplete, not fixed (feature completion is out of this audit's scope).** |

**Batch 4 subtotal: 24 mutating routes traced, 3 real findings, all closed with full proof rigor.** OAuth2's other routes (`/authorize`, `/token`, `/introspect`, `/revoke`, and their helper grant handlers) were read and traced but not included in the 24-route count above since they were not independently re-proven this pass; notes: `/authorize` issues an auth code bound to `current_user.id` only (no client-supplied identity, but also no explicit consent screen — a UX/protocol-completeness observation, not a proven IDOR); `/introspect` and `/revoke` require no client authentication (a deviation from RFC 7662 convention) but are not practically exploitable without already possessing the real token value. Both documented as P2/P3-level hardening notes in the gap register, not fixed (Phase 5's "do not redesign authentication protocols" instruction).

**Systemic pattern discovered, not fixed this batch**: the exact `not model.is_deleted` (Python `not` instead of SQLAlchemy `~`) bug recurs at 5 more call sites outside Hospital — `app/radiology/pacs.py:365,375,388` and `app/pharmacy/routes.py:504` and `app/routes/admin.py:257` — all confirmed by direct grep + a standalone SQLAlchemy behavior check (`.filter(False)` compiles to `WHERE 0=1`, always zero rows). Out of this batch's bounded scope (different, unaudited domains); registered in the gap register and repair queue as the next concrete, cheap, high-confidence fix candidate.

### Batch 5 (this pass — systemic boolean-filter closure + a mounted-router accounting correction)

A deterministic AST-based discovery pass (`scripts/security/boolean_not_filter_guard.py`, built this batch) — not a grep, per this batch's own "do not assume exact files or line numbers" instruction — found **28 total repo-wide occurrences** of the `not`-vs-`~` boolean-filter defect, 23 more than the "5 known sites" this batch's own directive assumed going in. All 28 fixed; the detector now returns zero hits. Full per-site evidence in `docs/security/AUTHORIZATION_GAP_REGISTER.md` (GAP-9) and `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` (Pattern 2, updated).

**LIMS is the headline finding**: `app/lims/routes.py` (`lims_routes.router`, mounted directly in `app/factory.py` — a genuinely distinct router from the legacy `routes/labs.py`/`routes/samples.py`/`routes/results.py` files this matrix's existing "Laboratory" line covers) had **20 of the 28 sites**, all LIVE, all tenant-scoped correctly (`_lab_id(current_user)`), across every list/get/dashboard-count route for Instrument, Specimen, Order, Panel, Result, Reagent, Consumable, Lot, ReferenceRangeDef, AutoValidationRule, LabReport, QCProgram, Supplier, Storage, DeltaCheckRule, Department, and Manufacturer. This router had never been individually vertical-slice-audited under any name before this batch — the entire LIMS listing surface was silently non-functional (every affected call returned empty/zero, not an error) until fixed. **`lims_routes.router` moves from UNKNOWN to VERIFIED this batch** — genuine new coverage, not a re-verification of already-audited work.

**`pharmacy_router` also moves from UNKNOWN to PARTIALLY VERIFIED**: 2 live sites traced (`GET /pharmacy/dashboard/expiry-alerts`, and the `GET /pharmacy/batches/expiring` route it shares a fixed method with — though that second route is itself shadowed by an earlier-registered `/batches/{batch_id}` path, a separate, pre-existing routing bug, NOT fixed here, out of bound), both correctly tenant-scoped via `self.lab_id` (server-derived from `user.lab_id`, never client-supplied) and gated by `get_current_user`. 3 more sites in this same router are DEAD code (`_get_or_404`, `auto_quarantine_expired`, `get_cold_chain_drugs` — zero callers anywhere).

**`radiology_router` was already audited** (this matrix's existing "Imaging/Radiology" line, 24 routes, `imaging-slice-*` repair-queue rows) — re-verified, not newly counted. 1 of its 3 buggy sites is LIVE (`revoke_share`, via `DELETE /radiology/sharing/{id}`, correctly ownership-scoped via `_study_for_user`); the other 2 (`access_share`, `list_shares`) are DEAD code.

**`app/routes/admin.py`'s router gains partial new evidence**: `list_pending_labs` (`GET /admin/labs/pending`) traced — gated by `require_permission("platform:manage_users")`, additionally province-scoped for `province_admin`. Only this one route traced; the router's other ~15+ routes remain UNKNOWN.

#### Mounted-router accounting correction (Phase 11 mandate: "recalculate from source, do not estimate")

Every prior batch this session counted mounted routers via `grep -c "app.include_router("` against `app/factory.py`, reporting **89**. This batch's mandatory recalculation found that count is **wrong** — not because routers were added, but because one line in `app/factory.py` (`for r in core_routes + feature_routes + advanced_routes + admin_routes + mobile_routes + compliance_routes: app.include_router(r.router)`, line 578-579) registers **29 routers** in a single loop iteration, which a textual line-count of `app.include_router(` only counts as **1**.

**Corrected total: 117 mounted routers** (89 − 1 [the loop line, previously counted once] + 29 [the routers it actually registers] = 117).

The 29 loop-registered routers: `login, register, verification, demo, setup, metrics, patients, results, test_results, dashboard, labs, samples, app_updates` (13, `core_routes`), `qr, id_scan, identity, notifications, ehr, ehr_fhir, cds_hooks, security, device_results` (9, `feature_routes`), `quality_control, critical_alerts, batch` (3, `advanced_routes`), `admin, admin_log_level` (2, `admin_routes`), `mobile` (1), `compliance` (1, `app/routes/compliance.py` — confirmed by direct code read to be a **distinct** router from the already-counted NIAM-axis `app/identity/compliance/routes.py`, not a duplicate).

Of these 29: `labs`, `samples`, `results` map to this matrix's existing "Laboratory (orders/samples/results)" audited line (already counted, just newly confirmed to be individually these 3 specific routers rather than a bundled reference). `admin` gained the one-route evidence above this batch (partial). The remaining **25 routers were never previously individually accounted for at all** in any prior batch's UNKNOWN estimate — genuinely newly surfaced by this correction, not new work product: `login, register, verification, demo, setup, metrics, patients, test_results, dashboard, app_updates, qr, id_scan, identity, notifications, ehr, ehr_fhir, cds_hooks, security, device_results, quality_control, critical_alerts, batch, admin_log_level, mobile, compliance`.

**This is a correction to the counting methodology, not a regression or new mounting activity.** No router was added to the running application by this batch; the routers were always there, always reachable, and always (accidentally) excluded from every previous batch's denominator.

**Batch 5 subtotal: 28 boolean-filter sites found and fixed (23 beyond the 5 assumed), 1 new detector built and self-tested, 3 routers moved from UNKNOWN to VERIFIED/PARTIALLY VERIFIED (`lims`, `pharmacy`, partial `admin`), mounted-router count corrected from 89 to 117.**

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
TOTAL LIVE MUTATING ROUTES WITH INDIVIDUALLY-VERIFIED EVIDENCE (cumulative through Batch 4)
----------------------------------------------------------------------------
~186 (legacy axis) + 51 (Platform Authority call sites, 4 domains) + 135
(NIAM organization RBAC, prior continuation) + 23 (Batch 2: billing,
lifecycle_platform, pilot_platform, mpi, fhir_interoperability) + 17
(Batch 3: consent, patient_card, canonical_patient, service_accounts,
mfa) + 24 (Batch 4: Hospital 23, oauth2 register 1) = ~436

WITH EXPLICIT AUTHORIZATION
---------------------------
~436 (all of the above — none of these routes were found unguarded at
the end of their respective passes; lifecycle_platform's 7 routes
(Batch 2) and Hospital's 19 routes + oauth2's register route (Batch 4)
had ZERO authorization until their respective fixes this session — see
gap register GAP-2/GAP-5/GAP-8 — and are counted here only post-fix)

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
full cycle) + Hospital's 19 role-gated routes, `_get_entity`'s fix (17
call sites), and 18 commit-fixed routes (Batch 4, three findings each
with a complete FIND→TRACE→REPRODUCE→FIX→NEGATIVE PROOF→REGRESSION
cycle) + oauth2's `register_client` (Batch 4) = 44 routes with the
complete lifecycle demonstrably closed.

PARTIALLY VERIFIED
------------------
~397 (everything else counted above — real evidence exists, from this
session or a prior one, but was not independently re-proven inside
*that specific bounded pass* with the full negative-proof cycle;
includes lifecycle_platform's other 6 routes, all of billing/
pilot_platform/mpi/fhir_interoperability's routes, Batch 3's 17
routes, Hospital's 4 already-gated routes, and password_reset/saml's 4
routes — VERIFIED via direct code read + existing/new test evidence,
not a from-scratch negative-proof cycle per route)

AUTHORIZATION GAP
-----------------
0 remaining open authorization gaps found through Batch 4. Found and
CLOSED this session: `lifecycle-platform-no-auth` (P0, Batch 2, zero
auth on 7 mutating routes); `hospital-facility-no-role-check` (P1,
Batch 4, zero role check on 19 mutating routes including clinical
patient-safety operations — bed assign/discharge/transfer, OT status,
surgical safety checklist); `oauth2-register-no-role-check` (P1, Batch
4, zero role check on platform-global OAuth2 client registration).
Also closed this batch, non-authorization but P1 severity:
`hospital-get-entity-boolean-bug` (a Python `not` vs SQLAlchemy `~`
typo made 17 nested-entity lookup call sites always return "not
found") and `hospital-missing-commit` (18 routes never called
`db.commit()` anywhere, so writes were never durably persisted despite
a 200/201 response — proven with two genuinely independent DB
sessions). See docs/security/AUTHORIZATION_GAP_REGISTER.md for full
evidence, plus the one item carried forward from a prior pass —
`adaptive-auth-account-id-idor`, still NEEDS_DECISION, not newly
discovered — non-authorization concurrency findings in billing (P2/P3,
documented not fixed, Batch 2), and a newly-registered systemic
`not`-vs-`~` boolean-filter pattern (5 more occurrences in
radiology/pharmacy/admin, documented not fixed, Batch 4, out of
bounded scope).

BLOCKED
-------
0 authorization findings blocked (the governance/national schema gaps
are BLOCKED for a different reason -- persistence, not authorization --
and are excluded from this count since there is no reachable route to
authorize)

UNKNOWN
-------
**Mounted-router denominator corrected this pass: 89 → 117** (see
Batch 5's "Mounted-router accounting correction" above — one line in
`app/factory.py` registers 29 routers via a `for` loop that a textual
`grep -c "app.include_router("` only counts as 1; this is a counting-
methodology fix, not new mounting activity).

Of the 28 net new routers this correction surfaces (29 loop routers −
1 already counted): 3 (`labs`/`samples`/`results`) map to the
already-audited "Laboratory" line above (no change), 1 (`admin`) gained
one route's evidence this pass (partial), and **25 are genuinely,
newly-honest UNKNOWN** — never individually accounted for by any prior
batch's estimate: `login, register, verification, demo, setup, metrics,
patients, test_results, dashboard, app_updates, qr, id_scan, identity,
notifications, ehr, ehr_fhir, cds_hooks, security, device_results,
quality_control, critical_alerts, batch, admin_log_level, mobile,
compliance` (the last being `app/routes/compliance.py`, confirmed
distinct from the already-counted NIAM-axis `app/identity/compliance/`).

Also this pass: `lims_routes.router` moves from UNKNOWN to VERIFIED
(20 sites traced, all LIVE, all tenant-scoped — the largest single
router audit this batch), `pharmacy_router` moves from UNKNOWN to
PARTIALLY VERIFIED (2 LIVE sites traced), `radiology_router` was
already audited (re-verified, not newly counted — 1 real regression
found and fixed within it).

**Corrected UNKNOWN: ~64 (previous, against the wrong 89 denominator)
+ 25 (newly surfaced by the router-count correction) − 3 (`lims`,
`pharmacy`, partial `admin` moved to VERIFIED/PARTIALLY VERIFIED this
pass) = ~86 of 117 mounted routers.** Recorded as UNKNOWN, not
silently assumed either safe or unsafe. This number is *larger* than
last pass's ~64 not because coverage regressed, but because the
denominator itself was wrong until this pass's mandatory
recalculation — exactly the "do not estimate, discover from source"
outcome this batch's own directive anticipated.
```

## Scope and honesty note

This matrix consolidates **real, already-gathered evidence** across
multiple bounded passes, most recently Batch 5 (systemic boolean-filter
closure — 28 sites found and fixed across LIMS/pharmacy/radiology/
admin, plus the mounted-router accounting correction from 89 to 117)
following Batch 4 (combined Hospital + password_reset/oauth2/saml — 24
mutating routes traced, 3 real findings closed), Batch 3 (consent,
patient_card, canonical_patient, service_accounts, mfa — 5 domains, 17
mutating routes, 0 new findings), and Batch 2 (billing,
lifecycle_platform, pilot_platform, `services/mpi`,
`capabilities/fhir_interoperability` — 5 domains, 23 mutating routes, 1
P0 found and closed). It is not a fresh route-by-route trace of all 117
mounted routers — that would be a multi-day undertaking on its own,
explicitly out of scope for any of these "discovery + proof only,
minimum resources" bounded passes. The ~86 routers marked UNKNOWN above
are the honest remainder as of Batch 5, against the *corrected* 117
denominator (was ~78 of 89 before Batch 2, ~73 of 89 before Batch 3,
~68 of 89 before Batch 4, ~64 of 89 before Batch 5 — all of those prior
"of 89" figures were computed against the undercounted denominator; see
Batch 5's accounting-correction note above for why ~86 of 117 is larger
despite continuous forward progress, not a regression).

**Already-audited domains — do not repeat in the next bounded batch**:
Platform Authority (certificates/federation/trust/governance),
Laboratory (`routes/labs.py`/`routes/samples.py`/`routes/results.py`),
Imaging/Radiology (`radiology_router`), EMS, Nursing, NHDW, Payments,
Devices, Biomedical, Command Center, Public Health, Blood Bank,
Critical Care, the 12 NIAM-axis domains (workflows/notifications/
compliance/admin/adaptive_auth/federation/governance/lifecycle
sub-services — note: `app/identity/compliance/` and `app/identity/admin/`
here, NOT the same-named `app/routes/compliance.py`/`app/routes/admin.py`),
billing, lifecycle_platform, pilot_platform, `services/mpi`,
`capabilities/fhir_interoperability`, consent, patient_card,
canonical_patient, service_accounts, mfa, hospital, password_reset,
oauth2, saml, **`lims_routes.router`, `pharmacy_router` (partial —
only 2 of its routes traced), `app/routes/admin.py`'s router (partial
— only 1 of its ~15+ routes traced)**.

**Next bounded batch candidates**: the 25 routers newly surfaced by
this batch's router-count correction are the highest-priority
candidates precisely because they were invisible to every prior batch
— `login, register, verification, demo, setup, metrics, patients,
test_results, dashboard, app_updates` (core, likely auth-adjacent —
some may overlap with already-audited auth flows, verify per-router
before assuming), `qr, id_scan, identity, notifications, ehr,
ehr_fhir, cds_hooks, security, device_results` (feature routes),
`quality_control, critical_alerts, batch` (advanced routes),
`admin_log_level, mobile, compliance` (`app/routes/compliance.py`,
distinct from the NIAM one). Also still open from before Batch 5:
`edge` (14 mutating routes), `ai_fabric` (23 mutating routes),
`control_plane` (10 mutating routes), `integrations`/
`advanced_integrations`, `chronic_care`, `certification`,
`citizen_platform`, `contracts`, `ai_telemetry`, `kernel`/
`clinical_gateway`, and the generic `routes/` package's remaining
untraced files (`claims`, `ai`, `optimizer`, `stats`,
`user_preferences`, `national_data`, `national_streaming`,
`care_continuum`, `clinical*`). Each still needs its own "what does
this router actually persist, and where" check before being called
LIVE with confidence. **Also worth periodic re-running**: `python3
scripts/security/boolean_not_filter_guard.py` (this batch's new
detector) as a cheap first check before any future domain audit, and
the pre-existing `python3 scripts/setattr_mass_assignment_guard.py`.
