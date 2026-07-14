# ADR-0006: Encounter_management Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** clinical
- **Layer:** application
- **Owner:** platform-team

## Context

Clinical encounter management: outpatient, emergency, inpatient, home visit, telemedicine, referral, admission, discharge, transfer, clinical notes

## Decision

Build the encounter_management capability as a reusable platform capability.

## Consequences

- Enables consistent clinical encounter management: outpatient, emergency, inpatient, home visit, telemedicine, referral, admission, discharge, transfer, clinical notes across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
