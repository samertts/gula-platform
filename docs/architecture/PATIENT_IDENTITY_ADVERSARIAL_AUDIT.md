# Patient Identity — Independent Adversarial Audit (Account 2)

**Hypothesis attacked:** *"GULA lacks a single consistent FHIR Patient-ID namespace."*
**Verdict: WRONG AS STATED — and the real finding is larger.**
Runtime proof `backend/tests/verification/test_patient_identity_namespace.py` (9 tests).

---

## Phase 1 — the hypothesis does not survive, because a mapping layer exists

An explicit, FK-enforced mapping layer is present and usable:

| Table | Shape | Role |
|---|---|---|
| `patients` | `id` **INTEGER**, `lab_id` NOT NULL, `health_id` VARCHAR(20) | per-tenant local record |
| `citizens` | `id` BIGINT, **`citizen_ulid` VARCHAR(26) NOT NULL**, `nid_hash`, `nid_verified`, `merged_into_id`, `status`, `version` | cross-tenant canonical identity (no `lab_id`) |
| `identity_claims` | `citizen_id`→`citizens.id` **NOT NULL**, `local_patient_id`→`patients.id` **NOT NULL**, `lab_id`→`labs.id` NOT NULL, `match_method` NOT NULL, `match_score`, `match_features` | the mapping, with how the link was made |
| `mpi_merge_audit` | `primary_citizen_id`, `secondary_citizen_id`, **`prev_hash` + `entry_hash` NOT NULL** | hash-chained, tamper-evident merge trail |

Resolution works at runtime: `patients.id=1 → citizens.id=1` via `identity_claims`.

So `patients.id` and `citizens.citizen_ulid` are **not competing namespaces** — they are
two layers of one MPI with a recorded, audited mapping. Multiple identifier forms plus a
mapping layer is an architecture, not drift. **The hypothesis is DISPROVEN as a defect claim.**

### IA-065 — the narrow claim that does survive · P3 · CONFIRMED

`citizens.citizen_ulid` is the stable, non-sequential canonical identifier, and **no FHIR
Patient reference anywhere in `backend/app` publishes it.** Asserted by search: `citizen_ulid`
appears in zero `"reference"`, `"identifier"` or `Patient/` constructions.

Nine builders publish `patients.id`. The one that attaches an identifier —
`interop._patient_reference` — uses `urn:gula:health-id` from `patients.health_id`, the
*local* record's public field, not the canonical ULID. The mapping exists behind the
boundary and is not surfaced at it. **Consistency choice with a decision attached, not a
vulnerability** — no tested path returns another tenant's row.

---

## IA-067 — two disjoint patient identity domains · P1 · CONFIRMED

This is the finding the hypothesis was groping at, and it is structural rather than cosmetic.

| Domain | Key | Type | Tables referencing it | MPI-mapped |
|---|---|---|---|---|
| **A** `patients.id` | integer PK | `INTEGER` | **35** (billing, claims, insurance, `identity_claims`, `dp_golden_records`, break-glass…) | **yes**, via `identity_claims` |
| **B** `national_patients.id` | ULID | `VARCHAR(26)` | **66** (EHR, care_continuum: antenatal, chronic disease, handovers, pathways…) | **no** |

**Tables carrying a foreign key to BOTH: zero.** Measured over the full ORM closure.

`identity_claims` targets `citizens.id`, `labs.id`, `lab_users.id`, `patients.id` — and
**never** `national_patients`. So the MPI bridges domain A to the canonical identity and
leaves domain B unreached.

Two patient entities, incompatible key types, 101 dependent tables between them, no bridge.
This is not two representations of one identity; by the schema's own foreign keys they are
independent identities.

**Security impact** none proven: each domain is queried within its own tenant guards, and no
cross-tenant read was reachable in any tested path. **Clinical/data-integrity impact** a
patient's laboratory record (domain A) and their EHR record (domain B) cannot be joined by
any FK, so a clinician view assembled from both relies on something outside the schema.

**DECISION GATE.** Whether these are meant to be one identity with a missing bridge, or two
deliberately separate registries, is an architectural decision. **Nothing created, mapped or
merged.**

---

## Phase 2 — cross-resource consistency (within domain A)

| Scenario | Result |
|---|---|
| same patient, two orders | both `Patient/1` — stable |
| same patient, core vs LIMS result | core `Patient/1`; LIMS `unknown` (NR-218) |
| different tenant | **404** from both stores |
| missing patient | not constructible — `lab_orders.patient_id` NOT NULL |

Core Observation publishes `Patient/<patients.id>` with **no** `identifier`. Provenance:
**NOT FOUND** — no builder in `backend/app`; not proven absent by design.

## Phase 3 — IA-064 stands, scope unchanged

Re-verified. `POST /fhir-interoperability/hl7/convert` uses PID-3 as the FHIR `Patient.id`;
tags only the Bundle envelope; two empty-PID messages both yield `Patient/synthetic-patient`.
**Persistence check:** the route converts and returns — it writes nothing, and the response is
not consumed by any other module (`grep`: no importer of its output path). So foreign and
synthetic ids **do not enter a persistent or canonical workflow** by any path measured.
INFERRED, not proven — reflection and out-of-tree callers were not covered.

## Bounds

- "no bridging table" is measured over `Base`, `NationalBase` and `EHRBase` metadata. A
  join performed in application code without a foreign key would not appear.
- `citizen_ulid` absence from FHIR is a search result, asserted by test.
- Provenance is NOT FOUND, not proven absent.
