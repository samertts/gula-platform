# AI_KNOWLEDGE_AUDIT.md

**Mission:** PROGRAM-KNOWLEDGE-001
**Date:** 2026-08-04
**Auditor:** OpenCode (big-pickle)

---

## 1. AUDIT SCOPE

Audit all existing AI knowledge, configuration, and documentation in the
GULA Platform repository to determine what exists, what is missing, and
what the `.ai/` knowledge system must incorporate.

---

## 2. EXISTING AI AGENT GUIDANCE FILES

| File | Lines | Category | Target AI | Status |
|---|---|---|---|---|
| `AGENTS.md` | 388 | Constitution + Instructions | All agents | ✅ EXISTS — Primary source of truth |
| `CLAUDE.md` | 430 | Operating Manual (v3.0) | Claude Code | ✅ EXISTS — Mandatory read-first entry |
| `COPILOT.md` | 40 | Constitution Rules | GitHub Copilot | ✅ EXISTS |
| `CODEX.md` | 41 | Constitution Rules | OpenAI Codex | ✅ EXISTS |

**Missing agent files:**
- `GEMINI.md` — NOT FOUND
- `.cursorrules` — NOT FOUND
- `.cursor/` — NOT FOUND
- `.github/copilot-instructions.md` — NOT FOUND (instructions are in root `COPILOT.md`)
- `.opencode/` configuration — NOT FOUND
- `.windsurfrules` — NOT FOUND
- `.aider*` — NOT FOUND

---

## 3. EXISTING `.ai/` DIRECTORY

**Status:** NOT FOUND

The `.ai/` directory does not exist. All knowledge must be created fresh.

---

## 4. EXISTING KNOWLEDGE INVENTORY

### 4.1 Project Brain (Live Knowledge Index)
| File | Status | Notes |
|---|---|---|
| `docs/brain/PROJECT_BRAIN.md` | ✅ EXISTS | Auto-generated, 157 lines, last: 2026-08-03 |
| `docs/brain/brain_index.json` | ✅ EXISTS | Machine-readable, 109 lines |

### 4.2 AI Governance (16 files)
| Category | Files | Status |
|---|---|---|
| Core governance | `AI_GOVERNANCE.md`, `AI_ARCHITECTURE_CONSTRAINTS.md`, `AI_PLATFORM_ARCHITECTURE.md`, `ai_policy.md` | ✅ EXISTS |
| Program status | `MASTER_ROADMAP.md`, `RISK_REGISTER.md` | ✅ EXISTS |
| Program reports | 9 completion reports (PROGRAM-003 through PROGRAM-012) | ✅ EXISTS |

### 4.3 Platform Constitution (49 files)
| Category | Files | Status |
|---|---|---|
| Numbered constitution (01-32) | 32 documents | ✅ EXISTS |
| Compliance reports | 8+ files | ✅ EXISTS |
| Data preservation | 5 files | ✅ EXISTS |
| Runtime certification | 13 files | ✅ EXISTS |

### 4.4 Architecture Decision Records (66 ADR files)
| Location | Files | Status |
|---|---|---|
| `docs/adr/` | 30 ADRs (ADR-001 through ADR-025, plus README) | ✅ EXISTS |
| `docs/architecture/` | 5 ADRs (ADR-008 through ADR-012) | ✅ EXISTS |
| `docs/decisions/` | 5 aggregated decision files | ✅ EXISTS |
| Domain-specific ADRs | 16 files across 12 locations | ✅ EXISTS |
| Backend capability ADRs | 10 files | ✅ EXISTS |

### 4.5 Documentation Footprint
| Category | Files | Status |
|---|---|---|
| Total under `docs/` | 591 files | ✅ EXISTS |
| `docs/` subdirectories | 78 | ✅ EXISTS |
| `docs/constitution/` | 49 files | ✅ EXISTS |
| `docs/ai/` | 16 files | ✅ EXISTS |
| `docs/architecture/` | 19 files | ✅ EXISTS |
| `docs/adr/` | 30 files | ✅ EXISTS |
| `docs/decisions/` | 5 files | ✅ EXISTS |
| `docs/runbooks/` | 7 operational runbooks | ✅ EXISTS |
| `docs/production/` | 10 production docs | ✅ EXISTS |
| `docs/security/` | 5 security docs | ✅ EXISTS |
| `docs/niam/` | 30+ identity platform docs | ✅ EXISTS |
| `docs/national/` | 11 national platform docs | ✅ EXISTS |
| `docs/sovereign/` | 50+ sovereign governance docs | ✅ EXISTS |
| `docs/technical-debt/` | 2 files (120KB + 381KB) | ✅ EXISTS |

### 4.6 CI/CD Governance Workflows
| Workflow | Status |
|---|---|
| `ai-governance.yml` | ✅ EXISTS — brain freshness + validation gate |
| `constitution-compliance.yml` | ✅ EXISTS — constitution compliance checker |
| `ci.yml` | ✅ EXISTS — main CI (ruff + tests + Docker) |
| `quality-gate.yml` | ✅ EXISTS — quality gate checks |

