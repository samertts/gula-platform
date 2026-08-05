# .ai/index/INDEX.md

**Mission:** PROGRAM-KNOWLEDGE-001
**Created:** 2026-08-04
**Last Updated:** 2026-08-05
**Status:** Active

---

## Master Knowledge Index

This is the single entry point for all AI knowledge in the GULA Platform.
Every knowledge artifact is referenced here, organized by category.

---

## Core Files

| File | Description | Status |
|---|---|---|
| `AI_OPERATING_CONSTITUTION.md` | **Supreme AI Constitution (CONST-000001)** | ✅ Active |
| `AGENTS.md` | Multi-agent guidance (references constitution) | ✅ Active |
| `CLAUDE.md` | AI Operating Manual v3.0 (references constitution) | ✅ Active |
| `COPILOT.md` | Copilot-specific rules (references constitution) | ✅ Active |
| `CODEX.md` | Codex-specific rules (references constitution) | ✅ Active |
| `GEMINI.md` | Gemini-specific rules (references constitution) | ✅ Active |
| `.github/copilot-instructions.md` | GitHub Copilot rules (references constitution) | ✅ Active |

---

## Knowledge Categories

### Constitution
Constitutional rules, governance policies, and platform law.

| File | Source | Description |
|---|---|---|
| `docs/constitution/01_VISION.md` | Constitution | Platform vision |
| `docs/constitution/05_ARCHITECTURE_PRINCIPLES.md` | Constitution | Architecture principles |
| `docs/constitution/08_SECURITY_CONSTITUTION.md` | Constitution | Security constitution |
| `docs/constitution/32_AI_EXECUTION_CONSTITUTION.md` | Constitution | AI execution law |
| `docs/constitution/COST_GOVERNANCE.md` | Constitution | Cost governance |
| `docs/ai/ai_policy.md` | AI Governance | AI policy v1.0 |
| `docs/ai/AI_GOVERNANCE.md` | AI Governance | Governance framework |
| `docs/ai/AI_ARCHITECTURE_CONSTRAINTS.md` | AI Governance | AI architecture constraints |

**Full list:** 49 files in `docs/constitution/`, 16 files in `docs/ai/`

### Architecture
Architecture decisions, system design, and technical direction.

| File | Source | Description |
|---|---|---|
| `docs/architecture/CANONICAL_ARCHITECTURE.md` | Architecture | Canonical architecture |
| `docs/architecture/KNOWLEDGE_GRAPH.md` | Architecture | Knowledge graph |
| `docs/architecture/MODULE_DEPENDENCY_MATRIX.md` | Architecture | Module dependencies |
| `docs/architecture/ENTITY_CATALOG.md` | Architecture | Entity catalog |
| `docs/architecture/ADR-008-layer-architecture.md` | Architecture | Layer architecture |
| `docs/architecture/ADR-009-uuid-pk-strategy.md` | Architecture | UUID PK strategy |
| `docs/architecture/ADR-011-fhir-strategy.md` | Architecture | FHIR strategy |
| `docs/architecture/ADR-012-sbom-strategy.md` | Architecture | SBOM strategy |
| `ARCHITECTURE.md` | Root | Deployment architecture |

**Full list:** 19 files in `docs/architecture/`

### ADR (Architecture Decision Records)
Formal architecture decisions with rationale, trade-offs, and consequences.

| File | Source | Description |
|---|---|---|
| `docs/adr/ADR-001-engineering-constitution.md` | ADR | Engineering constitution |
| `docs/adr/ADR-002-monolith-first.md` | ADR | Monolith first |
| `docs/adr/ADR-003-multi-tenant-isolation.md` | ADR | Multi-tenant isolation |
| `docs/adr/ADR-005-postgresql-redis-stack.md` | ADR | PostgreSQL + Redis |
| `docs/adr/ADR-006-clinical-ai-integration.md` | ADR | Clinical AI |
| `docs/adr/ADR-009-self-healing-infrastructure.md` | ADR | Self-healing infra |
| `docs/adr/ADR-012-identity-platform.md` | ADR | Identity platform |
| `docs/adr/ADR-014-observability-stack.md` | ADR | Observability |
| `docs/adr/ADR-015-disaster-recovery.md` | ADR | Disaster recovery |

