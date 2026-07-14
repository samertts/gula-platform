# ADR-0003: Search_service Capability

- **Status:** proposed
- **Date:** 2026-07-14
- **Domain:** infrastructure
- **Layer:** application
- **Owner:** platform-team

## Context

Unified search platform: full-text search across patients, orders, results, documents with filters, ranking, suggestions, indexing, permissions-aware

## Decision

Build the search_service capability as a reusable platform capability.

## Consequences

- Enables consistent unified search platform: full-text search across patients, orders, results, documents with filters, ranking, suggestions, indexing, permissions-aware across all platform modules
- Adds 1 new capability to the Capability Registry
- Requires integration with Kernel lifecycle management

## Compliance

- [ ] Registered in CapabilityRegistry
- [ ] All quality gates pass
- [ ] OpenAPI specification generated
- [ ] ADR documented
- [ ] Tests written and passing
