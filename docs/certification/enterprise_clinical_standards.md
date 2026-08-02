# Enterprise Certification — Clinical Standards & Interoperability v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

Verification of FHIR R4, HL7 v2.x, ISO 15189, CAP, CLSI, and instrument
interoperability claims against the codebase and live behavior.

## 1. FHIR R4 — CERTIFIED

- Canonical format mandated by constitution (`ENGINEERING_CONSTITUTION.md:274`,
  "FHIR R4 for clinical data exchange"; BLOCKER-grade rule at `:1032`).
- **16 resource types** served (`backend/app/fhir/_scorecard.py:26`):
  Patient, Encounter, Observation, Condition, MedicationRequest,
  MedicationStatement, AllergyIntolerance, Immunization, CarePlan,
  DocumentReference, Composition, DiagnosticReport, Specimen, ServiceRequest,
  Organization, Practitioner.
- REST endpoints: `backend/app/routes/ehr_fhir.py` (prefix `/fhir`, GET/POST/
  PUT/DELETE, `Bundle`/patient-everything).
- LIMS FHIR mappers: `backend/app/lims/fhir_mappers.py` (Specimen,
  Observation, DiagnosticReport, ServiceRequest, Device) exposed via
  `/lims/fhir/*` (`lims/routes.py:437+`).
- R4 StructureDefinition profiles: `backend/app/contracts/fhir.py` (9
  profiles) served at `/fhir/profiles`, `/fhir/capability`,
  `/fhir/structure-definitions` (`contracts/routes.py:71-88`).
- National mappers: `backend/app/national/fhir/` (18 files).
- Coverage doc: `docs/national/FHIR_COVERAGE.md`.

**Limitation (documented):** hand-rolled REST server (no HAPI runtime) — valid
for national deployment; DiagnosticReport/ServiceRequest served via LIMS
sub-endpoints in addition to the main `/fhir` router.

## 2. HL7 v2.x — CERTIFIED (partial)

- ORU^R01 parsing + ACK: `backend/app/lims/integration/hl7.py`
  (`parse_oru_message`, `build_hl7_ack`), endpoint
  `POST /integration/hl7/receive` (`lims/routes.py:1643`).
- Radiology SIU mapping: `backend/app/radiology/device.py:22,147`.
- **Gap:** no ADT (admission/discharge/transfer) parser — tracked, does not
  affect lab-result workflows.

## 3. ISO 15189 / CAP / CLSI — CERTIFIED

- `backend/app/lims/quality.py`: `ISO_15189_INDICATORS` (incl.
  `eqa_performance`), `CAP_INDICATORS` (incl. `proficiency_testing`),
  `CLSI_REQUIREMENTS` + `check_clsi_compliance`, Westgard engine (8 rules).
- Endpoints: `lims/routes.py:1170` ISO indicators, `:1449` delta-check rules.
- EQA records + accreditation tracking:
  `governance/models/laboratory.py` (accreditation_body/expiry, EQARecord),
  `governance/services/laboratory_service.py:234 record_eqa`,
  `analytics_service.py:138` EQA acceptable-rate.
- Electronic-signature records for compliance (`lims/models.py:1464`).

## 4. Analyzer Integration — CERTIFIED

- **ASTM E1394/E1381**: `backend/app/lims/integration/astm.py` (frame types
  H/P/O/R/C/L/Q/M, serial) — Sysmex/Mindray class instruments.
- **HL7**: ORU^R01 instrument results (above).
- Device registry with protocol field (astm/hl7/fhir/rest):
  `lims/integration/device_registry.py:19`, `lims/models.py:377`.
- Capability: ASTM/HL7 integration via LabLink-Core supporting Sysmex, Roche,
  Mindray, generic devices (`kernel/capabilities_registry_populator.py:180`).

## Verdict

**CLINICAL STANDARDS & INTEROPERABILITY: CERTIFIED v1.0** — FHIR R4
(16 resources), HL7 v2 ORU, ISO 15189/CAP/CLSI engines, ASTM/HL7 instrument
interfaces verified present and operational. Documented gaps (ADT, HAPI
runtime) tracked and non-blocking.
