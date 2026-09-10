# GULA Global Capability Radar

**Discovery phase · 2026-09-10 · nothing here is implemented.**

Machine-readable: `GULA_GLOBAL_CAPABILITY_RADAR.json`. Companions:
`GULA_OSS_CANDIDATE_REGISTRY.{md,json}`, `GULA_HEALTHCARE_IDEA_BACKLOG.{md,json}`.

GULA state comes from the BATCH-2 disposition matrix and direct inspection, not impression.
A project is named as a reference only where its licence was actually verified, or is
explicitly marked unverified.

## Summary

| State | Capabilities |
|---|---|
| `EXISTS_PARTIALLY` | 13 |
| `EXISTS_AND_VERIFIED` | 7 |
| `MISSING` | 4 |
| `BLOCKED` | 2 |

## The radar

| Capability | GULA state | Best reference | Gap | Strategy | Pri | Licence risk |
|---|---|---|---|---|---|---|
| **Identity / authn / authz** | `EXISTS_AND_VERIFIED` | Medplum access policies; SMART on FHIR scopes | Scope-based delegation for external apps not present | BUILD_NATIVE | P2 | NONE |
| **Person / Patient canonical entity** | `BLOCKED` | OpenMRS patient + identifier model | national_patients vs patients unresolved (NR-022) | BUILD_NATIVE | P0 | NONE |
| **Organization / Facility directory** | `BLOCKED` | OpenHIE Facility Registry | national_facilities double-mapped (NR-006) | BUILD_NATIVE | P0 | NONE |
| **Audit / hash-chained trail** | `EXISTS_AND_VERIFIED` | — | GULA is ahead: SHA-256 chained audit is not common in the OSS surveyed | BUILD_NATIVE | P3 | NONE |
| **Reference data / terminology service** | `MISSING` | Snowstorm; Snowstorm Lite (FHIR terminology) | backend/app/terminology has ZERO files; SNOMED/LOINC/ICD appear only as scattered strings | INTEGRATE | P0 | B |
| **Events / outbox** | `EXISTS_AND_VERIFIED` | — | Outbox pattern implemented and tested | BUILD_NATIVE | P3 | NONE |
| **EHR clinical record** | `MISSING` | OpenMRS; Medplum FHIR resources | 18 tables mapped, 0 physical, 16 blocked on national core | BUILD_NATIVE | P0 | NONE |
| **Encounter** | `MISSING` | FHIR Encounter | national_encounters referenced 42x, does not exist | BUILD_NATIVE | P0 | NONE |
| **Orders / results** | `EXISTS_AND_VERIFIED` | OpenELIS Global | GULA lims 35/35 physical; ahead | BUILD_NATIVE | P3 | NONE |
| **Medication catalogue / prescribing / dispensing** | `EXISTS_AND_VERIFIED` | — | 27/27 physical, zero drift, canonical identity settled — GULA's strongest domain | BUILD_NATIVE | P3 | NONE |
| **Drug interaction / clinical drug rules** | `EXISTS_PARTIALLY` | Open drug knowledge bases | Rules exist keyed on FK; content source unverified | ADAPT | P2 | E |
| **Imaging store / PACS** | `EXISTS_PARTIALLY` | Orthanc (GPLv3+); dcm4che (LGPL arm) | radiology/pacs.py exists; no image store | INTEGRATE | P1 | C |
| **Analyzer integration (ASTM/HL7)** | `EXISTS_AND_VERIFIED` | OpenELIS analyzer layer | device_bridge already does this | BUILD_NATIVE | P3 | NONE |
| **FHIR conformance / validation** | `EXISTS_PARTIALLY` | HAPI FHIR $validate | 6-file fhir package; no validator | INTEGRATE | P1 | A |
| **Health information exchange layer** | `EXISTS_PARTIALLY` | OpenHIM / OpenHIE | integration package is bespoke; no published architecture followed | USE_AS_REFERENCE | P1 | B |
| **OMOP research projection** | `MISSING` | OHDSI / OMOP CDM (public domain) | zero OMOP references in the repository | ADAPT | P2 | A |
| **Aggregate national indicators** | `EXISTS_PARTIALLY` | DHIS2 data element / indicator model | nhdw 14/14 physical but no indicator model | USE_AS_REFERENCE | P1 | A |
| **Blood bank end-to-end** | `EXISTS_AND_VERIFIED` | None credible found | GULA ahead of surveyed OSS; but NR-021 tenant leak is live | BUILD_NATIVE | P0 | NONE |
| **EMS / prehospital** | `EXISTS_PARTIALLY` | NEMSIS data model (via WebEMS) | 12/12 physical, 26 ops; no NEMSIS alignment | ADAPT | P2 | E |
| **Hospital admission / bed / OR** | `EXISTS_PARTIALLY` | OpenMRS bed management | 9 of 14 tables missing | BUILD_NATIVE | P1 | NONE |
| **Offline-first field operation** | `EXISTS_PARTIALLY` | CommCare (BSD / Apache-2.0) | edge_agent exists; sync conflict model unproven | USE_AS_REFERENCE | P1 | A |
| **Public health surveillance / outbreak detection** | `EXISTS_PARTIALLY` | DHIS2 | 19 ops; no outbreak detection logic verified | ADAPT | P1 | A |
| **Vaccination registry** | `EXISTS_PARTIALLY` | DHIS2 immunisation programmes | ehr_immunizations has 122 reachable ops and no table | BUILD_NATIVE | P1 | NONE |
| **Supply chain / procurement** | `EXISTS_PARTIALLY` | OpenBoxes (licence UNVERIFIED) | pharmacy inventory settled; warehouse undecided (NR-017) | BUILD_NATIVE | P2 | E |
| **Clinical decision support** | `EXISTS_PARTIALLY` | CDS Hooks; SMART on FHIR | cds_hooks route registered but EHR-blocked | BUILD_NATIVE | P1 | NONE |
| **AI assistance (documentation, summarisation)** | `EXISTS_PARTIALLY` | Self-hosted models | ai_fabric 17 files, stateless; no clinical authority — correct posture | BUILD_NATIVE | P2 | NONE |

