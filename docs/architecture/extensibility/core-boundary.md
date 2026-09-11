# Core boundary

**PROGRAM-EXT-001, Phase 2.** Normative. Everything here was measured against
the repository, not designed on paper.

The purpose of a boundary is to make one question answerable before code is
written: *if I add this, what else has to change?* The answer should be "nothing
in Core".

## 1. The five classes

| Class | What it is | May depend on | May NOT depend on |
| --- | --- | --- | --- |
| **CORE** | The runtime every request passes through, and the contracts everything else is written against | CORE only | anything below it |
| **CAPABILITY** | A reusable, domain-neutral service (audit, notification, workflow, search, storage, document, consent) | CORE, other CAPABILITY | any DOMAIN |
| **DOMAIN** | A clinical or business area (pharmacy, nursing, blood bank, radiology, LIMS, EMS) | CORE, CAPABILITY, other DOMAIN's **published contract** | another DOMAIN's internals |
| **INTEGRATION** | Adapters to things outside GULA (FHIR, HL7, insurance, national ID, Cloudflare) | CORE, CAPABILITY, DOMAIN contracts | nothing outside may reach *in* except through CORE |
| **APPLICATION/UI** | Route modules, frontends, the public site | everything below | — |
| **EXPERIMENTAL** | Present, not load-bearing, not yet classified | anything | nothing may depend on it |

"Published contract" means: a CORE-registered event, a versioned API, or a
capability descriptor. It does not mean "a Python class that happens to be
importable".

## 2. The classification, as measured

**CORE** — `app/kernel/` (101 files), `app/database.py`, `app/config.py`,
`app/factory.py`, `app/main.py`, `app/core/` (46), `app/security/` (21),
`app/models/` (32), `app/audit/`, `app/identity/` (123).

Identity is CORE, not a domain, and that is a decision rather than an
observation: the Identity Platform is the single trusted identity provider for
the whole ecosystem, so no domain may implement its own authentication or
authorization. Everything else being able to depend on it is the point.

**CAPABILITY** — `app/platform/` (16 modules: audit, authorization, caching,
documents, export, i18n, identity, notifications, organization, search, sync,
validation, workflow), `app/integration/` (95) for the ESB/CDC machinery,
`app/reference/` (22).

**DOMAIN** — `app/pharmacy/`, `app/nursing/`, `app/blood_bank/`,
`app/radiology/`, `app/lims/`, `app/ems/`, `app/critical_care/`,
`app/public_health/`, `app/biomedical/`, `app/hospital/`, `app/clinical/`,
`app/ehr/`, `app/care_continuum/`, `app/national/` (363),
`app/national_data/` (50), `app/nhdw/`, `app/insurance/`, `app/payments/`,
`app/financial/`.

**INTEGRATION** — `app/gateways/`, `app/interoperability/`,
`app/integration/connectors/`, `app/edge/`, `services/device_bridge/`.

**APPLICATION/UI** — `app/routes/` (63), `app/clinical_gateway/`,
`frontend/`, `frontend-v2/`, `frontend-v3/`, `client/`.

**EXPERIMENTAL** — `app/capabilities/` (268 files, see §4),
`app/research_platform/`, `app/pilot_platform/`, `app/knowledge_graph/`,
`app/ai_fabric/`, `backend/services/`, `backend/core/`.

Nothing was moved to satisfy this table. Where code sits in the wrong class, it
is recorded below rather than relocated — a classification that required a
refactor to be true would be a wish, not a measurement.

## 3. What the boundary already holds, and where it leaks

Measured by AST import analysis, not asserted:
**25 imports reach from one domain into another domain's internals** —
`models/`, `domain/`, `application/`, `infrastructure/`, `repositories/`.

| From | Into | Count | Example |
| --- | --- | --- | --- |
| `national_data` | `national` | 10 | `app.national.domain.citizen` |
| `national` | `ehr` | 6 | `app.ehr.models.allergy` |
| `nursing` | `ehr` | 3 | `app.ehr.models.medication` |
| `national_data` | `ehr` | 3 | `app.ehr.models.attachment` |
| `payments` | `financial` | 2 | `app.financial.models` |
| `national` | `lims` | 1 | `app.lims.models` |

