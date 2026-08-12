# National Platform SBOM — Missions 017-024

**Version:** 2.2.0  
**Date:** 2026-07-15  
**Platform:** GULA National Digital Health Platform  

## Python Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.115 | Web framework |
| uvicorn | latest | ASGI server |
| gunicorn | latest | WSGI server |
| redis | >=5.0 | Cache/queue client |
| python-multipart | >=0.0.20 | Form parsing |
| sqlalchemy | >=2.0 | ORM |
| alembic | >=1.13 | Migrations |
| pydantic | >=2.0 | Data validation |
| pydantic-settings | >=2.0 | Configuration |
| pyjwt | >=2.8 | JWT auth |
| cryptography | >=41 | Encryption |
| httpx | >=0.27 | HTTP client |
| sentry-sdk | >=2.0 | Error tracking |
| prometheus-client | >=0.19 | Metrics |
| psycopg2-binary | >=2.9 | PostgreSQL driver |
| python-dotenv | >=1.0 | Env loading |
| pyflakes | >=3.2 | Lint |
| flake8 | >=7.0 | Lint |
| pytest | >=8.0 | Testing |
| pytest-asyncio | >=0.23 | Async testing |
| ruff | >=0.3 | Lint/format |
| mypy | >=1.8 | Type checking |
| bandit | >=1.7 | Security scan |
| semgrep | >=1.50 | SAST |

## Mission 017 — National EHR Platform Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/national/fhir/` | 19 files | FHIR R4 mappers, validation, search, terminology |
| `app/ehr/` | 14 files | EHR base entity, models (allergy, care_plan, clinical_note, etc.) |
| `app/clinical/` | 12 files | CDS, knowledge, quality, research, terminology |
| `app/routes/ehr_fhir.py` | 1 file | FHIR REST endpoints (20+ resource types) |
| `app/routes/clinical*.py` | 4 files | Clinical documentation, orders, quality routes |

## Mission 018 — National Health Data Platform Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/national_data/` | 30+ files | Canonical models, MDM, event store, warehouse, governance, AI data |
| `app/health_data/` | 25+ files | Data lake, canonical mapping, streaming, governance |
| `app/routes/national_data.py` | 1 file | National data API routes |
| `app/routes/national_streaming.py` | 1 file | Streaming event routes |

## Mission 019 — National Platform Operations Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/control_plane/` | 25+ files | Operations center, fleet, release, registry, digital twin |
| `app/command_intelligence/` | 4 files | Incident and capacity intelligence |
| `scripts/` | 85 files | Operational scripts (backup, DR, monitoring, deploy) |
| `config/` | 90+ files | Infrastructure configuration (Prometheus, Grafana, HAProxy, etc.) |

## Mission 020 — National Digital Health Ecosystem Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/national/ecosystem/` | 15+ files | Connectors, partners, transformation, gateway |
| `app/national/ecosystem/connectors/` | 8 files | REST, FHIR, HL7, ASTM, File, Messaging, Webhook |
| `app/national/ecosystem/partners/` | 3 files | Partner registry, credentials, certificates |
| `app/national/ecosystem/gateway/` | 3 files | API gateway policies, routing |
| `app/integration/` | 80+ files | Integration framework, connectors, standards |
| `contracts/sdk/` | 3 SDKs | TypeScript, Dart, Python SDKs |

## Mission 021 — National Citizen Super App Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/citizen_platform/` | 18 files | Citizen identity, appointments, family, laboratory, medications |
| `frontend-v2/src/` | 85+ files | React + Firebase frontend (citizen/doctor/lab/ministry portals) |
| `frontend-v2/src/views/citizen/` | 10+ views | Citizen dashboard, health, family, medications, results |
| `frontend-v2/src/components/citizen/` | 6 components | DigitalTwin, FamilySwitcher, MedicineCabinet, etc. |

## Mission 022 — National Health Intelligence & Automation Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/national/intelligence/` | 15+ files | Automation, clinical/laboratory/hospital/public health intelligence |
| `app/national/intelligence/ai_platform/` | 1 file | LLM gateway, model registry, RAG engine |
| `app/national/intelligence/automation/` | 1 file | Task/rule/schedule/notification automation |
| `app/ai_fabric/` | 24 files | AI fabric with agents, RAG, knowledge graph |
| `app/research_platform/` | 19 files | Research, population health, epidemiology |

## Mission 023 — National Doctor Clinical Workspace Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/routes/clinical*.py` | 4 files | Clinical documentation, orders, quality |
| `app/routes/ehr_fhir.py` | 1 file | FHIR resource access |
| `frontend-v2/src/views/doctor/` | 2 views | PatientProfile, DoctorIntelligence |
| `frontend-v2/src/components/doctor/` | 6 components | ClinicalNotes, PrescriptionBuilder, etc. |

## Mission 024 — National Laboratory Desktop Professional Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `app/lims/` | 14 files | LIMS models, routes, services, state machine |
| `app/lims/integration/` | 5 files | ASTM, HL7, device registry, simulator |
| `app/lims/routes.py` | 1600+ lines | 50+ LIMS REST endpoints |
| `services/device_bridge/` | 30+ files | LabLink-Core: ASTM/HL7 device integration |

## Infrastructure Dependencies

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16 | Primary database |
| Redis | 7 | Cache, queue, session store |
| Nginx | latest | API gateway |
| Prometheus | latest | Metrics collection |
| Grafana | latest | Dashboards |
| HAProxy | latest | Load balancer |
| Docker | latest | Container runtime |

## Security Dependencies

| Tool | Purpose |
|------|---------|
| JWT (PyJWT) | Authentication tokens |
| Cryptography (Fernet) | Encryption at rest |
| bcrypt | Password hashing |
| mTLS | Partner certificate auth |
| OAuth2 / OIDC | External identity federation |

## License
Proprietary — GULA Platform. All rights reserved.
