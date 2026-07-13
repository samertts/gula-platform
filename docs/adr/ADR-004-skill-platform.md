# ADR-004: Skill Platform Architecture

**Status:** Accepted
**Date:** 2026-07-06
**Deciders:** Engineering Lead, AI Team

## Context

GULA requires an extensible system for adding AI capabilities and automation without modifying the core platform code. Each capability (clinical interpretation, anomaly detection, population health, etc.) should be self-contained.

## Decision

Adopt a skill-based plugin architecture where:
- Skills are independent, self-contained modules with defined interfaces
- The Kernel manages skill lifecycle (registration, isolation, lifecycle)
- Skills communicate through the event bus
- Skills are loaded at runtime from the `skills/` directory
- Each skill has declarative permissions and resource limits

## Alternatives Considered

- **Hardcoded AI features** — Rejected as not extensible
- **Microservices for each skill** — Rejected due to operational overhead

## Consequences

Positive:
- Extensible architecture for AI capabilities
- Clear isolation between skills
- Runtime loading without deployment

Negative:
- Requires Kernel infrastructure for lifecycle management
- Skill isolation adds complexity

## References

- `backend/app/kernel/` — Kernel implementation
- `backend/app/skills/` — Skill definitions
