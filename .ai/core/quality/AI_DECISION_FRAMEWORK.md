# AI Decision Framework

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Formal framework for AI decision-making. Defines criteria, weights,
escalation paths, and tie-breaking rules for all engineering decisions.

---

## Decision Criteria

| Criterion | Weight | Description |
|---|---|---|
| Correctness | 25% | Does it work correctly? |
| Maintainability | 20% | Is it easy to maintain? |
| Scalability | 15% | Will it scale? |
| Security | 15% | Is it secure? |
| Performance | 10% | Is it performant? |
| Reversibility | 10% | Can it be undone? |
| Cost | 5% | What is the cost? |

---

## Decision Matrix

For each alternative, score 0-10 on each criterion:

```
Score = (Correctness × 0.25) + (Maintainability × 0.20) +
        (Scalability × 0.15) + (Security × 0.15) +
        (Performance × 0.10) + (Reversibility × 0.10) +
        (Cost × 0.05)
```

**Choose highest score.**

---

## Escalation Matrix

| Decision Type | Authority | Approval |
|---|---|---|
| Minor bug fix | AI Agent | No |
| New feature | AI Agent | KUP required |
| Architecture change | Tech Lead | RFC + Approval |
| Security change | Security Lead | RFC + Approval |
| Constitution change | Project Owner | Explicit Approval |
| Data deletion | Project Owner | Explicit Approval |
| License change | Project Owner | Explicit Approval |

---

## Tie-Breaking Rules

When alternatives have equal scores:

1. **Security wins** — Choose more secure option
2. **Reversibility wins** — Choose easier to undo
3. **Simplicity wins** — Choose simpler option
4. **Open source wins** — Choose open source option
5. **Escalate** — If still tied, escalate to human

---

## Reversibility Assessment

| Level | Description | Example |
|---|---|---|
| EASY | Can be undone with git revert | Code change |
| HARD | Requires migration but possible | Schema change |
| IMPOSSIBLE | Cannot be undone | Data deletion |

**Prefer EASY > HARD > IMPOSSIBLE**

---

## Decision Documentation

Every decision must document:

1. **Context** — What situation required decision
2. **Alternatives** — What options were considered
3. **Criteria** — What factors were evaluated
4. **Scores** — How each alternative scored
5. **Choice** — What was chosen
6. **Reasoning** — Why this choice won
7. **Reversibility** — How to undo if needed
8. **Review date** — When to revisit

---

## Search Before Deciding

Before making any decision, search:

1. Constitution (AI_OPERATING_CONSTITUTION.md)
2. Bootstrap (AI_BOOTSTRAP.md)
3. ADR (docs/adr/)
4. Architecture (docs/architecture/)
5. Memory (.ai/core/memory/)
6. Skills (.ai/core/skills/)
7. Playbooks (.ai/core/playbooks/)
8. Runbooks (.ai/core/runbooks/)
9. Decisions (.ai/core/decisions/)
10. Failures (.ai/core/failures/)
11. Git history
12. Existing code

**Only then investigate externally.**

---

## References

- AI_OPERATING_CONSTITUTION.md — Section 3.6 (Decision Model)
- `.ai/core/decisions/` — Decision registry
- `docs/adr/` — Architecture Decision Records
