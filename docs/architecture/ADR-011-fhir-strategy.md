# ADR-011: FHIR Strategy

**Status:** Accepted
**Date:** 2026-07-18
**Constitutional Basis:** ENGINEERING_CONSTITUTION.md §14.1, PLATFORM-CONSTITUTION.md §3.3

## Context

The Platform Constitution mandates FHIR content-type on every clinical endpoint, and the Engineering Constitution requires "all clinical data exchange via FHIR R4." However, the existing API uses custom JSON schemas for internal operations and FHIR R4 only for the EHR interoperability endpoints (`/ehr/fhir`). A deployment model is needed that balances constitutional compliance with practical API design.

## Decision

Adopt a **dual-model strategy**: internal API uses canonical GULA JSON schemas, while all external clinical data exchange uses FHIR R4.

| Interface | Format | Purpose |
|-----------|--------|---------|
| Internal API (routes) | GULA JSON | Lab operations, dashboard, internal workflows |
| EHR Bridge (`/ehr/fhir`) | FHIR R4 | Hospital/ministry interoperability |
| Device Bridge | ASTM/HL7 → FHIR | Lab instrument data normalized to FHIR |
| Patient-facing APIs | GULA JSON + FHIR export | QR cards, citizen portal, data portability |

### Endpoints

- `GET /ehr/fhir/Patient/{id}` — FHIR Patient resource
- `GET /ehr/fhir/Observation/{id}` — FHIR Observation (lab results)
- `GET /ehr/fhir/DiagnosticReport/{id}` — FHIR DiagnosticReport
- `GET /patients/{id}/fhir` — FHIR export for a patient
- `Content-Type: application/fhir+json` on FHIR endpoints

## Rationale

- FHIR R4 is the constitutional mandate for clinical data exchange
- Internal custom JSON is more efficient for lab-specific workflows (batch operations, Arabic-first fields, lab-specific metadata)
- Dual model avoids forcing FHIR on every internal operation while satisfying the constitutional requirement for clinical exchange
- FHIR endpoints are versioned and independently deployable

## Consequences

- All new clinical exchange endpoints MUST support FHIR R4
- Internal APIs continue using custom JSON schemas
- The EHR bridge (`backend/app/routes/ehr_fhir.py`) is the canonical FHIR implementation
- FHIR resource mappings are documented in `docs/fhir/`
- Non-FHIR clinical endpoints must be evaluated for FHIR conversion on a case-by-case basis
- Content negotiation (Accept header) may be added in the future to serve FHIR from internal endpoints

## Compliance

- All external clinical data exchange uses FHIR R4
- Internal endpoints are exempt from FHIR content-type requirement
- FHIR endpoint coverage is tracked in the technical debt registry
- New clinical exchange integrations default to FHIR R4
