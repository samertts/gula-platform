# Documentation Rules

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Comprehensive documentation requirements for the GULA Platform.
Every major implementation updates documentation.

---

## Required Documentation by Change Type

| Change Type | Required Documentation |
|---|---|
| New feature | README, API docs, ADR if architectural |
| Bug fix | Failure record, lesson learned |
| Architecture change | ADR, architecture docs, migration plan |
| Security change | Security docs, ADR, risk assessment |
| Database change | Migration docs, schema docs |
| API change | API docs, OpenAPI spec |
| Deployment change | Deployment docs, runbook |
| Configuration change | Config docs, README |

---

## Documentation Standards

### Format
- **Primary:** Markdown
- **Code:** Inline comments (minimal)
- **API:** OpenAPI (auto-generated)
- **Diagrams:** Mermaid or ASCII

### Structure
- Title with purpose
- Prerequisites (if applicable)
- Step-by-step instructions
- Examples
- Troubleshooting
- References

### Quality
- Accuracy verified
- Examples tested
- Links validated
- No duplicates

---

## Documentation Locations

| Type | Location |
|---|---|
| Architecture | `docs/architecture/` |
| ADR | `docs/adr/` |
| API | OpenAPI spec (auto-generated) |
| Security | `docs/security/` |
| Runbooks | `docs/runbooks/` |
| Deployment | `docs/deployment/` |
| Knowledge | `.ai/core/` |

---

## Freshness Rules

| Document Type | Maximum Age | Review Cadence |
|---|---|---|
| Architecture | 6 months | Quarterly |
| ADR | Never expires | On change |
| API docs | 1 month | On release |
| Runbooks | 3 months | Quarterly |
| Knowledge | 1 month | Monthly |

---

## Review Process

1. Author creates documentation
2. Reviewer verifies accuracy
3. Reviewer checks for duplicates
4. Reviewer validates links
5. Documentation merged
6. Registry updated

---

## Rules

1. **Never document without evidence** — Verify before documenting
2. **Never duplicate** — Search before creating
3. **Always cross-reference** — Link related documents
4. **Always version** — Track changes
5. **Always verify** — Test examples before documenting

---

## References

- AI_OPERATING_CONSTITUTION.md — Section 5.9
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
