# NR-050 — `app/capabilities/` forensic discovery

**Evidence only.** Nothing in this batch was implemented, retired, renamed, moved
or deleted. The working tree carries documentation changes and nothing else.

Its purpose is to give the owner enough to choose between COMPLETE, RETIRE,
PRESERVE-AS-DISCOVERY and SPLIT, without that choice resting on an absence of
imports.

---

## 0. The headline, and a correction to my own earlier report

PROGRAM-EXT-001 recorded that *all ten* capability packages fail to import, 40 of
40 modules. **That was wrong in two ways** and is corrected here:

1. It was measured with a `sys.path` that did not include the repository root.
   The application, CI and pytest all run with it (`PYTHONPATH` in
   `iam-hardening.yml`, `conftest.py` line 38), and importability has to be
   measured in the environment the application actually runs in — the same
   lesson NR-044.3 learned with the `national/` repositories.
2. It sampled four module kinds per package rather than all 267 modules.

Measured correctly, in the real environment:

| | Packages | Modules |
| --- | --- | --- |
| Import cleanly today | **1** (`fhir_interoperability`) | **27 / 27** |
| Fail to import today | 9 | 0 / 240 |

And the reason the nine fail is **one character per package**.

---

## 1. Inventory

Ten packages, **267 Python modules, 4,832 lines**, in three structural tiers:

| Tier | Packages | Shape |
| --- | --- | --- |
| **1 — scaffold only** | `clinical_foundation`, `healthcare_consent`, `reporting_service`, `search_service`, `storage_service` | `capability.py`, `contract.py`, `routes.py`, `permissions.py`, `policies.py`, `health.py`, `commands/`, `queries/`, `events/`, `tests/` |
| **2 — scaffold + hexagonal layers** | `document_management`, `encounter_management`, `provider_management`, `workflow_engine` | tier 1 **plus** `domain/entities.py`, `domain/repository.py`, `application/service.py`, `infrastructure/repository.py`, `dto.py` |
| **3 — completed** | `fhir_interoperability` | tier 1 **plus** `models.py`, `schemas.py`, `service.py`, `hl7.py`, a migration, a physical table, registered routes |

Per package: 3–5 commands, 2–4 queries, 2–5 event classes, 2 test modules.

### References outside the tree

| Surface | Finding |
| --- | --- |
| **Backend registration** | `factory.py` imports **only** `fhir_interoperability`'s `models` and `routes`, by *relative* path. The other nine routers are never included. |
| **Kernel registry** | all ten are registered as `CapabilityDescriptor`s by `capabilities_registry_populator` and load at boot |
| **Frontend routes** | **nine live routes** in `frontend-v3/src/routes/index.tsx`, each behind a `RoleGuard` |
| **Frontend pages** | **nine pages** under `frontend-v3/src/pages/capabilities/`, each calling `api.get("/<capability>")` |
| **Frontend navigation** | all nine in `frontend-v3/src/permissions/index.ts` with Arabic labels, gated on `dashboard:read` |
| **Drift tooling** | all ten in `scripts/zero_drift_engine.py` with Arabic labels, icons and `section: clinical` |
| **Generator** | `app/engineering/generators/capability.py` — the tool that produced the tree; still live |
| **Technical-debt registry** | `docs/technical-debt/REGISTRY.md` — naming violations only (TD-3773+) |
| **Migrations** | none reference any of the nine; `20260815_0019_fhir_resource_registry.py` creates `fhir_resource_records` for the tenth |
| **CI** | no workflow references the tree |
| **Tests** | 20 test modules inside the tree; `pytest.ini` sets `testpaths = tests`, so **none is ever collected** |

---

## 2. Runtime status (two independent proofs each)

| Package | Class | Proof 1 | Proof 2 |
| --- | --- | --- | --- |
| `fhir_interoperability` | **C — registered and reachable** | 27/27 modules import in the app environment | `factory.py:144,656` registers its models and router; `fhir_resource_records` exists in the migrated database |
| `clinical_foundation` | **E — unimportable** | `ModuleNotFoundError: No module named 'clinical_foundation'` | its router is not included in `factory.py`; no migration references it |
| `healthcare_consent` | **E** | same | same |
| `reporting_service` | **E** | same | same |
| `search_service` | **E** | same | same |
| `storage_service` | **E** | same | same |
| `document_management` | **E + second defect** | same | plus `TypeError: non-default argument 'document_id' follows default argument 'id'` in 4 modules |
| `encounter_management` | **E + second defect** | same | same (`encounter_id`) |
| `provider_management` | **E + second defect** | same | same (`provider_id`) |
| `workflow_engine` | **E + second defect** | same | same (`workflow_id`) |

