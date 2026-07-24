# GULA Platform

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI Pipeline](https://github.com/samertts/gula-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/samertts/gula-platform/actions/workflows/ci.yml)
[![Quality Gate](https://github.com/samertts/gula-platform/actions/workflows/quality-gate.yml/badge.svg)](https://github.com/samertts/gula-platform/actions/workflows/quality-gate.yml)
[![CodeQL](https://github.com/samertts/gula-platform/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/samertts/gula-platform/actions/workflows/codeql-analysis.yml)
[![Release](https://img.shields.io/github/v/release/samertts/gula-platform)](https://github.com/samertts/gula-platform/releases)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/samertts/gula-platform/badge)](https://securityscorecards.dev/viewer/?uri=github.com/samertts/gula-platform)
[![GitHub Contributors](https://img.shields.io/github/contributors/samertts/gula-platform)](https://github.com/samertts/gula-platform/graphs/contributors)

Arabic-first healthcare platform for Iraqi medical laboratories — an open-source
Laboratory Information Management System (LIMS) and national healthcare platform.

---

## Overview

GULA Platform is a production-grade healthcare information system designed for
Iraqi medical laboratories. It provides end-to-end laboratory management —
from order entry and specimen tracking to result reporting and instrument
integration — with Arabic-first UX, offline capability, and enterprise-grade
security.

The platform has evolved from a single-laboratory LIMS into a national-scale
healthcare ecosystem supporting EHR, pharmacy, radiology, nursing, hospital
operations, AI-powered clinical intelligence, and citizen health services.

## Problem Statement

Medical laboratories in Iraq and the MENA region face unique challenges:

- **Language barrier**: Most LIMS software is English-first, creating usability
  issues for Arabic-speaking laboratory staff
- **Infrastructure limitations**: Unreliable internet connectivity requires
  offline-capable systems
- **Instrument integration**: Laboratories use diverse analyzers with ASTM/HL7
  protocols that require specialized device drivers
- **Regulatory compliance**: Healthcare data sovereignty and patient privacy
  requirements demand self-hosted, on-premises deployment
- **Cost constraints**: Commercial LIMS solutions are expensive and create
  vendor lock-in

GULA Platform addresses all of these through an open-source, Arabic-first,
offline-capable, self-hosted design.

## Features

### Laboratory Management
- Order entry and management with CPOE
- Specimen lifecycle tracking with chain of custody
- Result entry, verification, amendment with audit trail
- Quality control (Westgard rules, Levey-Jennings charts)
- Barcode and QR code support
- Configurable report printing (PDF, HTML, ZPL)

### Clinical & EHR
- Longitudinal patient records with FHIR R4 native data model
- Clinical documentation (SOAP, progress notes, discharge summaries)
- Medication management and CPOE
- Clinical decision support

### National Platform Modules
- **Hospital Desktop** — ADT, ward rounds, resource management
- **Nursing Platform** — Clinical care, medication administration, handover
- **Pharmacy Platform** — Drug catalog, e-prescription, inventory
- **Radiology/PACS** — DICOM storage, image viewer, AI imaging
- **Citizen Super App** — Health card, appointments, lab results
- **Population Health** — Analytics, epidemiology, outbreak detection

### Security & Compliance
- RBAC (9 roles, 13 permissions) + ABAC attribute engine
- JWT authentication with Redis blacklist revocation
- AES-256 encryption at rest, TLS in transit
- Immutable hash-chain audit logging
- Rate limiting, intrusion detection, risk-based authentication
- MFA (TOTP, HOTP, WebAuthn/FIDO2)

### Infrastructure
- Monolith-first deployment (FastAPI + PostgreSQL + Redis)
- Microservices tree for future decomposition
- Docker Compose for local development and production
- Kubernetes/Helm for container orchestration
- Self-healing system with circuit breaker and auto-repair
- Comprehensive monitoring (Prometheus, Grafana, Loki)

## Architecture

```
Internet
    |
    ▼
┌──────────────────────────────┐
│  Host nginx (TLS)            │
│  Certbot / Let's Encrypt     │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  api-gateway (Docker nginx)  │
│  Rate limiting, security     │
└──────────┬───────────────────┘
           ▼
┌──────────────────────────────┐
│  gula-backend (FastAPI)      │
│  Gunicorn + Uvicorn workers  │
│                              │
│  Middleware: 11 layers       │
│  Routes: 36+ modules         │
│  Services: Identity,         │
│  Clinical, Security, Trust   │
└──────┬───────────┬───────────┘
       ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│PostgreSQL│ │  Redis 7 │ │  Device  │
│    16    │ │          │ │  Bridge  │
└──────────┘ └──────────┘ └──────────┘
```

The platform follows a **monolith-first** deployment strategy: the backend monolith
in `backend/app/` is the production target, while a parallel microservices tree
(`services/`) exists for future decomposition.

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed architecture description.

## Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI (Python 3.12+) — Gunicorn + Uvicorn |
| Database | PostgreSQL 16 (SQLAlchemy async) |
| Cache | Redis 7 |
| Gateway | nginx (api-gateway) |
| Auth | JWT (HS256) + RBAC (9 roles x 13 permissions) |
| Frontend | React + TypeScript (frontend-v2/, frontend-v3/) |
| Device Bridge | LabLink-Core (ASTM/HL7 instrument integration) |
| Monitoring | Prometheus, Grafana, Loki |
| Container | Docker Compose, Kubernetes, Helm |
| Mobile | Android (Kotlin), iOS (Swift), Flutter Desktop |

## Quick Start

```bash
# Prerequisites: Docker and Docker Compose
git clone https://github.com/samertts/gula-platform
cd gula-platform
cp .env.example .env   # edit database passwords
make up                # start all services
make health            # verify everything is running
```

## Installation

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker 24+ and Docker Compose v2
- PostgreSQL 16 (if running outside Docker)
- Redis 7 (if running outside Docker)

### Docker (Recommended)

```bash
# Start full stack
make up

# Check service status
make ps

# View logs
make logs-backend
make logs-db
```

### Local Development (without Docker)

```bash
# Backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
# Edit .env with your local PostgreSQL and Redis connection details
cd backend && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend-v2
npm install
npm run dev
```

## Development

```bash
# Setup
make up                   # start all services
cd backend && python -m pytest tests/ -v  # run tests
ruff check backend/app/   # lint Python
mypy backend/app/         # type check

# Frontend
cd frontend-v2 && npm run dev

# Pre-commit hooks
pip install pre-commit && pre-commit install
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor guide and
[CLAUDE.md](CLAUDE.md) for the comprehensive developer reference.

## Testing

```bash
# All backend tests
cd backend && python -m pytest tests/ -v

# By category
pytest tests/ -m unit          # unit tests (no DB/network)
pytest tests/ -m integration   # integration tests (require DB)
pytest tests/ -m security      # security tests
pytest tests/ -m kernel        # kernel subsystem tests

# Frontend tests
cd frontend-v2 && npm test

# Load testing
make load-test

# Chaos testing
make chaos-run
```

## Deployment

### Docker Compose (Single Server)

```bash
make up
make health-deep
```

### Kubernetes / Helm

```bash
helm install gula-platform helm/gula-platform --namespace gula --create-namespace
```

### Deployment Strategies

The project includes:
- **Canary deployments** — incremental traffic shifting
- **Blue-green deployments** — zero-downtime switching
- **Auto-rollback** — automatic failure recovery
- **Disaster recovery** — failover, failback, point-in-time recovery

See [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) and
[DEPLOYMENT_PLATFORMS.md](DEPLOYMENT_PLATFORMS.md) for details.

## Project Structure

```
gula-platform/
├── backend/              # FastAPI backend (Python)
│   └── app/
│       ├── routes/       # 36+ API route modules
│       ├── models/       # SQLAlchemy ORM models
│       ├── services/     # Business logic
│       ├── security/     # Auth, JWT, RBAC, ABAC
│       ├── kernel/       # DI, events, plugins
│       └── audit/        # Audit logging
├── frontend/             # React SPA (legacy)
├── frontend-v2/          # React + Firebase (current)
├── frontend-v3/          # React + TypeScript (next-gen)
├── services/             # Microservices (future)
├── mobile/               # Android, iOS, Flutter Desktop
├── docs/                 # ADRs, specs, reference
├── helm/                 # Kubernetes Helm charts
├── k8s/                  # Kubernetes manifests
├── terraform/            # Infrastructure as Code
├── docker/               # Docker configurations
└── scripts/              # Operational scripts
```

## Platform Constitution

This platform is governed by **PROGRAM-CONSTITUTION-001** — permanent amendment
establishing Free First, Open Source First, Self-Hosted First, and Cost Governance
as immutable platform rules.

| Principle | Summary |
|-----------|---------|
| Free First | Free solution before any paid alternative |
| Open Source First | Open Source before proprietary |
| Self-Hosted First | Self-hosted before SaaS |
| No Vendor Lock-In | Every component replaceable |
| Zero Paid Dependency | Paid requires documented exception |
| Local AI First | Self-hosted inference before API |
| Free Security First | Open-source security tools |

Full policy: `docs/constitution/COST_GOVERNANCE.md`

## Key Documents

- [CHANGELOG.md](CHANGELOG.md) — Release history
- [ARCHITECTURE.md](ARCHITECTURE.md) — System architecture
- [CONTRIBUTING.md](CONTRIBUTING.md) — Contributor guide
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) — Community standards
- [SECURITY.md](SECURITY.md) — Vulnerability reporting
- [GOVERNANCE.md](GOVERNANCE.md) — Project governance
- [SUPPORT.md](SUPPORT.md) — Getting help
- [ROADMAP.md](ROADMAP.md) — Development roadmap
- [CLAUDE.md](CLAUDE.md) — Developer guide

## Contributing

We welcome contributions of all kinds! Please see:

- [Contributing Guide](CONTRIBUTING.md) — development setup, workflow, and standards
- [Code of Conduct](CODE_OF_CONDUCT.md) — community guidelines
- [Security Policy](SECURITY.md) — vulnerability reporting
- [Support](SUPPORT.md) — getting help
- [Governance](GOVERNANCE.md) — project governance model
- [Roadmap](ROADMAP.md) — planned features and milestones

## License

Copyright 2025-2026 GULA Platform Contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

See the [LICENSE](LICENSE) file for full license text and the [NOTICE](NOTICE) file for attribution notices.
