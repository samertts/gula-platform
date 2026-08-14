# Changelog

All notable changes to the GULA Platform are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **LIS interoperability pilot slice**
  - Tenant-scoped `GET /lims/orders/{id}/fhir-bundle` FHIR R4 collection Bundle for ServiceRequest, Specimen, and Observation resources
  - IHE PIXm ITI-83 query and MHD ITI-65/67/68 endpoints under `/national/interop`
  - Organisation-bound service accounts for interop, tenant-scoped inbox idempotency, final-report-only reads, and human review before inbound clinical processing
  - Metadata-only audit event for Bundle exports to avoid duplicating patient identity and result values in audit details
  - Arabic pilot runbook with rollout gates, privacy controls, rollback steps, and measurable impact indicators
- Open source community health files (CODE_OF_CONDUCT, SUPPORT, GOVERNANCE, MAINTAINERS)
- Apache 2.0 License and NOTICE file
- GitHub issue templates and pull request template
- CodeQL, Dependency Review, and Scorecard CI workflows
- FUNDING.yml for GitHub Sponsors

### Changed
- LIMS section, workstation, and instrument queries now enforce laboratory tenant isolation
- FHIR Bundle responses declare `application/fhir+json` and are documented in ADR-011
- License field in package.json and pyproject.toml updated to Apache-2.0
- README.md enhanced with badges and expanded documentation links

### Quality
- Added regression coverage for cross-laboratory LIMS access, workstation attachment, FHIR capabilities, Bundle composition, and export-audit minimization

## [2.3.2] - 2026-07-16

### Added
- **National Notification Platform** (2,606 LOC — 0→53 tests)
  - 53 new tests for NotificationPlatformService, domain entities, and error handling
  - Covers: send (all 10 channels, templates, scheduling, priorities, categories, correlation IDs, metadata)
  - Covers: batch send, template CRUD (create, render Jinja2/Mustache, update, delete)
  - Covers: user preferences (enable/disable, quiet hours, category opt-in/opt-out)
  - Covers: delivery reports, lifecycle (cancel, mark read, mark delivered, list/filter)
  - Covers: scheduling, stats, all error conditions (missing template, invalid template, channel blocked, etc.)

### Fixed
- Added missing `created_by` field to `NotificationBatch` domain entity

### Dependencies
- Added `jinja2`, `chevron` (template rendering engines)

### Quality
- All 53 new tests passing with in-memory repositories
- Total test count: 137 (84 prior + 53 notification platform)

## [2.3.1] - 2026-07-16

### Added
- **Identity Governance Persistence** (ADR-012 Phase 3)
  - 35 new tests for PersistedIdentityGovernanceService, PersistedBreakGlassService, and PersistedIdentityMergeEngine
  - Covers: citizen/newborn/foreigner/unknown registration, document linking & verification, search, optimistic locking
  - Covers: break-glass access lifecycle (request, revoke, expire, validate, list, stale expiry)
  - Covers: merge confidence calculation, propose/approve/reject merge, duplicate proposal detection
  - ADR-012 gap closed: Persisted identity governance services (407 LOC) now have full test coverage

### Quality
- All 35 new tests passing (SQLite in-memory, isolated per test)
- Total test count: 84 (49 identity/security/clinical-core + 35 governance persistence)

## [2.3.0] - 2026-07-16 — PI-001 WP2.5/WP3 + PI-002: National Identity, Security & Clinical Core

### Added
- **Identity Platform (PI-001 WP2.5)**
  - Offline Sync Engine: CRDT-compatible vector clock synchronization, conflict detection with 4 resolution strategies, encrypted local cache, operation signing, sync logging
  - Device Trust Service: Browser/device fingerprinting, trust level escalation, automatic deactivation
  - Risk-Based Authentication: Context-aware risk scoring (0-100), impossible travel detection, Tor/VPN/datacenter detection, adaptive responses
  - Identity Governance: PostgreSQL persistence with optimistic locking
  - 49 new tests across offline sync (20), device trust (15), risk-based auth (14)

