# NR-217 — Independent Adversarial Audit (Account 2)

**Auditor:** Account 2, isolated worktree, branch `claude/independent-audit-1`.
**Method:** attack each claim with independent evidence; accept none on report.
**Nothing pushed. No migration created. No LIMS→Core mapping invented.**

Account 1's commits are not objects in this store, so nothing here reproduces
or depends on its analysis. Where this contradicts a documented claim, the
contradiction is recorded rather than resolved.

---

## Verdicts

| # | Claim | Verdict |
|---|---|---|
| 1 | Core Lab is the canonical clinical laboratory stack (`lab_orders` / `samples` / `lab_results`) | **PARTIALLY CONTRADICTED** |
| 2 | `/lims` is a deliberate retained internal operational extension | **CONTRADICTED BY THE MODULE'S OWN TEXT** |
| 3 | `lims_orders` / `lims_specimens` / `lims_results` are FK-anchored extensions of core entities | **1 of 3 TRUE** |
| 4 | ADR-011 establishes `/fhir` = canonical external FHIR, `/lims` = internal lab ops | **DOCUMENTED, PARTIALLY IMPLEMENTED, OVER-ATTRIBUTED** |
| 5 | The remaining NR-217 gap is: `lims_results` has no executable path to `lab_results` | **SURVIVES, AND IS BROADER THAN STATED** |

---

## Claim 3 — the FK extension claim, measured per table

| Table | FK column | Target | Null | Unique | Cascade | Extension of a core entity? |
|---|---|---|---|---|---|---|
| `lims_orders` | `order_id` | `lab_orders.id` | NOT NULL | **unique=True** | CASCADE | **YES** — a true 1:1 extension |
| `lims_specimens` | `order_id` | `lab_orders.id` | NOT NULL | no | CASCADE | **NO** — anchored to the *order*, not to `samples` |
| `lims_results` | `order_id` | `lab_orders.id` | NOT NULL | no | CASCADE | **NO** — anchored to the *order*, not to `lab_results` |
| `lims_results` | `specimen_id` | `lims_specimens.id` | NOT NULL | — | CASCADE | internal to LIMS |

Core anchors, for comparison (`app/models/lab_result.py:31`, `app/models/sample.py:21`):
both `lab_results.order_id` and `samples.order_id` are `lab_orders.id`, NOT NULL, CASCADE.

So `lab_results` and `lims_results` are **siblings under the same parent order**,
not parent and child. The same holds for `samples` and `lims_specimens`.

Measured absences, all shapes searched:

- references to `lab_results` or `LabResult` as code in `app/lims/**`: **0**
  (two hits exist and are module-docstring prose at `models.py:4` and `__init__.py:4`)
- references to `samples` / `Sample` in `app/lims/models.py`: **0**
- `lims_results` has **no** foreign key, relationship, or column pointing at `lab_results`
- cross-store uniqueness: none. `lims_results` is unique on
  `(specimen_id, test_code)` (`models.py:1134`), which cannot constrain a
  divergent `lab_results` row for the same order and test.

**Consequence:** two clinical result stores can hold different values for the
same `lab_orders.id` + test, and nothing structurally prevents or detects it.

## Claim 2 — the module contradicts "extension"

Three statements of intent, all in the codebase, mutually inconsistent:

| Source | Says |
|---|---|
| `app/lims/README.md:6-9` | the LIMS "implements the **canonical** laboratory domain as a single bounded context" |
| `app/lims/models.py:834` (Specimen docstring) | "Complete specimen lifecycle — **replaces** existing Sample model." |
| `app/lims/models.py:4`, `__init__.py:4` | "Foundation models (Lab, LabOrder, LabResult, Patient, Sample, etc.) remain **untouched**." |

"Canonical", "replaces", and "untouched" cannot all be true of the same
module. The README's own breakdown is the most precise and matches the FK
evidence exactly: *Reuses* Lab / LabOrder / Patient, *Extends* with 33 new
entities — it never claims to reuse `Sample` or `LabResult`.

## Claim 5 — NR-217 survives and widens

| Question | Answer | Status |
|---|---|---|
| Does any code convert `lims_results` → `lab_results`? | no | **CONFIRMED (not found, exhaustive on symbol)** |
| Is `lims.models.Result` referenced outside `app/lims/`? | no | **CONFIRMED** |
| Modules outside `app/lims` importing `app.lims` at all | **2**: `national/api/routes/interop.py` (imports `LabReport`), `core/bootstrap/departments.py` (imports `Department`) — neither touches Order/Specimen/Result | CONFIRMED |
| `Result(` creation sites | **1**: `app/lims/services.py:276` `ResultService.create_result` | CONFIRMED |
| Does that path write `LabResult`? | no — 0 `LabResult` references in `services.py` | CONFIRMED |
| Do the ASTM/HL7 parsers in `app/lims/integration/` write LIMS results? | no references to Result | CONFIRMED |
| Callers of `app.lims.integration` outside `app/lims` | **0** | CONFIRMED |
| Is `/lims` served? | yes — `app/factory.py:686-687` | CONFIRMED |

