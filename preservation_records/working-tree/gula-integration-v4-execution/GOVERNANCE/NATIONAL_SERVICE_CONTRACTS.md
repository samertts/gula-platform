# NATIONAL SERVICE CONTRACTS — GULA multi-service integration contract baseline

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2827c1ff`
**Date:** 2026-11-17
**Companion document:** `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md`
**Status of `GOVERNANCE/FINAL_DECISION.md`:** **HOLD** (unchanged, and must stay HOLD)

> **Purpose.** This document is the mandatory compatibility contract that sits
> *between* the inventory and any service unification work. **No service may be
> unified, re-pointed, merged, or have its API re-shaped until its contract row
> in §6 is no longer `BLOCKED`.** Nothing in this document was produced by
> modifying, migrating, committing or deploying any service.

---

## 1. Scope, method and evidence

| # | Evidence | Artifact | Proves |
|---|---|---|---|
| E1 | Live `create_app()` → `app.openapi()` (exit 0) | `/tmp/opencode/remediation/openapi_20261117_084342.json` | 2116 operations / 1804 paths; 2060 with declared security, 56 without |
| E2 | OpenAPI prefix/tag analysis | `/tmp/opencode/remediation/openapi_analysis.txt` | per-service surface, public operation list |
| E3 | ORM vs migration coverage scan | `/tmp/opencode/remediation/coverage_by_context.json` | 833 ORM tables, 407 migrated (48.9 %), 426 unmigrated |
| E4 | Dependency-graph auth walk (2133 routes) | `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` §1–§5 | 2064 guarded / 69 unguarded, **69/69 public-by-design, 0 residual gaps**, R-01…R-11 open |
| E5 | Route/package registration audit | `backend/app/factory.py` (125 routers) + per-package `APIRouter` | which code is actually served |
| E6 | Event taxonomy scan | `/tmp/opencode/remediation/event_types.txt` | 121 distinct `event_type` values, 4 incompatible naming conventions |
| E7 | Error-contract source | `backend/app/core/error_contract.py:55`, `backend/app/factory.py:940-1090` | canonical error envelope + FHIR `OperationOutcome` |
| E8 | Idempotency source | `backend/app/core/idempotency.py` | `Idempotency-Key` semantics, 24 h TTL, per-lab scope |
| E9 | Rate-limit source | `backend/app/security/rate_limit.py` | fixed-window limiter, standard headers |
| E10 | Offline source | `backend/app/services/offline_sync_service.py`, `backend/app/integration/routes.py:249` | **in-memory only** offline engine |

**Reconciliation of the two "public" totals (do not conflate them):**

* **56** = OpenAPI operations with **no declared `security`** (`openapi_20261117_084342.json`).
* **69** = routes where a **dependency-graph walk** found no auth-shaped callable
  (includes non-OpenAPI routes such as probes). Authoritative classification, with
  per-endpoint handler/control/residual evidence, is `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md`
  — **69/69 public-by-design, 0 residual gaps**, residuals **R-01…R-11 open**.

Both are review triggers; neither is a confirmed vulnerability, and neither is closed here.

---

## 2. Contract vocabulary used below

| Term | Meaning |
|---|---|
| **Contract status** | `STABLE` = auth + typed schema + audit + tests + migrations; `DRAFT` = live but missing ≥1 of those; `BLOCKED` = a decision or schema gap prevents safe unification; `UNSERVED` = code exists but is not reachable in the running app |
| **Owned tables** | The table prefix(es) a service may write; no other service writes them (rule R-DB-1) |
| **Live ops** | Operations actually served, measured from E1 — not from source-file counting |
| **Typed** | `response_model=` / declared return schema in OpenAPI |
| **Audit** | Immutable audit-log writes (`log_action` / `AuditLog`), **not** `created_by`/`updated_by` columns |
| **Tenant** | Scoping key (`lab_id`, `organization_id`) enforced per request |

---

## 3. Cross-cutting contract primitives (all services MUST obey)

### 3.1 Authentication — **stable**

* Scheme: **HTTP bearer** (`components.securitySchemes.HTTPBearer`), 2060 / 2116 operations.
* `security` is not global; each router/dependency declares it. Absence of a
  `security` block does **not** by itself mean unauthenticated (see §3.2, router-level gates).
* Authentication ≠ authorization. Both are required for every clinical write.

### 3.2 Authorization — **UNSTABLE (inconsistent granularity)**

| Mechanism | Location | Uses | Contract meaning |
|---|---|---:|---|
| `get_current_user` | `security/dependencies.py` | **1 294** | authentication only — **no authorization** |
| `require_permission("<perm>")` | `security/dependencies.py:159` | **297** | role → permission map (O(1), `rbac.ROLE_PERMISSIONS`) |
| `require_role(...)` | `security/dependencies.py` | 39 | role gate |
| `require_admin` | `security/dependencies.py` | 16 | admin only |
| `require_institutional_permission("<perm>")` | `security/dependencies.py:143` | 14 | institutional account + lab permission |

Permission strings actually enforced (top of the distribution):

| Permission | Uses | Note |
|---|---:|---|
| `system:admin` | **91** | coarse superuser; gate for whole routers (below) |
| `patients:read` / `patients:write` | 21 / 20 | patient data |
| `dashboard:read` | 12 | |
| `payments:*` (7 distinct) | 36 | financial |
| `results:read` / `results:write` | 4 / 1 | laboratory |
| `lab:read` / `lab:manage` (institutional) | 6 / 6 | |
| `audit:read` | 6 | |

**Contract rule R-AUTH-1:** a clinical write endpoint must carry an explicit
permission (`require_permission` / `require_institutional_permission`), not only
`get_current_user`. Current compliance by service is in §6 — **only 5 of 18
services comply**.

**Router-level `system:admin` gates (over-restrictive for clinical use):**

| Router | Gate | Consequence |
|---|---|---|
| `/public-health` (§`public_health/api/routes.py:26`) | `require_permission("system:admin")` | surveillance cannot be operated by clinicians or epidemiologists |
| `/blood-bank` (`blood_bank/api/routes.py:39`) | `system:admin` | transfusion workflow is admin-only |
| `/biomedical` (`biomedical/api/routes.py:19`) | `system:admin` | equipment maintenance is admin-only |
| `/integration` (`integration/routes.py:22`) | `system:admin` | includes the only offline-sync trigger |

This is an **authorization design defect (too coarse), not a missing guard** — the
guards exist but make national services unusable by their intended clinical roles.
Any re-permissioning is a contract change and requires the owning decision (ADR-D).

### 3.3 Error contract — **stable and canonical**

Non-FHIR responses use `build_error_payload` (`core/error_contract.py:55`):

```json
{
  "code": "<derived-from-status|explicit>",
  "message": "<client-safe message>",
  "details": {},
  "request_id": "<request id or 'unknown'>",
  "timestamp": "<ISO-8601 UTC>",
  "detail": "<legacy-compat: same as message>",
  "detail_ar": "<Arabic message>"
}
```

* `details` is sanitised (validation locations, error types) — **never submitted values**.
* 5xx responses never expose exception text; production logs hold the detail.
* Unready-state production requests return **503** with `details.service_state = "not_ready"`.
* Requests identified as FHIR (see `_is_fhir_request`) return FHIR R4
  `OperationOutcome` with `media_type="application/fhir+json"`
  (`severity` = `fatal` for 5xx, `error` otherwise).
* Registered handlers: `DomainError`, `StarletteHTTPException`,
  `RequestValidationError`, `Exception` (`factory.py:1147-1150`).

**Contract rule R-ERR-1:** new services must raise `DomainError` (mapped to the
canonical envelope) or `HTTPException` (normalised by `public_http_detail`).
Returning ad-hoc `{"error": ...}` bodies violates the contract.

### 3.4 Pagination — **DRAFT (unstandardised)**

| Param | Endpoints |
|---|---:|
| `skip` | 84 |
| `limit` | 97 |
| `page` | 2 |
| `offset` | 2 |

`class PaginatedResponse` exists but is not universally used. **Contract rule
R-PAGE-1:** list endpoints must use `skip`/`limit` with a declared maximum; `page`
must not be introduced per-service without a versioned decision.

### 3.5 Idempotency — **stable where used, not enforced globally**

* Header: `Idempotency-Key` (`core/idempotency.py`).
* Storage: `idempotency_keys` table; replayed response returned; **24 h TTL**;
  **keys scoped per lab** to prevent cross-tenant replay.
* Documented usage: `POST /api/orders`, `POST /api/results`,
  `POST /api/results/{id}/validate`, `POST /api/samples`.
* 335 `idempotency_key` references across the codebase (claims, orders, results,
  batch, integrations, edge, citizen-relationship admin).

**Contract rule R-IDEM-1:** every state-changing clinical operation that can be
retried by a device/offline client must accept `Idempotency-Key`. Currently only a
subset do; device/offline retries against `care_continuum`, blood bank and
hospital writes are **not** idempotent.

### 3.6 Rate limiting — **stable**

`GlobalRateLimitMiddleware` (`factory.py:429-443`) + `security/rate_limit.py`:

* Redis-shared across workers when available, in-memory fallback in development.
* Fixed-window algorithm; standard headers
  `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`,
  `Retry-After` on 429.
* Per-tenant/IP key hashing; partner limits exist separately.
* Residual **R-11** (metrics open when `APP_ENV` is misconfigured) stays open.

### 3.7 Versioning — **DRAFT / effectively absent**

* Only 5 routers are versioned (`/api/v1/canonical-patients`, `/api/v1/governance`,
  `/api/v1/trust`, `/api/v1/telegram`, `/api/v1/clinical`).
* The other 2111 operations are unversioned top-level prefixes (`/lims`, `/ems`, …).
* OpenAPI `info.version = "2.5.0"`; there is no per-service version and no
  deprecation policy expressed in the schema.

**Contract rule R-VER-1:** unification must not rename existing paths. Any new
service surface is additive. A breaking re-shape requires an ADR + a versioned
alias, because 2111 unversioned operations cannot be migrated atomically.

### 3.8 Tenancy — **UNSTABLE**

* `TenantMixin` declared in `backend/app/models/base.py` and reused by
  `national/base.py`, `care_continuum/base.py`, `nursing/base.py`, `pharmacy/base.py`,
  `hospital/base.py`, `health_data/base.py`, `nhdw/base.py`, `clinical/research/models.py`.
* Route-level scoping is done ad hoc via `user.lab_id` (e.g.
  `routes/care_continuum.py:99-100` `_lab_id()`).
* Not every service scopes reads/writes by tenant; `hospital`, `devices` and
  parts of `insurance`/`billing` rely on role gates instead.

**Contract rule R-TEN-1:** a service may only read/write rows for the caller's
tenant (`lab_id` or `organization_id`). Cross-tenant reads require an explicit,
audited capability — never a default.

### 3.9 Events — **DRAFT (four incompatible naming conventions)**

* Transport: transactional **outbox** (`models/outbox.py`: `event_type`,
  `aggregate_type`, `aggregate_id`, `payload`, `status`, `attempts`, `last_error`,
  `created_at`, `processed_at`; `MAX_ATTEMPTS = 5`) + kernel event bus
  (`kernel/event_bus/`: `bus`, `dispatcher`, `inbox`, `outbox`, `retry_queue`,
  `dead_letter_queue`, `replay`, `recovery`, `snapshot`, `versioning`).
* Delivery semantics: **at-least-once**; consumers must be idempotent.
* 121 distinct `event_type` values exist, in four conventions:

| Convention | Example | Where |
|---|---|---|
| `namespace.entity.action` (lowercase dotted) | `lims.order.validated`, `ems.incident.created`, `public_health.outbreak.raised`, `bloodbank.component.prepared`, `biomedical.calibration.performed` | the 5 services with `domain/events.py` |
| bare `entity.action` | `order.validated`, `encounter.recorded`, `observation.recorded`, `create` | misc services |
| `UPPER_SNAKE` | `SECURITY_INCIDENT_CREATED`, `CONSENT_GRANTED`, `ADMIN_FACILITY_CREATED` | identity/security/governance |
| unnamespaced verb | `delivered`, `retried`, `quarantined`, `pinned`, `returned` | device/edge flows |

* Domain-event modules exist for: `lims` (46 classes), `ems` (12), `blood_bank` (10),
  `critical_care` (10), `biomedical` (10), `public_health` (7).
  **No domain events** for: `hospital`, `nursing`, `care_continuum`, `pharmacy`,
  `radiology`, `chronic_care`, `insurance`, `billing`, `devices`.
* `NationalDomainEvent` (`national/events/base.py:11`) carries
  `event_type, aggregate_id, aggregate_type, payload, timestamp, request_id,
  user_id, lab_id, org_id, correlation_id, causation_id, version`.

**Contract rule R-EVT-1 (proposed, needs approval):** one canonical event envelope
(`NationalDomainEvent`) and one naming convention (`<service>.<entity>.<action>`,
lowercase dotted, `version` incremented on breaking payload change). Existing
`UPPER_SNAKE` values are **not** renamed here — that is an ADR-level migration.

**Cross-service events that must exist for the patient journeys in §7:**

| Event | Producer | Consumers |
|---|---|---|
| `lims.specimen.collected`, `lims.result.critical`, `lims.report.finalized` | Laboratory | Care continuum, Hospital, Public health |
| `pharmacy.dispense.completed` | Pharmacy | Care continuum, Billing/insurance |
| `radiology.critical_finding.raised` | Radiology | Hospital, Care continuum |
| `ems.incident.created`, `ems.triage.performed` | EMS | Hospital (pre-arrival), Public health |
| `bloodbank.component.issued` | Blood bank | Hospital (transfusion) |
| `public_health.disease_case.reported`, `public_health.outbreak.raised` | Public health | National surveillance |
| `care_continuum.referral.accepted` | Care continuum | Hospital, Laboratory |
| `insurance.claim.adjudicated` | Insurance | Billing |

Rows marked **MISSING** in §6 are events with no producer today
(`pharmacy.*`, `radiology.*`, `care_continuum.*`, `insurance.*`, `hospital.*`).

### 3.10 Audit — **UNSTABLE (7 services have no immutable audit writes)**

* Immutable audit log: `backend/app/audit/audit_log.py` + `services/audit_service.py::log_action`.
* `created_by` / `updated_by` (AuditMixin) are **not** an immutable audit log and do
  not satisfy the constitutional requirement.
* Services with **0** immutable audit writes: `care_continuum`, `hospital`,
  `critical_care`, `blood_bank`, `biomedical`, `chronic_care`, `public_health`.

**Contract rule R-AUD-1:** every clinical state change must emit an immutable audit
event with actor, tenant, subject, action, before/after digest and request id.
`care_continuum` (74 clinical endpoints) is the largest violation.

### 3.11 Offline behaviour — **NOT SATISFIED (constitutional gap)**

* `OfflineSyncEngine` (`services/offline_sync_service.py`) implements vector clocks,
  conflict detection/resolution, HMAC-signed operations, and an encrypted store —
  **but all state lives in Python `dict`/`list` objects** (`_operations`, `_conflicts`,
  `_vector_clocks`, `_sync_log`). It is not durable, not shared across workers, and
  is lost on restart.
* Only HTTP surface: `POST /integration/offline/sync` — and the whole
  `/integration` router is gated `system:admin` (`integration/routes.py:22`).
* `GET /auth/mobile/app-info` still returns `"offline_mode": False` ("Coming soon").
* `/edge/*` manages *device* offline queue depth (`offline_queue_max`) but is an
  edge-agent control plane, not clinical offline capture.

**Contract rule R-OFF-1:** offline-first capture cannot be claimed for any service
until offline operations are persisted (durable queue) and reconciled through the
outbox. This blocks the "offline-first" national requirement for **all 18 services**.

### 3.12 FHIR — **stable where exposed**

* `/fhir` (28 ops) + `national/fhir/*` mappers (e.g. `FHIRImmunizationMapper`).
* Errors on FHIR routes use `OperationOutcome` (`factory.py:940-954`).
* FHIR mappers are not exercised by dedicated integration tests for
  immunization/public health (see §6 rows 08/09).

---

## 4. Database ownership boundaries

**Rule R-DB-1 — single writer.** Each table has exactly one owning service.
Cross-service reads go through the API or the event bus; **never** a direct write.

| Service | Owned table prefix | Tables | Migrated | Owner status |
|---|---|---:|---:|---|
| Laboratory | `lims_*` | 35 | 35 | ✅ clear |
| Pharmacy | `pharmacy_*` | 27 | 27 | ✅ clear |
| Radiology | `radiology_*` | 18 | 17 | ✅ clear (1 unmigrated) |
| Emergency | `ems_*` | 12 | 12 | ✅ clear |
| Blood bank | `blood_bank_*` | 17 | 17 | ✅ clear |
| Public health | `ph_*` | 6 | 6 | ✅ clear |
| Hospital | `hospital_*`, `hospitals`, `bed_assignments` | 14 | 1 | ⚠️ 12 uncovered |
| Nursing | `nursing_*` | 15 | 13 | ⚠️ 2 uncovered |
| Critical care | `critical_care_*` | 13 | 13 | ✅ |
| Care continuum | `cc_*` | 45 | **0** | ⛔ **BLOCKED** |
| EHR | `ehr_*` | 18 | **0** | ⛔ **BLOCKED** |
| Insurance | `ins_*` | 30 | **0** | ⛔ **BLOCKED** (also UNSERVED, §5) |
| Billing | `billing_*` | 5 | 5 | ✅ |
| Payments | `payments_*` | 28 | 28 | ✅ |
| Biomedical | `biomed_*` | 12 | 12 | ✅ |
| Devices | `device_*` | 10 | 10 | ✅ |
| National data | `dp_*` | 36 | **0** | ⛔ **BLOCKED** |
| Health data | `hd_*` | 17 | **0** | ⛔ **BLOCKED** |
| Document intelligence | — | 21 | **0** | ⛔ **BLOCKED** |
| National | mixed (106) | 106 | 8 | ⛔ **BLOCKED** |

**Ambiguous ownership (no rule may be applied until decided):**

| Table | Claimed by | Conflict |
|---|---|---|
| `national_facilities` | `app/models/clinical_scope.py` **and** `app/national/domain/facility.py` | two ORM definitions of one table |
| `insurance_coverages` | `billing_*` namespace **and** `ins_*` domain | dual ownership |
| `facilities` / `organizations` | national + identity + hospital | ownership unresolved (ADR-B) |
| `patients` | laboratory (`lab_patients`), MPI, EHR, national | canonical patient identity not enforced (ADR-B) |

**Rule R-DB-2 — no shared DB ownership.** A service may not create/alter another
service's tables in its own migration. Current violations to audit before Wave 5:
hospital-family, `insurance_coverages`, `facilities`.

---

## 5. Corrections to the inventory (evidence-based, not overwritten)

The inventory's §3/§16 recorded Insurance as **`PARTIAL`, 62 live ops**. That
figure conflated the *financial* surface (`/billing` 11, `/payments` 38, `/tiers` 4)
with insurance. Precise re-verification against E1 + E5:

| Claim | Evidence | Corrected finding |
|---|---|---|
| "Insurance = 62 live ops" | E1 tag census: `insurance` **1**, `claims` **4**; `/billing` 11, `/payments` 38, `/tiers` 4 belong to Billing/Payments/Subscriptions | **Insurance live ops = 5** (`GET /insurance/{id}`, and 4 under `/claims` from `routes/claims.py`) |
| Insurance API "exists but partial" | `backend/app/insurance/api/` defines **84 endpoints** across 8 modules — `claims` 14, `coverages` 8, `coverage_check` 6, `network` 10, `payments` 18, `policies` 9, `providers` 7, `referrals` 12 | **UNSERVED**: `backend/app/insurance/api/*` is **never imported** anywhere; `factory.py:541,605` registers `routes/insurance.py` (1 op), not the package |
| Insurance tests | 1 file | unchanged |
| Insurance tables | 30 `ins_*` | **0 migrated** (unchanged) |

**Consequence:** Insurance is **`UNSERVED / BLOCKED`**, not "partial": 84 coded
endpoints are dead surface, and there are **two parallel claims implementations**
(`routes/claims.py` → `services/claims_service.py`, live) and
(`insurance/api/claims.py` → `insurance/domain/services.py`, unserved).
This is a duplicate-functionality finding of release significance and is escalated
as **ADR-I**, not silently fixed.

No other inventory verdict changes. The hospital finding is **13 unmigrated of 14**, not 12:
the only migrated hospital table is `hospital_surgical_safety_checklists` (`20260820_0004`), and the
earlier "12 = 11 `hospital_*` + `hospitals`" **omitted `bed_assignments`**. `hospital_operation_theaters`
is **not** created by any migration — it is only the target of a conditional FK in `20260820_0004`
(so the earlier wording that treated it as present was wrong). Correction recorded additively in
`NATIONAL_SERVICE_INVENTORY.md` §15.3; it makes the blocker worse, not better.

---

## 6. Per-service contract rows (the unification gate)

Legend — **Contract** column: `STABLE` / `DRAFT` / `BLOCKED` / `UNSERVED`.
`Auth` = authentication only / **+authz** = explicit permission present.

| # | Service | Owned schema | Live API (prefix, ops) | Typed? | Auth | Audit | Events | Migrations | DB owner | Offline | Contract |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Laboratory | `lims_*` (35) | `/lims` 57, `/samples` 2, `/orders` 5, `/test-results` 6, `/qc` 3, `/labs` 3, `/test-profiles`, `/history`, `/patient-history`, `/batch` → **103** | **no** (0 `response_model`) | auth only on most (5 perm) | ✅ 9 | ✅ 46 classes | 35/35 | clear | ❌ | **DRAFT** — typed schemas missing; 6 public token/phone ops (E4 §4.5, R-09) |
| 02 | Hospital | `hospital_*` (14) | `/hospital` 25, `/nursing` 62, `/critical-care` 20 → **127** (attributed) | **no** | auth only | ❌ hospital, ❌ critical care, ✅ nursing 16 | ❌ hospital/nursing, ✅ critical care 10 | 1/14, 13/15, 13/13 | ⚠️ | ❌ | **BLOCKED** — 12 uncovered tables + no audit for hospital/critical-care |
| 03 | Primary care | `cc_*` (5) | `/care-continuum/*` 13 | **no** | auth + `lab_id` scoping (0 perm checks) | ❌ | ❌ | **0 %** | ⛔ | ❌ | **BLOCKED** — no migrations, no audit, no tests |
| 04 | Pharmacy | `pharmacy_*` (27) | `/pharmacy` 63 | partial (31 `response_model`) | auth only (0 perm) | ✅ 6 | ❌ | 27/27 | clear | ❌ | **DRAFT** — needs explicit authz + dispense events |
| 05 | Radiology | `radiology_*` (18) | `/radiology` 58 | **no** (0) | auth only | ✅ 4 | ❌ | 17/18 | clear | ❌ | **DRAFT** — 1 unmigrated table; critical-finding event missing |
| 06 | Emergency | `ems_*` (12) | `/ems` 26 | **no** (0) | auth + 2 perm | ✅ 2 | ✅ 12 classes | 12/12 | clear | ❌ | **DRAFT** — typed schemas + tests thin (2 files) |
| 07 | Blood bank | `blood_bank_*` (17) | `/blood-bank` 30 | **no** (0) | router `system:admin` | ❌ | ✅ 10 classes | 17/17 | clear | ❌ | **BLOCKED** — no immutable audit; admin-only gate |
| 08 | Immunization | `cc_*` + `ehr_immunizations` | `/care-continuum/vaccination|immunization|reminder|cold-chain|coordinate/ehr-immunization`, `/ehr/immunizations` → 13 | **no** | auth | ❌ | ✅ public_health class | **0 %** (cc, ehr) | ⛔ | ❌ | **BLOCKED** — schema + audit + tests missing |
| 09 | Public health | `ph_*` (6) + `nhdw` (15) | `/public-health` 14, `/nhdw` 51, `/intelligence` 28 → 110 | **no** | router `system:admin` | ❌ | ✅ 7 classes | 6/6, 14/15 | ~clear | ❌ | **DRAFT/BLOCKED** — admin-only gate; no audit; 2 test files |
| 10 | Dental | — | **0** | — | — | — | — | — | — | — | **NOT IMPLEMENTED** (enum signals only) |
| 11 | Maternal & child | `cc_*` (7) | `/care-continuum/pregnancy|antenatal|delivery|postnatal|growth|breastfeeding|child-development` → 9 | **no** | auth | ❌ | ❌ | **0 %** | ⛔ | ❌ | **BLOCKED** |
| 12 | Chronic disease | `cc_*` (5) + `/chronic-care` 7 | 15 | partial (5/7) | `require_institutional_permission("lab:read")` via `_read_actor` | ❌ | ❌ | **0 %** | ⛔ | ❌ | **BLOCKED** |
| 13 | Rehabilitation | — | **0** | — | — | — | — | — | — | — | **NOT IMPLEMENTED** |
| 14 | Mental health | — | **0** | — | — | — | — | — | — | — | **DATA/ANALYTICS ONLY** |
| 15 | Referral & continuity | `cc_*` (12) | 18 (referrals, journeys, follow-up, coordination, transitions, handovers) | **no** | auth | ❌ | ❌ | **0 %** | ⛔ | ❌ | **BLOCKED** — strongest candidate to unblock first |
| 16 | Insurance & claims | `ins_*` (30) + `billing_*`/`payments_*` | live insurance = **5**; billing 11, payments 38, tiers 4 | billing 13/13 ✅, claims 4/4 ✅, insurance package **unserved** | billing +authz | ✅ 59 (insurance code) | UPPER_SNAKE only | ins **0/30**; billing 5/5; payments 28/28 | ⚠️ `insurance_coverages` dual | ❌ | **UNSERVED / BLOCKED** (ADR-G, ADR-I) |
| 17 | Home healthcare | `cc_*` (2) | 4 (`home-care-plans`, `community-care-records`) | **no** | auth | ❌ | ❌ | **0 %** | ⛔ | ❌ | **BLOCKED** |
| 18 | Medical equipment | `biomed_*` (12) + `device_*` (10) | `/biomedical` 17, `/device-integration` 24 → 52 | devices 29/30 ✅, biomedical **no** | router `system:admin` (biomedical); institutional `lab:read` (devices) | ❌ | ✅ 10 (biomedical) | 12/12, 10/10 | clear | partial (edge queue only) | **DRAFT** — no audit for maintenance/calibration |

**Aggregate gate status:** **0 STABLE**, **5 DRAFT** (01, 04, 05, 06, 18),
**11 BLOCKED** (02, 03, 07, 08, 09, 11, 12, 15, 16, 17 + shared substrate),
**3 NOT IMPLEMENTED / ANALYTICS ONLY** (10, 13, 14).

---

## 7. Patient-centred integration contracts (the journeys to certify)

Each journey is a cross-service contract. It is **not** satisfied until every hop
has: authenticated + authorized caller, tenant scoping, typed payload, immutable
audit, and an idempotency key on writes.

### J1 — Primary care → Laboratory → Pharmacy → Follow-up
`POST /care-continuum/primary-care-encounters` → `POST /orders` → `POST /samples` →
`lims.result.critical` → `POST /pharmacy/dispense` → `POST /care-continuum/follow-up-plans`.
**Blockers:** `cc_*` unmigrated (0 %), no audit in care_continuum, no
`lims.result.*` → care-continuum consumer test, pharmacy write not authorized beyond authentication.

### J2 — Emergency → Hospital → Radiology → Laboratory → Discharge
`ems.incident.created` → `ems.triage.performed` → hospital admission →
`POST /radiology/exams` → `lims` results → discharge. **Blockers:** hospital schema
(12 uncovered), no hospital/critical-care audit, no `ems.*` → hospital consumer test.

### J3 — Maternal care → Laboratory → Pharmacy → Referral
pregnancy → antenatal → lab → pharmacy → referral accept. **Blockers:** `cc_maternal`
0 %, no audit, no events.

### J4 — Chronic disease → Primary care → Laboratory → Medication → Follow-up
**Blockers:** `cc_chronic_disease` 0 %, `/chronic-care` not audited, no
`disease-management` event.

### J5 — Immunization → Patient record → Public-health surveillance
`POST /care-continuum/vaccination-records` → `/ehr/immunizations` →
`public_health.vaccination.recorded` → surveillance. **Blockers:** `cc_*` + `ehr_*`
0 %, router admin-only, FHIR mapper untested end-to-end.

### J6 — Blood request → Compatibility → Hospital transfusion
`/blood-bank/crossmatch` → `bloodbank.component.issued` → hospital transfusion record.
**Blockers:** no immutable audit in blood bank (clinical-safety gap), admin-only gate,
no `bloodbank.*` → hospital consumer test.

### J7 — Referral → Receiving facility → Clinical feedback
`POST /care-continuum/referrals` → accept/reject → transitions-of-care → handover →
feedback. **Blockers:** 0 % migrations; this is the **first candidate** for
unblocking because the API already exists (18 ops) and no new clinical modelling is needed.

---

## 8. Compatibility rules for any service unification (binding)

| Rule | Requirement |
|---|---|
| **R-UNI-1** | This document must be accepted before the first unification change (satisfied by existence; acceptance is a Program Director act). |
| **R-UNI-2** | **OpenAPI before/after must be byte-identical** for every operation that already exists. Any delta must be additive and listed. |
| **R-UNI-3** | Error payloads must remain the canonical envelope (§3.3) — including legacy `detail`/`detail_ar`. |
| **R-UNI-4** | No table rename, no ownership transfer, no cross-service direct write (§4). |
| **R-UNI-5** | No test may be deleted, skipped, or weakened; unification must add contract tests per journey hop. |
| **R-UNI-6** | Unifying a service with 0 % migration coverage is **forbidden** until ADR-A is approved. |
| **R-UNI-7** | Any re-permissioning (e.g. replacing `system:admin` with clinical capabilities) is a contract change requiring ADR-D approval. |
| **R-UNI-8** | Every unification step is independently reversible with a single revert and must be recorded in the change manifest. |

---

## 9. Architecture decisions required before contract closure

| ADR | Decision | Blocks |
|---|---|---|
| **ADR-A** | Migration strategy for **426 unmigrated tables** (backfill vs accept-as-legacy vs retire) | 9 services + every journey (J1–J7) |
| **ADR-B** | Canonical ownership of `patients`, `facilities`, `organizations`, `national_facilities` (duplicate model) | J1–J7 identity, §4 ambiguity |
| **ADR-C** | `care_continuum` as one bounded context vs decomposition into 6 sub-services | rows 03/08/11/12/15/17, J1/J3/J4/J7 |
| **ADR-D** | Audit enforcement model (central interceptor vs per-service `log_action`) **and** the authorization model that replaces blanket `system:admin` | 7 services, all clinical writes, blood-bank safety |
| **ADR-E** | Public token/phone result access (`/r/{token}`, `/qr/{token}`, `/history/{phone}`) — retain/harden/retire | row 01, R-09 |
| **ADR-F** | Dual lab implementation consolidation (`lims/` vs `services/*_service.py`) | row 01, four-service contracts |
| **ADR-G** | Insurance schema provisioning (30 `ins_*`, 0 migrations) | row 16 |
| **ADR-H** | Shared Core boundary (must not become a service data store) | §4, all rows |
| **ADR-I** | **NEW** — the 84-endpoint `insurance/api/*` package is unserved: register it, or archive it and keep `routes/claims.py`? | row 16, duplicate claims |
| **ADR-J** | **NEW** — offline durability: persist `OfflineSyncEngine` state (DB/queue) or declare offline capture out of scope | all 18 rows, constitutional offline-first |

No item in this table may be resolved by implementation; each needs explicit approval.

---

## 10. What this document does **not** claim

* It does **not** certify any service as production-ready or clinically safe.
* It does **not** change `FINAL_DECISION.md` — that remains **HOLD**.
* It does **not** close R-01…R-11, MIG-EXISTING, the 426-table gap, or the four-service
  extraction criterion.
* It does **not** authorise unification: it defines the gate that unification must pass.
* Insurance figures in the inventory are corrected here **additively**; the inventory's
  original evidence path is preserved and no prior finding was deleted.

---

## 11. Phase 4 re-verification of J1–J7 (2026-11-17, additive — CC-006)

Reviewing the seven patient journeys in §7 against the Phase 3 engine evidence; **no contract rule,
journey status or blocker was changed, and no journey was marked testable or ready on the strength
of API/model existence.**

| Journey | §7 status / blockers retained | Phase 3 evidence cross-reference (isolated synthetic only) |
|---|---|---|
| J1 — Primary → Lab → Pharmacy → Follow-up | `cc_*` 0 % unmigrated, no audit in care_continuum, no coverage — **unchanged** | Workflow E-048/050 passed on SQLite harness only; strict P0 failures (F-003) and coverage holes (F-007) still open |
| J2 — Emergency → Hospital → Radiology → Lab → Discharge | hospital 13 uncovered tables (inventory §15.3), radiology 94.4 % — **unchanged** | FHIR/R4 E-047 passed; HL7 E-051 passed; not migration-schema or runtime evidence |
| J3 — Maternal → Lab → Pharmacy → Referral | `cc_*` 0 %, referral untested — **unchanged** | `test_citizen_relationship_workflow.py` 5 (E-048) does **not** close referral coverage (F-007) |
| J4 — Chronic → Primary → Lab → Medication → Follow-up | `cc_chronic_disease` 0 %, `/chronic-care` unaudited — **unchanged** | CDS synthetic tests passed (E-047) for `app/ai/healthcare_cds.py`; national CDS remains unverifiable (F-068, D-021 PENDING) |
| J5 — Immunization → Patient record → Surveillance | `cc_*` 0 %, 0 audit, 0 tests — **unchanged** | no new evidence; no verdict change |
| J6 — Blood request → Compatibility → Transfusion | no immutable audit, admin-only gate — **unchanged** | LIMS authorization 8 tests passed (E-046); blood-bank audit gap retained |
| J7 — Referral → Receiving facility → Feedback | referral coverage hole — **unchanged** | canonical workflow engine unit tests (E-048/050) do not prove referral feedback on migrated schema |

**Contract primitives (§3):** authentication stable, authorization/tenancy/audit/offline UNSTABLE or
NOT SATISFIED as recorded. Phase 3 confirms offline CRDT is first-wins (F-069) and the queue is
in-memory (F-028); R-OFF-1 remains unsatisfied. R-AUTH-1/R-ERR-1/R-IDEM-1 are not closed by test
passes. No approval (D-020/D-021/ADR-C…J) is inferred.

**Conclusion:** §1–§10 remain accurate and evidence-backed; this section is additive only.
`FINAL_DECISION.md` remains **HOLD**.