- **Security Platform (PI-001 WP3)**
  - Complete Zero Trust architecture with continuous verification
  - RBAC (9 roles × 13 permissions) + ABAC (attribute conditions engine)
  - JWT with Redis blacklist + perm_version double-layer revocation
  - OAuth2/OIDC with PKCE (S256), JWKS, introspection, revocation
  - MFA: TOTP, HOTP, WebAuthn/FIDO2/Passkeys, backup codes
  - SAML 2.0 SSO, Service Accounts with API keys
  - Rate limiting (Redis-backed fixed window, per-IP/per-user/per-auth)
  - Intrusion detection (time-windowed, per-IP caps)
  - Action risk scoring engine (0-10 scale)
  - Encrypted storage at rest (AES-256-GCM via Fernet, HMAC-signed)

- **Clinical Core (PI-002)**
  - MPI: Fellegi-Sunter probabilistic matcher, deterministic NID short-circuit
  - Citizen model with identity claims and merge audit chain
  - EHR: Clinical notes, encounters, diagnoses, allergies, medications, immunizations, care plans, vital signs, attachments
  - FHIR R4 API: Patient, Observation, DiagnosticReport, MedicationRequest, AllergyIntolerance, Condition, Encounter, Immunization, CarePlan
  - LIMS: Orders, samples, barcodes, QC, EQA, reference ranges, delta checks, Westgard rules
  - 47 Alembic migrations covering identity, clinical, security, financial, governance

### Tags
- `identity-platform-v1.0`, `security-platform-v1.0`, `clinical-core-v1.0`

## [2.3.0] - 2026-07-16 — Missions 025-028: National Healthcare Platforms

### Added
- **MISSION-025: National Hospital Desktop Workspace (NHDW)**
  - Hospital Dashboard, Patient Administration (ADT), Clinical Operations
  - Department Platform (Emergency, ICU, NICU, OR, etc.)
  - Resource Management, Hospital Communication, Telemedicine
  - Offline Platform with encrypted local SQLite, conflict resolution, delta sync
  - Desktop Experience: PySide6 Windows native, RTL, dark mode, accessibility
  - KPI Engine: Occupancy rates, ALOS, readmission, ED wait times
  - 50+ route endpoints

- **MISSION-026: National Nursing & Care Coordination Platform**
  - Nursing Dashboard, Clinical Care, Medication Administration
  - Nursing Documentation, Task Coordination, Care Coordination
  - Offline Platform, Medication Safety
  - 50+ route endpoints

- **MISSION-027: National Pharmacy Information Platform (NPIP)**
  - Medication Catalog, Prescription Management, Clinical Pharmacy
  - Inventory Management, Dispensing Platform, Citizen Integration
  - Offline Platform
  - 55+ route endpoints

- **MISSION-028: National Radiology Information System & PACS (NRISP)**
  - Radiology Workflow, RIS Platform, PACS Platform
  - Medical Device Integration (MRI, CT, X-Ray, Ultrasound, etc.)
  - Clinical Integration, AI Imaging Platform, Citizen Services
  - Offline Platform
  - 55+ route endpoints

## [2.2.0] - 2026-07-16 — Missions 037-039 & EXEC-001: Platform Constitution

### Added
- **MISSION-037: National Platform Constitution (NPCE)**
  - Architecture, Engineering, Quality, Security, AI, Developer, Operations, Release Constitutions
  - ADR-024: Platform Constitution & National Trust Framework

- **MISSION-038: National Trust, Compliance & Privacy Platform**
  - Privacy Platform, Digital Sovereignty, Compliance Framework
  - Trust Services, AI Trust, National Audit, Long-Term Preservation
  - Citizen Trust dashboard
  - Trust Platform Code: `backend/app/trust/`

- **MISSION-039: Autonomous Platform Factory (APFE)**
  - Repository Intelligence, Autonomous Code Factory
  - Autonomous Architecture, DevSecOps, Quality, Documentation, Operations

- **EXEC-001: National Platform Implementation Wave 1**
  - Implementation Audit, Missing Features Detection, Production Hardening, Pilot Deployment, National Rollout

- **Constitution Enforcement**
  - 20-Rule Enforcer, Architecture Guardian, Dependency Guardian
  - Makefile targets for constitution enforcement

### Changed
- Database Migration: `20260716_0013_national_trust_platform_tables.py`