**No package is classified F (dead with proof).** Absence of imports was never
accepted as sufficient, and in this tree it would have been actively misleading:
nine of them have live frontend routes pointing at them.

### The three defect classes, isolated

Simulated **without touching the repository** by putting `app/capabilities` on
`sys.path`, which makes the bare package name resolve — exactly what the broken
`__init__` files ask for:

| Defect | Where | Blast radius | Cost to fix |
| --- | --- | --- | --- |
| **D1** — `from <package>.capability import …`, a bare top-level import | 9 × `__init__.py` | the whole package is unimportable | **one character each** (`.capability`) |
| **D2** — `from backend.app.kernel.integration import get_kernel` | 10 × `capability.py` | resolves only because the repo root is on `sys.path`; the same dual-root fragility NR-044.3 found in `national/` | one line each |
| **D3** — `id: str = field(default_factory=…)` declared before non-default fields | 4 × `domain/entities.py` | `TypeError` at class creation, cascading to `domain/repository`, `application/service`, `infrastructure/repository` | field reorder |

With D1 simulated away, **6 packages import completely** and the remaining four
fail only on D3.

---

## 3. Contract compliance (PROGRAM-EXT-001)

All ten are registered descriptors, and all ten fail the contract on the same
four fields: `capability_id`, `documentation`, `test_paths`, `module_path` —
identical to the other 42 grandfathered capabilities. None declares
`required_permissions`, `tenant_scope` (beyond the default), `audit`,
`feature_flag`, `configuration` or `fhir_mappings`.

Structural assessment per §3 of the task:

| Package | Assessment |
| --- | --- |
| `fhir_interoperability` | **conceptually valid and implemented** — the only one |
| `document_management`, `encounter_management`, `provider_management`, `workflow_engine` | **conceptually valid, unimplemented, duplicated elsewhere** — hexagonal layering present but every method is a stub |
| `clinical_foundation`, `healthcare_consent`, `reporting_service`, `search_service`, `storage_service` | **structurally incomplete** — routes return `{"items": [], "total": 0}`; no domain model at all |

Every non-FHIR route handler in the tree returns a hardcoded empty page. They are
shaped like an API and answer nothing.

---

## 4. Canonical-owner analysis (evidence only — nothing consolidated)

| Capability | Existing implementations elsewhere | Overlap |
| --- | --- | --- |
| `document_management` | `platform/documents.py`, `national/document_platform/application/service.py`, `document_intelligence/` (4 ABCs) | service + data model; **no migration owned by any of them** |
| `workflow_engine` | `platform/workflow.py`, `national/workflow_runtime/`, `identity/workflows/engine.py` | service + events; `national/workflow_runtime` owns real tables and is registered |
| `healthcare_consent` | `identity/services/consent_service_v2.py` (`NiamConsentService`), `trust/services.py`, `national/security/consent_enforcement.py` | service + authorization; **and the registry lists `consent_management` 2.1.0 alongside `healthcare_consent` 1.0.0 — the same duplication at descriptor level** |
| `search_service` | `platform/search.py` | service |
| `reporting_service` | `platform/export.py`, descriptors `pdf_reporting` and `analytics` | service |
| `storage_service` | **nothing usable** | — |
| `clinical_foundation` | `app/clinical/`, `app/ehr/`, `health_data/canonical/models.py` | data model |
| `encounter_management` | `health_data/{warehouse,ods,canonical}/models.py`, `national/api/commands/create_encounter.py`, `national/policies/encounter_policy.py` | data model + commands |
| `provider_management` | `identity/` (persons, assignments), `national_data/models/mdm/ProviderRegistry.py`, `identity/federation/models.py`, `insurance/api/providers.py` | data model |
| `fhir_interoperability` | `app/fhir/` (`_capabilities`, `_reference`, `_scorecard`, `_validation_report`), `app/interoperability/` | **not a runtime duplicate** — `app/fhir/` registers no routes; it is a reference and scorecard module |

