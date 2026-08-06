# KUP Approval Workflow

**Mission:** GAIOS-002 Phase 8.5
**Created:** 2026-08-04
**Status:** Active

---

## Workflow

```
Task Completed
    ↓
Evidence Collected
    ↓
Knowledge Update Proposal (KUP)
    ↓
Technical Review
    ↓
Approval/Rejection
    ↓
Knowledge Merge
    ↓
Registry Update
    ↓
Knowledge Graph Update
    ↓
Version Increment
```

---

## Step 1: Task Completion

When a task is completed:
1. Verify all tests pass
2. Verify lint passes
3. Verify type checking passes
4. Collect evidence of completion

---

## Step 2: Evidence Collection

Gather evidence:
- Test results
- Lint output
- Type checking output
- Documentation updates
- Code changes
- Performance metrics

---

## Step 3: Knowledge Update Proposal

Create a KUP:
1. Copy KUP template
2. Fill in all required fields
3. Save to `.ai/core/kup/KUP-NNNNNN_[title].md`
4. Register in KUP README.md
5. Set status to "Proposed"

---

## Step 4: Technical Review

Review the KUP:
1. Check evidence quality
2. Verify no duplication
3. Check constitution compliance
4. Verify ADR compatibility
5. Assess risk
6. Check compatibility with existing knowledge

---

## Step 5: Approval Decision

### Approval Criteria
- Evidence is sufficient
- No duplication exists
- Constitution compliance confirmed
- ADR compatibility confirmed
- Risk is acceptable
- Compatibility confirmed

### Rejection Criteria
- Lacks evidence
- Duplicates existing knowledge
- Contradicts constitution
- Contradicts approved ADRs
- Introduces undocumented risks
- Contains temporary workarounds without justification

---

## Step 6: Knowledge Merge

On approval:
1. Create or update knowledge files
2. Maintain version history
3. Cross-reference related knowledge
4. Update frontmatter
5. Verify no broken links

---

## Step 7: Registry Update

Update the registry:
1. Add new entry with permanent ID
2. Record version
3. Record author
4. Record reviewer
5. Record approval date

---

## Step 8: Knowledge Graph Update

Update the knowledge graph:
1. Add new node
2. Add relationships
3. Verify no cycles
4. Update cross-references

---

## Step 9: Version Increment

Increment version:
1. Update version number
2. Record change summary
3. Record author
4. Record reviewer
5. Record approval date
6. Record constitution version

---

## Responsibilities

| Role | Responsibility |
|---|---|
| AI Assistant | Create KUP, provide evidence |
| Technical Reviewer | Review KUP, approve/reject |
| Project Owner | Final approval for critical changes |

---

## References

- `.ai/core/kup/README.md` — KUP system
- `.ai/core/kup/KUP_TEMPLATE.md` — KUP template
- `.ai/core/quality/GOVERNANCE_RULES.md` — Governance rules
