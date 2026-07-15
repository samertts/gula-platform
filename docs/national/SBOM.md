# Software Bill of Materials — National Healthcare Platform

## Python Runtime & Framework

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime |
| FastAPI | 0.109+ | Web framework |
| Uvicorn | 0.27+ | ASGI server |
| Gunicorn | 21.2+ | WSGI process manager |
| Pydantic | 2.5+ | Data validation & settings |
| Pydantic Settings | 2.1+ | Environment configuration |

## Database & ORM

| Component | Version | Purpose |
|-----------|---------|---------|
| PostgreSQL | 16 | Primary database |
| SQLAlchemy | 2.0+ | ORM & SQL toolkit |
| Alembic | 1.13+ | Database migrations |
| psycopg2-binary | 2.9+ | PostgreSQL adapter |
| asyncpg | 0.29+ | Async PostgreSQL adapter |
| SQLAlchemy-Utils | 0.41+ | Utility functions |

## Caching & Message Queue

| Component | Version | Purpose |
|-----------|---------|---------|
| Redis | 7 | Caching & session store |
| redis-py | 5.0+ | Redis client |
| RabbitMQ | 3.12+ | Message broker |
| aio-pika | 9.3+ | Async RabbitMQ client |

## Authentication & Security

| Component | Version | Purpose |
|-----------|---------|---------|
| PyJWT | 2.8+ | JWT encoding/decoding |
| python-jose | 3.3+ | JOSE (JWT/JWS/JWE) |
| cryptography | 41.0+ | Encryption primitives |
| bcrypt | 4.1+ | Password hashing |
| passlib | 1.7+ | Password hashing library |
| python-multipart | 0.0.6+ | Form data parsing |
| python-dotenv | 1.0+ | Environment file loading |

## FHIR / Healthcare

| Component | Version | Purpose |
|-----------|---------|---------|
| fhir.resources | 7.0+ | FHIR R4 data models |
| fhirpath-py | 0.8+ | FHIRPath evaluation |
| hl7 | 0.4+ | HL7 v2 message parsing |
| python-dicom | 2.4+ | DICOM image handling |

## Testing

| Component | Version | Purpose |
|-----------|---------|---------|
| pytest | 7.4+ | Test framework |
| pytest-asyncio | 0.23+ | Async test support |
| pytest-cov | 4.1+ | Code coverage |
| pytest-xdist | 3.5+ | Parallel test execution |
| httpx | 0.26+ | HTTP client for testing |
| factory-boy | 3.3+ | Test data factories |
| freezegun | 1.2+ | Time mocking |
| moto | 4.2+ | AWS service mocking |

## Monitoring & Observability

| Component | Version | Purpose |
|-----------|---------|---------|
| Prometheus | 2.50+ | Metrics collection |
| Grafana | 10.3+ | Metrics visualization |
| Grafana Loki | 3.0+ | Log aggregation |
| OpenTelemetry | 1.22+ | Distributed tracing |
| Python JSON Logger | 2.0+ | Structured logging |
| Sentry SDK | 1.40+ | Error tracking |

## Deployment & Infrastructure

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 24+ | Container runtime |
| Docker Compose | 2.24+ | Multi-container orchestration |
| nginx | 1.25+ | API gateway & reverse proxy |
| HAProxy | 2.9+ | Load balancer |
| MinIO | 2024+ | S3-compatible object storage |
| Elasticsearch | 8.11+ | Full-text search |
| Kibana | 8.11+ | Search visualization |

## Clinical Intelligence (AI/ML)

| Component | Version | Purpose |
|-----------|---------|---------|
| scikit-learn | 1.3+ | ML algorithms |
| sentence-transformers | 2.2+ | Text embeddings |
| numpy | 1.26+ | Numerical computing |
| pandas | 2.1+ | Data manipulation |
| transformers | 4.36+ | LLM integration |
| onnxruntime | 1.16+ | ML model inference |

## Internationalization

| Component | Version | Purpose |
|-----------|---------|---------|
| Babel | 2.13+ | i18n/l10n support |
| python-slugify | 8.0+ | URL/text slug generation |
| pyarabic | 1.0+ | Arabic text processing |

## Developer Tooling

| Component | Version | Purpose |
|-----------|---------|---------|
| flake8 | 7.0+ | Linter (error-only rules: E9, F821) |
| pyflakes | 3.1+ | Fast linter |
| mypy | 1.7+ | Static type checking |
| ruff | 0.1+ | Fast Python linter |
| black | 23.12+ | Code formatter |
| pre-commit | 3.6+ | Git hooks |
| safety | 2.4+ | CVE scanning |
| bandit | 1.7+ | Security scanning |
| hadolint | 2.12+ | Dockerfile linting |
| gitleaks | 8.18+ | Secret scanning |

## Database Schema Summary

| Schema | Tables | Models |
|--------|--------|--------|
| `public` | ~20 | Labs, users, orders, results, samples |
| `ehr` | 14 | Problems, allergies, medications, care plans, notes, immunizations, timeline |
| `hospital` | 13 | Hospitals, campuses, buildings, beds, departments, equipment |
| `cc` | 25+ | Referrals, care journeys, chronic disease, maternal, immunizations, tasks |
| `clinical` | 12+ | Terminology, guidelines, order sets, quality indicators |
| `national` | 20+ | Citizens, patients, encounters, facilities, organizations, practitioners |
| `national_data` | 15+ | Canonical, MDM, event store, governance, deidentification |

## Service Dependencies

```
gula-backend (FastAPI)
  ├── PostgreSQL 16 (primary data store)
  ├── Redis 7 (cache, sessions, rate limiting)
  ├── RabbitMQ 3.12+ (event bus, async processing)
  ├── MinIO / S3 (document/attachment storage)
  └── Elasticsearch 8 (full-text search, FHIR search)
```

## Network Ports

| Port | Service | Purpose |
|------|---------|---------|
| 443 | Host nginx | TLS termination |
| 8080 | api-gateway | Internal routing |
| 8000 | gula-backend | FastAPI application |
| 5432 | PostgreSQL | Database |
| 6379 | Redis | Cache |
| 5672 | RabbitMQ | AMQP |
| 15672 | RabbitMQ | Management UI |
| 9090 | Prometheus | Metrics |
| 3000 | Grafana | Dashboards |
| 9200 | Elasticsearch | Search API |
| 9000 | MinIO | S3 API |
