# GULA Platform v1.0 — Production Release

**Release Date:** 2026-07-15
**Version:** 2.1.0
**Release Tag:** `production-platform-v1.0`

---

## What's New

GULA Platform v1.0 is the first production release of Iraq's national healthcare
laboratory platform. This release consolidates 14 phases of development across
466 commits into a single, stable, production-ready system.

### Core Platform

- FastAPI monolith with gunicorn + uvicorn workers
- PostgreSQL 16 persistent storage with SQLAlchemy ORM
- Redis 7 caching, session management, and task queuing
- Docker Compose deployment with health-check orchestration
- nginx api-gateway with TLS termination and security hardening

### National Platform Runtime (9 modules)

- Rules Engine — declarative clinical rule evaluation
- Background Platform — asynchronous job orchestration
- Workflow Runtime — BPMN-like workflow execution
- Task Engine — distributed task scheduling
- Notification Platform — multi-channel notification delivery
- Document Platform — document management and generation
- Scheduling Platform — resource and appointment scheduling
- Search Platform — full-text and structured search
- Observability Platform — metrics, logging, and tracing

### National Data Platform

- Canonical patient, encounter, observation, medication, procedure, document models
- MDM (Master Data Management) — golden records, duplicate detection, merge actions
- Event Store — immutable event sourcing with snapshots and retention policies
- Data Warehouse — star-schema fact and dimension tables for analytics
- Data Governance — data lineage, catalog, quality rules, classifications, retention
- AI Data Platform — feature store, training datasets, vector embeddings, knowledge graph

### Governance & Security

- Policy Engine — declarative policy enforcement
- ABAC (Attribute-Based Access Control) with condition matching
- RBAC — 9 roles with 13 granular permissions
- Circuit Breaker — isolates failing DB/Redis with degraded mode
- Self-Healing Engine — auto-GC, pool recycle, reconnection
- Audit Logging — immutable hash chain for all mutations
- Consent Management — grant/revoke/check with break-glass override
- Intrusion Detection — pattern and threshold-based anomaly detection

### Clinical Intelligence

- Result interpretation engine (Arabic-first, patient-facing)
- Severity classification with critical flag detection
- Hallucination guard for AI-generated content
- Clinical state machine with conflict resolution
- Digital Twin simulation platform

### Hospital Information System

- Campus, building, floor, room, unit, bed, clinic management
- Operation theater scheduling
- Medical equipment tracking
- Cost center management

### Integration & Interoperability

- FHIR (R4) — DiagnosticReport, ServiceRequest, Patient, Observation
- Connector SDK — auto-generates client code
- HTTP/REST, GraphQL, WebSocket, gRPC, DICOM connectors
- Device bridge (ASTM/HL7) for lab instruments

### Patient & Citizen Features

- Digital patient cards with QR-based identity (HMAC-signed tokens)
- Citizen portal — test results, health records, appointment management
- Patient history with longitudinal data aggregation
- Family health record linking

### Financial Engine (Phase A)

- Schema-only bootstrap for campaigns, conversions, fraud detection
- Feature-flagged (disabled by default)

## Breaking Changes

- **None.** This release is fully additive and backwards compatible.

## New Features

- Complete National Platform Runtime (9 bounded-context modules)
- Complete National Data Platform (canonical models, MDM, event store, warehouse, governance, AI data)
- Complete Governance Layer with Command Intelligence
- Complete Hospital Information System
- Complete LIMS (Laboratory Information Management System) — 39 models, full routes
- Complete Care Continuum Platform
- Knowledge Graph with 10,858+ nodes and 9,778+ edges
- Master Roadmap Engine for strategic planning
- Digital Twin simulation platform
- 52 registered capabilities across 9 domains
- Full ABAC engine
- Identity Governance — citizen, newborn, foreigner, resident workflows
- Family Registry with guardian linking

## Security Improvements

- JWT with refresh token rotation and blacklisting
- Fernet encryption at rest for PII/national ID
- Comprehensive CSP, HSTS, X-Frame-Options headers
- Rate limiting with deque-based sliding window (1000× performance improvement)
- Circuit breaker with 3 degradation levels
- Idempotency key support for safe retries
- Body size limits (DoS protection)
- Request ID tracing across all layers
- Structured JSON logging in production
- RBAC + ABAC dual enforcement layer
- Intrusion detection with automatic response

## Performance Improvements

- Rate limiter: 219s → 0.22s for 100k checks (deque optimization)
- Adaptive concurrency — automatically sheds load under DB stress
- DB connection pooling with sliding window error tracking
- Response compression (GZip)
- Startup warmup for hot-path modules
- Kernel boot with 12-phase initialization
- Redis-backed task queue with crash isolation

## Deployment Notes

### Prerequisites

- Docker Engine 24+ and Docker Compose v2+
- PostgreSQL 16 (included in docker-compose)
- Redis 7 (included in docker-compose)
- Minimum 4 GB RAM, 2 vCPUs

### Quick Start

```bash
# Clone the repository
git clone https://github.com/samertts/gula-platform.git
cd gula-platform

# Generate secrets
make secrets-gen > .env

# Start the stack
make up

# Check health
make health-deep
```

### Environment Variables

All required environment variables are documented in `.env.example`.
Key variables:

| Variable | Required | Default |
|----------|----------|---------|
| `SECRET_KEY` | Yes | — |
| `ENCRYPTION_KEY` | Yes | — |
| `POSTGRES_PASSWORD` | Yes | — |
| `REDIS_PASSWORD` | Yes | — |
| `NID_HMAC_KEY` | Yes | — |
| `REFRESH_TOKEN_SECRET` | Yes | — |
| `CORS_ORIGINS` | No | https://gula-platform.org |
| `SENTRY_DSN` | No | — |
| `ALERT_WEBHOOK_URL` | No | — |

### Database Migrations

All migrations are in `backend/migrations/versions/`. Run automatically
on startup via Alembic. Manual:

```bash
cd backend && alembic upgrade head
```

### Monitoring

- Prometheus metrics at `/metrics/prom` (requires bearer token)
- Grafana dashboards at port 3000 (prometheus profile)
- Health endpoints: `/health`, `/health/ready`, `/health/deep`
- Alert webhook for Telegram/Discord/Slack integration

### Scaling

```bash
# Horizontal scaling with HAProxy
make scale REPLICAS=5
```

### Support

- Documentation: `docs/` directory
- SNDHS spec: `docs/sndhs/` (22 files)
- Operations runbook: `OPERATIONS.md`
- Performance guide: `PERFORMANCE_GUIDE.md`
- Deployment guide: `PRODUCTION_DEPLOYMENT.md`

---

### Previous Release Notes

For the complete changelog, see `CHANGELOG.md` (466 commits, 590+ lines).

---

*Release notes generated by GULA Production Freeze Agent on 2026-07-15 12:45 UTC*
