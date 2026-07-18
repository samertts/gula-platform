# GULA Platform — Dependency Graph
**Date:** 2026-07-17

---

## 1. Internal Module Dependencies

```
gula-backend
│
├── main.py
│   ├── config.py
│   ├── database.py
│   ├── routes/* (53+)
│   │   ├── services/* (34+)
│   │   │   ├── models/* (60+)
│   │   │   │   └── database.py
│   │   │   └── core/* (15+)
│   │   ├── security/* (15+)
│   │   │   ├── shared/auth/*
│   │   │   ├── shared/rbac/*
│   │   │   └── shared/security/*
│   │   ├── ai/*
│   │   ├── audit/*
│   │   └── tasks/*
│   ├── core/* (startup_guard, self_healing, etc.)
│   │   ├── database.py
│   │   └── shared/circuit_breaker/*
│   ├── security/dependencies.py
│   │   ├── shared/auth/*
│   │   └── shared/rbac/*
│   └── models/* (via lifespan import)
│
├── worker.py
│   ├── core/self_healing.py (RecoveryWorker)
│   ├── core/auto_repair.py
│   ├── services/outbox_service.py
│   └── database.py
│
└── shared/ (canonical library)
    ├── auth/
    │   ├── jwt.py
    │   ├── passwords.py
    │   ├── mfa.py
    │   └── webauthn.py
    ├── rbac/
    │   └── permissions.py
    ├── security/
    │   ├── encryption.py
    │   └── hmac.py
    ├── audit/
    │   └── audit.py
    ├── circuit_breaker/
    │   └── circuit_breaker.py
    └── messaging/
        └── messaging.py
```

---

## 2. External Service Dependencies

```
gula-backend (Monolith)
├── PostgreSQL 16     ─── Primary database
├── Redis 7           ─── Cache, rate limiting, session
├── Ollama (:11434)   ─── Local AI (optional)
├── Gemini API        ─── Cloud AI (optional, EO violation)
├── Groq API          ─── Cloud AI (optional, EO violation)
└── Sentry DSN        ─── Error tracking (optional)

gula-worker
├── PostgreSQL 16     ─── Outbox processing
└── Redis 7           ─── Cache, sliding window

services/device_bridge
└── Lab analyzers     ─── Sysmex, Roche, Mindray (serial/TCP)

services/ai
├── Ollama (:11434)   ─── Local AI (only provider)
└── Redis             ─── (optional, from config)

services/notification
└── RabbitMQ          ─── Alert consumer

services/{lab,order,patient,result,sample}
├── PostgreSQL        ─── Data storage
└── RabbitMQ          ─── Event publishing

frontend-v2
├── Firebase Auth     ─── Authentication
├── Cloud Firestore   ─── Data storage
└── FastAPI (minimal?) ─── Some API calls

client
└── FastAPI (tRPC)    ─── Full backend connection
```

---

## 3. Package Dependencies (Python - Production)

### From `requirements.txt` and `requirements-lock.txt`

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.139.0 | Web framework |
| uvicorn | 0.51.0 | ASGI server |
| gunicorn | 21.2+ | WSGI server |
| sqlalchemy | 2.0.51 | ORM |
| alembic | 1.18.5 | Migrations |
| psycopg2-binary | 2.9.9 | PostgreSQL driver |
| pydantic | 2.13.4 | Validation |
| python-jose | 3.4+ | JWT (HS256) |
| cryptography | 49.0.0 | Encryption (Fernet) |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| bcrypt | 4.1.3 | Hashing algorithm |
| redis | 8.0.1 | Redis client |
| httpx | 0.27+ | HTTP client |
| qrcode | 7.4.2 | QR generation |
| Pillow | 10.4.0 | Image processing |
| reportlab | 4.1.0 | PDF generation |
| arabic-reshaper | 3.0.0 | Arabic text |
| python-bidi | 0.4.2 | Bidirectional text |
| sentry-sdk | 2.65.0 | Error tracking |
| python-multipart | 0.0.20 | Form parsing |

### Development Dependencies
| Package | Version | Purpose |
|---------|---------|---------|
| pytest | 9.0.3 | Test framework |
| pytest-asyncio | 0.23+ | Async test support |
| factory_boy | 3.3.0 | Test fixtures |
| webauthn | 2.0.0 | WebAuthn testing |
| email-validator | 2.1.0 | Email validation |

---

## 4. Docker Image Dependencies

```
ghcr.io/samertts/gula-platform/backend (8 images in matrix)
├── python:3.11-slim
│   ├── fastapi + uvicorn + gunicorn
│   ├── sqlalchemy + alembic + psycopg2
│   ├── pydantic + python-jose + cryptography
│   ├── redis + httpx + sentry-sdk
│   └── reportlab + arabic-reshaper + python-bidi
│
├── svc-lab          (stub)
├── svc-order        (stub)
├── svc-patient      (stub)
├── svc-result       (stub with ClickHouse, Kafka, MinIO)
├── svc-sample       (stub)
├── svc-notification (stub with RabbitMQ)
└── svc-ai           (functional: Ollama gateway)

services/device_bridge → lablink-core:0.1.0 (Python 3.12)

Docker Compose Images:
├── postgres:16-alpine / postgres:14.11-alpine
├── redis:7-alpine
├── nginx:1.25-alpine (api-gateway + frontend)
├── prom/prometheus:v2.50.1
├── grafana/grafana:10.3.3
├── ollama/ollama:0.1.29
├── minio/minio:RELEASE.2024-01
├── rabbitmq:3.12-management
├── confluentinc/cp-kafka:7.5.0
├── clickhouse/clickhouse-server:23.8
├── hashicorp/vault:1.15
├── quay.io/keycloak/keycloak:23.0
├── edoburu/pgbouncer:1.22.1
└── prom/node-exporter:v1.7.0
```

---

## 5. CI/CD Pipeline Dependencies

```
GitHub Actions Runner
├── Python 3.11
├── PostgreSQL 16 (service container)
├── Redis 7.2 (service container)
├── Docker-in-Docker
│
├── Job: syntax-gate
│   ├── python -m py_compile
│   ├── import-walk (unittest.mock stubs)
│   └── flake8 --select=E9,F821
│
├── Job: migration-check
│   ├── alembic upgrade head
│   ├── required table verification
│   └── alembic downgrade -1 + upgrade head
│
├── Job: backend-test
│   ├── postgres:16-alpine (service)
│   └── redis:7.2-alpine (service)
│   ├── pytest tests/ -v
│
├── Job: security-scan
│   ├── safety check
│   ├── bandit -ll -ii
│   ├── hadolint
│   └── gitleaks
│
└── Job: build-and-push
    ├── Docker buildx (matrix: 8 images)
    └── trivy image scan
```

---

## 6. Key Dependency Findings

| Finding | Impact |
|---------|--------|
| Firebase Firestore is a separate data store not gated by backend | **CRITICAL** — dual-write risk |
| services/shared/ is a deprecated bridge | **LOW** — still functional |
| services/result has ClickHouse + Kafka + MinIO deps but is a stub | **MEDIUM** — premature complexity |
| Ollama dependency for local AI is optional | **LOW** — degrades gracefully |
| RabbitMQ is defined but only 1 microservice uses it | **LOW** — future-proofing |
| Terraform targets AWS, actual deployment is DigitalOcean | **HIGH** — infrastructure misalignment |
