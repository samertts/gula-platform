# Self-Improvement Protocol

**Mission:** GAIOS-002 Phase 7 + Phase 8.5 (KUP)
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

After every completed task, evaluate what was learned and generate
recommendations for knowledge improvement. Never update knowledge
automatically without approval.

**Every knowledge change requires a KUP (Knowledge Update Proposal).**

---

## Evaluation Checklist

After every completed task, answer:

### Knowledge
- What was learned?
- Should memory be updated?
- Should a capability change?
- Should a skill change?
- Should a playbook change?
- Should a runbook change?
- Should a decision be recorded?
- Should a failure record be created?
- Should documentation improve?

### Process
- Was the task efficient?
- Were there unnecessary steps?
- Could the process be automated?
- Were there repeated actions?

### Quality
- Was the result correct?
- Were there bugs introduced?
- Was testing adequate?
- Was documentation updated?

---

## Rules

1. Never update automatically - Generate recommendations only
2. Never delete - Only add or deprecate
3. Never duplicate - Search before creating
4. Always verify - Check existing knowledge first
5. Always version - Increment version on changes
6. Always document - Record what changed and why
7. **Always create KUP** - No knowledge bypasses the KUP workflow

---

## Integration Points

| When | Action | KUP Required |
|---|---|---|
| New skill learned | Create SKILL-NNNNNN | YES |
| Procedure changed | Update PLAYBOOK-NNNNNN | YES |
| Architecture changed | Update PROJECT_MEMORY | YES |
| Bug found | Create FAILURE-NNNNNN | YES |
| Choice made | Create DECISION-NNNNNN | YES |
| New capability | Create CAP-NNNNNN | YES |
| Incident occurred | Create INCIDENT-NNNNNN | YES |

---

## KUP Integration

When generating recommendations:
1. Create KUP for each recommendation
2. Follow KUP template
3. Register in KUP README.md
4. Await approval before merging
5. Update registry and graph after merge

---

**Status:** ACTIVE
