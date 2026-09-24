# NR-050 Capability Architecture Disposition

**Decision record / discovery report. No implementation was performed.**
Companion to `docs/architecture/nr-050-capability-tree-discovery.md`, which
recorded the original forensic discovery. This document carries the disposition
analysis that discovery was gathering evidence for.

Measured at `586f91c5`, working tree clean.

## Executive Summary

`app/capabilities/` is not one thing. It is **two populations that share a
directory**:

1. **`fhir_interoperability`** — a hand-written capability with a service, an
   ORM model, a migration, a physical table, institutional authorization and
   tenant scoping. It is registered in `factory.py` and it runs.
2. **The other nine** — output of `app/engineering/generators/capability.py`,
   the generator NR-053 repaired. They have no ORM model, no migration, no
   table, no registration, and handlers that return a literal
   `{"items": [], "total": 0}`. Nine of them cannot be imported at all.

The decisive evidence is not that nine packages fail to import. It is **what
they would do if they did not**. Every `capability.py` in all ten imports
`backend.app.kernel.integration`, and `backend.app.…` resolves to a *different
module object* than `app.…` for the same file — the container copies the
application twice (`COPY backend ./backend` and `COPY backend/app ./app`).
`app/kernel/integration.py` holds `_kernel_instance` as a module-level global.
So registering these capabilities as they stand would not be a no-op: it would
create a **second kernel with a second registry**, invisible to the one
`factory.py` boots.

That single fact separates "a template defect worth fixing" from "an
architecture that is not ready to be switched on", and it is why the
recommendation below is never "just register them".

Meanwhile the registry describes all ten as `maturity = PRODUCTION`.

## Current Repository State

| | |
| --- | --- |
| HEAD | `586f91c5` |
| Branch | `claude/p0-2-pharmacy-reconciliation` |
| Packages | 10 |
| Python modules | 268 |
| Registered app paths | 1787 |
| Registry descriptors | 52 |

## 10-Capability Inventory

| capability | files | LOC | shape | ORM model | migration | in `factory.py` |
| --- | ---: | ---: | --- | --- | --- | --- |
| `fhir_interoperability` | 27 | 911 | hand-written | **yes** (`FHIRResourceRecord`) | **yes** (`20260815_0019`) | **yes** |
| `encounter_management` | 34 | 559 | generated + hexagonal | no | no | no |
| `workflow_engine` | 33 | 541 | generated + hexagonal | no | no | no |
| `document_management` | 32 | 537 | generated + hexagonal | no | no | no |
| `provider_management` | 30 | 501 | generated + hexagonal | no | no | no |
| `clinical_foundation` | 24 | 383 | generated (CQRS only) | no | no | no |
| `healthcare_consent` | 22 | 356 | generated (CQRS only) | no | no | no |
| `reporting_service` | 22 | 356 | generated (CQRS only) | no | no | no |
| `storage_service` | 22 | 354 | generated (CQRS only) | no | no | no |
| `search_service` | 21 | 334 | generated (CQRS only) | no | no | no |

## Import Matrix

Two environments, because they answer different questions.

**(a) As the application runs** — repo root and `backend/` both on `sys.path`,
which is what `conftest.py`, CI and the container all provide:

| capability | package import | submodules with `__init__` bypassed | blocking defect |
| --- | --- | --- | --- |
| `fhir_interoperability` | **27/27 OK** | 22/22 | — |
| `clinical_foundation` | 0/24 | **19/19** | D1 only |
| `healthcare_consent` | 0/22 | **17/17** | D1 only |
| `reporting_service` | 0/22 | **17/17** | D1 only |
| `storage_service` | 0/22 | **17/17** | D1 only |
| `search_service` | 0/21 | **16/16** | D1 only |
| `encounter_management` | 0/34 | 22/26 | D1 + D3 |
| `document_management` | 0/32 | 20/24 | D1 + D3 |
| `provider_management` | 0/30 | 18/22 | D1 + D3 |
| `workflow_engine` | 0/33 | 21/25 | D1 + D3 |

**189 of 205 submodules import once one line per package is bypassed.** The
`0/N` column is a cascade: importing `app.capabilities.X.y` first executes the
broken `X/__init__.py`. Reporting only that column would badly overstate the
damage.

