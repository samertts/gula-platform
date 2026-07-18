# GULA Capability Maturity Matrix

**Version:** 1.0  
**Date:** 2026-07-18  
**Classification:** INTERNAL  

---

## Maturity Scale

| Level | Label | Description |
|-------|-------|-------------|
| 0 | Missing | Capability does not exist |
| 1 | Prototype | Experimental, incomplete, not production-ready |
| 2 | MVP | Minimum Viable Product, functional but limited |
| 3 | Production | Fully functional, tested, deployed |
| 4 | Enterprise | Scalable, compliant, hardened, integrated |
| 5 | World Class | Best-in-class, benchmarked, reference architecture |

---

## 1. Platform Core

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| Application Kernel | 3.5 | Production | Kernel subsystem (32 items) with DI, event bus, plugin system — but dual-system with legacy monolith |
| Configuration Management | 4.5 | Enterprise | `config.py` with fail-safe secrets, runtime-mode isolation, 100+ env vars, dual feature flags |
| Module System | 2.5 | MVP | Capability framework exists (12 modules) with CQRS pattern; 70 flat packages with inconsistent structure |
| Plugin Interface | 2.0 | MVP | Kernel plugin system with sandbox/hot-reload/permissions; not used by legacy monolith |
| Feature Flags | 4.0 | Enterprise | Per-tenant (DB-backed) + deployment-wide (env-var) dual system; permission versioning |
| Startup Lifecycle | 4.0 | Enterprise | Atomic startup guard, hybrid readiness, graceful degradation, 12-phase kernel boot |
| Health Endpoints | 5.0 | World Class | 5 endpoints (/health, /live, /ready, /status, /deep) with grade scoring, component latencies, memory |
| Self-Healing | 4.5 | Enterprise | 3-layer: circuit breaker (L1/L2/L3), auto-repair engine, adaptive concurrency; health watchdog |
| **Core Average** | **3.6** | **Production/Enterprise** | |

## 2. Security

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| Authentication (JWT) | 4.5 | Enterprise | JWT with token type discrimination, blacklist, refresh rotation, timing-safe login |
| Authorization (RBAC/ABAC) | 4.5 | Enterprise | 9 roles × 13 permissions, ABAC for tenant isolation, O(1) permission version check |
| Multi-Factor Auth | 3.5 | Production | TOTP MFA implemented in routes |
| OAuth2 / OIDC | 3.5 | Production | OAuth2 provider implemented, SAML SSO implemented |
| Passkeys | 0.0 | Missing | Not implemented |
| Secrets Management | 5.0 | World Class | Hard fail on missing/weak, rotation scripts, Vault configured |
| Encryption at Rest | 4.5 | Enterprise | Fernet AES-256 for PII, national ID; HMAC for cards |
| Encryption in Transit | 4.5 | Enterprise | TLS 1.3 at nginx, mTLS via Linkerd mesh |
| Audit Logging | 5.0 | World Class | Immutable hash-chain, correlation IDs, tamper detection, enhanced v2 for SNDHS |
| Intrusion Detection | 4.0 | Enterprise | Snort IDS, application-layer IDS, Fail2ban |
| SIEM Integration | 4.0 | Enterprise | Wazuh agent + Elastic Security configured |
| Web Application Firewall | 4.5 | Enterprise | nginx WAF with 6 zones, SQLi/XSS/command injection blocking |
| Rate Limiting | 4.5 | Enterprise | 6 zones in nginx + application-level; clinical writes exempt |
| Zero Trust | 4.0 | Enterprise | Linkerd mTLS, continuous verification, least privilege, micro-segmentation |
| Supply Chain Security | 4.0 | Enterprise | Dependabot (5 ecosystems), SBOM, license scanning, Trivy |
| Runtime Protection | 5.0 | World Class | AppArmor (300 lines), seccomp, no-new-privileges, security contexts |
| Threat Modeling | 2.0 | MVP | Security review process exists; formal threat modeling not documented |
| Penetration Testing | 2.0 | MVP | DAST configured (ZAP); external pen test not yet performed |
| Compliance | 3.5 | Production | OWASP Top 10, HIPAA-aware IaC; no formal ISO/SOC certification |
| **Security Average** | **3.8** | **Production/Enterprise** | |