Searched with the **real symbols**. An earlier pass of this audit searched for
`LimsResult`, which does not exist: the classes are `Order`, `Specimen`,
`Result` in `app.lims.models`. That first pass would have reported zero
consumers for the wrong reason, and is recorded here because the corrected
search is what makes the conclusion trustworthy.

**"Not found" is not "does not exist".** The claim here is bounded: exhaustive
over the symbol `Result` as imported from `app.lims.models`, over
`lims_results` as a table name, and over `app.lims` as an import path, within
`backend/app` and `backend/tests`. It does **not** cover reflection, raw SQL
built at runtime, or an external service holding its own connection.

## Claim 4 — ADR-011

`docs/architecture/ADR-011-fhir-strategy.md`, Status: Accepted, 2026-07-18.

| ADR claim | State |
|---|---|
| `/fhir` (`app/routes/ehr_fhir.py`) is the canonical FHIR implementation (line 44) | **IMPLEMENTED** — `/fhir/Observation/{id}` reads `LabResult` (`ehr_fhir.py:377`) |
| Internal API uses GULA JSON for lab operations | **IMPLEMENTED** |
| `GET /lims/orders/{id}/fhir-bundle` exports a tenant-scoped FHIR Bundle (line 30) | **IMPLEMENTED** — and it is the ADR's own exception to its dual model |
| `/lims` = "internal laboratory operations API" | **PARTIALLY IMPLEMENTED** — `/lims` also serves `GET /lims/results/{id}/fhir`, a FHIR resource endpoint the ADR does not list |
| ADR-011 settles `lab_results` vs `lims_results` canonicality | **NOT IN THE ADR** — the claim attributes this to ADR-011; ADR-011 is about wire format, and says nothing about which result store is authoritative |

**Two documents are numbered ADR-011**: `docs/adr/ADR-011-notification-platform.md`
and `docs/architecture/ADR-011-fhir-strategy.md`. A numbering collision, recorded
as an evidence hygiene issue.

### The FHIR divergence this exposes

Two served endpoints emit FHIR R4 Observations for the same order from
disconnected stores:

```
GET /fhir/Observation/{id}            ->  LabResult        (ehr_fhir.py:377)
GET /lims/orders/{id}/fhir-bundle     ->  lims.Result      (fhir_mappers.py:109)
GET /lims/results/{id}/fhir           ->  lims.Result      (routes.py:1465)
```

Resource ids are namespaced apart (`lims-obs-{id}` vs the bare `LabResult.id`),
so there is no id collision — but a consumer federating both receives two
disjoint Observation sets for one `lab_orders.id`, with nothing to reconcile
them. This is the clinical consequence of NR-217, and it is reachable today.

---

## IA-061 — the LIMS Observation names no patient

**Severity** P1 · **Status** CONFIRMED, runtime-reproduced · **Externally reachable** yes (authenticated, tenant-scoped)

- **File / symbol** `app/lims/fhir_mappers.py:108` `result_to_fhir`
- **Trigger** `GET /lims/results/{result_id}/fhir` (`app/lims/routes.py:1465`)
- **Observed** `subject == {"reference": "unknown", "display": ""}`
- **Expected** a reference to the patient that owns the specimen's order
- **Root cause** the subject is guarded by
  `hasattr(result.specimen, "order")`. `Specimen` has `order_id` but **no
  `order` relationship** — measured `hasattr(Specimen, "order") is False`; the
  only `order`-named relationship in the module is `Order.original_order`
  (`models.py:993`). The guard never passes, so the `else` branch always runs.
- **Runtime proof** `tests/verification/test_lims_observation_subject.py` —
  a persisted Lab → Patient → LabOrder → Specimen → Result, through the real
  mapper.
- **Negative proof NP-I** adding `Specimen.order` makes three of the five
  tests fail, including the runtime one; restored byte-identically (sha256).
- **Security impact** none found. The route is authenticated
  (`Depends(get_current_user)`) and tenant-scoped
  (`Result.lab_id == _lab_id(current_user)`). No cross-tenant read, no wrong
  patient named — the reference points at nothing.
- **Data-integrity impact** an Observation a consumer cannot file against a
  patient. The bundle path at `routes.py:1021` is unaffected: it calls
  `observation.pop("subject", None)` by design.

### The contradiction

The docstring of `order_to_fhir_service_request` — the fix that corrected the
ServiceRequest subject after it published `Patient/{order_id}` — justifies
itself partly with:

> `result_to_fhir` in this same module already reaches the patient correctly
> through `specimen.order.patient_id`

**That assertion is false.** `specimen.order` does not exist. The
ServiceRequest path was repaired correctly; the Observation path beside it was
assumed correct and never measured. Pinned as a test so it cannot be dropped
silently.

