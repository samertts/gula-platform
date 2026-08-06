# Knowledge Search Index

**Mission:** GAIOS-002 Phase 6 + Phase 8.5 (KUP)
**Created:** 2026-08-04
**Status:** Active
**Registry ID:** INDEX-SEARCH-000001

---

## Purpose

Searchable indexes for all knowledge artifacts. Support lookup by:
ID, Title, Tags, Category, Module, Technology, Risk, Confidence,
Related Knowledge.

---

## Index by ID

| ID Pattern | Category | Location |
|---|---|---|
| KUP-NNNNNN | Knowledge Updates | .ai/core/kup/ |
| CAP-NNNNNN | Capabilities | .ai/core/capabilities/ |
| DEC-NNNNNN | Decisions | .ai/core/decisions/ |
| FAILURE-NNNNNN | Failures | .ai/core/failures/ |
| SKILL-NNNNNN | Skills | .ai/core/skills/ |
| PLAYBOOK-NNNNNN | Playbooks | .ai/core/playbooks/ |
| RUNBOOK-NNNNNN | Runbooks | .ai/core/runbooks/ |
| CHECKLIST-NNNNNN | Checklists | .ai/core/checklists/ |
| LESSON-NNNNNN | Lessons | .ai/core/lessons/ |
| REPORT-NNNNNN | Reports | .ai/core/reports/ |
| ADR-NNN | ADRs | docs/adr/ |
| DEBT-NNNNNN | Technical Debt | .ai/core/quality/TECHNICAL_DEBT.md |

---

## Automation Scripts (PROGRAM-AUTOMATION-001)

| Script | Purpose | Category |
|---|---|---|
| validate_ai_system.py | AI Validation Engine | Validation |
| validate_constitution.py | Constitution Validator | Validation |
| validate_knowledge.py | Knowledge Validator | Validation |
| gula_ai_doctor.py | AI Health Doctor | Health |
| auto_registry.py | Auto registry updater | Maintenance |
| auto_learning_proposal.py | Auto learning proposals | Learning |
| change_traceability.py | Change traceability | Audit |
| debt_automation.py | Technical debt detection | Audit |
| health_reports.py | Periodic health reports | Reporting |
| enforce_policy.py | Enforcement policy | Enforcement |
| generate_dashboard.py | Enterprise dashboard | Reporting |
| install_ai_hooks.sh | Git hook installer | Enforcement |
| pre-commit-ai-hook.sh | Pre-commit validation | Enforcement |

---

## Index by Category

### Capabilities (20)

| ID | Title | Module | Risk |
|---|---|---|---|
| CAP-000001 | Lab Management | routes/lab.py | LOW |
| CAP-000002 | Sample Management | routes/samples.py | LOW |
| CAP-000003 | Test Results | routes/test_results.py | LOW |
| CAP-000004 | Quality Control | routes/quality_control.py | MEDIUM |
| CAP-000005 | Dashboard | routes/dashboard.py | LOW |
| CAP-000006 | Statistics | routes/stats.py | LOW |
| CAP-000007 | Admin Management | routes/admin.py | HIGH |
| CAP-000008 | Mobile API | routes/mobile.py | MEDIUM |
| CAP-000009 | Metrics | routes/metrics.py | LOW |
| CAP-000010 | Authentication | security/ | HIGH |
| CAP-000011 | FHIR Integration | fhir/ | HIGH |
| CAP-000012 | Identity Platform | niam/ | HIGH |
| CAP-000013 | National Integration | national/ | HIGH |
| CAP-000014 | Event Bus | events/ | MEDIUM |
| CAP-000015 | Audit Logging | audit/ | HIGH |
| CAP-000016 | Multi-tenancy | multi_tenancy/ | HIGH |
| CAP-000017 | RBAC/ABAC | security/ | HIGH |
| CAP-000018 | Offline-first | frontend-v3/ | MEDIUM |
| CAP-000019 | Arabic-first UI | frontend-v3/ | MEDIUM |
| CAP-000020 | Encryption | shared/security/ | HIGH |

### Decisions (12)

| ID | Title | Category | ADR |
|---|---|---|---|
| DEC-000001 | Monolith-first | Architecture | ADR-002 |
| DEC-000002 | PostgreSQL | Database | ADR-0005 |
| DEC-000003 | Redis caching | Infrastructure | ADR-0005 |
| DEC-000004 | UUID PKs | Database | ADR-0009 |
| DEC-000005 | FHIR R4 | Interop | ADR-011 |
| DEC-000006 | CycloneDX SBOM | Security | ADR-012 |
| DEC-000007 | NIAM identity | Security | ADR-012 |
| DEC-000008 | OpenTelemetry | Observability | ADR-014 |
| DEC-000009 | PITR + WAL | DR | ADR-015 |
| DEC-000010 | AI Constitution | AI Gov | CONST-000001 |
| DEC-000011 | Knowledge sys | AI Knowledge | GAIOS-001 |
| DEC-000012 | Bootstrap file | AI Bootstrap | GAIOS-002 |

### Failures (8)