## 3. AI Platform

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| AI Gateway | 4.5 | Enterprise | 8 providers (Ollama, Gemini, OpenAI, Claude, Azure, vLLM, OpenRouter, DeepSeek); failover, cost optimization |
| AI Guardrails | 5.0 | World Class | 10 absolutely-blocked ops, classification (4 levels), sandbox with operation whitelist |
| Human-in-the-Loop | 4.5 | Enterprise | Full approval lifecycle (Pending→Approved→Rejected→Expired→Executed), 30-min TTL |
| RAG Pipeline | 3.5 | Production | Full pipeline (embed→search→build context→LLM→citations); vector store in-memory only |
| Agent Framework | 3.5 | Production | 5 agents (Clinical, Laboratory, Security, Engineering, Citizen); stub-level LLM integration |
| Knowledge Graph | 4.0 | Enterprise | DB-backed, AST-based auto-scanner, 18 node/edge types, BFS traversal, snapshots |
| AI Governance | 4.5 | Enterprise | AI Constitution (7 articles), evaluation framework, model approval, prompt registry |
| AI Security | 4.5 | Enterprise | Prompt injection detection (12 patterns), PII protection (8 types), output validation |
| AI Observability | 4.0 | Enterprise | Usage tracking, p50/p95/p99 latency, cost tracking, per-model breakdowns, error monitoring |
| AI Cost Management | 3.0 | Production | Cost tracking implemented; optimization (local-first, caching) in progress |
| Offline AI | 2.0 | MVP | Ollama support configured for local inference; not fully integrated |
| Edge AI | 1.5 | Prototype | Edge agent exists; AI inference at edge not yet functional |
| Model Registry | 2.0 | MVP | Model approval workflow exists; full registry with versioning in progress |
| Prompt Registry | 3.5 | Production | Versioned prompts with lifecycle (draft→review→approved→active→deprecated→retired) |
| Evaluation Framework | 3.5 | Production | 7 dimensions (accuracy, bias, safety, hallucination, toxicity, fairness, robustness) |
| Hallucination Detection | 2.5 | MVP | Framework exists; production detection not fully implemented |
| A/B Testing | 0.0 | Missing | Not implemented |
| Fine-tuning Pipeline | 0.0 | Missing | Not implemented |
| **AI Average** | **3.1** | **Production** | |

## 4. Healthcare Platform

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| LIMS (Laboratory) | 5.0 | World Class | Full specimen lifecycle, Westgard QC, EQA, instruments, inventory, cold chain, chain of custody |
| EHR (Patient Records) | 4.5 | Enterprise | 14 model files (notes, meds, allergies, immunizations, family/social history, etc.) |
| Clinical Terminology | 5.0 | World Class | 10 standards (LOINC, SNOMED CT, ICD-10/11, RxNorm, ATC, CPT, UCUM) with full data models |
| Clinical Decision Support | 3.5 | Production | Comprehensive models (order sets, bundles, alerts, contraindications); limited service implementation |
| FHIR R4 | 3.0 | Production | Complete mappers for 5 resources; no FHIR API server deployed |
| HL7 v2.x | 4.0 | Enterprise | Device integration handler with ORU^R01 parser, ACK builder |
| ASTM E1394 | 4.0 | Enterprise | Lab device protocol handler with full frame parser |
| DICOM | 1.0 | Prototype | Radiology device integration exists; full DICOM not implemented |
| IHE Profiles | 0.0 | Missing | Not implemented |
| Radiology/PACS | 4.0 | Enterprise | Full modality management, imaging orders, PACS integration, AI-assisted reading |
| Pharmacy | 4.0 | Enterprise | Clinical decision support, inventory, dispensing, services |
| Blood Bank | 4.0 | Enterprise | DDD architecture, compatibility engine, domain entities |
| Nursing | 3.5 | Production | Medication administration, coordination, care planning |
| Critical Care | 3.5 | Production | DDD architecture, ICU-specific workflows |
| Emergency Services | 3.5 | Production | Dispatch, transport, handoff |
| Public Health | 3.5 | Production | Disease surveillance, outbreak management, population health |
| Hospital Information | 2.0 | MVP | Stub module (3 files); not production-ready |
| Device Integration | 4.0 | Enterprise | Sysmex, Roche, Mindray, generic connectors; ASTM/HL7 protocol support |
| Offline/Edge | 3.0 | Production | Edge agent with sync; conflict resolution implemented |
| Health Data Platform | 4.5 | Enterprise | ODS, warehouse, data lake, MDM, event store, streaming, governance |
| National Health Data | 3.0 | Production | NHDW models, SNDHS Phase 1 integration, national notification |
| Citizen Platform | 4.0 | Enterprise | 22 files covering PHR, telemedicine, appointments, messaging |
| Research Platform | 4.0 | Enterprise | 19 files (epidemiology, GIS, precision health, privacy) |
| **Healthcare Average** | **3.6** | **Production/Enterprise** | |