### Why it is not fixed here

Either repair is a decision, not an edit:

1. add a `Specimen.order` relationship — an ORM change to a module whose own
   docstring calls the foundation models untouched; or
2. resolve the patient in the route via `Specimen.order_id` →
   `lab_orders.patient_id` and pass it keyword-only, mirroring
   `order_to_fhir_service_request`'s existing precedent.

(2) matches the established pattern, but it changes a served FHIR response
shape, which CLAUDE.md puts behind human approval. **DECISION GATE.**

---

## IA-062 — two result stores, one laboratory event, no correlation

**Severity** P1 · **Confidence** CONFIRMED, runtime-reproduced · **Reachability** both halves served

Runtime proof `backend/tests/verification/test_dual_result_store_divergence.py`.
Negative proof NP-J (add a `lab_result_id` FK → the correlation test fails), restored byte-identically.

One `lab_orders` row, one analyte, a row written to each store. Both persist:

```
[dual] order=1  core=5.4  lims=9.9  -- both persisted
```

Divergent values for the same order and test are accepted by both stores, and
nothing detects it.

### Correlation: none

| Probe | Result |
|---|---|
| column in `lab_results` pointing at `lims_results` | none |
| column in `lims_results` pointing at `lab_results` | none |
| FK either direction | none |
| `lab_results` FK targets | `lab_orders.id`, `test_types.id` |
| `lims_results` FK targets | `lab_orders.id`, `labs.id`, `lab_users.id`, `lims_specimens.id`, `lims_instruments.id` |
| shared anchor | **`lab_orders.id` only** |

### What the LIMS constraint does and does not protect

`ix_lims_result_specimen` on `(specimen_id, test_code)` is unique and **works**:
a second LIMS result for the same specimen and test is refused with
`IntegrityError`. It is scoped to LIMS-owned columns, so it cannot see the core
store and cannot deduplicate across it. The protection is real and the gap is
precise.

### Tenancy models differ

```
lab_results   has lab_id: False   -- tenancy is transitive via order_id -> lab_orders.lab_id
lims_results  has lab_id: True    -- carries its own tenant column
```

`lab_results` NOT NULL columns: `id`, `order_id`, `test_name`, `token`, `version`.
A core-store query that omits the join to `lab_orders` has no tenant column to
filter on at all; the LIMS store cannot make that mistake. Recorded as an
asymmetry in the isolation model, not raised as a separate finding — core
tenant filtering is covered elsewhere.

### Served FHIR consequence

```
/fhir/Observation/1       id='1'           subject={'reference': 'Patient/1', 'type': 'Patient'}
/lims/results/1/fhir      id='lims-obs-1'  subject={'reference': 'unknown',   'display': ''}
```

Disjoint id namespaces, so no resource-id collision — and no way for a consumer
federating both to tell that the two Observations describe one physical
laboratory event. **This is not a security leak:** both endpoints are
authenticated and tenant-scoped, cross-tenant reads return 404, and no
unauthorised data is reachable. It is a clinical-integrity and
interoperability defect.

**DECISION GATE.** A correlation identity between the stores is an
architectural decision (which store is authoritative, and whether a projection
or a shared identity is introduced). No mapping was invented and no migration
created.

## Security findings — `/lims` ingress

Negative result, stated as a bounded measurement rather than a clean bill:

| Control | `/lims/orders/{id}/fhir-bundle` | `/lims/results/{id}/fhir` |
|---|---|---|
| Authentication | `require_permission("orders:read")` | `Depends(get_current_user)` |
| Unauthenticated | — | **401 measured** |
| Tenant isolation | `Order.lab_id == lab_id` **and** the LabOrder lookup filters `lab_id` | `Result.lab_id == _lab_id(current_user)` — **404 measured** for another tenant |
| Existence oracle | — | none: cross-tenant and missing-id are both 404 |
| Audit | `log_action("export", ...)` then commit | none |
| PHI expansion | subject deliberately dropped, documented | subject present but references nothing |

Both are tenant-scoped, now measured over HTTP rather than read from source. The read path carries no audit row, which is a
weaker control than the bundle beside it; not raised as a separate finding
because CLAUDE.md's audit invariant is written for mutations.

**Not covered this cycle:** replay protection, duplicate ingestion,
oversized payloads, rate limiting, and cross-facility access on the ASTM/HL7
ingress — those parsers have **no caller outside `app/lims`**, so there is no
reachable ingress to attack yet. UNVERIFIED, not clean.

---

## What would change these verdicts

- Any runtime reflection or raw SQL reaching `lims_results` from outside
  `app/lims` would narrow claim 5.
- An external service with its own DB connection reading `lims_results` is
  outside everything measured here.
- A `Specimen.order` relationship appearing anywhere makes IA-061 stale.

Each is pinned by a test that fails if it changes.