**(b) With `backend/` alone on the path** — exposes D2 and a second root:
every `capability.py` fails on `No module named 'backend'` (**10/10**,
`fhir_interoperability` included), and every `routes.py` fails on
`No module named 'shared'`. The `shared` dependency is legitimate — `shared/`
is a real top-level package the application imports — so this environment is
not the one the app runs in. It is recorded because it is the environment that
makes D2 visible.

### Defect classification

| defect | what it is | population | class |
| --- | --- | --- | --- |
| **D1** | `from <package>.capability import …` in `__init__.py` — a bare top-level import resolving against nothing | 9/10 (not `fhir`, which uses `from .capability`) | **template** — fixed at source by NR-053 |
| **D2** | `backend.app.…` in `capability.py` | **10/10** | **architecture** — see kernel-splitting above |
| **D3** | defaulted `id` ahead of required fields → `TypeError` at class creation | 4 packages × 4 modules | **template** — fixed at source by NR-053 |
| **D4 / NR-055** | route function names built from the hyphenated URL prefix | template only | **template** — fixed at source by NR-053 |

None of these is a "missing implementation" error. The missing implementation
is a separate fact, established below.

## Runtime Reachability Matrix

Chain: frontend → API call → registered route → router → service → repository →
ORM → table → migration.

| capability | breaks at | classification |
| --- | --- | --- |
| `fhir_interoperability` | **no break** (no frontend page, by design — it is a machine-facing interop surface) | **RUNTIME_REAL** |
| `clinical_foundation` | route never registered; no service, no ORM, no table | **TEMPLATE_ONLY** |
| `document_management` | ″ | **TEMPLATE_ONLY** |
| `encounter_management` | ″ | **TEMPLATE_ONLY** |
| `healthcare_consent` | ″ | **TEMPLATE_ONLY** |
| `provider_management` | ″ | **TEMPLATE_ONLY** |
| `reporting_service` | ″ | **TEMPLATE_ONLY** |
| `search_service` | ″ | **TEMPLATE_ONLY** |
| `storage_service` | ″ | **TEMPLATE_ONLY** |
| `workflow_engine` | ″ | **TEMPLATE_ONLY** |

No `UNKNOWN` was needed: every chain was traced to a specific break.

The nine are `TEMPLATE_ONLY` rather than `REGISTERED_BUT_UNREACHABLE` because
the break is not registration alone. Registering them changes nothing real:
the handler beneath returns a fabricated empty page, over no table.

## Canonical Ownership Matrix

Owners were identified from ORM models declaring `__tablename__`, not from
endpoint names.

| concept | candidate owners (model evidence) | canonical owner | confidence |
| --- | --- | --- | --- |
| FHIR / interop | `capabilities/fhir_interoperability/models.py` | **itself** — sole implementation | HIGH |
| encounter | `national/domain/encounter.py`, `care_continuum/models/primary_care.py`, `health_data/warehouse`, `health_data/ods` | **`national/domain/encounter`**, surfaced by `/national-data/encounters` (NR-054 bound the UI to it) | MEDIUM-HIGH |
| consent | `identity/models/consent.py`, `identity/lifecycle/models.py`, `national/domain/consent.py`, `research_platform/base.py` | **unresolved — NR-051** | LOW |
| document | `national/document_platform/infrastructure/models.py`, `document_intelligence/infrastructure/models.py` | **unresolved — NR-051** | LOW |
| workflow | `national/workflow_runtime/infrastructure/models.py` (sole persistent owner) | **`national/workflow_runtime`** — but NR-051 lists competing non-persistent implementations | LOW-MEDIUM |
| provider | `identity/federation/models.py`, `financial/models.py`, `health_data/warehouse`, `health_data/mdm` | **none** — no healthcare-practitioner registry exists | MEDIUM |
| reporting | `identity/compliance`, `radiology`, `lims`, `clinical/quality` — all domain-scoped | **none** — no platform-wide reporting service | MEDIUM |
| search | `research_platform/base.py`, `clinical/research/models.py`, `national/search_platform/infrastructure/models.py` | **none** for generic search | MEDIUM |
| storage | `radiology/models.py`, `lims/models.py` — both **physical specimen** storage | **none** for blob/object storage | HIGH |
| clinical foundation | — | **none** — the concept has no definition in the repository | MEDIUM |

