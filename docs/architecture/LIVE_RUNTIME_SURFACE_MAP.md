# GULA — Live Runtime Surface Map

**Correction (Authorization Coverage Batch 5)**: this document's
original "88 `app.include_router(...)` calls" count (and every later
batch's restatement of it as 89 after a routers-added recount) was
produced by a textual line-count of `app.include_router(` in
`app/factory.py`. That undercounts: one line
(`app/factory.py:578-579`, `for r in core_routes + feature_routes +
advanced_routes + admin_routes + mobile_routes + compliance_routes:
app.include_router(r.router)`) registers **29 routers** in a single
loop iteration, which a textual count only counts as 1. **The true
mounted-router count is 117** (89 − 1 + 29), confirmed by reading the
six list literals it iterates over directly. This is a
counting-methodology correction, not new mounting activity — see
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`'s Batch 5 section for
the full list of the 29 loop-registered routers and which of them were
already implicitly covered (`labs`/`samples`/`results`, under this
document's existing "Laboratory" references) versus genuinely
newly-surfaced UNKOWN routers (25 of them — `login, register,
verification, demo, setup, metrics, patients, test_results, dashboard,
app_updates, qr, id_scan, identity, notifications, ehr, ehr_fhir,
cds_hooks, security, device_results, quality_control, critical_alerts,
batch, admin_log_level, mobile, compliance`). The domain classifications
below (LIVE/SCHEMA-LATENT/NO-OWNED-MODELS/etc.) for the routers this
document already named remain valid; they simply were not the complete
set.

**Method**: ground truth, not directory-name inference. Every router
actually registered in `backend/app/factory.py::_register_routes` (88
`app.include_router(...)` calls, enumerated by parsing the file directly)
is cross-referenced against every `__tablename__` declared under that
router's owning package, checked for exact-string presence in
`backend/migrations/versions/*.py`.

**Important correction to earlier this-session discovery notes**: several
prior findings in `MUSTAFA_ACTIVE_REPAIR_QUEUE.md` (`ems-domain-discovery`)
classified `insurance`, `citizen_platform`, `document_intelligence`,
`knowledge_graph`, `health_data`, `research_platform` as "LATENT" based on
migration-table absence alone. That was a **route-reachability error**:
all of these domains' routers ARE mounted unconditionally in
`app/factory.py` — they are reachable today over HTTP. What was actually
true is narrower and worse: the route is live but its backing table does
not exist, so any real mutation 500s with `UndefinedTable`. This map
introduces the distinct **LIVE / SCHEMA-LATENT** category for exactly this
shape, and restates those findings under it.

**Known separate blocker**: a genuine blank-database `alembic upgrade
head` currently halts partway through the chain at
`20260820_0004_surgical_safety_checklists.py` (the pre-existing, already
BLOCKED `nhdw-hospital-structure-migration-gap` finding — unrelated to
this pass, requires human-approved migration). That means even the
TABLE-BACKED domains below are not provably reachable via a single clean
sequential replay *today*; this map's TABLE-BACKED classification means
"a `CREATE TABLE` for every declared model exists somewhere in the
migration set," not "a fresh deploy succeeds end-to-end" — those are
different claims and this map does not conflate them.

## Classification legend

| Class | Meaning |
|---|---|
| **LIVE** | Router mounted unconditionally + every declared table has a migration |
| **LIVE / PARTIAL** | Router mounted + some but not all declared tables have a migration (inconsistent — some endpoints work, others 500) |
| **LIVE / SCHEMA-LATENT** | Router mounted + **zero** declared tables have a migration (every mutating endpoint will 500) |
| **LIVE / NO-OWNED-MODELS** | Router mounted, package declares no `__tablename__` of its own — reads/writes via another domain's models (needs per-router confirmation, not assumed broken) |
| **FLAG-GATED** | Mounted only when an env-var feature flag is on |

## Domain classification (from the 88 registered routers)

### LIVE — table-backed, no gap found

`billing` (5), `biomedical` (12), `blood_bank` (17), `capabilities/fhir_interoperability` (1),
`command_center` (4), `critical_care` (13), `devices` (10), `ems` (12),
`identity`/NIAM (89), `lifecycle_platform` (5), `lims` (35), `payments` (28),
`pharmacy` (27), `pilot_platform` (5), `public_health` (6), `services/mpi` (3),
`trust` (6).

**Authorization coverage note (Batch 5)**: `lims` and `pharmacy`'s
table-backed status was already correctly recorded here, but neither
had ever been individually vertical-slice-audited for authorization
until this pass. `lims_routes.router` is now VERIFIED (20 routes
traced, all tenant-scoped correctly); `pharmacy_router` is PARTIALLY
VERIFIED (2 of its routes traced). Both also had real, live
data-correctness bugs found and fixed this pass (see
`docs/security/AUTHORIZATION_GAP_REGISTER.md` GAP-9) — the entire LIMS
listing/lookup/dashboard surface was silently non-functional until
fixed.

### LIVE / PARTIAL — inconsistent, needs per-table triage

| Domain | Tables declared | Missing | Sample missing |
|---|---|---|---|
| `national` (11 routers: rules_engine, background_platform, workflow_runtime, task_engine, notification_platform, document_platform, scheduling_platform, search_platform, observability, ecosystem, ecosystem_gateway, intelligence) | 114 | **103** | `national_addresses`, `national_admissions`, `national_advance_directives` |
| `governance` (governance_router, analytics_router — **top-level `app/governance/`, NOT `app/identity/governance/`, which is separate and fully backed**) | 64 | **58** | `gov_ai_audit_events`, `gov_ai_guardrails`, `gov_healthcare_workers`, `gov_professional_licenses`, `gov_digital_certificates`, `gov_security_policies` |
| `nhdw` | 15 | 1 | `nhdw_offline_changes` (offline-sync only; the admission/discharge/transfer journey already audited this session is unaffected) |
| `nursing` | 15 | 2 | `nursing_checklists`, `nursing_escalations` (the task/assignment journey already audited this session is unaffected) |
| `radiology` | 18 | 1 | `radiology_ai_jobs` (the report/exam journey already audited this session is unaffected) |
| `hospital` (Authorization Coverage Batch 4) | 14 | **13** | `hospitals`, `hospital_campuses`, `hospital_buildings`, `hospital_floors`, `hospital_departments`, `hospital_clinics`, `hospital_rooms`, `hospital_beds`, `hospital_units`, `hospital_operation_theaters`, `hospital_medical_equipment`, `hospital_cost_centers`, `bed_assignments` — the 14th, `hospital_surgical_safety_checklists`, nominally has a migration (`20260820_0004_surgical_safety_checklists.py`) but that migration is itself already-documented as blocked in the alembic chain (missing `hospital_operation_theaters` FK target), so in practice **0 of 14 are reachable on a clean sequential migration replay today** — closer in effect to the LIVE/SCHEMA-LATENT domains below than this table's other rows |

**`national` and `governance` are the two largest new findings of this
pass.** `national` alone backs 11 of the 88 registered routers (rules
engine, workflow runtime, task engine, notifications, documents,
scheduling, search, observability, ecosystem/gateway, intelligence) —
nearly all of it schema-latent. `governance` is a single router pair
(`/governance/*`) where 91% of its own declared tables have no migration
— clinical policy engines (`gov_clinical_policies`,
`gov_critical_result_policies`, `gov_delta_check_policies`,
`gov_repeat_testing_policies`, `gov_westgard_policies`), credentialing
(`gov_professional_licenses`, `gov_board_certifications`,
`gov_competency_assessments`), security/AI governance
(`gov_security_policies`, `gov_ai_guardrails`, `gov_ai_audit_events`,
`gov_llm_policies`, `gov_prompt_policies`), and national interop
(`gov_national_protocols`, `gov_national_tests`,
`gov_national_reference_labs`) are all reachable-but-non-persistable
today. This is **not the same package** as `app/identity/governance/`
(NIAM identity governance — authorities/councils/appeals/suspensions),
which this session's earlier batches 7a/7b/7c hardened and which IS fully
table-backed (verified directly: `gov_break_glass_accesses`,
`gov_guardians`, `gov_identity_records`, `gov_merge_proposals`,
`gov_qr_codes`, `gov_recovery_requests` — a different, small,
correctly-backed 6-table set under `app/identity/governance/` that
happens to share the `gov_` prefix). That prior work's "REAL POSTGRESQL
VERIFIED" claims are unaffected — re-confirmed by checking the actual
model classes the 7a/7b/7c batches touched, which are the identity
package's, not the top-level `app/governance/` package's.

### LIVE / SCHEMA-LATENT — every declared table is unbacked

| Domain | Router | Tables declared, 0 backed |
|---|---|---|
| `command_intelligence` | `command_intelligence_router` | 5 (`ai_recommendations`, `capacity_intelligence`, `incident_intelligence`, ...) |
| `document_intelligence` | `doc_intel_router` | 21 (`docint_documents`, `docint_annotations`, `docint_classifications`, `docint_entities`, `docint_access_control`, ...) |
| `health_data` | `health_data_router` | 17 (`hd_mdm_patient_index`, `hd_mdm_organization_index`, `hd_mdm_facility_index`, `hd_mdm_provider_index`, ...) |
| `knowledge_graph` | `knowledge_graph_router` | 3 (`knowledge_nodes`, `knowledge_edges`, `knowledge_graph_snapshots`) |
| `research_platform` | `research_platform_router` | 7 (`rp_research_projects`, `rp_research_datasets`, `rp_consent_records`, `rp_data_access_requests`, `rp_research_institutions`) |
| `roadmap` | `roadmap_router` | 8 (`roadmap_epics`, `roadmap_milestones`, `roadmap_architecture_decisions`, ...) |
| `simulation` | `simulation_router` | 5 (`digital_twins`, `capacity_plans`, `predictions`, ...) |

Every mutating endpoint in these 7 routers will raise `UndefinedTable` on
any real deployment. This is a production-readiness/availability finding,
not a security defect — there is nothing to exploit in a table that
cannot be written to — but it means these 7 domains are **not currently
eligible for the concurrency/authorization vertical-slice audit method**
this session has used elsewhere (that method assumes real persistence to
race against). They are excluded from the "next vertical slice"
candidate pool until/unless a human-approved migration lands for them.

### Correction — `capabilities` is not one domain, it's 10 routers, 9 of them DEAD

The original pass above counted `capabilities` as a single TABLE-BACKED
domain (1 table, `fhir_resource_records`, via the one router this repo
actually mounts — `fhir_interoperability`). That undercounted it: `app/capabilities/`
contains **10 independent sub-packages**, each with its own `routes.py`
and a `commands/` subpackage (46 command files total) —
`clinical_foundation`, `document_management`, `encounter_management`,
`fhir_interoperability`, `healthcare_consent`, `provider_management`,
`reporting_service`, `search_service`, `storage_service`,
`workflow_engine`. Grepped exhaustively (found while doing the
idempotency-mechanism inventory, `docs/security/IDEMPOTENCY_CLOSURE_STATUS.md`):
**only `fhir_interoperability`'s router is ever imported by
`app/factory.py`**; the other 9 routers have zero references anywhere in
the codebase. Reclassified: **DEAD** (9 of 10 sub-packages) — not
"needs per-router confirmation," confirmed unreachable.

### LIVE / NO-OWNED-MODELS — needs per-router confirmation before assuming broken

`ai_fabric`, `certification`, `chronic_care`, `citizen_platform`,
`clinical_gateway`, `contracts`, `control_plane`, `kernel`,
`notifications`, `platform`, and the generic `routes/` package (tiers,
citizen_portal, claims, ai, optimizer, stats, user_preferences,
integrations, advanced_integrations, edge, care_continuum,
ai_telemetry, clinical*, national_data, national_streaming) declare
zero `__tablename__` of their own. This
does **not** mean broken — many of these are legitimately thin
orchestration/read layers over shared models (`app/models/`,
`Patient`, `LabUser`, `CanonicalPatient`, etc.) or genuinely stateless
(e.g. `optimizer`, `stats` as read-only aggregation). Each one needs an
individual "what does this router actually persist, and where" check
before it can be called LIVE or LATENT with confidence — not yet
attempted for the routers still listed here; flagged as the honest
`UNKNOWN` bucket rather than silently assumed either way.

**Resolved in Authorization Coverage Batch 3** — confirmed LIVE, real
persistence via shared models, authorization traced and VERIFIED:
`canonical_patient` (writes `CanonicalPatient` via
`app/services/mpi/canonical_service.py`), `consent` (writes via
`app/services/consent_service.py`), `mfa` (writes `MFADevice` via
`app/security/mfa_service.py`), `service_accounts` (writes
`ServiceAccount` via `app/security/service_accounts.py`),
`patient_card` (reads/audits against `Patient`/`AuditLog`; issues
HMAC tokens, does not own a table itself).

**Resolved in Authorization Coverage Batch 4** — confirmed LIVE, real
persistence, authorization traced:
- `password_reset` (writes `LabUser.reset_token`/`password_hash`
  fields directly — no table of its own) — VERIFIED, no gap.
- `oauth2` (writes `OAuth2Client`/`OAuth2Token`, both real tables —
  `oauth2_clients`/`oauth2_tokens`) — 1 P1 authorization gap found and
  closed (`oauth2-register-no-role-check`; see gap register GAP-8).
- `saml` (reads/validates only; the `db` dependency is declared but
  unused — the route issues no session/token and writes nothing) —
  VERIFIED not exploitable, but reclassified as **functionally
  incomplete**, not a full SSO login flow.
- **`hospital`** — this domain was previously miscategorized twice:
  the `ems-domain-discovery` finding (an earlier pass) called it fully
  LATENT/disqualified on persistence grounds, while a later pass
  (`log-action-arg-order-hospital-service`) proceeded to fix and test
  parts of it anyway via the SQLite test harness. Batch 4 resolves the
  contradiction with hard evidence: **13 of `hospital`'s 14 tables have
  zero Alembic migration** (`hospitals`, `hospital_campuses`,
  `hospital_buildings`, `hospital_floors`, `hospital_departments`,
  `hospital_clinics`, `hospital_rooms`, `hospital_beds`,
  `hospital_units`, `hospital_operation_theaters`,
  `hospital_medical_equipment`, `hospital_cost_centers`,
  `bed_assignments`), and the 14th
  (`hospital_surgical_safety_checklists`) has a migration that is
  itself already-documented as blocked in the alembic chain (missing
  `hospital_operation_theaters` FK target,
  `20260820_0004_surgical_safety_checklists.py`). **Correct
  classification: LIVE / SCHEMA-BLOCKED** — every one of `hospital`'s
  23 mutating routes will 500 with `UndefinedTable` on a real,
  migration-driven Postgres deployment today, identical in kind to the
  7 already-documented schema-latent domains above (not a security
  defect — nothing is exploitable against a table that cannot be
  written to). It remains fully code-reachable and testable via this
  repo's own SQLite test harness (`HospitalBase.metadata` is created
  via `metadata.create_all()` in `conftest.py`, independent of
  Alembic) — the same harness the pre-existing Hospital tests already
  use, and the one Batch 4 used to find and close 3 real P1s (an
  authorization gap on 19 routes, a data-integrity bug in a shared
  entity-lookup helper, and a transaction-integrity bug where 18
  routes never committed their writes). See
  `docs/security/AUTHORIZATION_GAP_REGISTER.md` GAP-5/6/7 for full
  evidence. **Excluded from the "next vertical slice" candidate pool**
  going forward, matching this map's own stated policy for
  schema-latent domains, until a human-approved migration lands.

See `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md` and
`docs/security/AUTHORIZATION_GAP_REGISTER.md` for the full
route-level evidence on all of the above. Removed from this bucket's
"not yet confirmed" list above.

## What this map does NOT claim

- It does not claim CI-level verification (GitHub Actions remains blocked
  by an external account-level infra issue on this PR, documented
  separately, re-confirmed identically on every push this session).
- It does not claim the `national`/`governance` schema-latent findings
  are fixed — they require human-approved migrations (CLAUDE.md: "DB
  schema changes... require human approval") authored by whoever owns
  each domain's real table design, not invented here.
- It does not claim full route-by-route authorization/tenant-scope
  coverage — that is the separate `LIVE_MUTATION_SURFACE_REGISTRY.md`
  deliverable, not yet built (see scope note in
  `docs/security/FINAL_LIVE_SURFACE_SWEEP.md`).
