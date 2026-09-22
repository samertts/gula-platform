# GULA — Live Runtime Surface Map

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

### LIVE / PARTIAL — inconsistent, needs per-table triage

| Domain | Tables declared | Missing | Sample missing |
|---|---|---|---|
| `national` (11 routers: rules_engine, background_platform, workflow_runtime, task_engine, notification_platform, document_platform, scheduling_platform, search_platform, observability, ecosystem, ecosystem_gateway, intelligence) | 114 | **103** | `national_addresses`, `national_admissions`, `national_advance_directives` |
| `governance` (governance_router, analytics_router — **top-level `app/governance/`, NOT `app/identity/governance/`, which is separate and fully backed**) | 64 | **58** | `gov_ai_audit_events`, `gov_ai_guardrails`, `gov_healthcare_workers`, `gov_professional_licenses`, `gov_digital_certificates`, `gov_security_policies` |
| `nhdw` | 15 | 1 | `nhdw_offline_changes` (offline-sync only; the admission/discharge/transfer journey already audited this session is unaffected) |
| `nursing` | 15 | 2 | `nursing_checklists`, `nursing_escalations` (the task/assignment journey already audited this session is unaffected) |
| `radiology` | 18 | 1 | `radiology_ai_jobs` (the report/exam journey already audited this session is unaffected) |

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

### LIVE / NO-OWNED-MODELS — needs per-router confirmation before assuming broken

`ai_fabric`, `certification`, `chronic_care`, `citizen_platform`,
`clinical_gateway`, `contracts`, `control_plane`, `kernel`,
`notifications`, `platform`, and the generic `routes/` package (tiers,
citizen_portal, claims, ai, optimizer, stats, canonical_patient, consent,
user_preferences, mfa, password_reset, oauth2, saml, service_accounts,
integrations, advanced_integrations, edge, patient_card, care_continuum,
ai_telemetry, clinical*, hospital, national_data, national_streaming)
declare zero `__tablename__` of their own. This does **not** mean broken
— many of these are legitimately thin orchestration/read layers over
shared models (`app/models/`, `Patient`, `LabUser`, `CanonicalPatient`,
etc.) or genuinely stateless (e.g. `optimizer`, `stats` as read-only
aggregation). Each one needs an individual "what does this router actually
persist, and where" check before it can be called LIVE or LATENT with
confidence — not attempted in this pass; flagged here as the honest
`UNKNOWN` bucket rather than silently assumed either way.

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