**Semantic warnings recorded deliberately.** `provider` in the registered route
set means AI providers, payment providers and federation providers — not
practitioners. `/lims/storage` is refrigerators and shelves, not object
storage. Neither may be adopted as a canonical owner on name similarity.

## Duplication / Overlap Graph

| capability | concept | existing implementations | overlap verdict |
| --- | --- | --- | --- |
| `fhir_interoperability` | FHIR R4 / HL7 v2 | 1 (itself) | **no duplicate** |
| `encounter_management` | clinical encounter | 4 model families | duplicate of `national/domain/encounter` |
| `healthcare_consent` | consent | 4 | duplicate; owner unresolved (NR-051) |
| `document_management` | document | 2 | duplicate; owner unresolved (NR-051) |
| `workflow_engine` | workflow | 1 persistent + others | duplicate of `national/workflow_runtime` |
| `provider_management` | practitioner registry | 0 matching | **not a duplicate — a gap** |
| `reporting_service` | platform reporting | 0 matching (12 domain-scoped) | **not a duplicate — a gap** |
| `search_service` | generic search | 0 matching | **not a duplicate — a gap** |
| `storage_service` | object storage | 0 matching | **not a duplicate — a gap** |
| `clinical_foundation` | undefined | 0 | **concept undefined** |

The distinction matters for disposition: a duplicate can be consolidated; a gap
cannot be consolidated into anything, and retiring it removes a stated
requirement without replacing it.

## Architectural Value Matrix

0 none · 1 low · 2 medium · 3 high

| capability | runtime | domain | reuse | discovery | arch | completeness | owner clarity | prod-ready | dup risk | migration risk | future relevance |
| --- | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: | --: |
| `fhir_interoperability` | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 2 | 0 | 1 | 3 |
| `encounter_management` | 0 | 3 | 1 | 2 | 1 | 0 | 2 | 0 | 3 | 0 | 2 |
| `workflow_engine` | 0 | 2 | 2 | 2 | 1 | 0 | 1 | 0 | 3 | 0 | 3 |
| `document_management` | 0 | 2 | 2 | 2 | 1 | 0 | 1 | 0 | 3 | 0 | 3 |
| `healthcare_consent` | 0 | 3 | 2 | 2 | 1 | 0 | 1 | 0 | 3 | 0 | 3 |
| `provider_management` | 0 | 3 | 2 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 3 |
| `reporting_service` | 0 | 2 | 2 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 2 |
| `search_service` | 0 | 1 | 2 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 2 |
| `storage_service` | 0 | 1 | 3 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 3 |
| `clinical_foundation` | 0 | 1 | 0 | 2 | 1 | 0 | 0 | 0 | 1 | 0 | 1 |

Scores support the decisions below; none was made by score alone.

## Discovery Intelligence Preservation

The nine generated packages contain no generators, detectors or evidence
collectors — those live in `app/engineering/`, which NR-053 and NR-056
repaired. What the nine *do* carry, and what would be lost by deleting them:

1. **A stated capability taxonomy.** The `__init__` docstrings are the only
   place in the repository where several concepts are scoped at all — the
   `storage_service` docstring names S3/MinIO/Azure/GCS with versioning and
   encryption; `healthcare_consent` names break-glass and purpose-of-use.
   These are requirements statements, not code.
2. **A worked reference of the intended architecture.** The four hexagonal
   packages are the only complete domain/application/infrastructure examples in
   the codebase.
3. **The registry's own contract shape** (`capability.py` + `contract.py`).

**Architectural decision recorded, not executed:** runtime capability and
discovery/taxonomy artifacts should be separated, so that a docstring
describing an intended capability is not indistinguishable from a capability
that exists. No file is moved here.

## Disposition Matrix

One disposition per capability. **None executed.**