### Documentation
- `docs/constitution/PLATFORM-CONSTITUTION.md`
- `docs/trust/NATIONAL-TRUST-PLATFORM.md`
- `docs/factory/ENGINEERING-FACTORY.md`
- `docs/execution/EXECUTION-PROGRAM-001.md`
- `docs/adr/ADR-024-Platform-Constitution.md`

### Tags
- `platform-constitution-v1.0`, `national-trust-platform-v1.0`, `engineering-factory-v1.0`

## [2.2.0] - 2026-07-16 — Sprint-001: Repository Transformation & Foundation Lock

### Added
- `capabilities/` — 10 capability modules (clinical foundation, document/encounter management, FHIR, consent, etc.)
- `biomedical/`, `blood_bank/`, `citizen_platform/`, `command_center/`, `control_plane/`, `critical_care/`, `ems/`, `lifecycle_platform/`, `nhdw/`, `nursing/`, `pharmacy/`, `pilot_platform/`, `public_health/`, `radiology/`, `research_platform/`
- `national/` — Document, notification, scheduling, background, observability, rules, search, task engines
- `kernel/` — DI container, event bus, plugin system, runtime, validation, gateway, config, features

### Fixed
- 125 undefined-name errors resolved across capabilities framework
- 54 test files switched from `backend.app` to `app` imports

### Quality
- 172/173 kernel tests passing (1 pre-existing flaky isolation test)
- All security tests passing (39 tests), all identity tests passing
- Ruff: 0 syntax errors (E9), 0 undefined names (F821)

## [2.2.0] - 2026-07-15 — Missions 017-024: National Platforms

### Added
- **MISSION-017: National EHR Platform** — Longitudinal Patient Record, FHIR R4 Native, Clinical Documentation, Medication Platform, Orders Platform, Clinical Decision Support
- **MISSION-018: National Health Data Platform** — Unified Data Lake, Data Warehouse, MDM, Streaming Platform, National Analytics, Research Platform, AI Data Platform
- **MISSION-019: National Platform Operations** — Environment Management, Release Platform, 24/7 Operations Center, Monitoring, Incident Management, Security Operations, Backup & DR, Capacity Management
- **MISSION-020: National Digital Health Ecosystem** — Connector Framework, Partner Platform, Data Exchange, National API Gateway, Operational Resilience
- **MISSION-021: National Citizen Super App** — Citizen Identity, Health Card, QR/Barcode, Dashboard, Appointments, Laboratory Results, Clinical Records, Family Platform, Offline Support, Multi-Platform
- **MISSION-022: National Health Intelligence & Automation** — Automation Engine, Clinical Intelligence, Laboratory Intelligence, Hospital Intelligence, Public Health Intelligence, National AI Platform, Decision Support
- **MISSION-023: National Doctor Clinical Workspace** — Doctor Dashboard, Patient Workspace, Orders, Clinical Documentation, Decision Support, Secure Messaging, Offline Support
- **MISSION-024: National Laboratory Desktop Professional** — Laboratory Dashboard, Specimen Lifecycle, Analyzer Integration, Quality Management, Result Management, Printing Platform, Offline Support, Windows Native

## [2.1.0] - 2026-07-14 — Engineering Program M4.x

### Added
- M4.0 Environment Guardian: Full audit report
- M4.1 Repository Brain: Knowledge graph (10,858 nodes, 9,778 edges)
- M4.2 Architecture Intelligence: GULA-specific scoring engine
- M4.3 Dependency Intelligence: Complete SBOM, license report
- M4.4 Dependency Upgrade Engine: Lock file (58 pinned packages)
- M4.5 Quality Gate Orchestrator: All 5 gates passing
- M4.6 Supply Chain Security: Dependency Guardian
- M4.7 Security Hardening: Full security audit, 28 CWE mappings
- M4.8 Dependency Guardian: Permanent monitoring service
- M4.9 Security Knowledge Base: CWE-79 through CWE-918 mapped
- M5 Repository Optimization: Dead code, large modules cataloged
- M6 Kernel Certification: Auth gap fixed on all 11 kernel endpoints
- M7 Capability Factory: Capability catalog with migration roadmap

### Changed
- `backend/app/config.py`: REFRESH_TOKEN_SECRET independently random
- `backend/app/kernel/routes.py`: All 11 kernel endpoints now require JWT authentication

## [FOUNDATION v1.0] - 2026-07-14

