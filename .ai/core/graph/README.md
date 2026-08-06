# Knowledge Graph — Document Relationships

**Mission:** GAIOS-002 Phase 5 + Phase 8.5 (KUP) + MASTER-001
**Created:** 2026-08-04
**Status:** Active
**Registry ID:** GRAPH-000001

---

## Core Connections

```
AI_BOOTSTRAP.md (entry point)
    ↓
AI_OPERATING_CONSTITUTION.md (supreme authority)
    ↓
CLAUDE.md ←→ AGENTS.md ←→ COPILOT.md ←→ CODEX.md ←→ GEMINI.md
    ↓                ↓                ↓
docs/constitution/  docs/ai/         docs/architecture/
    ↓                ↓                ↓
.ai/core/constitution/  .ai/core/memory/  .ai/core/architecture/
    ↓                ↓                ↓
.ai/core/skills/    .ai/core/playbooks/  .ai/core/index/INDEX.md
    ↓                ↓                ↓
.ai/core/capabilities/  .ai/core/decisions/  .ai/core/failures/
    ↓                ↓                ↓
.ai/core/kup/ (Knowledge Governance)
    ↓
.ai/core/quality/ (Governance Rules, Decision Framework, Risk Management)
```

---

## Knowledge Governance (KUP)

Every knowledge change flows through the KUP system:

```
Knowledge Change → KUP Created → Review → Approval → Merge → Registry → Graph → Version
```

| KUP Component | Purpose |
|---|---|
| KUP README | KUP system overview |
| KUP Template | Template for proposals |
| Approval Workflow | How approvals work |
| Merge Policy | How to merge knowledge |
| Versioning | How to version knowledge |
| Quality Requirements | Quality standards |

---

## Authority Hierarchy

| Level | Document | Purpose |
|---|---|---|
| 1 | AI_OPERATING_CONSTITUTION.md | Supreme authority |
| 2 | AI_BOOTSTRAP.md | Entry point |
| 3 | CLAUDE.md | Full operating manual |
| 4 | AGENTS.md | Engineering rules + state |
| 5 | Tool-specific files | COPILOT.md, CODEX.md, GEMINI.md |
| 6 | docs/constitution/ | Domain constitutions |
| 7 | docs/adr/ | Architecture decisions |
| 8 | .ai/core/ | Knowledge system |

---

## Architecture → Everything

| Architecture Node | Connects To |
|---|---|
| CANONICAL_ARCHITECTURE.md | MODULE_DEPENDENCY_MATRIX, ENTITY_CATALOG |
| ADR-002-monolith-first | ADR-005 (PostgreSQL), ADR-009 (UUID) |
| ADR-005-postgresql-redis | ADR-014 (Observability), ADR-015 (DR) |
| ADR-011-fhir-strategy | docs/national/, FHIR coverage |
| MODULE_DEPENDENCY_MATRIX | All backend modules |

---

## Capabilities → Everything

| Capability | Connects To |
|---|---|
| CAP-000001 (Lab Mgmt) | SKILL-000004 (ruff naming), CAP-000002 (Samples) |
| CAP-000002 (Sample Mgmt) | CAP-000001 (Lab), CAP-000003 (Results) |
| CAP-000003 (Test Results) | CAP-000004 (QC), CAP-000005 (Dashboard) |
| CAP-000004 (Quality Control) | SKILL-000005 (Westgard), CAP-000003 (Results) |
| CAP-000005 (Dashboard) | CAP-000006 (Stats), CAP-000003 (Results) |
| CAP-000010 (Auth) | CAP-000017 (RBAC), CAP-000015 (Audit) |
| CAP-000011 (FHIR) | DEC-000005 (FHIR R4), CAP-000013 (National) |
| CAP-000012 (Identity) | DEC-000007 (NIAM), CAP-000010 (Auth) |
| CAP-000015 (Audit) | CAP-000016 (Multi-tenancy), CAP-000017 (RBAC) |
| CAP-000020 (Encryption) | CAP-000010 (Auth), FAILURE-000005 (Enc tests) |

---

## Decisions → Everything

| Decision | Connects To |
|---|---|
| DEC-000001 (Monolith) | ADR-002, CAP-000001-000009 |
| DEC-000002 (PostgreSQL) | ADR-005, CAP-000001-000006 |
| DEC-000004 (UUID PKs) | ADR-009, All capabilities |
| DEC-000005 (FHIR R4) | ADR-011, CAP-000011, CAP-000013 |
| DEC-000010 (Constitution) | CONST-000001, AI_BOOTSTRAP.md |
| DEC-000011 (Knowledge sys) | .ai/core/, GAIOS-001 |
| DEC-000012 (Bootstrap) | AI_BOOTSTRAP.md, GAIOS-002 |

---

## Failures → Everything

| Failure | Connects To |
|---|---|
| FAILURE-000001 (Bash trap) | SKILL-000001, LESSON-000003 |
| FAILURE-000002 (PATH dup) | SKILL-000001, PLAYBOOK-000001 |
| FAILURE-000003 (Test imports) | SKILL-000003, CAP-000001-000009 |
| FAILURE-000004 (Startup) | CAP-000010, CAP-000014 |
| FAILURE-000005 (Enc tests) | CAP-000020, SKILL-000004 |
| FAILURE-000006 (Westgard) | SKILL-000005, CAP-000004 |
| FAILURE-000007 (Timezone) | SKILL-000007, CAP-000003 |
| FAILURE-000008 (Docker WSL) | SKILL-000002, PLAYBOOK-000002 |