## 5. Infrastructure & Operations

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| Containerization | 5.0 | World Class | Multi-stage builds, resource limits, healthchecks, security contexts, profiles |
| Docker Compose | 5.0 | World Class | MVP + Full + Scale compose files; production-hardened patterns |
| Kubernetes | 4.0 | Enterprise | Kustomize + Helm + Linkerd + HPA; multi-environment overlays |
| Infrastructure as Code | 5.0 | World Class | Terraform with 12 modules, 5 environments, multi-region AWS, PHI tagging |
| CI Pipeline | 5.0 | World Class | 6 gated jobs, syntax/migration/contract/smoke/security gates, matrix builds, Trivy scan |
| CD Pipeline | 3.0 | Production | Blue-green/canary/auto-rollback scripts; not in CI workflows |
| Monitoring | 5.0 | World Class | Prometheus + 5 exporters + OTel Collector; 10 Grafana dashboards; 21 alert rules |
| Logging | 4.5 | Enterprise | Structured JSON, Loki aggregation, correlation IDs, DB query logging |
| Tracing | 4.0 | Enterprise | OpenTelemetry (3 pipelines), Tempo, Jaeger configured |
| Alerting | 4.5 | Enterprise | Alertmanager with Slack/PD/Email, 21 rules, health watchdog, escalation |
| Backup | 5.0 | World Class | Continuous backup + WAL archiving + S3 + SHA-256 + PITR + restore validation |
| Disaster Recovery | 4.5 | Enterprise | Cross-region DR, automated failover/failback, DR testing, multi-region topology |
| Service Mesh | 4.0 | Enterprise | Linkerd configured for mTLS, traffic splitting |
| Secret Management | 5.0 | World Class | Hard fail on missing, weak detection, rotation, Vault, KMS |
| Performance Testing | 4.0 | Enterprise | k6 + Locust + pytest stress/load/soak/spike/chaos; not fully in CI |
| Chaos Engineering | 4.0 | Enterprise | Chaos Mesh + shell-based chaos + pytest chaos tests |
| **Infrastructure Average** | **4.4** | **Enterprise** | |

## 6. Testing & Quality

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| Unit Tests | 4.0 | Enterprise | 1,755 test functions across 108 test files |
| Integration Tests | 4.0 | Enterprise | Sophisticated test infrastructure (SQLite with savepoint isolation, session-scoped engine) |
| Security Tests | 4.5 | Enterprise | JWT, auth, encryption, RBAC, tenant isolation, resilience, intrusion detection tests |
| Clinical Safety Tests | 5.0 | World Class | Boundary tests for every analyte, critical threshold validation, role enforcement, optimistic locking |
| Performance Tests | 4.0 | Enterprise | Throughput assertions, latency budgets, query counting, memory stability |
| Load Tests | 4.0 | Enterprise | k6 (4 scenarios) + Locust (3 user types) + custom pytest |
| Chaos Tests | 4.0 | Enterprise | DB outage, Redis outage, circuit breaker, tenant isolation under degradation |
| E2E Tests | 1.0 | Prototype | No browser-based E2E tests (Playwright/Cypress not implemented) |
| Frontend Tests | 1.0 | Prototype | No automated frontend tests |
| Linting | 5.0 | World Class | Ruff (all rules), pre-commit hooks, CI enforcement |
| Type Checking | 4.5 | Enterprise | Mypy strict mode with SQLAlchemy/Pydantic plugins |
| Coverage Measurement | 4.0 | Enterprise | Comprehensive measurement with module-level targets; overall 54% |
| Quality Gates | 5.0 | World Class | 9 quality gates (architecture, performance, security, database, API, FHIR, scalability, accessibility, offline) |
| **Testing Average** | **3.8** | **Production/Enterprise** | |

