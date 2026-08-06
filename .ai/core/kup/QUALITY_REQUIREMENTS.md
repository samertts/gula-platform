# KUP Quality Requirements

**Mission:** GAIOS-002 Phase 8.5
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

Ensure knowledge quality through strict requirements.
Accuracy is more important than quantity.
Consistency is more important than speed.

---

## Rejection Criteria

Reject proposals that:

### 1. Lack Evidence
- No test results
- No documentation references
- No code examples
- No previous experience

### 2. Duplicate Existing Knowledge
- Similar knowledge already exists
- No unique value added
- Would create maintenance burden

### 3. Contradict Constitution
- Violates AI_OPERATING_CONSTITUTION.md
- Conflicts with platform rules
- Introduces vendor lock-in

### 4. Contradict Approved ADRs
- Conflicts with architecture decisions
- Undermines technical direction
- Creates inconsistency

### 5. Introduce Undocumented Risks
- Security risks not documented
- Performance risks not documented
- Maintenance risks not documented

### 6. Contain Temporary Workarounds
- No justification for temporary solution
- No plan for permanent fix
- Technical debt without tracking

---

## Approval Criteria

Approve proposals that:

### 1. Have Sufficient Evidence
- Test results pass
- Documentation is accurate
- Code examples work
- Previous experience supports

### 2. Add Unique Value
- No duplication
- Fills knowledge gap
- Improves system understanding

### 3. Comply with Constitution
- Follows platform rules
- No vendor lock-in
- Free/open source first

### 4. Align with ADRs
- Supports architecture decisions
- Consistent with technical direction
- Enhances system design

### 5. Document Risks
- All risks identified
- Mitigations documented
- Acceptable risk level

### 6. Are Permanent Solutions
- No temporary workarounds
- Production-ready
- Maintainable

---

## Quality Metrics

| Metric | Requirement | Weight |
|---|---|---|
| Evidence quality | 80%+ | 30% |
| Documentation | 90%+ | 25% |
| Constitution compliance | 100% | 20% |
| ADR alignment | 100% | 15% |
| Risk assessment | Complete | 10% |

---

## Review Process

1. Check all required fields
2. Verify evidence quality
3. Search for duplication
4. Check constitution compliance
5. Verify ADR alignment
6. Assess risk level
7. Check compatibility
8. Make approval decision

---

## Rejection Format

When rejecting a KUP:

```markdown
## Rejection Reason

**KUP:** KUP-NNNNNN
**Reviewer:** [Name]
**Date:** [Date]

### Reason
[Clear explanation of why the KUP was rejected]

### Evidence
[Supporting evidence for rejection]

### Recommendation
[What the proposer should do instead]

### Appeal Process
[How to appeal the rejection]
```

---

## References

- `.ai/core/kup/README.md` — KUP system
- `.ai/core/kup/APPROVAL_WORKFLOW.md` — Approval workflow
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