| ID | Title | Severity | Root Cause |
|---|---|---|---|
| FAILURE-000001 | Bash arithmetic trap | LOW | set -e |
| FAILURE-000002 | WSL2 PATH duplication | LOW | Shell config |
| FAILURE-000003 | Broken test imports | MEDIUM | Restructuring |
| FAILURE-000004 | Startup coupling | MEDIUM | Eager init |
| FAILURE-000005 | Encryption tests | LOW | ValueError |
| FAILURE-000006 | Westgard 2-2s | MEDIUM | Rule ordering |
| FAILURE-000007 | Timezone bugs | LOW | datetime mismatch |
| FAILURE-000008 | Docker compose WSL | LOW | WSL2 limit |

### Skills (7)

| ID | Title | Tags |
|---|---|---|
| SKILL-000001 | WSL2 PATH dedup | shell, path, wsl2 |
| SKILL-000002 | Docker compose WSL | docker, wsl2 |
| SKILL-000003 | Broken test imports | pytest, imports |
| SKILL-000004 | Ruff naming violations | ruff, naming |
| SKILL-000005 | Westgard rule ordering | westgard, qc |
| SKILL-000006 | pytest DDL setup | pytest, conftest |
| SKILL-000007 | Timezone test bugs | timezone, datetime |

### Playbooks (4)

| ID | Title | Tags |
|---|---|---|
| PLAYBOOK-000001 | Fix duplicate PATH | shell, path |
| PLAYBOOK-000002 | Docker build optimization | docker, build |
| PLAYBOOK-000003 | npm/Node management | node, npm, nvm |
| PLAYBOOK-000004 | Python/uv environment | python, uv, venv |

### Runbooks (5)

| ID | Title | Severity |
|---|---|---|
| RUNBOOK-000001 | Backend down | CRITICAL |
| RUNBOOK-000002 | Database down | CRITICAL |
| RUNBOOK-000003 | Security incident | CRITICAL |
| RUNBOOK-000004 | High latency | HIGH |
| RUNBOOK-000005 | Disk full | HIGH |

---

## Index by Module

| Module | Capabilities | Skills | Failures |
|---|---|---|---|
| routes/lab.py | CAP-000001 | — | — |
| routes/samples.py | CAP-000002 | — | — |
| routes/test_results.py | CAP-000003 | SKILL-000007 | FAILURE-000007 |
| routes/quality_control.py | CAP-000004 | SKILL-000005 | FAILURE-000006 |
| routes/dashboard.py | CAP-000005 | — | — |
| routes/stats.py | CAP-000006 | — | — |
| routes/admin.py | CAP-000007 | — | — |
| routes/mobile.py | CAP-000008 | — | — |
| routes/metrics.py | CAP-000009 | — | — |
| security/ | CAP-000010, CAP-000017 | — | FAILURE-000004 |
| fhir/ | CAP-000011 | — | — |
| niam/ | CAP-000012 | — | — |
| national/ | CAP-000013 | — | — |
| events/ | CAP-000014 | — | — |
| audit/ | CAP-000015 | — | — |
| multi_tenancy/ | CAP-000016 | — | — |
| shared/security/ | CAP-000020 | — | FAILURE-000005 |
| conftest.py | — | SKILL-000003, SKILL-000006 | FAILURE-000003 |
| .bashrc | — | SKILL-000001 | FAILURE-000002 |

---

## Index by Technology

| Technology | Capabilities | Decisions |
|---|---|---|
| Python 3.12 | CAP-000001-000009 | DEC-000001 |
| FastAPI | CAP-000001-000009 | DEC-000001 |
| PostgreSQL | CAP-000001-000006 | DEC-000002 |
| Redis | CAP-000014 | DEC-000003 |
| SQLAlchemy | CAP-000001-000006 | DEC-000002 |
| React | CAP-000018, CAP-000019 | — |
| TypeScript | CAP-000018, CAP-000019 | — |
| Docker | CAP-000010-000017 | — |
| FHIR R4 | CAP-000011, CAP-000013 | DEC-000005 |
| Ollama | — | — |

---

## Index by Risk

| Risk | Capabilities |
|---|---|
| CRITICAL | — |
| HIGH | CAP-000007, CAP-000010, CAP-000011, CAP-000012, CAP-000013, CAP-000015, CAP-000016, CAP-000017, CAP-000020 |
| MEDIUM | CAP-000004, CAP-000008, CAP-000014, CAP-000018, CAP-000019 |
| LOW | CAP-000001, CAP-000002, CAP-000003, CAP-000005, CAP-000006, CAP-000009 |

---

## Index by Confidence

| Confidence | Capabilities |
|---|---|
| 95% | CAP-000001, CAP-000002, CAP-000003, CAP-000005 |
| 90% | CAP-000004, CAP-000006, CAP-000009, CAP-000010, CAP-000015, CAP-000020 |
| 85% | CAP-000007, CAP-000008, CAP-000016, CAP-000017, CAP-000019 |
| 80% | CAP-000011, CAP-000014 |
| 75% | CAP-000012 |
| 70% | CAP-000013, CAP-000018 |

---

## Usage

### Find by ID
```bash
grep -r "CAP-000001" .ai/core/
```

### Find by Module
```bash
grep -r "routes/lab.py" .ai/core/capabilities/
```

### Find by Risk
```bash
grep -r "HIGH" .ai/core/capabilities/README.md
```

### Find Related
```bash
grep -r "CAP-000004" .ai/core/  # Find everything related to QC
```

---

**Status:** ✅ ACTIVE
**Last Updated:** 2026-08-04