| capability | disposition | canonical owner | confidence |
| --- | --- | --- | --- |
| `fhir_interoperability` | **KEEP_AND_HARDEN** | itself | HIGH |
| `encounter_management` | **CONSOLIDATE** | `national/domain/encounter` | MEDIUM-HIGH |
| `workflow_engine` | **BLOCKED** | `national/workflow_runtime` (probable) | LOW-MEDIUM |
| `document_management` | **BLOCKED** | unresolved (NR-051) | LOW |
| `healthcare_consent` | **BLOCKED** | unresolved (NR-051) | LOW |
| `provider_management` | **COMPLETE_OR_REPLACE** | none exists | MEDIUM |
| `storage_service` | **COMPLETE_OR_REPLACE** | none exists | MEDIUM |
| `reporting_service` | **PRESERVE_DISCOVERY** | none exists | MEDIUM |
| `search_service` | **PRESERVE_DISCOVERY** | none exists | MEDIUM |
| `clinical_foundation` | **PRESERVE_DISCOVERY** | none exists | MEDIUM |

**No capability received DEPRECATE or RETIRE.** Neither is justified on the
evidence: DEPRECATE requires a proven canonical successor, which exists for at
most `encounter_management`; RETIRE requires proof of obsolescence with no
runtime, discovery or future value, and every one of the nine carries a stated
requirement that nothing else in the repository states.

### Per-capability rationale

**`fhir_interoperability` — KEEP_AND_HARDEN.** The only member of its
directory that is a capability rather than a template: 27/27 modules import,
routed through `factory.py`, `FHIRResourceRecord` backed by migration
`20260815_0019`, unique constraint on `(lab_id, resource_type, resource_id,
version)`, `require_institutional_permission("lab:read"/"lab:manage")`, and
HL7 ORU^R01 parsing to FHIR bundles. *Hardening required*: its `capability.py`
still imports `backend.app.kernel.integration` (D2), which is the
kernel-splitting hazard; and its registry descriptor carries no `module_path`,
`test_paths` or `documentation`. *Must not happen*: it must not be consolidated
into any other capability, and its table must not be dropped.

**`encounter_management` — CONSOLIDATE.** A canonical owner exists and is
already serving the UI: NR-054 bound the encounter page to
`GET /national-data/encounters`, proven live (200, JSON array, lab-scoped,
`patients:read`). The package duplicates that concept with no table.
*Prerequisite*: confirm that `national/domain/encounter` is the intended owner
against `care_continuum` and the `health_data` projections — they may be
legitimate downstream views rather than rivals. *Must not happen*: no second
encounter table; no new encounter API.

**`workflow_engine`, `document_management`, `healthcare_consent` — BLOCKED.**
All three concepts are named in NR-051 as having competing implementations with
no canonical owner. Choosing an owner here would decide NR-051 by side effect,
which this analysis is explicitly forbidden from doing. `workflow_engine` is
the closest to resolvable — `national/workflow_runtime` is the only persistent
owner — but NR-051 lists competing non-persistent implementations that must be
adjudicated first. *Blocking decision*: **NR-051 canonical ownership for
workflow, document and consent.**

**`provider_management`, `storage_service` — COMPLETE_OR_REPLACE.** Both
concepts are real and needed, and **neither has any existing implementation to
bind to**. Every registered `…/providers` path means a service provider, not a
practitioner; every registered `…/storage` path means physical specimen
storage. These are gaps, not duplicates. *Prerequisite*: a decision on whether
a practitioner registry belongs to Identity/NIAM or to a clinical domain, and
whether object storage is a platform service or a per-domain concern.

**`reporting_service`, `search_service`, `clinical_foundation` —
PRESERVE_DISCOVERY.** Their value today is the requirement statement, not the
code. Reporting is served by twelve domain-specific endpoints and there is no
evidence a platform-wide reporting service is wanted; search is a
cross-cutting concern rather than a domain, with 43 query-shaped endpoints
already; `clinical_foundation` has no definition anywhere to build against.
*Must not happen*: none of the three may be registered, because registering
them ships the fabricated empty response.

## Import Root / Kernel Hazard — proven live, partly repaired

The analysis above described this as a hazard. It was not: it was **live in
every running process**, and it is now measured, partly repaired and guarded.

### What was happening

`factory.py` imports `app.capabilities.fhir_interoperability.models`. That
executes the package `__init__`, which imports `capability.py`, which named
`backend.app.kernel.integration`. So a real `create_app()` loaded **36
`backend.app.*` modules** — a second copy of the application inside the same
process:

| shadow module | consequence |
| --- | --- |
| `backend.app.kernel.integration` | second kernel; `_kernel_instance` is a module-level global, so capability registration through it reaches a registry `factory.py` never boots |
| `backend.app.database` | second `Base`, **second `Engine`** |
| `backend.app.config` | config validation runs twice |
| `backend.app.national.task_engine.*` (13) | duplicate subsystem incl. ORM models |
| `backend.app.national.workflow_runtime.*` (14) | duplicate subsystem incl. ORM models |

Proven by identity rather than by reading: `app.kernel.integration is
backend.app.kernel.integration` → `False`, with identical `__file__`.

**What tempers the severity:** the shadow `Base` carries **0 tables**, so ORM
metadata is not corrupted; the shadow kernel's `_kernel_instance` is `None` and
nothing boots it; the shadow engine is never used. The damage today is a loaded
dormant tree, not active divergence. The danger is the moment anything
registers through it — which is precisely what the nine unregistered
capabilities would have done.

### Repaired here

Ten `capability.py` files, one line each, `backend.app.` → `app.`. A real
`create_app()` now loads **34** such modules and **no second kernel**.

### Not repaired here — NR-058

The residual 34 belong to `national/task_engine` and
`national/workflow_runtime`, which use that root throughout — for their own
internal references as well as for `database` and `config`. That is a
package-wide change with its own review, and this work was explicitly forbidden
from a repository-wide import migration undertaken merely because the defect
exists. Also outside: `services/governance`, `services/reference`,
`integration/connectors/email.py`.

### Prevention

`backend/tests/test_capability_import_roots.py` — 9 tests. AST (not grep) for
the capability tree; a **behavioural** assertion that a real application start
loads no second kernel, because the static check alone would have missed the
`factory.py → __init__ → capability.py` path that made this live; and an
NR-058 ledger that may shrink but never grow, with a per-entry test that fails
if a listed package is quietly repaired and left in the list.

### Root cause

`Dockerfile:24-26` copies the application twice: `COPY backend ./backend`
alongside `COPY backend/app ./app`. Removing that duplication is the permanent
fix and is **DECISION REQUIRED** — it changes the container layout.

## Registry Integrity

All ten descriptors declare `maturity = PRODUCTION` while nine cannot import
and only one is registered. Classification: **REGISTRY DEFECT**, specifically
*lifecycle design weakness* — `maturity` is author-declared and nothing
reconciles it against reachability. The existing guards check that `maturity`
is typed and that deprecated/retired capabilities name a successor; none checks
that a PRODUCTION capability can be imported or is routed.

Not changed here. Correcting the values is a one-field edit with no runtime
effect, but it is still execution, and the right fix is probably the invariant
rather than the values. **DECISION REQUIRED.**

## Safe Remediation Performed

| file(s) | defect | class | repair | test |
| --- | --- | --- | --- | --- |
| 10 × `app/capabilities/*/capability.py` | `backend.app.` import root (D2) | **ARCHITECTURE DEFECT** (not tooling — it split the kernel) | `backend.app.kernel.integration` → `app.kernel.integration` | `test_capability_import_roots.py` (9 tests, 3 negative-proven) |

**Deliberately NOT repaired, though mechanically trivial:**

- **D1** (bare `__init__` import, 9 packages) and **D3** (dataclass ordering, 4
  packages). Both are one-line template defects and both are within the letter
  of the autonomy granted. They are held because repairing them makes the four
  hexagonal packages *importable*, and their
  `infrastructure/repository.py` are the four remaining entries in the NR-044
  ledger — async-session code that was closed as unreachable. Making it
  reachable is an architectural consequence, not a mechanical one, and it would
  reopen a finding that was verified closed. That decision belongs to NR-050
  execution.

## Dependencies

```
NR-050
  ├── BLOCKED BY  NR-051  (canonical owner: workflow, document, consent)
  ├── BLOCKED BY  NR-022  (National Core scope — affects encounter and clinical_foundation)
  ├── INFORMS     NR-057  (30 further frontend orphans, same defect class)
  ├── INFORMED BY NR-053  (generator repaired — new capabilities will not repeat D1/D3/D4)
  ├── INFORMED BY NR-054  (the nine frontend routes already made honest)
  ├── INFORMED BY NR-056  (import-root repair; D2 in these packages is the same class, unfixed here)
  ├── OWNS        NR-044's remaining ledger of 4 (the four hexagonal repositories)
  └── RELATES TO  NR-006 (facility identity), NR-023 (shared metadata), NR-030 (tables without ORM)
```