**Full list:** 30 ADRs in `docs/adr/`, 10 capability ADRs, 16 domain ADRs = 56 total

### Decisions (Aggregated)
Consolidated decision documents by domain.

| File | Source | Description |
|---|---|---|
| `docs/decisions/ARCHITECTURE_DECISIONS.md` | Decisions | 84KB, all architecture decisions |
| `docs/decisions/SECURITY_DECISIONS.md` | Decisions | 84KB, all security decisions |
| `docs/decisions/OPERATIONS_DECISIONS.md` | Decisions | 78KB, all operations decisions |
| `docs/decisions/AI_DECISIONS.md` | Decisions | 61KB, all AI decisions |
| `docs/decisions/CLINICAL_DECISIONS.md` | Decisions | 64KB, all clinical decisions |

### Security
Security policies, baselines, and operational security.

| File | Source | Description |
|---|---|---|
| `docs/security/secret_management.md` | Security | Secret management |
| `docs/security/secret_rotation_plan.md` | Security | Secret rotation |
| `docs/security/repository_security.md` | Security | Repo security |
| `docs/security/public_repository_policy.md` | Security | Public repo policy |
| `docs/security/security_baseline.md` | Security | Security baseline |

### Testing
Testing strategy, policies, and quality gates.

| File | Source | Description |
|---|---|---|
| `docs/constitution/20_TESTING_POLICY.md` | Constitution | Testing policy |
| `docs/quality/quality_gates.md` | Quality | Quality gates |
| `docs/standards/engineering_standards.md` | Standards | Engineering standards |

### Quality & Governance
Quality policies, governance rules, and stability management.

| File | Source | Description |
|---|---|---|
| `.ai/core/quality/GOVERNANCE_RULES.md` | Quality | Governance rules |
| `.ai/core/quality/AI_DECISION_FRAMEWORK.md` | Quality | Decision framework |
| `.ai/core/quality/RISK_MANAGEMENT.md` | Quality | Risk management |
| `.ai/core/quality/STABILITY_POLICY.md` | Quality | Stability & change management |
| `.ai/core/quality/TECHNICAL_DEBT.md` | Quality | Technical debt tracker |
| `.ai/core/quality/DOCUMENTATION_RULES.md` | Quality | Documentation rules |
| `.ai/core/quality/CODING_STANDARDS.md` | Quality | Coding standards |
| `.ai/core/quality/SELF_IMPROVEMENT.md` | Quality | Self-improvement protocol |

### Governor (GULA-GOVERNOR-001)
Enterprise AI governance, coordination, safety and stability framework.

| File | Source | Description |
|---|---|---|
| `.ai/core/governor/README.md` | Governor | Governor layer overview |
| `docs/governor/README.md` | Governor | Governance documentation index |
| `docs/governor/PHASES.md` | Governor | Phase-by-phase design |
| `docs/governor/ENGINE_CONTRACT.md` | Governor | Engine communication contract |
| `AUTHORITY_MAP.md` | Governor | Chain of authority |
| `GOVERNOR_AUDIT_REPORT.md` | Governor | Phase 0 system audit |
| `AI_HEALTH_DASHBOARD.md` | Governor | Phase 12 health dashboard |
| `GOVERNOR_IMPLEMENTATION_REPORT.md` | Governor | Phase 13 implementation report |

### AI Kernel (GULA-KERNEL-001)
Enterprise AI Execution Kernel — the permanent execution layer every AI Engine
depends on (execution, coordination, resource/state management, security,
communication, knowledge access, checkpointing, recovery).