### 4.7 Backend Capability ADRs
| Capability | Status |
|---|---|
| document_management | ✅ EXISTS |
| fhir_interoperability | ✅ EXISTS |
| storage_service | ✅ EXISTS |
| encounter_management | ✅ EXISTS |
| workflow_engine | ✅ EXISTS |
| clinical_foundation | ✅ EXISTS |
| reporting_service | ✅ EXISTS |
| provider_management | ✅ EXISTS |
| search_service | ✅ EXISTS |
| healthcare_consent | ✅ EXISTS |

---

## 5. KNOWLEDGE GAPS ANALYSIS

### 5.1 Critical Gaps (Must Create)

| Gap | Priority | Reason |
|---|---|---|
| `.ai/` directory structure | CRITICAL | Foundation for entire knowledge system |
| `.ai/core/skills/` | CRITICAL | No skill library exists |
| `.ai/core/playbooks/` | CRITICAL | No playbook system exists (docs/runbooks/ exists but not in .ai format) |
| `.ai/core/memory/` | CRITICAL | No structured project memory in .ai/ |
| `.ai/core/index/` | CRITICAL | No centralized index |
| `.ai/core/constitution/` | CRITICAL | Constitution exists in docs/ but not indexed in .ai/ |
| `.ai/core/templates/` | HIGH | No standardized templates for skills/playbooks/runbooks |

### 5.2 Important Gaps (Should Create)

| Gap | Priority | Reason |
|---|---|---|
| `.ai/core/architecture/` | HIGH | Architecture knowledge scattered across docs/ |
| `.ai/core/security/` | HIGH | Security decisions exist but not in .ai/ |
| `.ai/core/testing/` | HIGH | Testing strategy documented but not in .ai/ |
| `.ai/core/performance/` | MEDIUM | Performance docs exist but not in .ai/ |
| `.ai/core/devops/` | MEDIUM | DevOps docs exist but not in .ai/ |
| `.ai/core/database/` | MEDIUM | Database docs exist but not in .ai/ |
| `.ai/core/knowledge_graph/` | MEDIUM | `docs/architecture/KNOWLEDGE_GRAPH.md` exists but not connected |

### 5.3 Nice-to-Have Gaps

| Gap | Priority | Reason |
|---|---|---|
| `.ai/core/research/` | LOW | For storing research findings |
| `.ai/core/roadmap/` | LOW | ROADMAP.md exists but not in .ai/ |
| `.ai/core/automation/` | LOW | Automation scripts exist but not documented in .ai/ |
| `.ai/core/reviews/` | LOW | No review system exists |
| `.ai/core/quality/` | LOW | Quality gates exist but not in .ai/ |
| `.ai/core/checkpoints/` | LOW | For task checkpoint tracking |

---

## 6. MERGE STRATEGY

### 6.1 What to REUSE (not recreate)
- `AGENTS.md` — keep as-is, reference from .ai/
- `CLAUDE.md` — keep as-is, reference from .ai/
- `docs/constitution/` — index into .ai/core/constitution/
- `docs/adr/` — index into .ai/core/decisions/ (or .ai/core/architecture/)
- `docs/brain/PROJECT_BRAIN.md` — reference from .ai/index/
- `docs/runbooks/` — convert to .ai/core/playbooks/ format
- `docs/security/` — index into .ai/core/security/
- `docs/architecture/` — index into .ai/core/architecture/
- `docs/ai/` — index into .ai/core/memory/

### 6.2 What to CREATE (new)
- `.ai/` directory structure (all subdirectories)
- `.ai/core/skills/` — empty, populated as problems are solved
- `.ai/core/templates/` — skill template, playbook template, runbook template
- `.ai/core/index/INDEX.md` — master index
- `.ai/core/memory/` — structured project memory
- `.ai/core/playbooks/` — operational playbooks (ENV-001 will create first ones)
- `.ai/core/checkpoints/` — task checkpoint system

### 6.3 What to NOT touch
- `docs/constitution/` — never modify, only reference
- `docs/adr/` — never modify, only reference
- `AGENTS.md` — never modify without explicit request
- `CLAUDE.md` — never modify without explicit request

---

## 7. RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Creating duplicate knowledge | Medium | Medium | Audit-first, merge strategy, check existing before creating |
| Overwriting existing docs | Low | High | Never modify docs/, only reference from .ai/ |
| Breaking existing CI/CD | Low | High | .ai/ is new directory, no existing CI depends on it |
| Index staleness | Medium | Low | Auto-refresh via `make brain` + future automation |
| Knowledge fragmentation | Low | Medium | Single .ai/index/INDEX.md as entry point |

---

## 8. RECOMMENDATIONS

1. **Create `.ai/` structure immediately** — all subdirectories, templates, and index
2. **Bridge existing knowledge** — create reference files in .ai/ that point to docs/ originals
3. **Start with empty skills** — skills are created by solving real problems, not pre-seeded
4. **Create first playbook** — "Fix PATH" from ENV-001 as proof of concept
5. **Create first skill** — "Fix Duplicate PATH Entries" from ENV-001 findings
6. **Wire into self-learning** — after every task, auto-evaluate if a skill/playbook should be created

---

## 9. APPROVAL REQUIRED

**Step 1 Audit complete.** Awaiting approval to proceed with Step 2 (Create Knowledge System).