`NR-050 → NR-044`: the ledger's four entries are exactly
`document_management`, `encounter_management`, `provider_management` and
`workflow_engine`. That ledger cannot shrink below 4 until NR-050 is executed —
it is the last thing holding NR-044 open.

## Risks

| risk | severity | note |
| --- | --- | --- |
| Registering any of the nine as-is | **P1** | ships a fabricated empty dataset over no table, and splits the kernel via D2 |
| Deleting the nine | P2 | loses the only statement of several intended capabilities |
| Consolidating on a name match | P2 | `provider`/`storage` semantics differ from their namesakes |
| Leaving `maturity = PRODUCTION` | **P1** | the registry asserts ten production capabilities; nine do not run |
| Duplicate application tree in the container | **P1** | `backend.app.*` and `app.*` load the same file as two modules with independent globals |

## Open Decisions

1. **NR-051** — canonical owner for workflow, document, consent. Blocks three.
2. **NR-022** — National Core scope. Affects `encounter_management` and
   `clinical_foundation`.
3. Does a **practitioner registry** belong to Identity/NIAM or a clinical domain?
4. Is **object storage** a platform service or per-domain?
5. Should the registry's `maturity` for the nine be corrected now, or as part
   of execution? (Correcting it is a one-field change with no runtime effect,
   but it is still an execution step and was not taken here.)

## Required Future Work

Ordered, each a separate task:

1. Correct `maturity` for the nine from `PRODUCTION` to something truthful.
2. Harden `fhir_interoperability`: D2 in `capability.py`; complete its descriptor.
3. Resolve the duplicate application tree in the Dockerfile.
4. Resolve NR-051, then execute the three BLOCKED dispositions.
5. Execute `encounter_management` consolidation.
6. Decide and execute `provider_management` / `storage_service`.
7. Separate discovery taxonomy from runtime capability packages.
8. Shrink the NR-044 ledger once 4 and 5 land.

## Explicitly Out of Scope

Not touched, deliberately: NR-051, NR-057, NR-022, NR-046, NR-041, NR-042,
National Core, `factory.py`, migrations, frontend routes, CI, dependencies,
`CapabilityRegistry` runtime behaviour, auth/security behaviour. No package was
deleted, retired, renamed, moved or merged; no ORM model, migration or API was
created; no router was registered.

## Evidence / Commands

| claim | command |
| --- | --- |
| package inventory | `find app/capabilities -name '*.py'` + per-dir `wc -l` |
| import matrix (a) | submodule import with a stub `__init__` in `sys.modules`, `PYTHONPATH=repo:backend` |
| import matrix (b) | same, `PYTHONPATH=backend` |
| D1 population | `grep` each `__init__.py` — only `fhir` uses `from .capability` |
| two module objects | `import app.kernel.integration as a; import backend.app.kernel.integration as b; a is b` → `False`, same `__file__` |
| kernel singleton | `app/kernel/integration.py:15` `_kernel_instance: Kernel \| None = None` |
| registry maturity | `_get_all_descriptors()` → 52; the ten all `PRODUCTION`, all missing `module_path` |
| registration | `grep` in `app/factory.py` — only `fhir_interoperability` |
| ORM models | `grep -rl "__tablename__" app/capabilities/` → only `fhir_interoperability/models.py` |
| FHIR migration | `migrations/versions/20260815_0019_fhir_resource_registry.py` |
| canonical owners | `grep` `__tablename__` per concept across `app/` |
| container duplication | `Dockerfile:24-26` |

## Confidence

**Overall: HIGH** for the two-population split, the import matrix, the defect
classification, the reachability matrix and the kernel-splitting hazard — all
measured, not inferred.

**Per-disposition** as tabulated: HIGH for `fhir_interoperability`;
MEDIUM-HIGH for `encounter_management`; MEDIUM for the four gaps; **LOW for
the three blocked on NR-051**, and that low confidence is the reason they are
BLOCKED rather than assigned.
