# ADR-0008: Fhir_interoperability Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** integration
- **Layer:** infrastructure
- **Owner:** platform-team

## Context

FHIR/HL7 interoperability: FHIR R4 resources, HL7 v2 messages, LOINC coding, SNOMED CT, ICD-10, ICD-11 ready, UCUM units, IHE profiles, terminology services

## Decision

Build the fhir_interoperability capability as a reusable platform capability.

## Consequences

- Enables consistent fhir/hl7 interoperability: fhir r4 resources, hl7 v2 messages, loinc coding, snomed ct, icd-10, icd-11 ready, ucum units, ihe profiles, terminology services across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
