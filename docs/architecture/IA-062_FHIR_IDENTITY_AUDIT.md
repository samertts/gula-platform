# FHIR Patient Identity — Independent Adversarial Audit (Account 2)

**ID NOTE.** This file carries the requested name, but `IA-062` is already
assigned in this register to the dual result-store divergence
(`NR-217_ADVERSARIAL_AUDIT.md`). The findings in this document are therefore
**IA-063** and **IA-064**. Recorded rather than silently renumbered.

**Scope attacked:** every site in `backend/app` that constructs a Patient or
subject reference — 50 `Patient/` occurrences, reduced to 9 distinct builders.
**Runtime proof:** `backend/tests/verification/test_fhir_patient_identity.py` (10 tests).
**Nothing fixed. No schema change. Not pushed.**

---

## Phase 1–2 — the builder inventory

| Site | Source entity → field | Target resource | Runtime output |
|---|---|---|---|
| `routes/ehr_fhir.py:88` `_patient_ref` | caller-supplied `patient_id` | 8 resources | `{reference: "Patient/{id}", type: "Patient"}` |
| `routes/ehr_fhir.py:409` (inline) | `LabOrder.patient_id` | Observation | `{reference: "Patient/1", type: "Patient"}` — **correct** |
| `lims/fhir_mappers.py:117` | `result.specimen.order.patient_id` (relationship absent) | Observation | `{reference: "unknown", display: ""}` — **NR-218 / IA-061** |
| `lims/fhir_mappers.py:285` | keyword-only `patient_id`, no default | ServiceRequest | `{reference: "Patient/1", display: ""}` — **correct** |
| `national/api/routes/interop.py:118` `_patient_reference` | `Patient.id` + `health_id` + canonical | DiagnosticReport | `{reference, identifier, display}` |
| `national/fhir/*.py` (10 modules) | `{record,request,statement,care_plan}.patient_id` or keyword | 11 resources | `{reference: "Patient/{patient_id}"}` |
| `national/api/routes/encounter.py:163` | `encounter.patient_id` | Encounter | conditional on non-null |
| `capabilities/fhir_interoperability/hl7.py:131,145` | **HL7 PID-3** | Observation, DiagnosticReport | `Patient/MRN-FOREIGN-9001` — **IA-064** |
| `integration/fhir_r4_exchange.py:91,100,109,119` | hardcoded | 4 resources | `Patient/synthetic-patient-001` — **unreachable, 0 importers** |

## Phase 4 — can a non-patient id be published as the patient? **VERIFIED_NEGATIVE**

Measured with three patients and one order so the id spaces overlap:

```
correct = 'Patient/1'
core Observation      -> 'Patient/1'    correct
lims ServiceRequest   -> 'Patient/1'    correct
lims Observation      -> 'unknown'      NR-218, not a wrong id
```

None of `Patient/<LabOrder.id>`, `Patient/<LimsOrder.id>`,
`Patient/<Specimen.id>`, `Patient/<LimsResult.id>` or `Patient/<LabResult.id>`
is reachable. **The NR-219 repair holds at this HEAD** and the
wrong-but-valid-looking class is closed on the laboratory paths. This is a
confirmation of existing work, not a new finding.

## Phase 5 — the matrix

| Scenario | Result |
|---|---|
| same patient, two orders | both `Patient/1` — stable |
| different patient, same test | each names its own patient |
| different tenant | **404 on both stores** (`lims` 404, core 404) |
| missing patient | not constructible: `lab_orders.patient_id` is NOT NULL |
| invalid order (`order_id=999999`) | `/lims/results/{id}/fhir` still 200, subject unchanged — the mapper never reads the order |
| valid LIMS result | `subject = unknown` |
| valid core result | `subject = Patient/{patients.id}` |

## Phase 6 — are published Patient ids stable public identifiers? **No**

```
published Patient/1 is patients.id (integer PK)
patients.health_id exists but is not used in the reference
```

Every reference publishes the **internal integer primary key**. A stable
public identifier (`patients.health_id`) exists on the model and is used by
exactly one builder — `interop.py:118` adds it as a FHIR `identifier`
*alongside* the internal `reference`. The other eight builders publish the
internal id alone.

This is a sequential, guessable identifier in an externally-facing resource
reference. It is **not** an existence oracle here, because every tested path
returns 404 for another tenant's row and the reference is only ever emitted
inside a resource the caller is already authorised to read. Recorded as an
identity-exposure property with a decision attached, not as a vulnerability.

## Phase 7 — resources audited

Observation (core + LIMS + national + HL7), ServiceRequest, DiagnosticReport,
Specimen, Bundle, Patient, Encounter, Condition, Procedure, CarePlan,
MedicationRequest, MedicationStatement, Immunization, AllergyIntolerance,
DocumentReference. **Provenance: no builder found** — `grep` over
`backend/app` returns no `"resourceType": "Provenance"`. NOT FOUND, which is
not the same as absent by design; ADR-011 does not mention Provenance either.

