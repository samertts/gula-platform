# ADR-0004: Reporting_service Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** reporting
- **Layer:** application
- **Owner:** platform-team

## Context

Enterprise reporting: dashboards, charts, PDF reports, Excel exports, CSV exports, scheduled reports, distribution via email

## Decision

Build the reporting_service capability as a reusable platform capability.

## Consequences

- Enables consistent enterprise reporting: dashboards, charts, pdf reports, excel exports, csv exports, scheduled reports, distribution via email across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
