# Changelog — National Governance Layer

## [1.0.0] — 2026-07-14

### Governance Layer Freeze

The National Governance Layer is now frozen at v1.0.0. All future modules MUST
consume this layer. No bypassing allowed.

### Phase 1 — National Governance Model
- Governance hierarchy (Republic → MoH → Directorates → ... → Units → Employees)
- Multi-tenancy, delegation, emergency/temporary/regional administration, acting roles
- Full tree traversal (children, subtree, path, ancestors)

### Phase 2 — National Healthcare Number Governance
- Health number issuance with collision-resistant generation
- Lost/reissue workflow with full audit trail
- Merged/split identity with hash-chained records
- Historical tracking via health number audit log
- Health card lifecycle management (citizen, digital, lab, radiology, hospital, insurance)

### Phase 3 — Citizen Registry Integration
- Abstract connector adapter pattern (STUB/LIVE/SHADOW)
- 9 connector types: National ID, Birth Registry, Death Registry, Civil Status,
  Passport, Residence, Visa, Family Registry, Ration Card
- All connectors have working STUB implementations
- Extensible via `register_adapter()` for future LIVE integrations

### Phase 4 — Healthcare Worker Governance
- Workforce registry with employee codes, professions, specializations
- Professional licensure management with verification workflow
- Board certification tracking
- Training records with completion tracking
- Competency assessment with levels (beginner → master)
- Worker privileges with scope and expiry
- Department rotation tracking
- Attendance records
- Productivity recording (daily/weekly/monthly/annual)
- National ranking engine (quality score + tests performed)

### Phase 5 — National Laboratory Governance
- Laboratory registry (10 lab types: private, government, military, university,
  veterinary, food, environmental, forensic, reference)
- Equipment registry with maintenance scheduling
- Analyzer registry with test menu and calibration tracking
- QC recording with automatic Westgard rule evaluation
- EQA recording with deviation/Z-score calculation
- Reagent inventory management with low-stock alerts
- National test catalog with LOINC/CPT mapping
- National panel definitions
- Reference lab designation (national/regional)

### Phase 6 — Clinical Governance
- Clinical policies with versioning and review cycles
- Medical guidelines with evidence levels
- National protocols with decision trees and ICD-10 mapping
- Critical result policies with notification/escalation rules
- Repeat testing policies with frequency limits
- Delta check policies with percentage/absolute thresholds
- Westgard QC rule configuration (1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10x)
- Reference range governance (by gender, age, source)
- Approval policies with role-based escalation
- Consultation policies with specialty routing

### Phase 7 — National Analytics
- Lab statistics by type and geography
- Workforce statistics by profession
- Equipment utilization by status
- Turnaround time analysis
- Quality indicators (QC in-control rate, EQA acceptable rate)
- National dashboard, governorate dashboards, lab dashboards
- Citizen/disease statistics stubs (delegates to national domain)

### Phase 8 — National Security Governance
- National audit event logging with severity classification
- Security policies with category, version, and review tracking
- Break-glass policies with configurable rules
- Threat intelligence with MITRE ATT&CK integration
- Incident management lifecycle
- Risk registry with likelihood/impact scoring
- Data classification with PII/PHI/encryption/retention
- Digital certificate lifecycle management

### Phase 9 — National Interoperability
- Protocol registry (FHIR, HL7, DICOM, IHE, OpenAPI, GraphQL, REST, gRPC,
  MQTT, AMQP, Event Bus)
- Master data agreements with sync frequency and conflict resolution
- Terminology mapping (bidirectional, with equivalence)
- Canonical field mapping with transformations

### Phase 10 — AI Governance
- AI guardrails (prompt injection, privacy, safety, etc.)
- LLM governance policies with use case restrictions
- Prompt policies with sanitization and length limits
- Full AI audit trail with input/output hashing
- Human approval workflow for AI outputs
- AI risk classification with clinical impact assessment
- Model validation records with accuracy/precision/recall/F1

### Governance Policy Engine
- 17 governance actions with risk levels
- Critical/high/medium/low classification
- Elevated approval enforcement for high-risk actions
- Default DENY stance

### Architecture
- 48 SQLAlchemy models across 8 domains (10 model modules)
- 10 service classes with 150+ methods
- 55 REST endpoints in 2 route modules
- 25 governance-specific enums
- Extends only through governance services
- Zero modifications to Foundation or National Healthcare Domain
