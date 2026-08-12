# ADR-0002: Workflow_engine Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** infrastructure
- **Layer:** application
- **Owner:** platform-team

## Context

Generic workflow engine: approvals, states, transitions, business rules, timers, escalations, notifications, audit trail

## Decision

Build the workflow_engine capability as a reusable platform capability.

## Consequences

- Enables consistent generic workflow engine: approvals, states, transitions, business rules, timers, escalations, notifications, audit trail across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
