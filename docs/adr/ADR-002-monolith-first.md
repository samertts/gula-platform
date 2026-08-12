# ADR-002: Monolith First Architecture

**Status:** Accepted
**Date:** 2026-01-01
**Deciders:** Engineering Lead

## Context

GULA started as a microservices architecture with separate services for lab, order, patient, result, and notification domains. This created deployment complexity, debugging difficulty, and development overhead for a small team.

## Decision

Adopt a monolith-first architecture: build the core platform as a single FastAPI application (`backend/app/`) with well-defined internal modules. Microservices boundaries (in `services/`) are preserved for future decomposition but are not the primary deployment target.

## Alternatives Considered

- **Pure microservices** — Rejected due to operational complexity
- **Modular monolith** — Chosen as the middle ground

## Consequences

Positive:
- Simplified deployment (single Docker image)
- Faster development velocity
- Easier debugging and testing
- Shared code in `shared/` library

Negative:
- Requires discipline to maintain module boundaries
- Future decomposition requires extraction effort

## References

- `backend/app/` — Monolith implementation
- `services/` — Future microservice boundaries