## Phase 8 / 11 — the Bundle subject omission is NOT classified as a defect

`/lims/orders/{id}/fhir-bundle` pops `subject` from every entry. The route
docstring states the reason (patient identity is not expanded in laboratory
exports, to prevent accidental PHI duplication), the behaviour matches the
statement exactly, ADR-011 line 55 records it, and the export writes a
metadata-only audit event. Consistent with the documented privacy decision.

---

## IA-063 — three reference builders, three shapes · P3 · CONFIRMED

| Builder | Shape |
|---|---|
| `ehr_fhir._patient_ref` | `{reference, type}` |
| `lims._fhir_reference` | `{reference, display}` |
| `interop._patient_reference` | `{reference, identifier, display}` |

FHIR R4 permits any subset of `Reference`, so all three are **valid**; this is
an inconsistency, not invalidity, and is filed P3 for that reason. The
consequence is that a consumer cannot rely on `subject.type` being present, and
only one of the three carries the canonical `health_id` identifier that would
let an external system resolve the patient without trusting an internal id.

`ehr_fhir.py:409` builds its subject inline rather than calling its own
`_patient_ref`. Checked: the literal is **shape-identical** to the helper, so
this is duplication, not divergence. **Not a defect**, asserted so it stays
that way.

## IA-064 — the served HL7 converter mints patient identity · P2 · CONFIRMED

**File / symbol** `app/capabilities/fhir_interoperability/hl7.py:110` `to_fhir_bundle`
**Trigger** `POST /fhir-interoperability/hl7/convert` (`routes.py:67`), registered at `factory.py:656`
**Authorization** `require_institutional_permission("lab:manage")` — authenticated, write-level

Three measured behaviours:

**(a) An external identifier enters the internal reference namespace.**
`patient_id = message.patient_identifier or "synthetic-patient"`, where
`patient_identifier` is **PID-3** — minted by the sending facility. Measured:

```
Patient.id                      = "MRN-FOREIGN-9001"
Observation.subject.reference   = "Patient/MRN-FOREIGN-9001"
DiagnosticReport.subject.ref    = "Patient/MRN-FOREIGN-9001"
```

Everywhere else in the platform `Patient/{x}` means `patients.id`. A consumer
holding `Patient/MRN-FOREIGN-9001` and `Patient/1` cannot tell from the
reference which identifier domain each belongs to.

**(b) The simulation marker is on the envelope only.** The Bundle carries
`meta.tag = synthetic-only` and the response carries `simulationOnly: true`,
but measured:

```
resources WITHOUT meta: ['Patient', 'Observation', 'DiagnosticReport']
```

A collection Bundle exists to be unbundled; once it is, nothing on the
resources says they are synthetic. The contrast is instructive: the
**unreachable** `integration/fhir_r4_exchange.py` applies `_synthetic_meta()`
to all seven of its resources individually. The reachable converter is the
weaker of the two.

**(c) Unidentified patients collapse into one identity.** Two distinct ORU^R01
messages with an empty PID-3:

```
CTRL-NOPID-1 -> Patient/synthetic-patient
CTRL-NOPID-2 -> Patient/synthetic-patient
```

The fallback is constant, so two different unidentified people share one
patient identity. Unlike NR-218's `"unknown"`, this value *looks* like a real
id and will merge rather than fail.

**Severity P2, not higher, and the reasons are measured not assumed:** the
endpoint is authenticated at write level, it declares `simulationOnly: true`,
its own error text calls itself "the synthetic converter", and it persists
nothing — it converts and returns. No cross-tenant exposure and no PHI leak
was found. The risk is that its output is structurally indistinguishable from
production FHIR once separated from the response envelope.

**Security impact** none proven. **Clinical / data-integrity impact** a
received bundle filed from this endpoint would attribute results to a foreign
identifier, or merge distinct unidentified patients.

**DECISION GATE.** Three candidate repairs, all requiring authority this audit
does not have: tag each resource as the sibling module already does; namespace
the reference (`Patient/hl7-{PID-3}`) to keep identifier domains apart; or make
an absent PID-3 a 422 instead of a fabricated identity. The third changes a
served endpoint's contract. **Nothing applied.**

---

## Negative proofs

| | Perturbation | Test that must fail | Restore |
|---|---|---|---|
| NP-K | tag each HL7 resource | `test_ia064_the_synthetic_tag_is_on_the_bundle_only` | byte-identical (sha256) |
| NP-L | make the no-PID fallback unique per message | `test_ia064_two_messages_..._collapse_into_one_patient` | byte-identical (sha256) |

## Bounds on these claims

- "0 importers" for `fhir_r4_exchange` is a search result over `backend/app`,
  asserted by a test. It is **INFERRED unreachable**, not proven dead: no
  importer and no route were found; reflection or an out-of-tree caller is
  outside what was measured.
- **Provenance** is NOT FOUND, not proven absent.
- ADR-011 does not define a canonical result store, a patient identity
  contract, or Provenance. Claims about those are not attributable to it.
