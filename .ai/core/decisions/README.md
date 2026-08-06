# Decision Registry

**Mission:** GAIOS-002 Phase 3
**Created:** 2026-08-04
**Status:** Active
**Registry ID:** DECISION-000001

---

## Purpose

Every engineering decision receives a permanent immutable ID.
Decisions document WHY choices were made, not just WHAT was chosen.

---

## Registry

| ID | Decision | Category | Confidence | ADR |
|---|---|---|---|---|
| DEC-000001 | Monolith-first architecture | Architecture | 95% | ADR-002 |
| DEC-000002 | PostgreSQL as primary DB | Database | 95% | ADR-0005 |
| DEC-000003 | Redis for caching | Infrastructure | 95% | ADR-0005 |
| DEC-000004 | UUID primary keys | Database | 90% | ADR-0009 |
| DEC-000005 | FHIR R4 compliance | Interoperability | 95% | ADR-011 |
| DEC-000006 | CycloneDX SBOM | Security | 90% | ADR-012 |
| DEC-000007 | Custom identity (NIAM) | Security | 85% | ADR-012 |
| DEC-000008 | OpenTelemetry + Jaeger | Observability | 90% | ADR-014 |
| DEC-000009 | PITR + WAL backup | DR | 90% | ADR-015 |
| DEC-000010 | AI Constitution as supreme authority | AI Governance | 95% | CONST-000001 |
| DEC-000011 | Knowledge system at .ai/ | AI Knowledge | 90% | GAIOS-001 |
| DEC-000012 | Bootstrap file as entry point | AI Bootstrap | 95% | GAIOS-002 |

---

## Template

Each decision entry documents:
- **Context:** Situation requiring decision
- **Problem:** What needed to be solved
- **Alternatives:** Options considered
- **Trade-offs:** Pros/cons of each
- **Chosen Solution:** What was decided
- **Reasoning:** Why this choice
- **Consequences:** Expected outcomes
- **Rollback:** How to undo
- **Future Review:** When to revisit
- **Related ADR:** Architecture decision record
- **Confidence:** 0-100%

---

## References

- `docs/adr/` — Architecture Decision Records
- `docs/decisions/` — Aggregated decision docs
- `docs/architecture/` — Architecture documentation
- `.ai/core/registry/REGISTRY.md` — master registry
