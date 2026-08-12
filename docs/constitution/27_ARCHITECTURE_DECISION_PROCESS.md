# GULA Architecture Decision Process

## Purpose

The Architecture Decision Process ensures that every significant architectural change is deliberate, documented, reviewed, and aligned with the Constitution. It prevents ad-hoc decisions that accumulate into technical debt.

## What Requires an ADR

- Introduction of a new technology, framework, or library
- Database schema changes that affect multiple domains
- API version changes
- New integration patterns or protocols
- Security architecture changes
- Changes to the authentication or authorization model
- Changes to the deployment architecture
- Changes to the testing strategy
- Any decision with long-term maintenance implications

## ADR Template

```markdown
# ADR-{NNN}: {Title}

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
What is the issue motivating this decision? What forces are at play?

## Decision
What is the change being proposed? What will be different after implementation?

## Consequences
What becomes easier? What becomes harder? What trade-offs are being made?

## Compliance
How will compliance with this decision be verified?

## References
- Constitution sections
- Related ADRs
- External references
```

## Decision Flow

```
                    ┌─────────────┐
                    │  Proposal   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Triage by  │
                    │ Architecture│
                    │    Board    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼────┐ ┌─────▼────┐
        │  Minor   │ │Standard │ │  Major   │
        │ (Fast    │ │ (Review)│ │(Full     │
        │  Track)  │ │         │ │ Board)   │
        └─────┬────┘ └────┬────┘ └─────┬────┘
              │           │            │
        ┌─────▼────┐ ┌────▼────┐ ┌─────▼────┐
        │ Quick    │ │ 7-day   │ │ 14-day   │
        │ Review   │ │ Review  │ │ Deep Dive│
        └─────┬────┘ └────┬────┘ └─────┬────┘
              │           │            │
        ┌─────▼───────────▼────────────▼────┐
        │         Final Decision           │
        │   (Approve / Approve with Cond.  │
        │          / Defer / Reject)       │
        └────────────────┬─────────────────┘
                         │
                    ┌────▼────┐
                    │Document │
                    │& Close  │
                    └─────────┘
```

## Review Cadence

- **Architecture Board** meets bi-weekly
- **Emergency decisions** may be made asynchronously with 48-hour review window
- **Quarterly deep dive** on architecture health, technical debt, and roadmap alignment

## ADR Lifecycle

1. **Draft** — Author writes the ADR
2. **Proposed** — Submitted for review
3. **Accepted** — Approved by Architecture Board
4. **Implemented** — Code changes deployed
5. **Superseded** — Replaced by a newer ADR
6. **Deprecated** — No longer relevant

## ADR Storage

ADRs are stored in `docs/architecture/decisions/` with the naming convention `NNN-title.md`. A `README.md` serves as the index.