| File | Source | Description |
|---|---|---|
| `.ai/core/kernel/README.md` | Kernel | Execution-layer overview |
| `docs/kernel/README.md` | Kernel | Execution-layer documentation index |
| `docs/kernel/PHASES.md` | Kernel | Phase-by-phase design (0–18) |
| `docs/kernel/CONTRACT.md` | Kernel | 16-field engine contract + autonomy |
| `KERNEL_AUDIT_REPORT.md` | Kernel | Phase 0 foundation audit |
| `KERNEL_IMPLEMENTATION_REPORT.md` | Kernel | Phase 18 implementation report |
| `ENTERPRISE_READINESS_SCORE.md` | Kernel | Readiness score (100/100, grade A) |
| `AI_OPERATING_STATUS.md` | Kernel | Operating status |

### AI Kernel Extensions (GULA-KERNEL-EXT-001)
Enterprise Kernel Extensions — Plugin SDK, Policy Engine, Compatibility,
Migration, Event Bus, Workflow, Marketplace, Evolution, Memory, Health.

| File | Source | Description |
|---|---|---|
| `KERNEL_EXTENSION_AUDIT.md` | Kernel Ext | Phase 0 extension audit |
| `.ai/core/sdk/README.md` | SDK | Plugin SDK overview |
| `.ai/core/sdk/PLUGIN_SPEC.md` | SDK | Plugin specification |
| `.ai/core/sdk/PLUGIN_API.md` | SDK | Plugin API reference |
| `.ai/core/sdk/PLUGIN_LIFECYCLE.md` | SDK | Plugin lifecycle |
| `.ai/core/sdk/PLUGIN_SECURITY.md` | SDK | Plugin security & sandbox |
| `.ai/core/sdk/PLUGIN_TESTING.md` | SDK | Plugin testing & certification |
| `.ai/core/policies/README.md` | Policy | Policy Engine overview |
| `.ai/core/policies/POLICIES.md` | Policy | Human-readable policy catalogue |
| `.ai/core/policies/policies.json` | Policy | Machine-readable policy set |
| `.ai/core/compat/README.md` | Compat | Compatibility Framework overview |
| `.ai/core/compat/engine_compatibility.json` | Compat | Engine contract matrix |
| `.ai/core/migrations/README.md` | Migration | Migration Framework overview |
| `.ai/core/migrations/migration_plans.json` | Migration | Migration plan registry |
| `.ai/core/events/README.md` | Event Bus | Enterprise Event Bus overview |
| `.ai/core/events/event_journal.json` | Event Bus | Delivery journal |
| `.ai/core/workflows/README.md` | Workflow | Workflow Engine overview |
| `.ai/core/workflows/workflows.json` | Workflow | Workflow state |
| `.ai/core/marketplace/README.md` | Marketplace | AI Marketplace overview |
| `.ai/core/marketplace/marketplace_catalog.json` | Marketplace | Catalog |
| `.ai/core/evolution/README.md` | Evolution | Evolution Engine overview |
| `.ai/core/evolution/evolution_state.json` | Evolution | Signal/proposal state |
| `.ai/core/memory/README.md` | Memory | Enterprise AI Memory overview |
| `.ai/core/memory/memory_store.json` | Memory | Memory store |

### Database
Database schema, migrations, and data decisions.

| File | Source | Description |
|---|---|---|
| `docs/database/DATABASE_SCHEMA.md` | Database | Full schema (62KB) |
| `docs/database/entity_deduplication_plan.md` | Database | Deduplication plan |

### Performance
Performance optimization and monitoring.

| File | Source | Description |
|---|---|---|
| `docs/performance/query-optimization-guide.md` | Performance | Query optimization |

### DevOps / Infrastructure
Deployment, CI/CD, and infrastructure.

| File | Source | Description |
|---|---|---|
| `docs/DEPLOYMENT.md` | Docs | Deployment guide |
| `docs/production/production_guide.md` | Production | Production guide |
| `docs/production/deployment_guide.md` | Production | Deployment guide |
| `docs/production/scaling_guide.md` | Production | Scaling guide |
| `docs/production/incident_response.md` | Production | Incident response |