Six of the ten collide with an NR-051 concept that has no canonical owner yet.

---

## 5. Runtime value vs discovery value

Scored separately, as required.

| Package | Runtime value | Discovery / intelligence value |
| --- | --- | --- |
| `fhir_interoperability` | **High** — live | **High** — the only worked example of a completed capability; `hl7.py` carries HL7v2↔FHIR mapping |
| `document_management` | Zero | **Medium-high** — a clean hexagonal template (domain / application / infrastructure / dto) that the platform has nowhere else |
| `encounter_management` | Zero | **Medium-high** — same, plus an encounter domain model that the national and health_data trees each re-invent |
| `provider_management` | Zero | **Medium-high** — same, and provider identity is scattered across five modules today |
| `workflow_engine` | Zero | **Medium-high** — same; three workflow implementations exist and none is canonical |
| `clinical_foundation` | Zero | **Medium** — its commands and queries (`add_allergy`, `add_diagnosis`, `record_vitals`, `get_clinical_history`) are a CQRS vocabulary for the clinical domain |
| `healthcare_consent` | Zero | **Medium** — consent as a first-class capability rather than a field on another model |
| `reporting_service`, `search_service`, `storage_service` | Zero | **Low** — generic names, no domain content, canonical owners already exist or the concept is trivial |

The four Tier-2 packages are the strongest discovery assets in the tree: they are
the **only** hexagonal domain/application/infrastructure examples in the
repository, and PROGRAM-EXT-001's extension template was written without them.

---

## 6. History

Two commits touch the tree, both on **15 August 2026**:

* **`d33021e3`** — "feat(devices): add tenant-scoped gateway outbox reliability".
  A large mixed commit that added **304 files** (264 of them Python) under `app/capabilities/`
  alongside unrelated device work. The tree was generated, committed in bulk,
  and never revisited.
