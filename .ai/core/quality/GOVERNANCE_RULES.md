# AI Governance Rules

**Mission:** GAIOS-002 Phase 8 + Phase 8.5 (KUP) + MASTER-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

All future AI work must follow these governance rules.
Every implementation must produce evidence, verification,
rollback plan, documentation, and knowledge update proposal.

---

## Knowledge Governance (KUP System)

**No engineering knowledge becomes permanent automatically.**

### RFC → KUP Workflow
```
Task Completed → Evidence Collected → RFC (if significant) → KUP Created → Technical Review → Approval → Knowledge Merge → Registry Update → Graph Update → Version Increment
```

### When RFC is Required
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

### KUP Rules
1. Never update knowledge directly
2. Every permanent knowledge modification requires approval
3. Search before creating (merge policy)
4. Version every change
5. Preserve historical knowledge
6. No knowledge bypasses the KUP workflow
7. Significant changes require RFC before KUP

### KUP References
- `.ai/core/kup/README.md` — KUP system
- `.ai/core/kup/RFC_WORKFLOW.md` — RFC workflow
- `.ai/core/kup/KUP_TEMPLATE.md` — KUP template
- `.ai/core/kup/APPROVAL_WORKFLOW.md` — Approval workflow
- `.ai/core/kup/MERGE_POLICY.md` — Merge policy
- `.ai/core/kup/VERSIONING.md` — Versioning system
- `.ai/core/kup/QUALITY_REQUIREMENTS.md` — Quality requirements

---

## Mandatory Rules

### Before Implementation
1. Read AI_BOOTSTRAP.md
2. Read AI_OPERATING_CONSTITUTION.md
3. Search existing knowledge
4. Verify no duplication
5. Create checkpoint if long task
6. **Classify change** (A-I per Stability Policy)

### During Implementation
1. Work in phases (max 5 min or 50 files)
2. Save state after each phase
3. Run tests after each phase
4. Verify correctness
5. **Maintain feature isolation**

### After Implementation
1. Run tests
2. Run lint
3. Run type checking
4. Generate evidence
5. Create rollback plan
6. Update documentation
7. Create KUP for knowledge updates
8. **Update technical debt if applicable**

---

## Required Outputs

Every implementation must produce:

| Output | Purpose |
|---|---|
| Evidence | Proof it works |
| Verification | How to confirm |
| Rollback | How to undo |
| Documentation | What changed |
| KUP | Knowledge update proposal |

---

## Compliance

| Rule | Check | Enforcement |
|---|---|---|
| Audit first | Read before modify | Block if skipped |
| Backup before modify | Create checkpoint | Block if destructive |
| No duplication | Search before create | Warn if duplicate |
| No overwrite | Merge intelligently | Block if overwrite |
| Version control | Commit messages | Enforce conventional |
| Human readable | Markdown format | Enforce |
| No secrets | Scan before commit | Block if found |
| No credentials | Scan before commit | Block if found |
| No auto-constitution | Explicit approval | Block if auto-modified |
| KUP required | Knowledge changes | Block if bypassed |

---

## Approval Matrix

| Change Type | Approval Required |
|---|---|
| New skill | KUP required |
| New playbook | KUP required |
| New capability | KUP required |
| New decision | KUP required |
| Failure record | KUP required |
| Memory update | KUP required |
| Constitution change | YES - explicit |
| API breaking change | YES - explicit |
| Data deletion | YES - explicit |
| License change | YES - explicit |

---

## Change Classification

Every change must be classified per Stability Policy:

| Class | Type | Review |
|---|---|---|
| A | Bug Fix | Standard |
| B | Documentation | Standard |
| C | Feature | Enhanced |
| D | Performance | Enhanced |
| E | Security | Security Review |
| F | Refactoring | Architecture Review |
| G | Architecture | RFC + Approval |
| H | Infrastructure | RFC + Approval |
| I | Breaking Change | RFC + Explicit Approval |

---

## Stability Rules

1. **Feature isolation** — Features must not modify unrelated code
2. **No hidden refactoring** — Refactoring must be in dedicated PRs
3. **Rollback required** — Every non-trivial change needs rollback
4. **Debt tracking** — Known debt gets DEBT-NNNNNN ID
5. **Performance budget** — Features must define performance impact
6. **Security review** — Security-sensitive changes require review

---

## Monitoring

Track governance compliance:
- Audit-first violations: 0
- Duplication attempts: 0
- Constitution modifications: 0
- Secret exposures: 0
- Unapproved deletions: 0
- KUP bypasses: 0
- KUP approvals: 0
- KUP rejections: 0

---

**Status:** ACTIVE
