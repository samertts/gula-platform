# ADR-001: Engineering Constitution as Root Authority

**Status:** Accepted
**Date:** 2026-07-06
**Deciders:** Engineering Lead, Architecture Committee

## Context

The GULA Platform lacked a single authoritative document governing engineering decisions. Multiple undocumented conventions led to inconsistent implementations across repositories.

## Decision

Adopt the Engineering Constitution as the root authority for all engineering decisions. The Constitution defines:
- Core values and principles
- Decision-making framework
- Architecture governance
- Quality standards and enforcement

All ADRs, code reviews, and architectural decisions must be consistent with the Constitution.

## Alternatives Considered

- **Informal conventions** — Rejected due to inconsistency
- **External framework (TOGAF, SAFe)** — Rejected as too heavyweight for the team size

## Consequences

Positive:
- Single source of truth for engineering decisions
- Clear criteria for code review and architecture approval

Negative:
- Constitution must be maintained and updated as the platform evolves

## References

- CLAUDE.md (engineering handbook)
