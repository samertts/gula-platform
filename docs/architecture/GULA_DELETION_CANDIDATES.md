# GULA Reduction Map — Deletion / Retirement Candidates

**Batch:** BATCH-2.8 · **Head:** `ae3e1f56`
**Deletions executed in this batch: 0.** Every candidate is DEFER or RETIRE, for
reasons given per item. Nothing was deleted to demonstrate activity.

---

## 1. A methodology finding that changes the whole exercise

A naive "no inbound imports" scan reported **629** dead modules. It was wrong:
`app/blood_bank/api/routes.py` (21 live endpoints), `app/nursing/routes.py` and
`app/radiology/routes.py` were all in that list.

**Cause:** the scan did not resolve *relative* imports. `factory.py` registers
routers with `from .blood_bank.api.routes import router`, which an AST walk
records as `blood_bank.api.routes`, not `app.blood_bank.api.routes`. Resolving
relative imports against the containing package drops the count to **68**, and
all three known-live routers are then correctly recognised.

**Consequence: any reduction work on this repository that uses import-reachability
must resolve relative imports.** Deleting on the naive result would have removed
the Blood Bank API. This is exactly the spec's rule — *absence of imports is
evidence, not proof of deadness* — with a concrete demonstration.

Even at 68, zero inbound references is **not** proof: dynamic registration,
entry points, plugins and string-based dispatch all defeat it. The 68 are DEFER,
pending per-item evidence.

## 2. Candidates with proven evidence

These come from reachability analysis done across BATCH-2.5 to 2.8, not from the
import scan.

| Item | Type | Evidence | Class | Confidence |
|---|---|---|---|---|
| 6 Blood Bank transition keys — `crossmatch_requested`, `draft`, `issued_order`, `ordered_transfusion`, `received_sample`, `testing_crossmatch` | B (domain) | No code writes them **and** no transition can reach them — unreachable in both directions | **RETIRE** | HIGH |
| 5 Blood Bank service methods — `record_transfusion`, `start_transfusion`, `complete_transfusion`, `issue_units`, `perform_crossmatch` | B (domain) | Zero callers anywhere; each strictly weaker than an existing `*_safely` counterpart | **RETIRE** | HIGH |
| `app/national/task_engine/` (15 tables) | C (ORM) | No table physical, no reachable operation | **RETIRE** | HIGH |
| `app/national/domain/facility.py::Facility` | C (ORM) | 18 columns, zero physical backing, duplicate claim on a name `app.database.Base` owns physically | **RETIRE** (NR-006) | HIGH |
| `CitizenPlatformBase` registration in `env.py` | D (migration) | Registered for autogenerate, maps zero tables, no concrete model inherits it | **REMOVE_REGISTRATION** | HIGH |
| `app/insurance/` (13 tables) | B/C | None physical, no reachable operation, awaiting a product decision | **DEFER** | MEDIUM |
| 68 modules with zero resolved inbound references | A/B | Import evidence only | **DEFER** | LOW |

### Why nothing was deleted

The six transition keys are the only items with proof strong enough for DELETE.
They are classified RETIRE instead because removing them edits a **clinical**
state machine, and the NR-007 `(entity, state)` rewrite will rewrite that table
anyway. Deleting them now buys nothing and spends risk in a clinical path. The
five service methods are the same argument at a larger scale.

## 3. Duplicate ownership — §7

| Entity | Canonical owner | Secondary / projection | Legacy | Duplicate |
|---|---|---|---|---|
| Person | National (`national_citizens`) — unbuilt | — | — | — |
| Patient | **Core `patients`** | `national_patients` (PROJECTION) | — | — |
| Practitioner | **National `national_practitioners`** — unbuilt | — | `lab_orders.doctor_name` free text | `lab_users` is an *account*, not a duplicate |
| Organization | National — unbuilt | — | — | — |
| Facility (operational) | **Core `facilities`** | — | — | — |
| Facility (national resource) | **Core `national_facilities`** via `clinical_scope` | — | — | **`national.domain.facility.Facility`** |
| Visit / Encounter | **Core `visits`** | `national_encounters` (PROJECTION), `CanonicalEncounter` (impl) | 5 unconstrained string columns | — |
| Drug | Core `pharmacy_drug_catalog` | — | — | resolved in P0-2 |
| Identity / User | Core `lab_users` + NIAM | — | — | — |
| Clinical episode | **Core `visits`** | — | `lab_orders` as anchor | — |
| Orders / Results | Core `lab_orders` / `lab_results` | — | — | — |

**One duplicate transactional owner remains: `national_facilities`.** Everything
else is either canonical, an allowed projection, or unbuilt.

## 4. §8 — the named high-value candidates

**A. `national.domain.facility.Facility`** → **RETIRE**. `clinical_scope.NationalFacility`
matches migration `20260813_0004` exactly and owns the physical FK from
`clinical_ehr_facility_bindings`. Not merged; the two are separate resources.

**B. `clinical_encounters`** → **DO-NOT-CREATE / ARCHITECTURE-REJECTED.** `visits`
exists physically, `lab_orders.visit_id` already references it under an enforced
constraint, and migration `20260505_0003` states the visit-based architecture.
Creating it would be a fourth episode representation. No repository evidence
disproves this.

**C. Blood Bank legacy mutation paths** — `process_component` **ACTIVE** (routed,
`POST /components`); `record_transfusion`, `start_transfusion`,
`complete_transfusion` **UNREACHABLE → RETIRE_CANDIDATE** (zero callers).

**D. Synthetic state keys** — 7 LIVE, 6 DEAD/SYNTHETIC, 15 UNRESOLVED. Only the
6 are proven dead. The 15 stay **BLOCKED — CLINICAL OWNER REQUIRED**.

**E. Empty metadata bases** — one: `CitizenPlatformBase`. **REMOVE_REGISTRATION**,
not deletion; the abstract entities may still be the basis of a citizen platform.
No physical table is touched.

## 5. §10 — dormant and future domains

Classified without deleting any. Their **architecture and discovery tooling is
`PRESERVE_FOR_GLOBAL_VISION`** even where runtime is dormant.

| Area | Class |
|---|---|
| `citizen_platform` | **DORMANT** — base registered, zero models; portal routes exist |
| `national/*` (16 unreferenced modules) | **FUTURE** — the National Core is specified, unbuilt |
| `research_platform` | **FUTURE** |
| `insurance` | **DEFER** — product decision |
| `engineering/productivity` | **PRESERVE_FOR_GLOBAL_VISION** — tooling, not runtime |
| `knowledge_graph`, `certification` | **PRESERVE_FOR_GLOBAL_VISION** |
| `simulation`, `edge`, `digital twin` | **FUTURE** |

## 6. What must NOT be deleted

Nothing in `tools/gula_intel/`, `scripts/enterprise_readiness/`,
`docs/enterprise-readiness/`, `docs/architecture/` or any guard under
`backend/tests/` that pins a finding. These are the intelligence layer — see
`GULA_GLOBAL_VISION_INTELLIGENCE_INDEX.md`.

Nor any migration, any audit path, any authorization path, any identity model,
or any physical table.