### Added
- **Event Platform Completion**: Snapshot Engine, Recovery Engine, EventBus
- **Integration Foundation Completion**: Connector Registry, Connector SDK, HTTP/REST, GraphQL, WebSocket, gRPC, DICOM Connectors
- **Identity Foundation Completion**: Identity Governance Service, Family Registry, Identity Merge Engine
- **Reference Services Completion**: Master Reference Data Service, Universal Identifier Service, National Laboratory Catalog
- **Healthcare Foundation Completion**: Organization model, ABAC Engine
- **Program v3.0 — Capability Factory & Automation (M005)**
  - Enhanced CapabilityDescriptor, CapabilityRegistry, Capability Generator
  - Capability Registry Populator (44 capabilities across 9 domains)
  - Kernel Bootloader Enhancement, CapabilityFlagManager, CLI Enhancement
  - Capability Report with dependency graph
  - M006/M007 capability scaffolds

### Quality
- 55 new tests covering all new modules — all passing
- Ruff: all checks passing
- Bandit: clean

## [2026-07-13] — Production Validation

### Added
- Engineering automation: `shared/di_container` enterprise DI container

### Fixed
- Python 3.10 `datetime.UTC` compatibility across 49 files
- `StrEnum` compatibility for Python 3.10
- RateLimiter performance: list → deque (1000x improvement)
- Generator bug fixes in plugin, capability, testing, and CLI generators

### Changed
- `explicit_package_bases = true` in mypy config
- README.md and ARCHITECTURE.md rewritten to reflect Docker Compose + PG16 + Redis 7 stack

### Performance
- RateLimiter: 219s → 0.22s for 100k checks

### Quality
- All 1420 tests passing, 9 stress tests passing, Bandit clean

## [Release History Prior to 2026-07-13]

### Added
- Full production-grade platform with medical laboratory management
- Multi-tier SaaS system, citizen portal, RBAC, JWT auth
- AI integration (Gemini, Ollama, Groq), clinical intelligence
- Lab instrument integration (ASTM/HL7)
- Docker Compose deployment, Kubernetes manifests
- Monitoring stack (Prometheus, Grafana, Loki)
- k6 load testing framework
- Extensive security hardening and audit
- Self-healing system, circuit breaker, auto-repair engine
- Chaos engineering and resilience testing
- Disaster recovery and continuous backup
- Performance optimization and stress testing

### Security
- JWT with refresh token rotation
- RBAC with 9 roles
- Rate limiting, encryption at rest
- Audit logging with hash chain integrity

### Fixed
- Numerous 502 Bad Gateway resolutions
- nginx routing and port conflict fixes
- CI pipeline stabilization
- Migration and database schema fixes
- Security vulnerability patches (Dependabot alerts)
- Production hardening across all layers

### Infrastructure
- Docker Compose with PostgreSQL 16, Redis 7, nginx
- Kubernetes manifests for microservices deployment
- Helm charts for Kubernetes deployment
- Render and DigitalOcean deployment configurations
- GitHub Actions CI/CD with syntax gate, linting, testing, security scanning

### Tags
Multiple release tags including:
- `application-platform-v1.0`, `care-continuum-v1.0`, `citizen-super-app-v1.0`
- `clinical-core-v1.0`, `clinical-platform-v1.0`, `deployment-platform-v1.0`
- `doctor-workspace-v1.0`, `ehr-platform-v1.0`, `engineering-factory-v1.0`
- `foundation-v1.0`, `governance-v1.0`, `hospital-platform-v1.0`
- `identity-platform-v1.0`, `integration-contracts-v1.0`
- `national-ai-platform-v1.0`, `national-certification-v1.0`
- `platform-consolidation-v2.1.0`, `platform-constitution-v1.0`
- `production-platform-v1.0`, `runtime-platform-v1.0`, `security-platform-v1.0`
- `v1.0.0-RC1`, `v2.1.0-engineering-factory`

## Early Development

This project began as an Iraqi medical laboratory management system (LIMS) and
evolved into a national healthcare platform. Early milestones include:

- Initial MVP with lab result platform and smart interpretation
- Multi-tenant SaaS system with tiered subscription
- Production hardening and security certification
- National platform expansion (identity, clinical, hospital, pharmacy, radiology)
- Engineering factory automation and capability generation
