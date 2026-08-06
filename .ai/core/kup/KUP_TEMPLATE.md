# KUP Template

Use this template for every Knowledge Update Proposal.

---

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
[Why this knowledge is needed. What problem does it solve?]

## Evidence
[Proof that this knowledge is correct. Include:
- Test results
- Documentation references
- Code examples
- Previous experience]

## Affected Knowledge
[List all files that will be created or modified]
- [ ] File 1: [path] — [change description]
- [ ] File 2: [path] — [change description]

## Related Skills
[List skills related to this knowledge]
- SKILL-NNNNNN: [description]

## Related Playbooks
[List playbooks related to this knowledge]
- PLAYBOOK-NNNNNN: [description]

## Related ADR
[List architecture decisions related to this knowledge]
- ADR-NNN: [title]

## Related Architecture
[List architecture components related to this knowledge]
- [Component]: [relationship]

## Confidence
[0-100]% — How confident are we in this knowledge?

| Factor | Score | Notes |
|---|---|---|
| Evidence quality | [0-100]% | [Notes] |
| Testing coverage | [0-100]% | [Notes] |
| Documentation | [0-100]% | [Notes] |
| Peer review | [0-100]% | [Notes] |

## Risk Assessment
[What risks does this knowledge introduce?]

| Risk | Severity | Mitigation |
|---|---|---|
| [Risk 1] | [LOW/MEDIUM/HIGH] | [Mitigation] |
| [Risk 2] | [LOW/MEDIUM/HIGH] | [Mitigation] |

## Compatibility Analysis
[Does this conflict with existing knowledge?]

| Existing Knowledge | Conflict? | Resolution |
|---|---|---|
| [Knowledge 1] | [YES/NO] | [Resolution] |
| [Knowledge 2] | [YES/NO] | [Resolution] |

## Reviewer
[Who reviews this?]

| Reviewer | Role | Status |
|---|---|---|
| [Name] | [Role] | [Pending/Approved/Rejected] |

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

## Usage

1. Copy this template
2. Fill in all fields
3. Save as `.ai/core/kup/KUP-NNNNNN_[title].md`
4. Register in KUP README.md
5. Await review
6. On approval, merge to knowledge base
7. Update registry and graph
