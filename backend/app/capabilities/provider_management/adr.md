# ADR-0005: Provider_management Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** clinical
- **Layer:** application
- **Owner:** platform-team

## Context

Healthcare provider management: doctors, nurses, technicians, pharmacists, licensing, specialties, schedules, availability, permissions

## Decision

Build the provider_management capability as a reusable platform capability.

## Consequences

- Enables consistent healthcare provider management: doctors, nurses, technicians, pharmacists, licensing, specialties, schedules, availability, permissions across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