So the rule in §1 is **not** currently satisfied, and saying otherwise would
have been the easiest and least useful thing to write here. The guard is
therefore a *ledger*, in the shape NR-044 established: the six edges above are
recorded with their counts, and the guard fails when a **new** edge appears or
an existing one grows. A guard that failed on the first run would be switched
off within a week; one that freezes the debt and forces every addition through
review is one that survives.

Two readings of the same data are worth separating. `payments → financial` and
`national_data → national` look like a single bounded context split across two
packages — the fix there is probably to merge or to publish a contract, not to
add an adapter. `nursing → ehr.models.medication` is different: it is a domain
reading another domain's ORM rows directly, which is exactly what a published
contract exists to prevent. Neither is resolved here; both are named.

One CORE edge is deliberate and recorded so it reads as a decision rather than
drift: `app/identity/services/clinical_authorization_context_service.py` imports
`app.models.organization` and `app.services.clinical_scope_bridge_service`,
because NR-047 established that `organizations` is the referenced authority for
clinical organization identity.

## 4. `app/capabilities/` — present, and dead

Ten capability packages (268 files) exist under `app/capabilities/`:
`clinical_foundation`, `document_management`, `encounter_management`,
`fhir_interoperability`, `healthcare_consent`, `provider_management`,
`reporting_service`, `search_service`, `storage_service`, `workflow_engine`.

**None of them imports.** Every `__init__.py` uses a bare top-level import
(`from document_management.capability import ...`) that resolves against no
package, and every `capability.py` imports `from backend.app.kernel.integration`
— a root that does not exist on the application's path. All 40 modules
(`__init__`, `capability`, `contract`, `routes` × 10) raise
`ModuleNotFoundError`.

Their `execute()` bodies return `{"success": True}`. Four of their repositories
are also in the NR-044 unreachable-async ledger, so they would be unreachable
twice over.

Only one thing in this tree is wired into the application:
`app/factory.py` imports `capabilities.fhir_interoperability.models` and
`.routes` — by relative path, which resolves — so the FHIR capability's models
and routes are live while its `capability.py` manifest is not.

This is recorded as **NR-050**. It is not repaired here: PROGRAM-EXT-001 was
asked to establish a foundation, not to resurrect 268 files of generated
scaffolding, and the decision of whether these ten are worth completing or
should be retired is the user's. Until that decision, the guards treat the
registry — which does load — as the source of truth, and do not import this
tree.

## 5. Registries: how many, and which one is canonical

Sixty classes in `app/` are named `*Registry`. Most are domain data
registries (cancer, birth, death, device, terminology) and are not architecture.
Four are architectural, and that is three too many:

| Registry | Loads at boot? | Holds |
| --- | --- | --- |
| `kernel.runtime.capability_registry.CapabilityRegistry` | **yes**, via `kernel/runtime/bootloader.py` | 52 `CapabilityDescriptor`s |
| `kernel.module.registry` | on demand | `ModuleDescriptor`, parsed from `module.json` |
| `kernel.plugin.registry` | on demand | `PluginDescriptor` |
| `platform.PlatformRegistry` | at import of `app/platform/*` | ad-hoc dicts |

**`CapabilityRegistry` is canonical.** It is the only one populated at boot,
the only one with a typed descriptor, and the only one with a dependency graph.
`PlatformRegistry` is a parallel, untyped store of the same idea; it is not
deleted here (that would be unrelated remediation) but no new code may register
with it, and the guard enforces that.

## 6. The finding that matters most

No descriptor in the canonical registry carries a `module_path`, a
`documentation` path or a `test_paths` entry — 52 out of 52. So the registry
describes 52 capabilities and cannot be checked against a single line of the
code that implements them. It is a catalogue, not a contract.

That is what PROGRAM-EXT-001 changes going forward: the fields are now part of
the descriptor, the contract requires them, and the 52 that predate it are
named in `GRANDFATHERED` so the debt is counted rather than absent.
