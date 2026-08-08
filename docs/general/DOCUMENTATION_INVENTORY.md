# GULA Platform — Documentation Inventory

**Generated:** 2026-07-23  
**Version:** 1.0  
**Scope:** Complete repository documentation discovery

---

## Table of Contents

1. [Discovery Methodology](#1-discovery-methodology)
2. [Documentation by Category](#2-documentation-by-category)
3. [Repository Stats](#3-repository-stats)
4. [Index Files](#4-index-files)
5. [Document Location Map](#5-document-location-map)

---

## 1. Discovery Methodology

- **Search scope:** Entire repository root at `/home/samertts/workspace/projects/gula-platform`
- **Patterns scanned:** `**/*.md`, `**/*.rst`, `**/docs/**`, `**/adr/**`, `**/decisions/**`, `**/architecture/**`
- **Exclusions:** `node_modules/`, `__pycache__/`, `.git/`, `venv/`, `*.venv/`
- **Date:** 2026-07-23
- **Method:** Git-based file enumeration + glob pattern matching

---

## 2. Documentation by Category

### 2.1 Root-Level Documentation (55 files)

| File | Type | Description |
|------|------|-------------|
| `README.md` | Overview | Repository overview, quick start |
| `README_COMPREHENSIVE.md` | Overview | Detailed comprehensive README |
| `CLAUDE.md` | Guide | AI assistant developer guide |
| `ARCHITECTURE.md` | Architecture | Architecture overview, middleware stack |
| `CHANGELOG.md` | Release | Release history (859 lines) |
| `CONTRIBUTING.md` | Process | Contribution guidelines |
| `QUALITY.md` | Quality | Quality documentation |
| `SECURITY.md` | Security | Security overview |
| `FIELD_SECURITY.md` | Security | Field-level security |
| `SECURITY_HARDENING.md` | Security | Security hardening guide |
| `SECURITY_CERTIFICATION.md` | Security | Security certification report |
| `SECURITY_REMEDIATION_REPORT.md` | Security | Security remediation |
| `TESTING.md` | Testing | Testing overview |
| `DEPLOYMENT_TESTING.md` | Testing | Deployment testing guide |
| `PRODUCTION_DEPLOYMENT.md` | Deployment | Production deployment |
| `DEPLOYMENT_PLATFORMS.md` | Deployment | Deployment platforms |
| `DEPLOYMENT_CREDENTIALS.md` | Deployment | Deployment credentials |
| `OPERATIONS.md` | Operations | Operations guide |
| `PERFORMANCE_GUIDE.md` | Performance | Performance guide |
| `INFRASTRUCTURE_GUIDE.md` | Infrastructure | Infrastructure guide |
| `IDENTITY_ARCHITECTURE.md` | Architecture | Identity architecture |
| `TENANT_MODEL.md` | Architecture | Multi-tenant model |
| `USER_TYPES.md` | Architecture | User types |
| `PERMISSION_CATALOG.md` | Security | Permission catalog |
| `ABAC_DESIGN.md` | Security | ABAC design document |
| `BREAK_GLASS_POLICY.md` | Security | Break glass policy |
| `ROADMAP.md` | Strategy | Platform roadmap |
| `MASTER_SYSTEM_ATLAS.md` | Atlas | Comprehensive system atlas (1346 lines) |
| `STRATEGIC_ANALYSIS.md` | Strategy | Strategic analysis |
| `OPTIMIZATIONS.md` | Technical | Optimizations |
| `MARKETING_STRATEGY.md` | Business | Marketing strategy |
| `BUSINESS_PLAN.md` | Business | Business plan |
| `analysis_report.md` | Report | Analysis report |
| `final_report.md` | Report | Final report |
| `pitch_deck_content.md` | Business | Pitch deck content |
| `API_CONTRACT_REPORT.md` | API | API contract report |
| `PLATFORM_READINESS_AUDIT.md` | Audit | Platform readiness audit |
| `BATCH1_CLOSURE_AUDIT.md` | Audit | Batch 1 closure audit |
| `MASTER_AUDIT_2050.md` | Audit | Master audit |
| `ARCHITECTURE_CLEANUP_REPORT.md` | Architecture | Architecture cleanup report |
| `RC_READINESS_REPORT.md` | Release | Release candidate readiness |
| `RELEASE_READINESS_REPORT.md` | Release | Release readiness |
| `DEPENDENCY_INTELLIGENCE_REPORT.md` | Technical | Dependency intelligence |
| `PROGRAM-07M-REPORT.md` | Report | Program 07M report |
| `PROGRAM-07C-REPORT.md` | Report | Program 07C report |
| `ANDROID_CI_REPAIR_REPORT.md` | DevOps | Android CI repair |
| `DATABASE_CERTIFICATION.md` | Certification | Database certification |
| `DEVOPS_CERTIFICATION.md` | Certification | DevOps certification |
| `ACCESSIBILITY_CERTIFICATION.md` | Certification | Accessibility certification |
| `MASTER_RELEASE_CERTIFICATION.md` | Certification | Master release certification |
| `PERFORMANCE_CERTIFICATION.md` | Certification | Performance certification |
| `CERTIFICATION-v1.0.md` | Certification | Certification v1.0 |
| `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md` | Certification | Enterprise production certification |
| `openapi.json` | API Spec | OpenAPI specification |

### 2.2 `docs/` Directory (40+ subdirectories, 275+ files)

| Subdirectory | File Count | Description |
|-------------|------------|-------------|
| `docs/adr/` | 27 | Architecture Decision Records (ADR-001 to ADR-025) |
| `docs/decisions/` | 5 | Decision logs (architecture, operations, AI, clinical, security) |
| `docs/constitution/` | 47 | 31 constitution articles + data_preservation/ (5) + runtime/ (13) + validation |
| `docs/architecture/` | 12 | Canonical architecture, entity catalog, knowledge graph, ADRs 008-012 |
| `docs/sndhs/` | 18 | SNDHS-lite specification (15 docs + phase1 runbook) |
| `docs/sovereign/` | 77 | Sovereign domain (phases 16-25, READMEs, risk registers) |
| `docs/enterprise/` | 22 | Enterprise architecture, atlases (executive/), gap analysis |
| `docs/engineering/` | 13 | Quality gates, technical debt, risk register, blueprints |
| `docs/freeze/` | 23 | Release snapshots (pi-003, pi-004, pi-005) |
| `docs/production/` | 9 | Deployment, DR, incident response, operations, scaling |
| `docs/national/` | 12 | National healthcare platform docs |
| `docs/security/` | 1 | Security baseline |
| `docs/runbooks/` | 7 | Operational runbooks |
| `docs/templates/` | 7 | Document templates (ADR, assessment, decision log, risk) |
| `docs/certification/` | 4 | Certification framework |
| `docs/database/` | 1 | Entity deduplication plan |
| `docs/ai/` | 4 | AI architecture and policy |
| `docs/performance/` | 1 | Query optimization |
| `docs/reference/` | 3 | Digital Library Index, Reference Catalog, Knowledge Graph |
| `docs/technical-debt/` | 2 | Technical debt registry |
| `docs/metrics/` | 5 | Metrics cache files (JSON) |
| 15+ more subdirectories | ~30 | Ecosystem, evolution, execution, factory, genome, governance, healthcare, learning, operations, preview, quality, trust, ux-audit |

### 2.3 Architecture Decision Records (45+ files across locations)

| Location | Count |
|----------|-------|
| `docs/adr/` | 25 ADRs + README |
| `docs/architecture/` | 5 supplemental ADRs (ADR-008 to ADR-012) |
| Sub-platform ADRs | 8 (national, nursing, pharmacy, radiology, runtime, hospital-workspace, plus backend capabilities) |

### 2.4 Certification Reports (15+ files)

| File | Path |
|------|------|
| Database Certification | `DATABASE_CERTIFICATION.md` |
| DevOps Certification | `DEVOPS_CERTIFICATION.md` |
| Accessibility Certification | `ACCESSIBILITY_CERTIFICATION.md` |
| Master Release Certification | `MASTER_RELEASE_CERTIFICATION.md` |
| Performance Certification | `PERFORMANCE_CERTIFICATION.md` |
| Enterprise Production Certification | `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md` |
| Certification v1.0 | `CERTIFICATION-v1.0.md` |
| Security Certification | `SECURITY_CERTIFICATION.md` |
| Identity Certification | `identity_report/IDENTITY_CERTIFICATION.md` |
| runtime/ certifications | `docs/constitution/runtime/` (13 files) |
| Accreditation Workflows | `docs/certification/ACCREDITATION_WORKFLOWS.md` |

### 2.5 Readme Files (55+ across repository)

| Location | Description |
|----------|-------------|
| `README.md` | Root repo overview |
| `README_COMPREHENSIVE.md` | Root comprehensive overview |
| `docs/adr/README.md` | ADR index and process |
| `docs/constitution/README.md` | Constitution overview |
| `docs/sovereign/README.md` | Sovereign domain overview |
| `docs/sndhs/README.md` | SNDHS overview |
| `docs/templates/README.md` | Template documentation |
| `backend/app/models/README.md` | Models documentation |
| `backend/app/routes/README.md` | Routes documentation |
| `backend/app/security/README.md` | Security documentation |
| `backend/app/services/README.md` | Services documentation |
| `backend/app/core/README.md` | Core infrastructure documentation |
| `backend/app/lims/README.md` | LIMS documentation |
| `backend/app/notifications/README.md` | Notifications documentation |
| `backend/app/interoperability/README.md` | Interoperability documentation |
| `frontend-v2/README.md` | Frontend overview |
| `frontend-v3/README.md` | Frontend v3 overview |
| `services/device_bridge/README.md` | Device bridge overview |
| `nhop-platform/README.md` | NHOP overview |
| `edge_agent/README.md` | Edge agent overview |
| `digitalocean/README.md` | DigitalOcean deployment |
| `supabase/README.md` | Supabase integration |
| 30+ SDK/package sub-readmes | Contracts, packages/uap, assessment/ subdirectories |

---

## 3. Repository Stats

| Metric | Value |
|--------|-------|
| Total Markdown (`.md`) files | ~420 |
| Total documentation files | ~500+ (incl. OpenAPI specs, doc-oriented YAML, txt) |
| ADR files | ~45 (across all locations) |
| Certification reports | ~15 |
| Security documents | ~20 |
| Architecture documents | ~30 |
| Deployment guides | ~15 |
| Assessment reports | ~15 |
| Runbooks | 7 |
| Empty documentation directories | `docs/checklists/`, `docs/playbooks/`, `docs/policies/`, `docs/roadmaps/` |

---

## 4. Index Files

| File | Location | Description |
|------|----------|-------------|
| DIGITAL_LIBRARY_INDEX | `docs/reference/DIGITAL_LIBRARY_INDEX.md` | Standards, references, architectures, tools |
| REFERENCE_CATALOG | `docs/reference/REFERENCE_CATALOG.md` | Searchable reference catalog (80+ entries) |
| KNOWLEDGE_GRAPH | `docs/reference/KNOWLEDGE_GRAPH.md` | Platform knowledge graph |
| MASTER_SYSTEM_ATLAS | `MASTER_SYSTEM_ATLAS.md` | Comprehensive system atlas |
| ADR README | `docs/adr/README.md` | ADR index |
| CLAUDE.md | `CLAUDE.md` | AI assistant guide (primary developer onboarding) |

---

## 5. Document Location Map

```
gula-platform/
├── README.md                          # Quick start, overview
├── CLAUDE.md                          # Developer guide (primary)
├── ARCHITECTURE.md                     # Architecture overview
├── CHANGELOG.md                        # Release history
├── CONTRIBUTING.md                     # Contributing guide
├── QUALITY.md                          # Quality docs
├── SECURITY.md                         # Security overview
├── TESTING.md                          # Testing guide
├── MASTER_SYSTEM_ATLAS.md              # System atlas
├── DOCUMENTATION_INVENTORY.md          # THIS DOCUMENT
├── DOCUMENTATION_GAP_ANALYSIS.md       # Gap analysis (sibling)
├── DOCUMENTATION_COMPLETION_REPORT.md  # Completion report (sibling)
├── docs/
│   ├── adr/                            # ADR records (25 + README)
│   ├── decisions/                      # Decision logs (5)
│   ├── constitution/                   # Platform constitution (31+ articles)
│   ├── architecture/                   # Architecture docs (12)
│   ├── sndhs/                          # SNDHS specification (18)
│   ├── sovereign/                      # Sovereign domain (77)
│   ├── enterprise/                     # Enterprise architecture (22)
│   ├── engineering/                    # Engineering docs (13)
│   ├── production/                     # Production guides (9)
│   ├── national/                       # National platform (12)
│   ├── reference/                      # Reference indexes (3)
│   ├── runbooks/                       # Operational runbooks (7)
│   ├── templates/                      # Document templates (7)
│   ├── ai/                             # AI architecture (4)
│   └── ...                             # 25+ more subdirectories
├── identity_report/                    # Identity certification (8 files)
├── contracts/                          # API contracts, SDKs
├── backend/app/
│   ├── models/README.md                # ORM model documentation
│   ├── routes/README.md                # Route documentation
│   ├── security/README.md              # Security documentation
│   ├── services/README.md              # Service layer documentation
│   └── core/README.md                  # Core infrastructure documentation
├── frontend-v2/README.md               # Frontend documentation
├── services/device_bridge/README.md    # Device bridge docs
├── assessment/                         # Assessment reports (15+)
├── mobile/                             # App store listings
└── architecture/                       # Architecture docs (25 files)
```

---

*Generated by DOCUMENTATION-EXCELLENCE-001 program. Living document — update as documentation evolves.*