---

## Skills → Problems

| Skill | Related Problem |
|---|---|
| SKILL-000001 (PATH dedup) | ENV-001, WSL2, .bashrc |
| SKILL-000002 (Docker compose) | WSL2, docker-compose.exe |
| SKILL-000003 (pytest imports) | FAILURE-000003, conftest.py |
| SKILL-000004 (ruff naming) | N806/N815/N817 violations |
| SKILL-000005 (Westgard) | FAILURE-000006, 2-2s rule |
| SKILL-000006 (pytest DDL) | conftest.py, auth test setup |
| SKILL-000007 (Timezone) | FAILURE-000007, datetime bugs |

---

## Playbooks → Operations

| Playbook | Related Operations |
|---|---|
| PLAYBOOK-000001 (Fix PATH) | .bashrc, .profile, PATH |
| PLAYBOOK-000002 (Docker build) | Dockerfile, .dockerignore |
| PLAYBOOK-000003 (npm/Node) | NVM, node_modules |
| PLAYBOOK-000004 (Python/uv) | .venv, pyproject.toml |

---

## Constitution → Law

| Constitution | Domain |
|---|---|
| 01-04 | Vision, Mission, Values, Philosophy |
| 05-07 | Architecture, Domain, Engineering |
| 08-10 | Security, Clinical, Laboratory |
| 11-18 | AI, UI/UX, Data, API, DB, Events, Plugins, Workflows |
| 19-32 | Governance, Testing, Docs, Release, Compatibility, etc. |

---

## Search Index

To find knowledge by topic:
- **PATH/shell**: SKILL-000001, PLAYBOOK-000001, ENV-001 reports
- **Docker**: SKILL-000002, devops/README.md, deploy.yml
- **Security**: security/README.md, 08_SECURITY_CONSTITUTION
- **Testing**: testing/README.md, 20_TESTING_POLICY
- **Architecture**: architecture/README.md, CANONICAL_ARCHITECTURE
- **Database**: database/README.md, DATABASE_SCHEMA.md
- **API**: ADR-014, API_COVERAGE.md
- **FHIR**: ADR-011, docs/national/
- **Capabilities**: .ai/core/capabilities/README.md
- **Decisions**: .ai/core/decisions/README.md, docs/decisions/
- **Failures**: .ai/core/failures/README.md
- **Constitution**: AI_OPERATING_CONSTITUTION.md, docs/constitution/
- **KUP**: .ai/core/kup/README.md, KUP system

---

## Cross-Reference Matrix

| From | To | Relationship |
|---|---|---|
| AI_BOOTSTRAP.md | AI_OPERATING_CONSTITUTION.md | References (authority) |
| AI_BOOTSTRAP.md | CLAUDE.md | References (manual) |
| AI_BOOTSTRAP.md | .ai/core/ | References (knowledge) |
| AI_OPERATING_CONSTITUTION.md | AGENTS.md | Supersedes |
| AI_OPERATING_CONSTITUTION.md | CLAUDE.md | Supersedes |
| AI_OPERATING_CONSTITUTION.md | COPILOT.md | Supersedes |
| AI_OPERATING_CONSTITUTION.md | CODEX.md | Supersedes |
| AI_OPERATING_CONSTITUTION.md | GEMINI.md | Supersedes |
| .ai/core/capabilities/ | .ai/core/skills/ | Uses |
| .ai/core/capabilities/ | .ai/core/playbooks/ | Uses |
| .ai/core/decisions/ | docs/adr/ | Aggregates |
| .ai/core/failures/ | .ai/core/incidents/ | Reports to |
| .ai/core/failures/ | .ai/core/lessons/ | Generates |
| .ai/core/failures/ | .ai/core/skills/ | Creates |
| .ai/core/kup/ | .ai/core/quality/ | Governs |
| .ai/core/kup/ | .ai/core/registry/ | Updates |
| .ai/core/kup/ | .ai/core/graph/ | Updates |
| .ai/core/quality/ | .ai/core/kup/ | Enforces |
| .ai/core/quality/ | .ai/core/decisions/ | Framework |
| .ai/core/quality/ | .ai/core/quality/STABILITY_POLICY.md | Stability |
| .ai/core/quality/ | .ai/core/quality/TECHNICAL_DEBT.md | Debt tracking |
| .ai/core/desktop/ | .ai/core/backend/ | API consumer |
| .ai/core/monitoring/ | .ai/core/performance/ | Metrics |
| .ai/core/observability/ | .ai/core/monitoring/ | Tracing |
| .ai/core/api/ | .ai/core/backend/ | Endpoints |
| scripts/validate_ai_system.py | .ai/core/ | Validates |
| scripts/validate_constitution.py | AI_OPERATING_CONSTITUTION.md | Validates |
| scripts/validate_knowledge.py | .ai/core/ | Validates |
| scripts/gula_ai_doctor.py | .ai/core/ + docs/ | Health checks |
| scripts/auto_registry.py | .ai/core/registry/ | Auto-updates |
| scripts/change_traceability.py | .git/ | Audits |
| scripts/enforce_policy.py | .ai/core/ + scripts/ | Enforces |
| scripts/health_reports.py | reports/health/ | Generates |

---

**Status:** ✅ EXPANDED
**Last Updated:** 2026-08-04
