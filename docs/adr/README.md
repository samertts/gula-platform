# Architecture Decision Records

**GULA Platform — Medical Laboratory SaaS**
**Constitution Reference:** Section 7

---

## What is an ADR?

An Architecture Decision Record (ADR) captures a significant architectural decision along with its context and consequences. ADRs are immutable once accepted — they record what was decided and why, not what is currently true.

## When to Write an ADR

Write an ADR when:

- Choosing a technology or framework
- Defining an architectural pattern
- Establishing a security or data policy
- Making a decision that affects the whole system
- Deciding against an alternative (record what was rejected and why)

Do not write an ADR for:

- Minor code changes
- Bug fixes
- Configuration tweaks
- Temporary workarounds

## ADR Process

1. **Draft** — Create a new ADR file using the template below
2. **Discuss** — Share with the team for feedback
3. **Decide** — Engineering Lead approves or rejects
4. **Record** — Update the index below
5. **Implement** — Apply the decision to the codebase

## ADR Template

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD
**Deciders:** List of people involved

## Context

What is the situation that requires a decision?

## Decision

What was decided?

## Alternatives Considered

What other options were evaluated?

## Consequences

What are the positive and negative outcomes?

## References

Links to related ADRs, Constitution sections, or code.
```

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](ADR-001-engineering-constitution.md) | Engineering Constitution as Root Authority | Accepted | 2026-07-06 |
| [ADR-002](ADR-002-monolith-first.md) | Monolith First Architecture | Accepted | 2026-01-01 |
| [ADR-003](ADR-003-multi-tenant-isolation.md) | Multi-Tenant Isolation via lab_id | Accepted | 2026-01-01 |
| [ADR-004](ADR-004-skill-platform.md) | Skill Platform Architecture | Accepted | 2026-07-06 |
| [ADR-005](ADR-005-postgresql-redis-stack.md) | PostgreSQL 16 with Redis 7 | Accepted | 2026-07-08 |
| [ADR-006](ADR-006-clinical-ai-integration.md) | Clinical AI Integration | Accepted | 2026-07-08 |
| [ADR-007](ADR-007-device-bridge-astm-hl7.md) | Device Bridge ASTM/HL7 | Accepted | 2026-07-08 |
| [ADR-008](ADR-008-patient-card-system.md) | Patient Card System | Accepted | 2026-07-08 |
| [ADR-009](ADR-009-self-healing-infrastructure.md) | Self-Healing Infrastructure | Accepted | 2026-07-08 |
| [ADR-010](ADR-010-sndhs-government-integration.md) | SNDHS-lite Government Integration | Accepted | 2026-07-08 |

## Constitution Reference

Section 7 of the Engineering Constitution establishes ADRs as the record of architectural decisions. All significant architectural decisions must be captured as ADRs before implementation.
