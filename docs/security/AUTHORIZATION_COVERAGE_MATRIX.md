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
TOTAL LIVE MUTATING ROUTES WITH INDIVIDUALLY-VERIFIED EVIDENCE THIS SESSION
----------------------------------------------------------------------------
~186 (legacy axis) + 51 (Platform Authority call sites, 4 domains) + 135
(NIAM organization RBAC, prior continuation) = ~372

WITH EXPLICIT AUTHORIZATION
---------------------------
~372 (all of the above — none of these routes were found unguarded;
this is a description of what was already audited, not a repo-wide total)

WITH TENANT ISOLATION
---------------------
~321 (legacy axis's tenant-scoped rows + NIAM organization-scoped rows;
excludes the SYSTEM_CONTROLLED admin-only domains where tenant scope is
deliberately not applicable — biomedical/command_center/public_health/
blood_bank/critical_care, 11+6+8 routes plus 2 suite-level domains)

WITH OBJECT OWNERSHIP CHECK
---------------------------
~9 individually-documented ownership validations (radiologist_id,
nurse_id, device/connector resolution, facility-scoped reservation
IDOR test, certificate api-key spoofed-created_by rejection) — this is
a count of *documented instances*, not a claim that every route needing
one has it; most routes in the matrix do not require object-ownership
validation by their nature (platform-wide admin operations, INSERT-only
creates)

WITH AUDIT
----------
~372 minus the 3 SYSTEM_CONTROLLED domains where no dedicated audit
table was observed (biomedical/command_center/public_health -- they log
via standard application logs, not a dedicated AuditLog/PaymentAuditEvent
row; not verified as a gap, just not confirmed present)

WITH IDEMPOTENCY WHERE REQUIRED
-------------------------------
Clinical commands (Laboratory/Imaging/EMS/Blood Bank via
ClinicalCommandGuard): confirmed. Payments (PaymentIntent): confirmed.
Devices (DeviceOutboxMessage): confirmed. Everything else: NOT
INDIVIDUALLY VERIFIED this pass -- most of the ~372 routes above are not
inherently idempotency-sensitive (reads, or creates where a duplicate
POST is an acceptable user-facing retry, not a clinical/financial
duplicate-effect risk).

WITH EXPLICIT TRANSACTION CONTRACT
-----------------------------------
ClinicalCommandGuard's claim/complete contract is explicit and
documented at the source. Payments/Devices/Biomedical/Command
Center/Public Health CAS fixes each individually proved commit/rollback
correctness as part of their own real-Postgres proof. Not
independently re-verified as a standalone Phase-3-style trace in this
pass.

FULLY VERIFIED
---------------
Platform Authority certificates cluster (8 routes, 64 tests, re-run
green this pass) + the 6 CAS-fixed domains' specific fixed routes (6
routes) = 14 routes with the complete FIND→TRACE→PROVE→FIX→NEGATIVE
PROOF→REGRESSION lifecycle demonstrably closed.

PARTIALLY VERIFIED
------------------
~358 (everything else counted above — real evidence exists, from this
session or a prior one, but was not independently re-proven inside
*this specific bounded pass*)

AUTHORIZATION GAP
-----------------
0 newly found this pass (this was a discovery pass; see
docs/security/AUTHORIZATION_GAP_REGISTER.md for the one item carried
forward from a prior pass — `adaptive-auth-account-id-idor`, still
NEEDS_DECISION, not newly discovered)

BLOCKED
-------
0 authorization findings blocked (the governance/national schema gaps
are BLOCKED for a different reason -- persistence, not authorization --
and are excluded from this count since there is no reachable route to
authorize)

UNKNOWN
-------
The remaining ~78 of the 89 mounted routers not named above (the
schema-latent 7, the `NO-OWNED-MODELS` ~11 packages, `national`'s 11
routers, `governance`'s 1 router, and every router this session has not
yet vertical-slice-audited) — their route-level authorization mechanism
was NOT traced in this pass. Recorded as UNKNOWN, not silently assumed
either safe or unsafe.
```

## Scope and honesty note

This matrix consolidates **real, already-gathered evidence** from this
session and re-confirms a subset of it (the certificates cluster, 64
tests, re-run green this pass; the platform-authority-grant-has-no-route
finding, independently re-derived this pass via grep). It is not a
fresh route-by-route trace of all 89 mounted routers — that would be a
multi-day undertaking on its own, explicitly out of scope for this
"discovery + proof only, minimum resources" bounded pass. The ~78
routers marked UNKNOWN above are the honest remainder.
