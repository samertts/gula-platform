# Phase 19-03 — Terminology Governance

## Why It Matters

Clinical and laboratory data uses controlled vocabularies (LOINC, ICD,
SNOMED CT, FHIR-defined value sets). When vocabularies drift faster than
mappings, patient-safety errors creep in: a code that meant X last year now
means Y, or a code from a peer's newer release has no local mapping.

## Governance Body

The **Terminology Governance Committee** (TGC) is responsible for:

- Approving the active version of each vocabulary in production.
- Approving new mappings.
- Reviewing drift reports.
- Coordinating with peer institutions on shared mappings.
- Producing the terminology release notes per platform release.

Members:
- Clinical informatics lead
- Lab director representative
- Platform engineering lead
- Privacy officer (review)
- Regulator liaison (observer)

## Vocabularies in Scope

| Vocabulary | Use | Source | Update cadence |
|------------|-----|--------|----------------|
| LOINC | Lab tests | Regenstrief | 2× per year |
| ICD-10 / ICD-11 | Diagnoses | WHO / national | Annual |
| SNOMED CT | Clinical findings | SNOMED International | 2× per year |
| FHIR ValueSets | FHIR-defined controlled values | HL7 | Per FHIR release |
| Local Iraq codes | Local extensions | National authority | Ad-hoc |

## Mapping Discipline

For each vocabulary:

1. Active version pinned in a configuration file, NOT in code constants.
2. Cross-walk to the previous version maintained.
3. Unmapped codes fail closed: an inbound HL7/FHIR message with an unmapped
   code goes to dead-letter for review, never silently substituted.
4. New mappings are committed with a TGC approval reference.
5. Deprecated mappings are not deleted; they are marked deprecated with the
   replacement code reference.

## Storage Shape (recommended)

```
vocabulary_version
+-------------+----------+----------+-----------+
| vocabulary  | version  | active   | approved  |
+-------------+----------+----------+-----------+
| LOINC       | 2.78     | true     | yyyy-mm-dd|
| LOINC       | 2.77     | false    | ...       |
+-------------+----------+----------+-----------+

terminology_mapping
+-------------+--------+--------+-------------+----------+
| from_vocab  | from_v | code   | to_vocab    | to_code  |
+-------------+--------+--------+-------------+----------+
```

These tables are documentation-shape; implementation is deferred.

## Drift Detection

A scheduled job (future phase) compares incoming codes from peers against
the active mapping. Output:

- new codes seen
- codes that shifted meaning (heuristic: same code, different
  display/category in source data)
- ratio of unmapped → total in last 24h

A spike in unmapped is a SEV-3.

## Cross-Walk for Result Comparison

Phase 20 (epidemiology) and Phase 22 (economics) need historical comparison
across vocabulary versions. The cross-walk tables make this safe.

A direct historical comparison without cross-walk is forbidden.

## Adapter Integration

Phase 16 adapters consult the terminology service for code translation.
Adapter manifests declare which vocabularies they consume.

## SNOMED Licence Boundary

GULA does not redistribute SNOMED CT content. Mappings reference SNOMED
codes but do not embed SNOMED display strings or hierarchies. Peer-side
SNOMED licensing is the peer's responsibility.

## Validation

- Every release: TGC sign-off on active vocabulary versions.
- Every quarter: drift report.
- Every year: full mapping review.

A failed review blocks the affected adapter or analytics path; clinical
data still flows through pre-existing direct paths.