* **`3b7c9b70`** (PR #209, same day) — "feat(fhir): add tenant-scoped FHIR R4
  resource registry". This **completed one capability**, and its very first
  change was:

  ```diff
  -from fhir_interoperability.capability import Fhir_interoperabilityCapability
  +from .capability import Fhir_interoperabilityCapability
  ```

That is the strongest single piece of evidence in this document. Completing a
capability starts by fixing D1 — someone already did it once, for one package,
and the pattern is recorded in the history.

Nothing has touched the other nine in the four weeks since.

---

## 7. Future GULA fit

| Package | Correct long-term class (conceptually — nothing moved) |
| --- | --- |
| `fhir_interoperability` | INTEGRATION |
| `document_management`, `search_service`, `storage_service`, `reporting_service`, `workflow_engine` | REUSABLE CAPABILITY |
| `clinical_foundation`, `encounter_management`, `provider_management` | DOMAIN (clinical) — not capabilities; they model clinical entities, not reusable services |
| `healthcare_consent` | CORE — consent is an identity/authorization concern, and `identity/` already owns three implementations |

Three of the ten are misclassified by their own location: a capability package
holding a clinical domain model is a category error, and it is part of why
`encounter_management` duplicates the national and health_data trees.

---

## 8. Decision matrix

| Capability | Runtime | Owner | Duplicate? | Data | API | Authz | Tenant | Tests | Docs | Discovery | GULA fit | Disposition | Confidence | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fhir_interoperability` | **C live** | platform | no | owns `fhir_resource_records` | registered | `get_current_user` | undeclared | uncollected | descriptor only | High | INTEGRATION | **KEEP** | High | §2, §6 |
| `document_management` | E+D3 | none | **yes ×3** | none | orphan route | stub | undeclared | uncollected | none | High | CAPABILITY | **PRESERVE-DISCOVERY** → COMPLETE or RETIRE after NR-051 | Medium | §2, §4, §5 |
| `encounter_management` | E+D3 | none | **yes ×3** | none | orphan route | stub | undeclared | uncollected | none | High | DOMAIN | **BLOCKED** — needs a domain decision | Medium | §4, §7 |
| `provider_management` | E+D3 | none | **yes ×4** | none | orphan route | stub | undeclared | uncollected | none | High | DOMAIN | **BLOCKED** — needs a domain decision | Medium | §4, §7 |
| `workflow_engine` | E+D3 | none | **yes ×3** | none | orphan route | stub | undeclared | uncollected | none | High | CAPABILITY | **BLOCKED** — NR-051 canonical owner first | High | §4 |
| `healthcare_consent` | E | none | **yes ×3 + descriptor twin** | none | orphan route | stub | undeclared | uncollected | none | Medium | CORE | **BLOCKED** — NR-051 canonical owner first | High | §4 |
| `clinical_foundation` | E | none | yes ×2 | none | orphan route | stub | undeclared | uncollected | none | Medium | DOMAIN | **BLOCKED** — needs a domain decision | Medium | §4, §7 |
| `search_service` | E | none | **yes** (`platform/search.py`) | none | orphan route | stub | undeclared | uncollected | none | Low | CAPABILITY | **CONSOLIDATE** into `platform/search.py` | High | §4 |
| `reporting_service` | E | none | **yes** (`platform/export.py`, 2 descriptors) | none | orphan route | stub | undeclared | uncollected | none | Low | CAPABILITY | **CONSOLIDATE** | Medium | §4 |
| `storage_service` | E | none | **no usable implementation exists** | none | orphan route | stub | undeclared | uncollected | none | Low | CAPABILITY | **COMPLETE or REPLACE** — this is a real gap | Medium | §4, NR-051 |

**No disposition here rests on absence of imports.** Every row cites either a
live frontend route, a canonical-owner collision, or a domain-model duplication.

---

## 9. The NR-050 questions, answered

**A. Can all ten be retired safely? No.** `fhir_interoperability` is live — model,
migration, physical table, registered routes, frontend page. Retiring the other
nine is *possible* but is not a backend-only change: it means also removing nine
frontend routes, nine pages, nine navigation entries and ten drift-engine
entries, or leaving navigable pages pointing at nothing.

**B. Can all ten be completed safely? Yes technically, no economically.** The
three defect classes are small and well understood, and PR #209 is the worked
precedent (~600 lines plus a migration for one capability). But six of the ten
collide with an NR-051 concept that has no canonical owner, so completing them
first would multiply the duplication this programme is trying to reduce.

**C. Should they be split? Yes — this is the recommendation.** Three groups:
- **runtime**: `fhir_interoperability` (keep), `storage_service` (a real gap);
- **discovery/intelligence**: the four Tier-2 hexagonal packages, preserved as
  the platform's only worked hexagonal template;
- **blocked on decisions**: the rest.

**D. Require a canonical-owner (NR-051) decision first:** `workflow_engine`,
`healthcare_consent`, `document_management`, `search_service`,
`reporting_service`.

**E. Require a product/domain decision:** `clinical_foundation`,
`encounter_management`, `provider_management` — whether clinical entities live in
`app/clinical`, `app/ehr`, `app/health_data` or `app/national`. That question is
larger than NR-050 and overlaps NR-022.

**F. Genuinely obsolete: none.** Not one package met the bar for F. The weakest
three (`search_service`, `reporting_service`, `storage_service`) are thin, but
two duplicate a canonical owner (so they are CONSOLIDATE, not obsolete) and the
third fills a gap nothing else fills.

---

## 10. Recommendation

**RECOMMENDED DECISION — SPLIT, and do the cheap safety work first.**

**DECISION BASIS.** The tree is not dead code and not a finished platform; it is
*one generator bug away from importable*, with one member already completed and
nine members already wired into a shipped UI. Retiring it would throw away the
only hexagonal template in the repository and require frontend surgery; completing
it wholesale would harden six duplications before their owners are decided.

**CONFIDENCE.** High on the facts (§1–§6, all measured). Medium on the
disposition, because six rows depend on decisions that are not mine.

**BLOCKERS.** NR-051's six canonical-owner decisions; the clinical-domain
location question in §9E.

**MINIMUM NEXT ACTION — two items, neither of which needs the NR-050 decision:**

1. **Fix the generator** (`app/engineering/generators/capability.py`). It still
   emits all three defects — the bare import at line 485, `backend.app` at
   lines 8/191/514, and the dataclass ordering in its entity template. Every
   capability generated from today is born broken. This is **NR-053**, and it is
   a genuine fix regardless of what happens to the ten.
2. **Decide what the nine orphan frontend routes should do** (**NR-054**). Nine
   navigable pages, gated only on `dashboard:read`, call backend endpoints that
   are not registered. Whatever NR-050 decides, that is a user-visible defect
   today.

Neither was performed here.
