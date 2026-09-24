# GULA OSS Candidate Registry

**Discovery phase · 2026-09-10 · no code has been copied, forked or added as a dependency.**

Licences were verified against project sources. **Anything unverified says UNKNOWN rather
than a guess**, and popularity was never treated as evidence of anything.

| Class | Meaning |
|---|---|
| `A_SAFE_TO_REUSE` | permissive; reuse permitted |
| `B_REUSE_WITH_CONDITIONS` | copyleft or content licence conditions apply |
| `C_STUDY_OR_ISOLATED_SERVICE` | no code reuse; separate process only |
| `D_LICENSE_BLOCKED` | proprietary |
| `E_UNKNOWN_REQUIRES_LEGAL_REVIEW` | licence not established |

| Project | Licence | Class | Verified | Strategy | Decision |
|---|---|---|---|---|---|
| **Medplum** | Apache-2.0 | `A` | yes | USE_AS_REFERENCE | STUDY — adopt its FHIR resource shapes and access-policy model; do not adopt its datastore |
| **HAPI FHIR** | Apache-2.0 | `A` | yes | INTEGRATE | INTEGRATE as a stateless validation service; never as a datastore |
| **Snowstorm** | Apache-2.0 (code) | `B` | yes | INTEGRATE | INTEGRATE the code, but the SNOMED CT *content* licence is separate from Apache-2.0 and depends on Iraq's SNOMED Interna |
| **DHIS2** | BSD-3-Clause | `A` | yes | USE_AS_REFERENCE | STUDY its data-element/indicator model; do not run it as a parallel system |
| **OMOP CDM / OHDSI** | Public domain (CDM spec); tools vary | `A` | yes | ADAPT | ADAPT as a read-only projection from the warehouse; per-tool licences must be checked individually |
| **OpenMRS** | MPL-2.0 with Healthcare Disclaimer | `B` | yes | USE_AS_REFERENCE | STUDY the concept dictionary and encounter model. MPL-2.0 is file-level copyleft: any reused file stays MPL |
| **OpenELIS Global** | MPL-2.0 | `B` | yes | USE_AS_REFERENCE | STUDY only. GULA's LIMS is further along than adopting this would leave it |
| **OpenHIM** | MPL-2.0 | `B` | yes | USE_AS_REFERENCE | STUDY the OpenHIE component pattern — it is the closest published architecture to what GULA's national layer needs |
| **CommCare** | BSD (HQ), Apache-2.0 (Android client) | `A` | yes | USE_AS_REFERENCE | STUDY its offline sync and conflict model; GULA keeps its own edge agent |
| **Orthanc** | GPLv3+ (core), AGPLv3+ (some plugins) | `C` | yes | INTEGRATE | INTEGRATE as a separate service over DICOMweb only. Never link, never embed, never fork into the repository |
| **dcm4che / dcm4chee** | MPL-1.1 / GPL-2.0 / LGPL-2.0 triple | `B` | yes | INTEGRATE | Alternative to Orthanc if a full archive is needed; heavier |
| **OpenEMR** | GPL | `C` | yes | USE_AS_REFERENCE | STUDY only. GPL makes code reuse incompatible with GULA's licensing posture; PHP stack is a poor fit |
| **Open-source blood bank projects (GitHub topic)** | Mixed, mostly MIT on student projects | `E` | **no** | REJECT | REJECT. GULA's blood bank is materially ahead of what is publicly available |
| **WebEMS** | UNKNOWN | `E` | **no** | USE_AS_REFERENCE | STUDY the NEMSIS data model. Do not adopt code with an unverified licence |
| **Gula Health (commercial, unrelated)** | Proprietary | `D` | **no** | USE_AS_REFERENCE | STUDY publicly observable product patterns only, once the site can actually be read. No relationship of any kind exists  |

## Licence hazards worth stating explicitly

- **Orthanc is GPLv3+, and some plugins are AGPLv3+.** Running it as a separate process that
  GULA talks to over DICOMweb is mere aggregation and imposes nothing. Linking to it, or
  embedding an AGPL plugin, would — and AGPL reaches network use, not just distribution.
- **Snowstorm's Apache-2.0 covers the code, not the content.** SNOMED CT terminology is
  licensed separately through SNOMED International. Iraq's member status is **UNKNOWN** and
  must be confirmed by a person before any terminology work starts.
- **MPL-2.0 (OpenMRS, OpenELIS, OpenHIM) is file-level copyleft.** Reading the design is free;
  any file copied in stays MPL and must be published as such.
- **OpenEMR is GPL.** Studying it is fine. Copying from it would relicense GULA.
- **WebEMS's licence could not be established.** The NEMSIS *data model* is the valuable part
  and carries no such risk.

## Gula Health

Evaluated only as a product benchmark, at the user's request. **No relationship of any kind
exists or is implied between Gula Health and the GULA Platform; the name similarity is
coincidental.** The site is blocked by this environment's egress proxy, so nothing beyond a
search-result description of its stated mission could be read. Its capabilities are recorded
as **UNVERIFIED** rather than guessed at, and no technical architecture has been inferred.