### Runbooks
Operational runbooks for common tasks.

| File | Source | Description |
|---|---|---|
| `docs/runbooks/backend_down.md` | Runbooks | Backend down recovery |
| `docs/runbooks/database_down.md` | Runbooks | Database down recovery |
| `docs/runbooks/disk_full.md` | Runbooks | Disk full recovery |
| `docs/runbooks/security_incident.md` | Runbooks | Security incident |
| `docs/runbooks/high_latency.md` | Runbooks | High latency |
| `docs/runbooks/certificate_expiry.md` | Runbooks | Certificate expiry |
| `docs/runbooks/failed_deployment.md` | Runbooks | Failed deployment |

### Brain (Live Knowledge Index)
Auto-generated project intelligence.

| File | Source | Description |
|---|---|---|
| `docs/brain/PROJECT_BRAIN.md` | Brain | Auto-generated knowledge index |
| `docs/brain/brain_index.json` | Brain | Machine-readable index |

### AI Automation (PROGRAM-AUTOMATION-001)
Enforced governance automation.

| File | Source | Description |
|---|---|---|
| `scripts/validate_ai_system.py` | Automation | AI Validation Engine |
| `scripts/validate_constitution.py` | Automation | Constitution Validator |
| `scripts/validate_knowledge.py` | Automation | Knowledge Validator |
| `scripts/gula_ai_doctor.py` | Automation | AI Health Doctor |
| `scripts/auto_registry.py` | Automation | Auto registry updater |
| `scripts/auto_learning_proposal.py` | Automation | Auto learning proposals |
| `scripts/change_traceability.py` | Automation | Change traceability |
| `scripts/debt_automation.py` | Automation | Technical debt detection |
| `scripts/health_reports.py` | Automation | Periodic health reports |
| `scripts/enforce_policy.py` | Automation | Enforcement policy |
| `scripts/generate_dashboard.py` | Automation | Dashboard generator |
| `scripts/install_ai_hooks.sh` | Automation | Git hook installer |
| `scripts/pre-commit-ai-hook.sh` | Automation | Pre-commit validation |
| `AI_HEALTH_DASHBOARD.md` | Automation | Enterprise dashboard |
| `AUTOMATION_AUDIT_REPORT.md` | Automation | Audit report |
| `PROGRAM_AUTOMATION_IMPLEMENTATION_REPORT.md` | Automation | Implementation report |

---

## .ai/ Internal Files

### Templates
| File | Description |
|---|---|
| `.ai/core/templates/SKILL_TEMPLATE.md` | Skill document template |
| `.ai/core/templates/PLAYBOOK_TEMPLATE.md` | Playbook document template |
| `.ai/core/templates/RUNBOOK_TEMPLATE.md` | Runbook document template |

### Memory
| File | Description |
|---|---|
| `.ai/core/memory/PROJECT_MEMORY.md` | Persistent project memory |
| `.ai/core/memory/KNOW-000001_*.md` | Knowledge: environment standardization |

### Skills (7)
| File | Description |
|---|---|
| `.ai/core/skills/SKILL-000001_*.md` | WSL2 PATH deduplication |
| `.ai/core/skills/SKILL-000002_*.md` | WSL2 Docker compose fix |
| `.ai/core/skills/SKILL-000003_*.md` | Fix failing pytest imports |
| `.ai/core/skills/SKILL-000004_*.md` | Fix ruff N806/N815/N817 naming |
| `.ai/core/skills/SKILL-000005_*.md` | Fix Westgard rule ordering |
| `.ai/core/skills/SKILL-000006_*.md` | Optimize pytest DDL setup |
| `.ai/core/skills/SKILL-000007_*.md` | Fix timezone test bugs |

### Playbooks (4)
| File | Description |
|---|---|
| `.ai/core/playbooks/PLAYBOOK-000001_*.md` | Fix duplicate PATH entries |
| `.ai/core/playbooks/PLAYBOOK-000002_*.md` | Fix Docker build failure |
| `.ai/core/playbooks/PLAYBOOK-000003_*.md` | Fix npm/Node.js issues |
| `.ai/core/playbooks/PLAYBOOK-000004_*.md` | Fix Python/uv environment |

