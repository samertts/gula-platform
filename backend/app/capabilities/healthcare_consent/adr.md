# ADR-0009: Healthcare_consent Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** identity_security
- **Layer:** application
- **Owner:** platform-team

## Context

Healthcare-specific consent: patient privacy preferences, access policies, break-glass emergency override, purpose of use enforcement, granular data sharing controls

## Decision

Build the healthcare_consent capability as a reusable platform capability.

## Consequences

- Enables consistent healthcare-specific consent: patient privacy preferences, access policies, break-glass emergency override, purpose of use enforcement, granular data sharing controls across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