## Where GULA is already ahead

Stated plainly because it changes what is worth doing:

- **Pharmacy** — 27/27 tables physical, zero drift, canonical identity settled (internal integer key,
  public UUID4, mutable business code that is never a key). None of the surveyed OSS has a
  cleaner identity story.
- **Blood bank** — an explicit state machine, independent crossmatch verification and a
  two-person transfusion rule. The public blood-bank projects found on GitHub are coursework.
- **Hash-chained audit** — SHA-256 chained audit logging was not present in the surveyed OSS.
- **LIMS** — 35/35 tables physical; adopting OpenELIS would be a step backwards.
- **Analyzer integration** — the device bridge already speaks ASTM/HL7 to real instruments.

**The corollary matters more than the compliment:** replacing any of these with an external
project would discard verified work. The gaps are elsewhere.

## The three real gaps

1. **Terminology — `backend/app/terminology` contains zero files.** SNOMED, LOINC and ICD
   appear only as scattered strings in five unrelated modules. This is the single largest
   missing foundation, and it is the one where mature OSS (Snowstorm, Apache-2.0) is
   unambiguously better than building. The blocker is not code: the **SNOMED CT content**
   licence is separate from the server's Apache licence and depends on Iraq's SNOMED
   International membership, which this discovery could not establish.
2. **The national core** — person, practitioner, encounter, facility. Already the BATCH-2
   blocker (NR-022); the survey confirms every mature platform solves this *first*.
3. **Imaging storage** — `radiology/pacs.py` exists with no store behind it. Orthanc solves
   it, at GPLv3+, usable only as a separate service over DICOMweb.

