# Technical Debt Registry

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Track known technical debt. Debt must never be hidden.
Every known debt gets a permanent immutable ID.

---

## Registry

| ID | Description | Impact | Priority | Risk | Status |
|---|---|---|---|---|---|
| DEBT-000001 | Knowledge graph ASCII only | Low queryability | MEDIUM | LOW | Open |
| DEBT-000002 | 62 backref= in inactive contexts | Maintenance burden | LOW | LOW | Open |
| DEBT-000003 | mypy times out on full codebase | No full type check | MEDIUM | MEDIUM | Open |
| DEBT-000004 | Docker compose v1 broken in WSL | No multi-container orchestration | LOW | LOW | Open |
| DEBT-000005 | 379 ruff violations (E402/N801/N999) | Lint noise | LOW | LOW | Open |
| DEBT-000006 | No CI integration for knowledge validation | Manual maintenance | MEDIUM | MEDIUM | **Resolved** (PROGRAM-AUTOMATION-001) |
| DEBT-000007 | ADR number collisions (011, 012, 013) | Confusion risk | LOW | LOW | Open |
| DEBT-000008 | Near-duplicate files in constitution/ | Maintenance burden | LOW | LOW | Open |
| DEBT-000009 | 518 debt findings (dead docs, unreferenced knowledge) | Knowledge clutter | MEDIUM | LOW | Open |

---

## Template

```markdown
| ID | Description | Impact | Priority | Risk | Status |
|---|---|---|---|---|---|
| DEBT-NNNNNN | [Description] | [Impact] | [LOW/MEDIUM/HIGH] | [LOW/MEDIUM/HIGH] | [Open/In Progress/Resolved] |
```

---

## Debt Fields

| Field | Description |
|---|---|
| ID | DEBT-NNNNNN |
| Description | What is the debt |
| Impact | How it affects the system |
| Priority | LOW/MEDIUM/HIGH |
| Risk | Risk if not addressed |
| Estimated Cost | Effort to resolve |
| Recommended Resolution | How to fix |
| Status | Open/In Progress/Resolved |
| Discovered | When it was found |
| Related ADR | Related architecture decisions |

---

## Priority Levels

| Level | Description | Response Time |
|---|---|---|
| HIGH | Critical debt, blocking | Immediate |
| MEDIUM | Significant debt | Next sprint |
| LOW | Minor debt | Backlog |

---

## Rules

1. **Never hide debt** — Every known debt gets an entry
2. **Always document** — Description, impact, resolution
3. **Always track** — Status changes tracked
4. **Never ignore** — Debt must be addressed or explicitly deferred

---

## Related Knowledge

- `.ai/core/failures/` — Resolved failures
- `.ai/core/quality/STABILITY_POLICY.md` — Stability policy
- `.ai/core/quality/RISK_MANAGEMENT.md` — Risk management

---

## References

- `.ai/core/registry/REGISTRY.md` — Knowledge registry
