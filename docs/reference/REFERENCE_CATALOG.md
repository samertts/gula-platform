# GULA Platform Reference Catalog

> Version: 1.0 | Status: Living Document | Last Updated: 2026-07-17
> Total Entries: 80+

---

## Catalog Legend

| Field | Description |
|-------|-------------|
| **ID** | Unique reference identifier |
| **Category** | Health/Security/Architecture/Tech/Medical/GULA |
| **Title** | Reference name |
| **Source** | Publisher/Organization |
| **Version** | Version number/date |
| **Relevance** | Critical/Important/Useful |
| **Status** | Adopted/Evaluating/Planned/Referenced |
| **Location** | URL or file path |

---

## Healthcare Standards (15 entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| H-001 | **ICD-10** | WHO | 2019 | Critical | Adopted | `backend/app/models/` — diagnosis fields |
| H-002 | **ICD-11** | WHO | 2022 | Critical | Planned | [who.int/classifications/icd11](https://who.int/classifications/icd11) |
| H-003 | **LOINC** | Regenstrief Institute | 2.77 | Critical | Adopted | `backend/app/models/lab_test.py` — loinc_code |
| H-004 | **SNOMED CT International** | SNOMED International | 2025 July | Critical | Adopted | `backend/app/models/clinical_finding.py` — snomed_ct_code |
| H-005 | **HL7 v2.5.1** | HL7 International | 2.5.1 | Critical | Adopted | `services/device_bridge/app/parsers/` |
| H-006 | **HL7 FHIR R4** | HL7 International | 4.0.1 | Critical | Planned | `services/fhir/` (planned) |
| H-007 | **HL7 CDA R2** | HL7 International | R2 | Useful | Referenced | Not integrated |
| H-008 | **ISO 15189:2022** | ISO | 2022 | Critical | Adopted | Lab quality framework |
| H-009 | **ISO 27001:2022** | ISO | 2022 | Critical | Adopted | Security management framework |
| H-010 | **ISO 27799:2016** | ISO | 2016 | Important | Adopted | Healthcare security |
| H-011 | **ISO 13606:2019** | ISO | 2019 | Important | Planned | EHR interoperability |
| H-012 | **CAP Laboratory Accreditation** | CAP | Latest | Important | Evaluating | [cap.org](https://cap.org) |
| H-013 | **CLSI EP28-A3c Reference Intervals** | CLSI | A3c | Important | Adopted | Reference range methodology |
| H-014 | **CLSI C24-Ed4 QC** | CLSI | Ed4 | Important | Adopted | Statistical QC |
| H-015 | **WHO Essential Diagnostics List** | WHO | 2023 | Important | Referenced | [who.int/diagnostics](https://who.int/diagnostics) |

---

## Security Frameworks (12 entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| S-001 | **OWASP Top 10** | OWASP | 2021 | Critical | Adopted | [owasp.org/Top10](https://owasp.org/Top10) |
| S-002 | **OWASP ASVS** | OWASP | 4.0.3 | Important | Adopted | [owasp.org/ASVS](https://owasp.org/ASVS) |
| S-003 | **OWASP MASVS** | OWASP | 2.0 | Important | Referenced | Mobile app security |
| S-004 | **NIST SP 800-53 Rev 5** | NIST | Rev 5 | Critical | Adopted | Security controls |
| S-005 | **NIST SP 800-207 Zero Trust** | NIST | 2020 | Important | Evaluating | Zero Trust architecture |
| S-006 | **NIST Cybersecurity Framework** | NIST | 2.0 | Important | Adopted | [nist.gov/cyberframework](https://nist.gov/cyberframework) |
| S-007 | **CIS Controls v8** | CIS | v8 | Important | Referenced | [cisecurity.org/controls](https://cisecurity.org/controls) |
| S-008 | **PCI DSS** | PCI SSC | 4.0 | Useful | Planned | Payment security (Phase B) |
| S-009 | **HIPAA Privacy/Security Rules** | HHS | Final Rule | Important | Referenced | US expansion reference |
| S-010 | **GDPR** | EU | 2018 | Important | Referenced | EU patient data |
| S-011 | **Iraqi eHealth Law** | Iraq MoH | Draft | Critical | Monitoring | Future regulation |
| S-012 | **Iraqi Data Protection Law** | Iraq | Draft | Critical | Monitoring | Patient data privacy |

---

## Architecture Patterns (12 entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| A-001 | **Strangler Fig Pattern** | Fowler | - | Critical | Adopted | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md` |
| A-002 | **Saga Pattern** | Distributed systems | - | Important | Evaluating | Transaction management |
| A-003 | **CQRS** | Fowler/Young | - | Important | Planned | Read/write separation (Phase 2) |
| A-004 | **Event Sourcing** | Fowler | - | Important | Planned | Audit, financial (Phase 3) |
| A-005 | **Outbox Pattern** | Transactional messaging | - | Critical | Adopted | `backend/app/services/outbox_service.py` |
| A-006 | **Circuit Breaker** | Fowler | - | Critical | Adopted | `backend/app/core/self_healing.py` |
| A-007 | **Bulkhead Pattern** | Resilience | - | Important | Adopted | Per-service connection pools |
| A-008 | **API Gateway Pattern** | Microservices | - | Critical | Adopted | nginx api-gateway |
| A-009 | **Service Mesh** | Istio/Linkerd | - | Important | Planned | Phase 2+ |
| A-010 | **Twelve-Factor App** | Heroku | - | Important | Adopted | Guiding methodology |
| A-011 | **Domain-Driven Design (Tactical)** | Evans/Vernon | - | Important | Adopted | Aggregates, Value Objects |
| A-012 | **Domain-Driven Design (Strategic)** | Evans | - | Important | Adopted | Bounded contexts, context map |

---

## Technology References (18 entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| T-001 | **Python 3.11+** | Python Foundation | 3.11-3.13 | Critical | Adopted | [python.org/docs](https://python.org/docs) |
| T-002 | **FastAPI** | tiangolo | 0.115+ | Critical | Adopted | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| T-003 | **SQLAlchemy 2.0+** | SQLAlchemy | 2.0+ | Critical | Adopted | [sqlalchemy.org](https://sqlalchemy.org) |
| T-004 | **Alembic** | SQLAlchemy | 1.14+ | Critical | Adopted | `backend/migrations/` |
| T-005 | **PostgreSQL 16** | PostgreSQL Global | 16 | Critical | Adopted | [postgresql.org/docs/16](https://postgresql.org/docs/16) |
| T-006 | **Redis 7** | Redis | 7.2+ | Critical | Adopted | [redis.io/docs](https://redis.io/docs) |
| T-007 | **Docker Compose** | Docker | 2.x | Critical | Adopted | `docker-compose.yml` |
| T-008 | **Kubernetes** | CNCF | 1.31+ | Important | Planned | `k8s/` manifests |
| T-009 | **Terraform** | HashiCorp | 1.10+ | Important | Adopted | IaC |
| T-010 | **Prometheus** | CNCF | 3.x | Critical | Adopted | `config/prometheus/` |
| T-011 | **Grafana** | Grafana Labs | 11.x | Critical | Adopted | `config/grafana/` |
| T-012 | **React** | Meta | 19.x | Critical | Adopted | `frontend-v2/` |
| T-013 | **TypeScript** | Microsoft | 5.x | Critical | Adopted | `frontend-v2/` |
| T-014 | **Firebase** | Google | 11.x | Important | Adopted | `frontend-v2/` (Auth, Firestore) |
| T-015 | **tRPC** | tRPC | 11.x | Important | Adopted | `client/` |
| T-016 | **Cloudflare** | Cloudflare | - | Critical | Adopted | CDN, WAF, Workers |
| T-017 | **Istio** | CNCF | 1.24+ | Important | Evaluating | Service mesh (Phase 2) |
| T-018 | **Pydantic v2** | Pydantic | 2.x | Critical | Adopted | FastAPI-native validation |

---

## Medical Guidelines (12 entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| M-001 | **Tietz Textbook of Clinical Chemistry** | Rifai et al. | 7th Ed | Critical | Referenced | Clinical chemistry |
| M-002 | **Henry's Clinical Diagnosis** | McPherson, Pincus | 24th Ed | Critical | Referenced | Lab medicine |
| M-003 | **Iraqi MoH Lab Testing Protocols** | Iraqi MoH | Latest | Critical | Adopted | All lab tests |
| M-004 | **WHO Essential Lab Tests** | WHO | 2023 | Important | Referenced | Primary care tests |
| M-005 | **Iraqi National Drug Formulary** | Iraqi MoH | Latest | Important | Referenced | Medication coding |
| M-006 | **Iraqi Communicable Disease Surveillance** | Iraqi MoH | Latest | Important | Referenced | Notifiable diseases |
| M-007 | **Iraqi Population Health Metrics** | WHO/Iraq | Latest | Critical | Referenced | Reference ranges |
| M-008 | **SNDHS Data Dictionary** | Iraqi MoH | Phase 1 | Critical | Adopted | `docs/sndhs/` |
| M-009 | **CLSI EP05-A3 Precision** | CLSI | A3 | Important | Adopted | Measurement precision |
| M-010 | **CDC Lab Guidelines Infectious Disease** | CDC | Latest | Important | Referenced | Infectious disease |
| M-011 | **WHO Lab Quality Mgmt System Handbook** | WHO | 2nd Ed | Important | Referenced | ISO 15189 implementation |
| M-012 | **Iraqi Reference Ranges** | Iraqi MoH | Latest | Critical | Adopted | Population-specific ranges |

---

## GULA-Specific Documents (20+ entries)

| ID | Title | Source | Version | Relevance | Status | Location |
|----|-------|--------|---------|-----------|--------|----------|
| G-001 | **CLAUDE.md** | Platform Team | Current | Critical | Adopted | `/CLAUDE.md` |
| G-002 | **Makefile** | Platform Team | Current | Critical | Adopted | `/Makefile` |
| G-003 | **Main Docker Compose** | Platform Team | Current | Critical | Adopted | `docker-compose.yml` |
| G-004 | **CI Pipeline** | Platform Team | Current | Critical | Adopted | `.github/workflows/ci.yml` |
| G-005 | **Deploy Pipeline** | Platform Team | Current | Critical | Adopted | `.github/workflows/deploy.yml` |
| G-006 | **Platform Evolution Plan** | Platform Team | 1.0 | Critical | Adopted | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md` |
| G-007 | **Future Architecture** | Platform Team | 1.0 | Critical | Adopted | `docs/evolution/FUTURE_ARCHITECTURE.md` |
| G-008 | **Long-Term Evolution** | Platform Team | 1.0 | Critical | Adopted | `docs/evolution/LONG_TERM_EVOLUTION.md` |
| G-009 | **Digital Library Index** | Platform Team | 1.0 | Critical | Adopted | `docs/reference/DIGITAL_LIBRARY_INDEX.md` |
| G-010 | **Reference Catalog** | Platform Team | 1.0 | Critical | Adopted | `docs/reference/REFERENCE_CATALOG.md` |
| G-011 | **Knowledge Graph** | Platform Team | 1.0 | Critical | Adopted | `docs/reference/KNOWLEDGE_GRAPH.md` |
| G-012 | **SNDHS Architecture (22 files)** | Platform Team | Phase 1 | Critical | Adopted | `docs/sndhs/` |
| G-013 | **SNDHS Phase 1 Runbook** | Platform Team | Phase 1 | Critical | Adopted | `docs/sndhs/phase1/RUNBOOK.md` |
| G-014 | **SNDHS Backfill Script** | Platform Team | Phase 1 | Critical | Adopted | `scripts/sndhs_phase1_backfill.py` |
| G-015 | **Base Schema Migration** | Platform Team | 2025-03-22 | Critical | Adopted | `backend/migrations/versions/20250322_0000_create_base_schema.py` |
| G-016 | **App Entry Point (main.py)** | Platform Team | Current | Critical | Adopted | `backend/app/main.py` |
| G-017 | **Configuration (config.py)** | Platform Team | Current | Critical | Adopted | `backend/app/config.py` |
| G-018 | **Self-Healing System** | Platform Team | Current | Critical | Adopted | `backend/app/core/self_healing.py` |
| G-019 | **Startup Guard** | Platform Team | Current | Critical | Adopted | `backend/app/core/startup_guard.py` |
| G-020 | **Auth & Security** | Platform Team | Current | Critical | Adopted | `backend/app/security/` |
| G-021 | **Outbox Service** | Platform Team | Current | Critical | Adopted | `backend/app/services/outbox_service.py` |
| G-022 | **Full Stack Docker Compose** | Platform Team | Current | Important | Adopted | `docker-compose.full.yml` |
| G-023 | **HAProxy Config** | Platform Team | Current | Important | Adopted | `config/haproxy/haproxy.cfg` |
| G-024 | **Self-Audit Agent** | Platform Team | Current | Important | Adopted | `scripts/self_audit_agent.py` |
| G-025 | **System Context** | Platform Team | 1.0 | Critical | Adopted | `docs/architecture/SYSTEM_CONTEXT.md` |
| G-026 | **Architecture Decision Log** | Platform Team | 1.0 | Critical | Adopted | `docs/architecture/ARCHITECTURE_DECISION_LOG.md` |
| G-027 | **Domain Glossary** | Platform Team | 1.0 | Critical | Adopted | `docs/domain/DOMAIN_GLOSSARY.md` |
| G-028 | **Event Catalog** | Platform Team | 1.0 | Critical | Adopted | `docs/events/EVENT_CATALOG.md` |
| G-029 | **Database Schema** | Platform Team | 1.0 | Critical | Adopted | `docs/database/DATABASE_SCHEMA.md` |
| G-030 | **API Coverage** | Platform Team | 1.1 | Critical | Adopted | `docs/api/API_COVERAGE.md` |
| G-031 | **UI Component Catalog** | Platform Team | 1.1 | Important | Adopted | `docs/frontend/UI_COMPONENT_CATALOG.md` |
| G-032 | **Workflow Catalog** | Platform Team | 1.0 | Critical | Adopted | `docs/workflows/WORKFLOW_CATALOG.md` |
| G-033 | **Module Dependency Matrix** | Platform Team | 1.0 | Important | Adopted | `docs/architecture/MODULE_DEPENDENCY_MATRIX.md` |
| G-034 | **Migration Guide** | Platform Team | 1.0 | Critical | Adopted | `docs/deployment/MIGRATION_GUIDE.md` |
| G-035 | **Configuration Reference** | Platform Team | 1.0 | Critical | Adopted | `docs/configuration/CONFIGURATION_REFERENCE.md` |
| G-036 | **Feature Matrix** | Platform Team | 1.0 | Important | Adopted | `docs/management/FEATURE_MATRIX.md` |
| G-037 | **Known Limitations** | Platform Team | 1.0 | Important | Adopted | `docs/release/KNOWN_LIMITATIONS.md` |
| G-038 | **Compatibility Matrix** | Platform Team | 1.0 | Important | Adopted | `docs/platform/COMPATIBILITY_MATRIX.md` |
| G-039 | **Support Policy** | Platform Team | 1.0 | Important | Adopted | `docs/release/SUPPORT_POLICY.md` |
| G-040 | **Documentation Inventory** | Platform Team | 1.0 | Important | Adopted | `DOCUMENTATION_INVENTORY.md` |
| G-041 | **Documentation Gap Analysis** | Platform Team | 1.0 | Important | Adopted | `DOCUMENTATION_GAP_ANALYSIS.md` |
| G-025 | **K8s Manifests** | Platform Team | Current | Important | Evaluating | `k8s/` |

---

## Catalog Quick Reference — By Category

### Critical (High Priority for All Team Members)

| ID | Title | Category |
|----|-------|----------|
| H-001 | ICD-10 | Healthcare |
| H-003 | LOINC | Healthcare |
| H-004 | SNOMED CT | Healthcare |
| H-005 | HL7 v2.5.1 | Healthcare |
| H-008 | ISO 15189:2022 | Healthcare |
| H-009 | ISO 27001:2022 | Healthcare |
| S-001 | OWASP Top 10 | Security |
| S-004 | NIST SP 800-53 | Security |
| S-011 | Iraqi eHealth Law | Security |
| A-001 | Strangler Fig Pattern | Architecture |
| A-005 | Outbox Pattern | Architecture |
| A-006 | Circuit Breaker | Architecture |
| A-008 | API Gateway Pattern | Architecture |
| T-001 | Python 3.11+ | Technology |
| T-002 | FastAPI | Technology |
| T-003 | SQLAlchemy 2.0+ | Technology |
| T-005 | PostgreSQL 16 | Technology |
| T-006 | Redis 7 | Technology |
| T-016 | Cloudflare | Technology |
| M-003 | Iraqi MoH Lab Testing Protocols | Medical |
| M-007 | Iraqi Population Health Metrics | Medical |
| M-008 | SNDHS Data Dictionary | Medical |
| M-012 | Iraqi Reference Ranges | Medical |
| G-001 | CLAUDE.md | GULA |
| G-002 | Makefile | GULA |
| G-006 | Platform Evolution Plan | GULA |
| G-012 | SNDHS Architecture | GULA |

### Important (Significant for Specific Roles)

| ID | Title | Category | Primary Role |
|----|-------|----------|--------------|
| H-010 | ISO 27799:2016 | Healthcare | Security |
| H-011 | ISO 13606:2019 | Healthcare | Architect |
| H-012 | CAP Accreditation | Healthcare | Lab Ops |
| H-013 | CLSI EP28-A3c | Healthcare | Lab Domain |
| S-002 | OWASP ASVS | Security | Developer |
| S-005 | NIST SP 800-207 | Security | Architect |
| S-006 | NIST CSF | Security | Security |
| S-009 | HIPAA | Security | Legal |
| S-010 | GDPR | Security | Legal |
| A-002 | Saga Pattern | Architecture | Developer |
| A-003 | CQRS | Architecture | Architect |
| A-004 | Event Sourcing | Architecture | Architect |
| A-007 | Bulkhead | Architecture | Developer |
| T-008 | Kubernetes | Technology | DevOps |
| T-009 | Terraform | Technology | DevOps |
| T-012 | React | Technology | Frontend |
| T-017 | Istio | Technology | DevOps |
| M-001 | Tietz Textbook | Medical | Lab Domain |
| M-002 | Henry's Diagnosis | Medical | Lab Domain |

### Useful (Good to Know)

| ID | Title | Category |
|----|-------|----------|
| H-007 | HL7 CDA R2 | Healthcare |
| H-015 | WHO Essential Diagnostics | Healthcare |
| S-003 | OWASP MASVS | Security |
| S-007 | CIS Controls v8 | Security |
| S-008 | PCI DSS | Security |

---

## Catalog Update Process

1. **Adding entries**: Contact Platform Architecture Team with ID, title, source, version, relevance, status, location
2. **Updating versions**: Automated quarterly scan; manual verification
3. **Status changes**: When a standard is adopted/evaluated/planned, update status field
4. **Removing entries**: Never delete; mark status as "Superseded" with replacement ID

---

## References by Status

### Adopted (38)
H-001, H-003, H-004, H-005, H-008, H-009, H-010, H-013, H-014, S-001, S-002, S-004, S-006, A-001, A-005, A-006, A-007, A-008, A-010, A-011, A-012, T-001, T-002, T-003, T-004, T-005, T-006, T-007, T-009, T-010, T-011, T-012, T-013, T-014, T-015, T-016, T-018, M-003, M-008, M-012, G-001 through G-024

### Evaluating (5)
H-012, S-005, A-002, T-017, M-005

### Planned (6)
H-002, H-006, H-011, S-008, A-003, A-004

### Referenced (15)
H-007, H-015, S-003, S-007, S-009, S-010, G-025, M-001, M-002, M-004, M-006, M-009, M-010, M-011

### Monitoring (2)
S-011, S-012

---

*Total entries: 80+ (Healthcare: 15, Security: 12, Architecture: 12, Technology: 18, Medical: 12, GULA: 25)*
