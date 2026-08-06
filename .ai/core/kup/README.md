# Knowledge Update Proposals (KUP)

**Mission:** GAIOS-002 Phase 8.5
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

No engineering knowledge becomes permanent automatically.
Every newly generated knowledge artifact must first become a
Knowledge Update Proposal (KUP) with status: Proposed.

---

## Status Flow

```
Proposed → Under Review → Approved/Rejected → Merged → Archived
```

| Status | Description |
|---|---|
| Proposed | KUP created, awaiting review |
| Under Review | Being evaluated by reviewer |
| Approved | Accepted for merge |
| Rejected | Not accepted (with explanation) |
| Merged | Applied to knowledge base |
| Archived | Historical record |

---

## KUP Registry

| ID | Title | Status | Date |
|---|---|---|---|
| KUP-000001 | GAIOS-002 Knowledge System | Proposed | 2026-08-04 |
| KUP-000002 | AI Constitution (CONST-000001) | Approved | 2026-08-04 |
| KUP-000003 | AI Bootstrap (AI_BOOTSTRAP.md) | Approved | 2026-08-04 |

---

## Template

Each KUP must contain:

```markdown
---
id: KUP-NNNNNN
type: kup
title: "[Title]"
version: "1.0.0"
created: "[Date]"
status: Proposed
confidence: [0-100]%
tags: [kup, knowledge, governance]
---

# KUP-NNNNNN: [Title]

## Summary
[1-2 sentence summary of the knowledge change]

## Motivation
[Why this knowledge is needed]

## Evidence
[Proof that this knowledge is correct]

## Affected Knowledge
[List all files that will be created or modified]

## Related Skills
[Skills related to this knowledge]

## Related Playbooks
[Playbooks related to this knowledge]

## Related ADR
[Architecture decisions related to this knowledge]

## Related Architecture
[Architecture components related to this knowledge]

## Confidence
[0-100%] — How confident are we in this knowledge?

## Risk Assessment
[What risks does this knowledge introduce?]

## Compatibility Analysis
[Does this conflict with existing knowledge?]

## Reviewer
[Who reviews this?]

## Approval Status
[Proposed/Under Review/Approved/Rejected]

## Creation Date
[When was this created?]

## Version History
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0.0 | [Date] | [Author] | Initial proposal |
```

---

## Rules

1. **Never update directly** — Every permanent knowledge modification requires approval
2. **Never skip review** — No knowledge bypasses the KUP workflow
3. **Never duplicate** — Search before creating
4. **Always version** — Increment version on changes
5. **Always document** — Record what changed and why
6. **Always verify** — Check existing knowledge first

---

## References

- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
- `.ai/core/quality/SELF_IMPROVEMENT.md` — Self-improvement protocol
- `.ai/core/registry/REGISTRY.md` — Knowledge registry
- `.ai/core/graph/README.md` — Knowledge graph
