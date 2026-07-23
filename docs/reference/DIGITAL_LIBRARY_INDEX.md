# GULA Platform Digital Library Index

> Version: 1.0 | Status: Living Document | Last Updated: 2026-07-17
> Maintainer: Platform Architecture Team

---

## 1. Healthcare Standards

### 1.1 WHO Standards and Classifications

| Standard | Version | GULA Usage | Location/Reference | Priority |
|----------|---------|------------|-------------------|----------|
| **ICD-10** | 2019 (WHO) | Diagnosis coding for lab orders, visit diagnosis | `backend/app/models/` diagnosis fields | Critical |
| **ICD-11** | 2022 (WHO) | Future migration target (ICD-10 → ICD-11 by 2029) | [who.int/classifications/icd11](https://who.int/classifications/icd11) | Planned |
| **WHO ATC/DDD** | 2024 | Anatomical Therapeutic Chemical classification for lab-related medications | [who.int/atc_ddd](https://who.int/atc_ddd) | Useful |
| **WHO Essential Diagnostics List** | 2023 | Laboratory test catalog alignment | [who.int/diagnostics](https://who.int/diagnostics) | Important |
| **WHODrug Global** | 2024 | Medication coding for lab-interference checking | [who.int/whodrug](https://who.int/whodrug) | Useful |
| **WHO Family of International Classifications (FIC)** | Current | Framework for all health classifications used | [who.int/classifications](https://who.int/classifications) | Important |

### 1.2 HL7 Standards

| Standard | Version | GULA Usage | Location | Priority |
|----------|---------|------------|----------|----------|
| **HL7 v2.x** | 2.5.1 | Lab instrument communication (device_bridge), hospital integration | `services/device_bridge/app/parsers/` | Critical |
| **HL7 FHIR R4** | 4.0.1 | Future API layer (Phase 2+), SNDHS integration | `services/fhir/` (planned) | Critical |
| **HL7 CDA** | R2 | Clinical document exchange (legacy systems) | Not currently used | Referenced |
| **HL7 V2+** | 2.9 | Enhanced lab messaging (future) | Evaluation | Planned |

### 1.3 LOINC

| Aspect | Detail |
|--------|--------|
| **Version** | 2.77 (2025) |
| **Usage** | Lab test coding; all lab tests in GULA mapped to LOINC codes |
| **Coverage** | ~500 LOINC codes currently mapped; target 100% by Phase 2 |
| **Source** | [loinc.org](https://loinc.org) |
| **GULA Implementation** | `backend/app/models/lab_test.py` — `loinc_code` field |
| **Maintenance** | Quarterly LOINC update import; automated mapping validation |
| **Priority** | Critical |

### 1.4 SNOMED CT

| Aspect | Detail |
|--------|--------|
| **Version** | International Edition 2025 (July) |
| **Usage** | Clinical finding coding, result interpretation, patient conditions |
| **Coverage** | ~2,000 SNOMED concepts mapped to lab interpretations |
| **Source** | [snomed.org](https://snomed.org) |
| **GULA Implementation** | `backend/app/models/clinical_finding.py` — `snomed_ct_code` field |
| **Maintenance** | Semi-annual SNOMED release update |
| **Priority** | Critical |

### 1.5 ICD Coding

| Standard | Version | Status in GULA | Migration Plan |
|----------|---------|---------------|----------------|
| **ICD-10-AM** | Australian Modification 10th Ed | Currently used for Iraqi MoH reporting | Maintain until ICD-11 mandate |
| **ICD-11** | WHO 2022 | Evaluation | Full migration by 2029 (Phase 3) |

### 1.6 ISO Standards

| Standard | Title | Version | GULA Relevance | Status |
|----------|-------|---------|---------------|--------|
| **ISO 15189:2022** | Medical laboratories — Requirements for quality and competence | 2022 | Core: lab quality management, QC tracking, proficiency testing | Adopted |
| **ISO 27001:2022** | Information security management | 2022 | Security: ISMS framework, risk management, controls | Adopted |
| **ISO 27799:2016** | Health informatics — Information security management | 2016 | Healthcare-specific security controls | Adopted |
| **ISO 13606:2019** | EHR interoperability | 2019 | Future EHR exchange | Planned (2030) |
| **ISO 22857:2020** | Health informatics — Guidelines on data protection | 2020 | Cross-border data transfer | Referenced |
| **ISO 80001-1:2021** | Risk management for medical IT networks | 2021 | Device bridge security | Important |
| **ISO 8601** | Date/time format | Current | All timestamps use ISO 8601 | Adopted |
| **ISO 3166** | Country codes | Current | Country fields, multi-region | Adopted |
| **ISO 639-1** | Language codes | Current | Arabic (ar), English (en), Kurdish (ku), etc. | Adopted |

### 1.7 Professional Standards

| Standard | Organization | Relevance | Status |
|----------|-------------|-----------|--------|
| **CAP Laboratory Accreditation** | College of American Pathologists | Lab quality, proficiency testing | Evaluating |
| **CLSI Guidelines** | Clinical and Laboratory Standards Institute | Lab procedures, reference ranges, QC | Adopted |
| **CLSI EP28-A3c** | CLSI | Defining, establishing, verifying reference intervals | Important |
| **CLSI C24-Ed4** | CLSI | Statistical quality control | Important |
| **CLSI EP05-A3** | CLSI | Evaluation of precision of quantitative measurement | Important |
| **JCI Accreditation** | Joint Commission International | Hospital lab standards | Evaluating |
| **IQMS (Iraqi Quality Management System)** | Iraqi MoH | National lab quality standards | Critical |
| **EFLM Guidelines** | European Federation of Clinical Chemistry | Lab medicine best practices | Referenced |

### 1.8 Regulatory Standards

| Standard | Region | Relevance | Status |
|----------|--------|-----------|--------|
| **Iraqi MoH Lab Licensing** | Iraq | All labs must be licensed | Critical |
| **Iraqi eHealth Law (draft)** | Iraq | Future regulatory framework | Monitoring |
| **Iraqi Data Protection Law** | Iraq | Patient data privacy | Monitoring |
| **SNDHS Technical Specifications** | Iraq | National HIE integration | Critical |
| **KSA Health Data Law** | KSA | Data localization for Saudi expansion | Planned |
| **UAE Health Data Law** | UAE | Federal/emirate regulations for UAE expansion | Planned |
| **GDPR** | EU | EU patient data protection | Important |
| **HIPAA** | US | US market expansion (future) | Referenced |

---

## 2. Architecture References

### 2.1 Architecture Frameworks

| Framework | Version | Usage in GULA | Location |
|-----------|---------|---------------|----------|
| **TOGAF 10** | 10th Ed | Enterprise architecture planning | Reference methodology |
| **Zachman Framework** | 3.0 | Taxonomy reference | Reference taxonomy |
| **C4 Model** | Current | System documentation, diagram generation | `docs/diagrams/` |
| **Arc42** | Current | Architecture documentation template | `docs/architecture/` |
| **REST API Maturity Model (Richardson)** | - | API evolution: Level 2 → Level 3 (HATEOAS eventual) | API design |
| **Reactive Manifesto** | v2.0 | Async, resilient, responsive design principles | Architecture principles |

### 2.2 Microservices Patterns

| Pattern | Source | GULA Application | Status |
|---------|--------|-----------------|--------|
| **Strangler Fig** | Fowler | Module extraction from monolith | Adopted (mandatory) |
| **Saga** | Distributed computing | Long-running transactions across services | Evaluating |
| **CQRS** | Fowler, Young | Read/write separation for Results, Stats | Planned (Phase 2) |
| **Event Sourcing** | Fowler | Audit log, financial ledger | Planned (Phase 3) |
| **Outbox Pattern** | Transactional messaging | Event publishing (already implemented) | Adopted |
| **Circuit Breaker** | Fowler | DB/Redis isolation (`core/self_healing.py`) | Adopted |
| **Bulkhead** | Resilience engineering | Per-service connection pools | Adopted |
| **Backend-for-Frontend (BFF)** | SoundCloud | API per client type | Planning |
| **API Gateway** | Microservices | nginx api-gateway | Adopted |
| **Service Mesh** | Istio/Linkerd | Inter-service communication (future) | Planned |
| **Sidecar** | Deployment pattern | Istio sidecar injection | Planned (Phase 2) |
| **Ambassador** | Deployment pattern | Service proxy | Evaluating |
| **Twelve-Factor App** | Heroku | Config, logging, disposability | Adopted (guiding) |

### 2.3 Domain-Driven Design

| Resource | Type | Relevance | Location |
|----------|------|-----------|----------|
| **Domain-Driven Design (Evans)** | Book | Core strategic design methodology | General reference |
| **Implementing Domain-Driven Design (Vernon)** | Book | Tactical patterns (Aggregates, Value Objects) | General reference |
| **Strategic DDD (Context Mapping)** | Practice | Bounded context identification | `docs/evolution/FUTURE_ARCHITECTURE.md` |
| **Event Storming** | Practice | Domain event identification | `docs/evolution/FUTURE_ARCHITECTURE.md` #4 |
| **Domain Events** | Pattern | Inter-service communication | `backend/app/services/outbox_service.py` |

### 2.4 Integration Patterns

| Pattern | Reference | Usage | Status |
|---------|-----------|-------|--------|
| Enterprise Integration Patterns | Hohpe, Woolf | Message routing, transformation, endpoints | Reference |
| Request-Reply | Messaging | Synchronous inter-service calls | Adopted |
| Publish-Subscribe | Messaging | Event-driven communication | Adopted |
| Competing Consumers | Scalability | Background worker processing | Adopted |
| Dead Letter Queue | Reliability | Failed message handling | Planning |

---

## 3. Security References

### 3.1 Industry Standards

| Standard | Version | Relevance | Status |
|----------|---------|-----------|--------|
| **OWASP Top 10** | 2021 | Web application vulnerabilities | Critical |
| **OWASP ASVS** | 4.0.3 | Application security verification | Important |
| **OWASP MASVS** | 2.0 | Mobile app security (frontend-v2) | Important |
| **NIST SP 800-53** | Rev 5 | Security controls framework | Adopted |
| **NIST SP 800-207** | 2020 | Zero Trust architecture | Planned (Phase 3) |
| **NIST Cybersecurity Framework** | 2.0 | Overall security program | Adopted |
| **CIS Controls** | v8 | Prioritized security actions | Important |
| **PCI DSS** | 4.0 | Payment security (Financial Engine Phase B) | Planned |

### 3.2 Cryptographic References

| Standard | Usage | GULA Implementation |
|----------|-------|---------------------|
| **AES-256-GCM** | Patient data encryption | `ENCRYPTION_KEY` in `config.py` |
| **HMAC-SHA256** | Patient card tokens, NID blind index | `NID_HMAC_KEY`, `DEVICE_HMAC_KEY` |
| **Argon2** | Password hashing (future) | Evaluating (currently bcrypt) |
| **JWT (RFC 7519)** | Authentication tokens | `security/auth.py` |
| **OAuth 2.0 (RFC 6749)** | Authorization framework | Planned (Phase 1) |
| **OpenID Connect** | Identity layer | Planned (Phase 1) |
| **TLS 1.3** | Transport security | nginx termination |
| **mTLS** | Service-to-service auth | Planned (Phase 2) |
| **BLAKE2** | Future hashing | Evaluating |

### 3.3 Compliance References

| Requirement | Source | GULA Compliance |
|-------------|--------|-----------------|
| Patient consent management | Iraqi MoH, GDPR | In design |
| Data breach notification | Iraqi Data Protection Law | Procedure needed |
| Right to access | GDPR | Patient data export API needed |
| Right to erasure | GDPR | Partial (medical records retention exception) |
| Data portability | GDPR | FHIR export |
| Data localization | KSA/UAE laws | Per-region data storage |
| Audit trail integrity | ISO 15189, Iraqi MoH | Audit chain v2 implemented |
| Encryption at rest | ISO 27001, HIPAA | AES-256-GCM |
| Encryption in transit | All standards | TLS 1.3 |

---

## 4. AI/ML References

### 4.1 Clinical AI Best Practices

| Resource | Publisher | Relevance | Status |
|----------|-----------|-----------|--------|
| **WHO Ethics and Governance of AI for Health** | WHO 2021 | AI ethics framework | Adopted |
| **FDA AI/ML-Based Software as a Medical Device** | FDA | Regulatory framework (US expansion) | Referenced |
| **EU AI Act** | European Commission | AI regulation (GDPR context) | Monitoring |
| **HL7 FHIR for ML** | HL7 | ML on FHIR data | Evaluating |
| **ClinicalBERT** | Research | Clinical NLP baseline | Referenced |
| **Arabic Clinical BERT** | Research | Arabic NLP for clinical notes | Evaluating |
| **Llama/Mistral (Arabic fine-tune)** | Open source | Arabic clinical LLM foundation | Evaluating (Phase 3) |
| **SHAP/LIME** | Interpretability | Model explanation | Adopted |
| **MLflow** | Model lifecycle | Model registry, experiment tracking | Planned |

### 4.2 AI/ML Architecture

| Component | Technology | Stage | Notes |
|-----------|-----------|-------|-------|
| Model Registry | MLflow | Phase 3 | Track experiments, model versions |
| Feature Store | Feast | Phase 3 | Consistent feature computation |
| Training Pipeline | Kubeflow | Phase 3 | GPU cluster training |
| Cloud Inference | FastAPI + ONNX | Phase 2 | GPU-serving for complex models |
| Edge Inference | ONNX Runtime | Phase 2 | Lightweight models on edge_agent |
| LLM Serving | vLLM / TGI | Phase 3 | Arabic clinical LLM serving |
| A/B Testing | Shadow mode | Phase 2 | Compare model versions |
| Monitoring | Prometheus + custom metrics | Phase 2 | Model drift, accuracy |

### 4.3 Key AI Publications for GULA

| Publication | Year | Relevance |
|------------|------|-----------|
| Rajkomar et al., "Scalable and accurate deep learning for EHR" | 2018 | Foundation for clinical ML |
| Topol, "High-performance medicine: AI convergence" | 2019 | AI in clinical practice |
| Nasa et al., "Critical value reporting in lab medicine" | 2020 | Critical value detection |
| WHO "Digital Health Guidelines" | 2020 | Digital health standards |
| Iraqi MoH "National eHealth Strategy" | 2021 | National digital health direction |

---

## 5. Developer Guides

### 5.1 Backend

| Technology | Version | Guide | Location |
|-----------|---------|-------|----------|
| **Python** | 3.11+ | Official docs | [python.org/docs](https://python.org/docs) |
| **FastAPI** | 0.115+ | FastAPI docs | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| **Uvicorn** | 0.34+ | ASGI server | [uvicorn.org](https://uvicorn.org) |
| **Gunicorn** | 23.0+ | WSGI/ASGI workers | [gunicorn.org](https://gunicorn.org) |
| **SQLAlchemy** | 2.0+ | ORM, async | [sqlalchemy.org](https://sqlalchemy.org) |
| **Alembic** | 1.14+ | Migrations | [alembic.sqlalchemy.org](https://alembic.sqlalchemy.org) |
| **Pydantic** | 2.x | Data validation, settings | [docs.pydantic.dev](https://docs.pydantic.dev) |
| **Redis** (redis-py) | 5.x | Cache, streams | [redis-py.readthedocs.io](https://redis-py.readthedocs.io) |
| **Starlette** | 0.41+ | ASGI toolkit (FastAPI base) | [starlette.io](https://starlette.io) |
| **Pytest** | 8.x | Testing | [docs.pytest.org](https://docs.pytest.org) |
| **httpx** | 0.28+ | HTTP client (async testing) | [httpx.org](https://httpx.org) |
| **Flake8** | 7.x | Linting (E9, F821 rules) | [flake8.pycqa.org](https://flake8.pycqa.org) |
| **Pyflakes** | 3.x | Linting (CI) | [pypi.org/pyflakes](https://pypi.org/pyflakes) |

### 5.2 Frontend

| Technology | Version | Guide | Location |
|-----------|---------|-------|----------|
| **React** | 19.x | Official docs | [react.dev](https://react.dev) |
| **TypeScript** | 5.x | TypeScript handbook | [typescriptlang.org](https://typescriptlang.org) |
| **Firebase** | 11.x | Firebase docs (Auth, Firestore) | [firebase.google.com/docs](https://firebase.google.com/docs) |
| **tRPC** | 11.x | tRPC docs (`client/` app) | [trpc.io](https://trpc.io) |
| **Vite** | 6.x | Build tool | [vite.dev](https://vite.dev) |
| **Tailwind CSS** | 4.x | Styling | [tailwindcss.com](https://tailwindcss.com) |

### 5.3 DevOps

| Technology | Version | Guide | Location |
|-----------|---------|-------|----------|
| **Docker** | 27.x | Docker docs | [docs.docker.com](https://docs.docker.com) |
| **Docker Compose** | 2.x | Orchestration | [docs.docker.com/compose](https://docs.docker.com/compose) |
| **Kubernetes** | 1.31+ | K8s docs | [kubernetes.io/docs](https://kubernetes.io/docs) |
| **Terraform** | 1.10+ | IaC | [developer.hashicorp.com/terraform](https://developer.hashicorp.com/terraform) |
| **GitHub Actions** | - | CI/CD | [docs.github.com/actions](https://docs.github.com/actions) |
| **Helm** | 3.x | K8s packaging | [helm.sh](https://helm.sh) |
| **ArgoCD** | 2.x | GitOps | [argo-cd.readthedocs.io](https://argo-cd.readthedocs.io) |
| **Prometheus** | 3.x | Metrics | [prometheus.io/docs](https://prometheus.io/docs) |
| **Grafana** | 11.x | Dashboards | [grafana.com/docs](https://grafana.com/docs) |
| **Cloudflare** | - | CDN, WAF, Workers | [developers.cloudflare.com](https://developers.cloudflare.com) |

---

## 6. Operational Manuals

### 6.1 Database Administration

| Topic | Resource | Location |
|-------|----------|----------|
| **PostgreSQL 16 Administration** | Official docs | [postgresql.org/docs/16](https://postgresql.org/docs/16) |
| **Performance Tuning** | PostgreSQL Wiki | [wiki.postgresql.org/PerformanceOptimization](https://wiki.postgresql.org/PerformanceOptimization) |
| **Backup and Recovery** | pg_dump/pg_restore | `Makefile` → `make backup` |
| **Replication** | Streaming replication, pglogical | Planned (Phase 2+) |
| **Connection Pooling** | PgBouncer | Planned (Phase 2) |
| **Monitoring** | pg_stat_statements + Prometheus | `config/prometheus/` |
| **Migration Management** | Alembic | `backend/migrations/` |
| **PostGIS** | GIS extension | Future (for lab location mapping) |

### 6.2 Redis Administration

| Topic | Resource | Location |
|-------|----------|----------|
| **Redis 7 Administration** | Official docs | [redis.io/docs](https://redis.io/docs) |
| **Sentinel** | High availability | Planned (Phase 2) |
| **Cluster** | Sharding | Planned (Phase 3) |
| **Persistence** | RDB/AOF | `config/redis/` |
| **Streams** | Event bus | `backend/app/services/outbox_service.py` |
| **Monitoring** | Redis INFO + Prometheus | `config/prometheus/` |

### 6.3 Infrastructure Administration

| Topic | Resource | Location |
|-------|----------|----------|
| **Nginx** | nginx.org docs | `config/nginx/` |
| **HAProxy** | HAProxy docs | `config/haproxy/haproxy.cfg` |
| **Prometheus** | prometheus.io/docs | `config/prometheus/` |
| **Grafana** | grafana.com/docs | `config/grafana/` |
| **DigitalOcean** | DO docs | `digitalocean/`, `scripts/diagnose-droplet.sh` |
| **Cloudflare** | Cloudflare docs | `cloudflare/` |

---

## 7. Medical References

### 7.1 Laboratory Medicine Textbooks

| Title | Author | Relevance |
|-------|--------|-----------|
| **Tietz Textbook of Clinical Chemistry and Molecular Diagnostics** | Rifai, Horvath, Wittwer | Core reference for lab test interpretation |
| **Henry's Clinical Diagnosis and Management by Laboratory Methods** | McPherson, Pincus | Comprehensive lab medicine |
| **Clinical Laboratory Hematology** | McKenzie | Hematology lab testing |
| **Clinical Microbiology Procedures Handbook** | ASM Press | Microbiology testing |
| **Laboratory Quality Management System Handbook** | WHO | ISO 15189 implementation |

### 7.2 Clinical Guidelines

| Guideline | Organization | Relevance |
|-----------|-------------|-----------|
| **Iraqi MoH Lab Testing Protocols** | Iraqi MoH | All lab tests, reference ranges for Iraqi population |
| **WHO Essential Laboratory Tests** | WHO | Primary care lab test selection |
| **CDC Laboratory Guidelines** | CDC | Infectious disease testing |
| **Guidelines for Point-of-Care Testing** | CLSI | POCT management (future) |
| **Reference Ranges for Clinical Laboratory Tests** | Various | Age/gender-specific reference intervals |

### 7.3 Iraqi-Specific Medical References

| Reference | Source | Relevance |
|-----------|--------|-----------|
| **Iraqi National Drug Formulary** | Iraqi MoH | Medication coding |
| **Iraqi Communicable Disease Surveillance** | Iraqi MoH | Notifiable disease reporting |
| **Iraqi Population Health Metrics** | WHO/Iraq | Reference ranges for Iraqi demographics |
| **SNDHS Data Dictionary** | Iraqi MoH | National HIE data fields |

---

## 8. GULA-Specific References

### 8.1 Documentation Index

| Document | Location | Description |
|----------|----------|-------------|
| **CLAUDE.md** | `/CLAUDE.md` | AI assistant guide, architecture overview, conventions |
| **Makefile** | `/Makefile` | All development commands and targets |
| **README** | `/README.md` | Project overview |
| **Docker Compose** | `docker-compose.yml` | Local deployment configuration |
| **Docker Compose Full** | `docker-compose.full.yml` | Full infra (Prometheus, Grafana, HAProxy, Loki) |
| **Docker Compose Scale** | `docker-compose.scale.yml` | Horizontal scaling configuration |
| **CI Pipeline** | `.github/workflows/ci.yml` | CI job definitions |
| **Deploy Pipeline** | `.github/workflows/deploy.yml` | Deployment workflow |
| **Blue-Green Deploy** | `.github/workflows/blue-green-deploy.yml` | Zero-downtime deployment |

### 8.2 Architecture Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **System Context** | `docs/architecture/SYSTEM_CONTEXT.md` | Complete platform context, actors, data flows |
| **Architecture Decision Log** | `docs/architecture/ARCHITECTURE_DECISION_LOG.md` | Chronological decision history |
| **Module Dependency Matrix** | `docs/architecture/MODULE_DEPENDENCY_MATRIX.md` | Module coupling and dependency analysis |
| **Platform Evolution Plan** | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md` | Evolution strategy |
| **Future Architecture** | `docs/evolution/FUTURE_ARCHITECTURE.md` | Target architecture vision |
| **Long-Term Evolution** | `docs/evolution/LONG_TERM_EVOLUTION.md` | 5-10 year roadmap |
| **Digital Library Index** | `docs/reference/DIGITAL_LIBRARY_INDEX.md` | This document |
| **Reference Catalog** | `docs/reference/REFERENCE_CATALOG.md` | Searchable reference catalog |
| **Knowledge Graph** | `docs/reference/KNOWLEDGE_GRAPH.md` | Platform knowledge graph |
| **Domain Glossary** | `docs/domain/DOMAIN_GLOSSARY.md` | Healthcare, lab, admin, clinical terminology |
| **Event Catalog** | `docs/events/EVENT_CATALOG.md` | All published events with producers, consumers |
| **Database Schema** | `docs/database/DATABASE_SCHEMA.md` | Tables, relationships, indexes, constraints |
| **API Coverage** | `docs/api/API_COVERAGE.md` | All API endpoints, coverage analysis |
| **UI Component Catalog** | `docs/frontend/UI_COMPONENT_CATALOG.md` | Reusable frontend components |
| **Workflow Catalog** | `docs/workflows/WORKFLOW_CATALOG.md` | Lab-domain workflows with state machines |
| **Configuration Reference** | `docs/configuration/CONFIGURATION_REFERENCE.md` | All env vars, defaults, secrets |
| **Feature Matrix** | `docs/management/FEATURE_MATRIX.md` | Feature status across backend/frontend/API/tests |

### 8.3 Architecture Decision Records (ADRs)

| ADR | Location | Status |
|-----|----------|--------|
| **ADR Index + 25 records** | `docs/adr/` | Active |
| **Architecture Decision Log** | `docs/architecture/ARCHITECTURE_DECISION_LOG.md` | Active |
| **Decision Logs** | `docs/decisions/` | Active |

### 8.4 SNDHS Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **SNDHS Architecture** | `docs/sndhs/` | Full SNDHS architecture (22 files) |
| **Phase 1 Runbook** | `docs/sndhs/phase1/RUNBOOK.md` | Production deployment guide |
| **Backfill Script** | `scripts/sndhs_phase1_backfill.py` | Data backfill for SNDHS fields |
| **Rollback SQL** | `scripts/sndhs_phase1_rollback.sql` | Rollback SNDHS migration |
| **Disable Script** | `scripts/sndhs_phase1_disable_flags.sh` | Disable SNDHS flags |

### 8.5 Migration Files

| Migration | Location | Description |
|-----------|----------|-------------|
| Base Schema | `backend/migrations/versions/20250322_0000_create_base_schema.py` | Bootstrap (immutable) |
| SNDHS Patients | `backend/migrations/versions/20260505_0001_sndhs_phase1_extend_patients.py` | National ID fields |
| SNDHS Index | `backend/migrations/versions/20260505_0002_sndhs_phase1_index_national_id.py` | Indexes |
| SNDHS Visits | `backend/migrations/versions/20260505_0003_sndhs_phase1_visits_table.py` | Visits table |
| SNDHS Orders | `backend/migrations/versions/20260505_0004_sndhs_phase1_lab_orders_visit_id.py` | Order-visit link |
| SNDHS Audit | `backend/migrations/versions/20260505_0005_sndhs_phase1_audit_logs_v2.py` | Audit v2 |
| SNDHS Constraints | `backend/migrations/versions/20260505_0006_sndhs_phase1_constraints.py` | Constraints |
| Financial Phase A | `backend/migrations/versions/20260505_0001_financial_engine_phase_a.py` | Financial schema |

### 8.6 Code Architecture References

| Component | Location | Lines | Description |
|-----------|----------|-------|-------------|
| **App Entry Point** | `backend/app/main.py` | ~500 | FastAPI app, lifespan, middleware, routes |
| **Config** | `backend/app/config.py` | ~400 | Environment configuration |
| **Database** | `backend/app/database.py` | ~200 | SQLAlchemy engine, pool, contextvars |
| **Self-Healing** | `backend/app/core/self_healing.py` | ~300 | Circuit breaker, degraded mode |
| **Auto-Repair** | `backend/app/core/auto_repair.py` | ~200 | GC, pool recycle |
| **Startup Guard** | `backend/app/core/startup_guard.py` | ~150 | `system_ready` flag |
| **Feature Flags** | `backend/app/core/feature_flags.py` | ~100 | Per-tenant flags |
| **SNDHS Flags** | `backend/app/core/sndhs_flags.py` | ~100 | Deployment-wide flags |
| **RBAC** | `backend/app/security/rbac.py` | ~150 | 9 roles × 13 permissions |
| **Auth** | `backend/app/security/auth.py` | ~300 | JWT, get_current_user |
| **Order State Machine** | `backend/app/domain/order_state.py` | ~150 | Lab order state machine |

### 8.7 Test References

| Test Module | Location | Coverage |
|-------------|----------|----------|
| Integration Tests | `backend/tests/test_comprehensive.py` | All major routes |
| Stress Tests | `backend/tests/test_stress.py` | Performance under load |
| System Tests | `backend/tests/test_system_improvements.py` | Clinical interpretation, stats, AI |
| Security Tests | `backend/tests/test_security.py` | JWT, auth, encryption |
| Patient Card Tests | `backend/tests/test_patient_card.py` | QR cards, HMAC tokens |
| MPI Tests | `backend/tests/test_mpi_matcher.py` | Patient deduplication |
| Outbox Tests | `backend/tests/test_outbox_service.py` | Event outbox |
| Feature Flag Tests | `backend/tests/test_feature_flags.py` | Feature matrix |
| Edge Platform Tests | `backend/tests/test_edge_platform.py` | Edge sync |
| Stability Tests | `backend/tests/test_stability_assertions.py` | Data integrity |

### 8.8 Scripts

| Script | Location | Purpose |
|--------|----------|---------|
| Self-Audit Agent | `scripts/self_audit_agent.py` | Claude-powered code audit |
| Diagnose Droplet | `scripts/diagnose-droplet.sh` | Read-only diagnostics |
| Repair Droplet | `scripts/repair-droplet.sh` | Destructive repair |
| SNDHS Backfill | `scripts/sndhs_phase1_backfill.py` | National ID backfill |
| SNDHS Rollback | `scripts/sndhs_phase1_rollback.sql` | Rollback migration |
| Disable Flags | `scripts/sndhs_phase1_disable_flags.sh` | Disable SNDHS |

### 8.9 Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| **Main Docker Compose** | `docker-compose.yml` | Core services |
| **Full Stack** | `docker-compose.full.yml` | Monitoring stack |
| **Scale Config** | `docker-compose.scale.yml` | Horizontal scaling |
| **HAProxy Config** | `config/haproxy/haproxy.cfg` | Load balancing |
| **Prometheus Config** | `config/prometheus/` | Metrics scraping |
| **Grafana Dashboards** | `config/grafana/` | Provisioned dashboards |
| **Supabase Config** | `supabase/` | Managed Postgres |
| **K8s Manifests** | `k8s/` | Kubernetes deployment |
| **Cloudflare Config** | `cloudflare/` | DNS, Workers, CDN |
| **DigitalOcean Config** | `digitalocean/` | Droplet deployment |

### 8.8 Operational & Release Documentation

| Document | Location | Description |
|----------|----------|-------------|
| **Migration Guide** | `docs/deployment/MIGRATION_GUIDE.md` | Upgrade process, rollback, schema migration |
| **Compatibility Matrix** | `docs/platform/COMPATIBILITY_MATRIX.md` | OS/browser/DB/Redis/Docker/K8s compatibility |
| **Support Policy** | `docs/release/SUPPORT_POLICY.md` | Release lifecycle, LTS, EOL, upgrade path |
| **Known Limitations** | `docs/release/KNOWN_LIMITATIONS.md` | Current limitations and technical debt |
| **Documentation Inventory** | `DOCUMENTATION_INVENTORY.md` | Complete documentation file inventory |
| **Documentation Gap Analysis** | `DOCUMENTATION_GAP_ANALYSIS.md` | Gap analysis against enterprise standards |

### 8.9 Routes Reference

| Route Module | Path | Description |
|-------------|------|-------------|
| Patient Card | `backend/app/routes/patient_card.py` | QR-backed digital patient cards |
| Stats | `backend/app/routes/stats.py` | Statistics and trends |
| Edge | `backend/app/routes/edge.py` | Edge platform |
| AI | `backend/app/routes/ai.py` | Clinical intelligence |
| Compliance | `backend/app/routes/compliance.py` | Regulatory compliance |
| +31 other route modules | `backend/app/routes/` | Auth, labs, orders, results, samples, etc. |

---

## Appendix A: Document Maintenance

This index is maintained by the Platform Architecture Team. Updates:
- **Monthly**: Verify links, add new references
- **Quarterly**: Update versions for standards and technologies
- **Annually**: Full review and reorganization

## Appendix B: Reading Recommendations

| Role | Start Here |
|------|------------|
| **New Developer** | `CLAUDE.md` → `Makefile` → `backend/app/main.py` |
| **Platform Architect** | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md` → `docs/evolution/FUTURE_ARCHITECTURE.md` |
| **Security Engineer** | `backend/app/security/` → `backend/app/core/self_healing.py` |
| **Frontend Developer** | `frontend-v2/` → `client/` |
| **DevOps Engineer** | `docker-compose.yml` → `Makefile` → `.github/workflows/` |
| **AI/ML Engineer** | `backend/app/ai/` → `docs/evolution/FUTURE_ARCHITECTURE.md` #9 |
| **Lab Domain Expert** | `backend/app/domain/order_state.py` → `backend/app/models/` |
| **SNDHS Integrator** | `docs/sndhs/` → `scripts/sndhs_phase1_backfill.py` |
| **Healthcare Standards** | This document → LOINC/SNOMED resources → FHIR documentation |

---

*End of Digital Library Index*
