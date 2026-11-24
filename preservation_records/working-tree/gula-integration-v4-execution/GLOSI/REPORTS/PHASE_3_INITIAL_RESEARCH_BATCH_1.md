# GLOSI Phase 3 — Initial Research Batch B1

**Date:** 2026-11-15
**Status:** PARTIAL
**Scope:** Source, version, license, and maintenance verification for 16 projects. No numeric scoring and no adoption.

## 1. Result summary

- 16 records created (`GLOSI-0001`–`GLOSI-0016`) with 16 proposed decision records.
- 16/16 repository metadata sources verified.
- All evaluations are `PARTIAL` / confidence `LOW`.
- All decisions are proposed: `STUDY` (10) or `MONITOR` (6).
- No record is approved, integrated, or adopted.

## 2. Verified records

| ID | Project | Latest verified version | License | Proposed decision | Evaluation |
|---|---|---|---|---|---|
| GLOSI-0001 | OpenELIS Global | 3.3.0 | MPL-2.0 | STUDY | PARTIAL |
| GLOSI-0002 | SENAITE | v2.6.0 | GPL-2.0 | STUDY | PARTIAL |
| GLOSI-0003 | OpenMRS | 2.8.10 | MPL-2.0 | MONITOR | PARTIAL |
| GLOSI-0004 | Bahmni | 1.3.0 | MPL-2.0 | MONITOR | PARTIAL |
| GLOSI-0005 | DHIS2 | 43.2.1 (security hotfix) | BSD-3-Clause | STUDY | PARTIAL |
| GLOSI-0006 | SORMAS | v1.104.0 | GPL-3.0 | MONITOR | PARTIAL |
| GLOSI-0007 | OpenHIE | UNKNOWN (no tagged release verified) | MPL-2.0 | STUDY | PARTIAL |
| GLOSI-0008 | OpenHIM | v8.5.0 | MPL-2.0 | STUDY | PARTIAL |
| GLOSI-0009 | HAPI FHIR | v8.10.3 | Apache-2.0 | STUDY | PARTIAL |
| GLOSI-0010 | Open Concept Lab (OCL) | 2.3.252 | MPL-2.0 | MONITOR | PARTIAL |
| GLOSI-0011 | Keycloak | 26.8.2 | Apache-2.0 | STUDY | PARTIAL |
| GLOSI-0012 | OpenBao | v2.7.2 | MPL-2.0 | STUDY | PARTIAL |
| GLOSI-0013 | OpenTelemetry Collector | v0.165.0 | Apache-2.0 | MONITOR | PARTIAL |
| GLOSI-0014 | Prometheus | v3.16.0 | Apache-2.0 | MONITOR | PARTIAL |
| GLOSI-0015 | Apache CouchDB | 3.5.3 | Apache-2.0 | STUDY | PARTIAL |
| GLOSI-0016 | Automerge | js/automerge-3.5.0 | MIT | STUDY | PARTIAL |

## 3. Source-verification notes

- **OpenELIS:** verified at `DIGI-UW/OpenELIS-Global-2`; the former repository location is renamed and must not be cited.
- **OpenMRS and Bahmni:** GitHub license API returned `NOASSERTION`; the repository `LICENSE` files were inspected and recorded as MPL-2.0.
- **OpenHIE:** specification/community architecture, recorded as `technical_documentation`; no tagged release verified.
- **OpenHIM:** canonical repository is `jembi/openhim-core-js`; latest verified release is v8.5.0, while repository activity is newer.
- **OCL:** `OpenConceptLab/oclapi` is archived/deprecated; the successor `OpenConceptLab/oclapi2` is recorded.
- **DHIS2:** 43.2.1 is sourced from the official DHIS2 downloads page because GitHub releases are not used.
- **CouchDB:** 3.5.3 is sourced from the official CouchDB download page; GitHub releases returned no releases.
- **GHES/GitHub API:** all metadata retrieved at `2026-11-15T09:48:36Z`; API rate limit was 45 remaining at snapshot start.

## 4. Evidence

- Snapshot: `GLOSI/REPORTS/evidence/phase3_source_verification.json`
- Raw evidence: `/tmp/opencode/glosi/evidence/` (46 files: repository metadata, releases/tags, LICENSE files, official web pages).
- The snapshot includes SHA-256 hashes for every raw evidence file.

## 5. Limitations

- No functional, architectural, security, privacy, performance, or legal review has been completed.
- No dimension score is assigned; `PARTIAL` is intentional and must not be read as a quality judgment.
- Production-usage evidence, CVE review, SBOM review, and maintainer responsiveness remain `UNKNOWN`.
- Legal compatibility with GULA distribution and Iraqi hosting requirements remains unreviewed.

## 6. Phase result

**PARTIAL** — Source metadata is verified for all 16 projects; substantive evaluation and approval are not complete.
