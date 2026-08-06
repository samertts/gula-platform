# RFC Workflow (Pre-KUP Review)

**Mission:** GAIOS-MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Before creating a Knowledge Update Proposal (KUP), significant knowledge
changes must go through an RFC (Request for Comments) phase. This allows
broader review BEFORE formal proposal.

---

## When RFC is Required

| Change Type | RFC Required |
|---|---|
| New capability | YES |
| New decision | YES |
| Architecture change | YES |
| Security change | YES |
| Constitution change | YES |
| New skill | NO (KUP only) |
| New playbook | NO (KUP only) |
| Minor update | NO (KUP only) |
| Bug fix documentation | NO (KUP only) |

---

## RFC Workflow

```
Task Identified
    ↓
Evidence Collected
    ↓
RFC Created (.ai/core/kup/RFC-NNNNNN.md)
    ↓
Open for Comments (7 days max)
    ↓
Comments Addressed
    ↓
RFC Accepted/Rejected
    ↓
KUP Created (if accepted)
    ↓
KUP Workflow (standard)
```

---

## RFC Template

```markdown
---
id: RFC-NNNNNN
type: rfc
title: "[Title]"
version: "1.0.0"
created: "[Date]"
status: Draft
author: "[Author]"
tags: [rfc, knowledge, governance]
---

# RFC-NNNNNN: [Title]

## Summary
[1-2 sentence summary]

## Motivation
[Why this change is needed]

## Proposed Change
[What exactly will change]

## Alternatives Considered
[What other options were evaluated]

## Impact Assessment
- Affected modules: [list]
- Affected knowledge: [list]
- Risk level: [LOW/MEDIUM/HIGH]
- Reversibility: [EASY/HARD/IMPOSSIBLE]

## Evidence
[Supporting evidence for the change]

## Open Questions
[Questions for reviewers]

## Timeline
- RFC opened: [Date]
- Comments due: [Date + 7 days]
- Decision: [Date]

## References
- Related ADR: [list]
- Related Skills: [list]
- Related Playbooks: [list]
```

---

## RFC Review Process

1. **Author** creates RFC with evidence
2. **Reviewers** comment within 7 days
3. **Author** addresses comments
4. **Decision** made: Accept/Reject/Defer
5. **If Accepted:** Create KUP, follow standard workflow
6. **If Rejected:** Document reason, archive RFC
7. **If Deferred:** Set new review date

---

## RFC Status

| ID | Title | Status | Author |
|---|---|---|---|
| (none yet) | | | |

---

## Rules

1. **Never skip RFC** for significant changes
2. **Always provide evidence** with RFC
3. **Always address comments** before decision
4. **Always document decision** with reasoning
5. **Always archive** rejected RFCs

---

## References

- `.ai/core/kup/README.md` — KUP system
- `.ai/core/kup/KUP_TEMPLATE.md` — KUP template
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
