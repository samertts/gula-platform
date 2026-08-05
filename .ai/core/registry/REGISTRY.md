---
id: REGISTRY-000001
type: registry
title: "Knowledge Registry"
version: "1.1"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [registry, index, knowledge]
---

# Knowledge Registry

All knowledge artifacts with unique IDs. IDs are immutable and never reused.

## Knowledge Update Proposals (KUP)

| ID | Title | Status | Confidence |
|---|---|---|---|
| KUP-000001 | GAIOS-002 Knowledge System | Proposed | 95% |
| KUP-000002 | AI Constitution (CONST-000001) | Approved | 95% |
| KUP-000003 | AI Bootstrap (AI_BOOTSTRAP.md) | Approved | 95% |

## Skills

| ID | Title | Status | Confidence |
|---|---|---|---|
| SKILL-000001 | WSL2 PATH Deduplication | Approved | 100% |
| SKILL-000002 | WSL2 Docker Compose Resolution | Approved | 100% |
| SKILL-000003 | Fix Failing Pytest Imports | Approved | 100% |
| SKILL-000004 | Fix Ruff N806/N815/N817 Naming | Approved | 100% |
| SKILL-000005 | Fix Westgard Rule Ordering | Approved | 100% |
| SKILL-000006 | Optimize Pytest DDL Setup | Approved | 100% |
| SKILL-000007 | Fix Timezone Test Bugs | Approved | 90% |

## Playbooks

| ID | Title | Status | Confidence |
|---|---|---|---|
| PLAYBOOK-000001 | Fix Duplicate PATH Entries | Approved | 100% |
| PLAYBOOK-000002 | Fix Docker Build Failure | Approved | 90% |
| PLAYBOOK-000003 | Fix npm/Node.js Issues | Approved | 90% |
| PLAYBOOK-000004 | Fix Python/uv Environment | Approved | 90% |

## Memory Records

| ID | Title | Status | Confidence |
|---|---|---|---|
| KNOW-000001 | Environment Standardization | Approved | 100% |

## Runbooks

| ID | Title | Status | Confidence |
|---|---|---|---|
| RUNBOOK-000001 | Backend Down Recovery | Approved | 95% |
| RUNBOOK-000002 | Database Down Recovery | Approved | 95% |
| RUNBOOK-000003 | Security Incident Response | Approved | 90% |
| RUNBOOK-000004 | High Latency Investigation | Approved | 90% |
| RUNBOOK-000005 | Disk Full Recovery | Approved | 90% |

## Checklists

| ID | Title | Status | Confidence |
|---|---|---|---|
| CHECKLIST-000001 | Code Review | Approved | 100% |
| CHECKLIST-000002 | Pre-Commit | Approved | 100% |
| CHECKLIST-000003 | Deployment | Approved | 95% |

## Reports

| ID | Title | Status |
|---|---|---|
| REPORT-000001 | GAIOS-001 Completion | Approved |
| REPORT-000003 | ENV-001 Phase 3: Node | Approved |
| REPORT-000004 | ENV-001 Phase 4: Tools | Approved |

## Automation Artifacts (PROGRAM-AUTOMATION-001)

| Script | Purpose | Status |
|---|---|---|
| validate_ai_system.py | AI Validation Engine (17 sections) | Active |
| validate_constitution.py | Constitution Validator | Active |
| validate_knowledge.py | Knowledge Validator | Active |
| gula_ai_doctor.py | AI Health Doctor (20 checks) | Active |
| auto_registry.py | Auto registry updater | Active |
| auto_learning_proposal.py | Auto learning proposals | Active |
| change_traceability.py | Change traceability | Active |
| debt_automation.py | Technical debt automation | Active |
| health_reports.py | Periodic health reports | Active |
| enforce_policy.py | Enforcement policy | Active |
| generate_dashboard.py | Enterprise dashboard | Active |
| install_ai_hooks.sh | Git hook installer | Active |
| pre-commit-ai-hook.sh | Pre-commit validation | Active |

## Technical Debt

| ID | Description | Status |
|---|---|---|
| DEBT-000001 | Knowledge graph ASCII only | Open |
| DEBT-000002 | 62 backref= in inactive contexts | Open |
| DEBT-000003 | mypy times out on full codebase | Open |
| DEBT-000004 | Docker compose v1 broken in WSL | Open |
| DEBT-000005 | 379 ruff violations | Open |
| DEBT-000006 | ~~No CI integration for knowledge~~ | **Resolved** (PROGRAM-AUTOMATION-001) |
| DEBT-000007 | ADR number collisions | Open |
| DEBT-000008 | Near-duplicate files in constitution/ | Open |

## Governor (GULA-GOVERNOR-001)

| Artifact | Location | Status |
|---|---|---|
| GULA-GOVERNOR-001 | scripts/governor/ + scripts/governor.py | Active |
| GOVERNOR_AUDIT_REPORT.md | repo root | Active |
| AUTHORITY_MAP.md | repo root | Active |
| AI_HEALTH_DASHBOARD.md | repo root | Active |
| GOVERNOR_IMPLEMENTATION_REPORT.md | repo root | Active |
| docs/governor/ | docs | Active |
| .ai/core/governor/README.md | knowledge | Active |

## AI Kernel (GULA-KERNEL-001)

| Artifact | Location | Status |
|---|---|---|
| GULA-KERNEL-001 | scripts/kernel/ + scripts/kernel.py | Active |
| KERNEL_AUDIT_REPORT.md | repo root | Active |
| KERNEL_IMPLEMENTATION_REPORT.md | repo root | Active |
| ENTERPRISE_READINESS_SCORE.md | repo root | Active |
| AI_OPERATING_STATUS.md | repo root | Active |
| docs/kernel/ | docs | Active |
| .ai/core/kernel/README.md | knowledge | Active |

## AI Kernel Extensions (GULA-KERNEL-EXT-001)

| Artifact | Location | Status |
|---|---|---|
| GULA-KERNEL-EXT-001 | scripts/kernel/ext/ | Active |
| KERNEL_EXTENSION_AUDIT.md | repo root | Active |
| Plugin SDK (Phase 1) | scripts/kernel/ext/plugin.py | Active |
| SDK docs | .ai/core/sdk/ | Active |
| Policy Engine (Phase 2) | scripts/kernel/ext/policy.py | Active |
| Policy catalog | .ai/core/policies/ | Active |
| Compatibility Framework (Phase 3) | scripts/kernel/ext/compatibility.py | Active |
| Compatibility matrix | .ai/core/compat/ | Active |

## Total Count

| Category | Count |
|---|---|
| KUPs | 3 |
| Skills | 7 |
| Playbooks | 4 |
| Runbooks | 5 |
| Checklists | 3 |
| Memory Records | 2 |
| Reports | 3 |
| Bridge Files | 16 |
| Templates | 3 |
| Lessons | 3 |
| Capabilities | 20 |
| Decisions | 12 |
| Failures | 8 |
| Technical Debt | 8 (1 resolved) |
| Automation Scripts | 13 |
| Governor Modules | 18 |
| Kernel Modules | 19 |
| SDK Artifacts | 6 |
| Policies | 16 |
| Compat Matrix | 7 contracts |
| **Total Artifacts** | **170** |