### Bridge Files
| File | Description |
|---|---|
| `.ai/core/architecture/README.md` | Bridge to docs/architecture/ |
| `.ai/core/security/README.md` | Bridge to docs/security/ |
| `.ai/core/testing/README.md` | Bridge to docs/testing/ |
| `.ai/core/devops/README.md` | Bridge to docs/devops/ |
| `.ai/core/database/README.md` | Bridge to docs/database/ |
| `.ai/core/frontend/README.md` | Bridge to frontend knowledge |
| `.ai/core/mobile/README.md` | Bridge to mobile knowledge |
| `.ai/core/backend/README.md` | Bridge to backend knowledge |
| `.ai/core/performance/README.md` | Bridge to performance knowledge |
| `.ai/core/infrastructure/README.md` | Bridge to infrastructure |

### Registry & Graph
| File | Description |
|---|---|
| `.ai/core/registry/REGISTRY.md` | Knowledge artifact registry |
| `.ai/core/graph/README.md` | Document relationship graph |

### Index
| File | Description |
|---|---|
| `.ai/core/index/INDEX.md` | This file — master index |

---

## Semantic Search Tags

To find knowledge, search by these tags:

- **architecture** — architecture decisions, system design
- **security** — security policies, threat model, OWASP
- **testing** — test strategy, quality gates
- **deployment** — CI/CD, Docker, Kubernetes
- **database** — PostgreSQL, Redis, migrations
- **api** — API design, REST, FHIR
- **performance** — optimization, monitoring, caching
- **clinical** — clinical safety, HL7, FHIR
- **identity** — authentication, authorization, RBAC, ABAC
- **mobile** — Android, iOS, Flutter
- **frontend** — React, TypeScript, UI/UX
- **backend** — FastAPI, Python, services
- **governance** — AI governance, constitution
- **stability** — change management, rollback, feature isolation
- **technical-debt** — debt tracking, DEBT-NNNNNN
- **devops** — Docker, CI/CD, infrastructure
- **disaster-recovery** — backup, restore, failover
- **incident** — incident response, postmortem
- **national** — national platform, Iraqi healthcare
- **sovereign** — sovereign invariants, data sovereignty

---

## Statistics

| Category | Count |
|---|---|
| Constitution files | 49 |
| Architecture files | 19 |
| ADR files | 56 |
| Decision files | 5 |
| Security files | 5 |
| Runbooks | 7 |
| Production docs | 10 |
| AI governance | 16 |
| Skills (.ai) | 7 |
| Playbooks (.ai) | 4 |
| Runbooks (.ai) | 5 |
| Checklists (.ai) | 3 |
| Bridge files (.ai) | 16 |
| Templates | 3 |
| Memory records | 2 |
| Lessons | 3 |
| Reports | 3 |
| Registry | 1 |
| Knowledge graph | 1 |
| Capabilities | 20 |
| Decisions | 12 |
| Failures | 8 |
| KUP system | 9 |
| Quality docs | 9 |
| Technical Debt | 9 |
| Automation scripts | 13 |
| AI Automation reports | 3 |
| Search indexes | 2 |
| Prompts | 2 |
| Reviews | 1 |
| Research | 1 |
| Roadmap | 1 |
| Checkpoints | 1 |
| **Total .ai artifacts** | **~105** |
| **Total bridged artifacts** | **~171** |
| **Grand total** | **~276** |

---

## Maintenance

This index is manually maintained. Update when:
- New ADRs are created
- New skills are added to `.ai/core/skills/`
- New playbooks are created in `.ai/core/playbooks/`
- Architecture changes significantly
- Security decisions change
- New runbooks are added

**Auto-refresh:** `make brain` regenerates `docs/brain/PROJECT_BRAIN.md`
