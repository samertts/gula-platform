# GULA Platform — Complete Repository Map
**Date:** 2026-07-17

---

## Root Directory Structure

```
gula-platform/
├── .github/               # CI/CD workflows (6 files)
│   └── workflows/
│       ├── ci.yml                    # Main CI (644 lines, 7 jobs)
│       ├── deploy.yml                # SSH-based deployment
│       ├── blue-green-deploy.yml     # K8s blue-green
│       ├── canary-deploy.yml         # Linkerd canary
│       ├── auto-rollback.yml         # Rollback on failure
│       └── quality-gate.yml          # 9 quality gates
│
├── backend/               # Core monolith (PRODUCTION)
│   ├── app/               # FastAPI application (~120K LOC)
│   │   ├── main.py        # App init, 11 middleware layers, 50+ routes
│   │   ├── config.py      # Env vars, secrets, 200+ settings
│   │   ├── database.py    # SQLAlchemy engine, pool, contextvars
│   │   ├── worker.py      # Background worker (6 resilient loops)
│   │   ├── routes/        # 53+ route modules
│   │   ├── models/        # 26+ ORM model files
│   │   ├── services/      # 34+ business logic files
│   │   ├── core/          # 15 infrastructure modules
│   │   ├── security/      # 15 security modules
│   │   ├── clinical/      # Terminology, CDS, quality, knowledge
│   │   ├── ai/            # AI sandbox, guardrails
│   │   ├── edge/          # Edge AI platform (10+ files)
│   │   ├── financial/     # Schema-only (Phase A)
│   │   ├── audit/         # Audit logging
│   │   ├── firewall/      # Rate limiting, IP blocklist
│   │   ├── gateways/      # External system adapters (8 files)
│   │   ├── notifications/ # Multi-channel notifications
│   │   ├── legal/         # Consent/legal models
│   │   ├── tasks/         # Background tasks (Outbox)
│   │   ├── hospital/      # Hospital management
│   │   ├── lims/          # National LIMS (35 tables)
│   │   ├── pharmacy/      # Pharmacy platform (23+ tables)
│   │   ├── radiology/     # Radiology platform (19+ tables)
│   │   ├── nursing/       # Nursing platform (15+ tables)
│   │   ├── ems/           # Emergency medicine (12+ tables)
│   │   ├── blood_bank/    # Blood bank (11+ tables)
│   │   ├── critical_care/ # Critical care (13+ tables)
│   │   ├── biomedical/    # Biomedical engineering (11+ tables)
│   │   ├── public_health/ # Public health surveillance
│   │   ├── nhdw/          # National Health Data Warehouse
│   │   ├── health_data/   # Warehouse, ODS, MDM, Canonical
│   │   ├── command_center/# National command center
│   │   ├── command_intelligence/ # AI-driven intelligence
│   │   ├── national/      # National platform components
│   │   ├── national_data/ # National data exchange
│   │   ├── trust/         # Trust platform
│   │   ├── governance/    # Governance models
│   │   ├── contracts/     # Contract interfaces
│   │   ├── knowledge_graph/ # Clinical knowledge graph
│   │   ├── roadmap/       # Platform roadmap tracking
│   │   ├── simulation/    # Digital twins, simulations
│   │   ├── citizen_platform/ # Citizen portal
│   │   ├── control_plane/ # Runtime control plane
│   │   ├── certification/ # Platform certification
│   │   ├── interoperability/ # Cross-platform interop
│   │   ├── research_platform/ # Clinical research
│   │   ├── ecosystem/     # Partner ecosystem
│   │   ├── pilot_platform/ # Pilot deployment
│   │   ├── lifecycle_platform/ # Component lifecycle
│   │   ├── workflow/      # Workflow engine
│   │   └── ...            # ~70 total directories
│   │
│   ├── migrations/        # Alembic (48 migration files)
│   │   └── versions/      # 20250322_0000 → 20260716_0016
│   ├── tests/             # 124 test files
│   └── requirements*.txt  # Dependencies
│
├── services/              # Microservices (10 subdirectories)
│   ├── device_bridge/     # LabLink-Core — ASTM/HL7 (36 files, MATURE)
│   ├── ai/                # Ollama AI service (FUNCTIONAL)
│   ├── autonomous_manager/ # Self-healing manager (FUNCTIONAL)
│   ├── lab/               # Lab CRUD (STUB)
│   ├── order/             # Order CRUD + events (STUB)
│   ├── patient/           # Patient CRUD + events (STUB)
│   ├── result/            # Result + ClickHouse + Kafka + MinIO (STUB+)
│   ├── sample/            # Sample tracking (STUB)
│   ├── notification/      # RabbitMQ consumer (STUB)
│   └── shared/            # Deprecated bridge to canonical shared/
│
├── frontend-v2/           # React + Firebase (citizen/doctor/lab/ministry)
├── client/                # tRPC + React SPA
├── frontend/              # Static HTML PWA
├── hospital_desktop/      # Desktop application
│
├── shared/                # Canonical shared library
│   ├── auth/              # JWT, passwords, MFA, WebAuthn
│   ├── rbac/              # Permissions (9 roles × 13+ permissions)
│   ├── security/          # Encryption, HMAC
│   ├── audit/             # Hash-chained audit
│   ├── circuit_breaker/   # Circuit breaker pattern
│   └── messaging/         # RabbitMQ message broker
│
├── ai/                    # Top-level AI modules
├── scripts/               # 35+ operational scripts
├── edge_agent/            # Edge computing agent
├── nhop-platform/         # National Health Oversight (separate FastAPI)
├── cli/                   # Developer CLI v2.1.0
├── server/                # Express.js gateway
│
├── config/                # Infrastructure configuration (~93 files)
│   ├── nginx/             # API gateway + frontend nginx configs
│   ├── prometheus/        # Scrape configs + alerting rules
│   ├── grafana/           # Provisioned dashboards
│   ├── haproxy/           # HAProxy load balancer
│   ├── postgres/          # PostgreSQL production config
│   ├── redis/             # Redis configuration
│   ├── rabbitmq/          # RabbitMQ config + definitions
│   ├── vault/             # HashiCorp Vault config
│   ├── tempo/             # Distributed tracing
│   ├── loki/              # Log aggregation
│   ├── security/           # SAST/DAST/container scanning configs
│   ├── siem/               # Elastic Security + Wazuh
│   └── quality-gates/     # 9 quality gate implementations
│
├── k8s/                   # Kubernetes manifests
│   ├── base/              # Kustomize base (14 files)
│   └── overlays/          # dev/, prod/, region-eu/, region-me/
│
├── terraform/             # AWS IaC (~65 files)
│   ├── modules/           # 12 modules (networking, security, DB, K8s, etc.)
│   └── environments/      # dev/, staging/, pilot/, prod/, dr/
│
├── helm/                  # Helm chart (38 template files)
│   └── gula-platform/     # Chart v1.0.0, App v2.1.0
│
├── digitalocean/          # DO App Platform spec
├── cloudflare/            # Edge workers, WAF rules, DNS
├── supabase/              # Managed Postgres config
│
├── docs/                  # ~200+ documentation files
│   ├── adr/               # 24 Architecture Decision Records
│   ├── sovereign/         # National sovereignty (~65 files, 10 phases)
│   ├── sndhs/             # SNDHS-lite spec (17 files)
│   ├── runbooks/          # 7 incident response runbooks
│   ├── production/        # 9 production guides
│   ├── engineering/       # Constitution, quality gates, risk register
│   └── ...                # Clinical, AI, edge, identity, integration
│
├── docker-compose.yml     # MVP compose (7 services)
├── docker-compose.full.yml # Full compose (25+ services, 821 lines)
├── docker-compose.scale.yml # Horizontal scaling (HAProxy)
├── Dockerfile              # Frontend build
├── Makefile                # 70+ targets (522 lines)
│
├── nginx.conf             # Standalone nginx (151 lines)
├── deploy.sh              # Universal deployment (351 lines)
├── setup-production.sh    # One-command production setup (244 lines)
│
├── .env.example           # Env template (364 lines)
├── .env.production        # Production env template
├── pyproject.toml         # Python project config
├── package.json           # Node project
├── pnpm-workspace.yaml    # PNPM workspace
├── tsconfig.json          # TypeScript config
├── vite.config.ts         # Vite build config
├── vercel.json            # Vercel deployment
│
└── README*.md, ARCHITECTURE.md, CHANGELOG.md, etc.
```