## 7. Developer Experience

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| CLI Tools | 3.0 | Production | Makefile automation (50+ targets), Python CLI package |
| Hot Reload | 2.0 | MVP | Standard development server; not fully optimized for rapid iteration |
| Documentation | 4.0 | Enterprise | 648 markdown files, 24 ADRs, 25 architecture documents, runbooks, playbooks |
| API Documentation | 4.0 | Enterprise | OpenAPI auto-generation, CI-enforced contract verification |
| Templates | 3.0 | Production | Module structures exist; no formal generator |
| SDK | 1.5 | Prototype | Contracts directory exists (DTOs, FHIR specs); no packaged SDK |
| Developer Portal | 1.0 | Prototype | No dedicated developer portal |
| Debugging | 3.0 | Production | Structured logging, correlation IDs; no remote debugging configured |
| Generator Tools | 2.0 | MVP | Some automation scripts; no module/API/service generators |
| **DX Average** | **2.6** | **Production** | |

## 8. Business Readiness

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| Subscription Model | 3.5 | Production | Tier-based subscription with feature flags, route enforcement |
| Marketplace | 1.0 | Prototype | Plugin marketplace concept exists; not implemented |
| Enterprise Licensing | 1.0 | Prototype | No enterprise license model |
| Government Licensing | 2.0 | MVP | SNDHS integration shows government capability; no formal government licensing |
| Support Model | 2.0 | MVP | Community/professional/enterprise tiers defined; not operationalized |
| Billing Engine | 1.0 | Prototype | Financial Engine Phase A (schema only); no billing routes |
| Business Analytics | 3.0 | Production | Dashboard analytics, business KPI tracking, subscription metrics |
| Partner Network | 1.0 | Prototype | No formal partner program |
| **Business Average** | **1.8** | **MVP** | |

## 9. National Readiness

| Capability | Score | Level | Evidence |
|-----------|-------|-------|----------|
| SNDHS Integration | 3.0 | Production | Phase 1 complete (patients, visits, audit v2, national ID); 6 migrations |
| National ID | 3.0 | Production | Encrypted national ID field with HMAC key |
| National Health Data | 2.5 | MVP | NHDW models, ETL pipeline; not production-deployed |
| Citizen Platform | 3.0 | Production | Portal with PHR, telemedicine, messaging; not fully deployed |
| Government API | 2.0 | MVP | Gateway adapter concept exists; no government-facing API server |
| Arabic Support | 4.0 | Enterprise | Arabic-first design, bilingual error responses, Arabic PDFs |
| Local Regulations | 2.5 | MVP | Iraqi MoH integration; broader regulatory coverage incomplete |
| **National Average** | **2.9** | **MVP/Production** | |

## 10. Overall Maturity Summary

| Domain | Score | Level | Priority |
|--------|-------|-------|----------|
| Infrastructure & Operations | 4.4 | Enterprise | Maintain |
| Security | 3.8 | Enterprise | Maintain |
| Testing & Quality | 3.8 | Enterprise | Improve routes/services coverage |
| Platform Core | 3.6 | Enterprise | Resolve architectural drift |
| Healthcare | 3.6 | Enterprise | Complete FHIR API, Hospital module |
| AI Platform | 3.1 | Production | Connect pgvector, complete agent implementations |
| National Readiness | 2.9 | Production | Complete SNDHS Phase 2, NHDW deployment |
| Developer Experience | 2.6 | Production | Invest in SDK, generators, dev portal |
| Business Readiness | 1.8 | MVP | Address business model, licensing, marketplace |
| **Overall** | **3.4** | **Production** | |

---

*This capability matrix is based on thorough repository analysis. Scores reflect actual evidence, not aspirations.*
