# FHIR/HL7 Interoperability Capability

**Domain:** integration
**Layer:** infrastructure
**Version:** 1.1.0

## Purpose

This capability is GULA's original interoperability boundary. It provides a small, typed FHIR R4 resource registry and a deterministic synthetic HL7 v2 `ORU^R01` converter. It borrows public standards and architectural patterns from projects such as HAPI FHIR, Medplum, and OpenHIM, but contains no copied source code or user interface.

## Tenant and safety boundary

All resource reads and writes are scoped by the authenticated institutional user's `lab_id`. Citizen accounts are rejected by the backend before service execution. The converter never persists the raw HL7 message, opens a socket, or connects to a laboratory analyzer; it returns a synthetic Bundle marked `simulationOnly: true`. A real adapter must run behind the separately governed Gateway and must pass the same tenant, certificate, audit, and allowlist controls.

## API

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/fhir-interoperability/health/` | Public health check | Capability liveness |
| GET | `/fhir-interoperability/metadata` | Public metadata | Supported resource types and FHIR version |
| GET | `/fhir-interoperability/` | Institutional `lab:read` | List supported resource types |
| POST | `/fhir-interoperability/resources` | Institutional `lab:manage` | Store a validated resource in the current lab |
| GET | `/fhir-interoperability/resources/{resource_type}` | Institutional `lab:read` | Tenant-scoped searchset Bundle |
| GET | `/fhir-interoperability/resources/{resource_type}/{resource_id}` | Institutional `lab:read` | Tenant-scoped resource read |
| POST | `/fhir-interoperability/hl7/convert` | Institutional `lab:manage` | Convert synthetic `ORU^R01` to a FHIR Bundle |

The first supported resource set is `Patient`, `Encounter`, `Observation`, `DiagnosticReport`, `Specimen`, `ServiceRequest`, `MedicationRequest`, `Practitioner`, and `Organization`. The registry uses a composite uniqueness key `(lab_id, resource_type, resource_id, version)`, allowing independent institutions to use the same local resource identifier without cross-tenant visibility.

## Public-project influence and implementation rule

The implementation uses standards and capability ideas only. HAPI FHIR and Medplum informed resource-oriented contracts; OpenHIM informed the mediator boundary; OpenELIS informed the future laboratory event mapping. GULA does not copy their code, visual design, database schema, or proprietary deployment assumptions. Each future dependency requires a separate SPDX/license, SBOM, security, and operational review.

## Events and commands

The capability retains the platform event vocabulary `FhirResourceCreated`, `Hl7MessageReceived`, and `TerminologyUpdated`, and the commands `convert_to_fhir`, `convert_from_hl7`, and `validate_resource`. The current HTTP boundary exposes only deterministic, synthetic operations; asynchronous delivery and real protocol adapters remain Gateway work.

## License

Proprietary — GULA Platform. External projects are references only and remain subject to their own licenses; no external source code is included by this capability.
