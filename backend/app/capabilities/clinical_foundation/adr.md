# ADR-0007: Clinical_foundation Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** clinical
- **Layer:** application
- **Owner:** platform-team

## Context

Clinical data foundation: diagnoses, problems, allergies, medications, procedures, observations, vitals, immunizations, clinical history

## Decision

Build the clinical_foundation capability as a reusable platform capability.

## Consequences

- Enables consistent clinical data foundation: diagnoses, problems, allergies, medications, procedures, observations, vitals, immunizations, clinical history across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
