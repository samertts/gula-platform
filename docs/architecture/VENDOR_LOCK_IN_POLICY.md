# Vendor Lock-In Policy

**Version:** 1.0.0
**Date:** 2026-07-23
**Authority:** Platform Constitution Amendment — PROGRAM-CONSTITUTION-001, Article 6
**Status:** ADOPTED — FROZEN — PERMANENT

---

## Policy Statement

Every component of the GULA National Digital Health Platform MUST be
replaceable. The platform MUST NEVER be coupled to any single vendor,
cloud provider, or commercial service.

---

## Abstraction Mandate

### Section 1 — Every Dependency Must Have an Abstraction Layer

```python
# CORRECT — Abstracted dependency
class StorageBackend(ABC):
    @abstractmethod
    async def store(self, key: str, data: bytes): ...
    @abstractmethod
    async def retrieve(self, key: str) -> bytes: ...

class MinioStorage(StorageBackend):
    ...

class LocalFilesystemStorage(StorageBackend):
    ...

# WRONG — Direct vendor coupling
from minio import Minio  # Direct dependency
client = Minio(endpoint="...")
client.put_object(...)
```

### Section 2 — Abstraction Requirements

Every abstraction layer MUST:
1. Define a **interface** (ABC, Protocol, or trait)
2. Have at least **2 implementations** (primary + fallback/mock)
3. Be **testable** with in-memory mocks
4. Be **documented** with replacement guide
5. Not expose vendor-specific types in the interface

---

## Prohibited Coupling

### Directly Prohibited

- **AWS-specific SDK calls** in business logic
- **Azure-specific annotations** throughout codebase
- **Google Cloud client libraries** without abstraction
- **Firebase SDK** (removed per Firebase deprecation)
- **Supabase client** without abstraction layer
- **Auth0 SDK** without abstraction
- **Okta SDK** without abstraction
- **Stripe SDK** without abstraction layer
- **Twilio SDK** without abstraction layer
- **SendGrid SDK** without abstraction layer
- **Any commercial SaaS SDK** in core domain code

### Architecture Violation Patterns

| Pattern | Severity | Detection |
|---------|----------|-----------|
| Vendor SDK in core domain | BLOCKER | Import analysis |
| Vendor types exposed in public API | BLOCKER | API review |
| Vendor-specific config without abstraction | HIGH | Config audit |
| No fallback for vendor service | HIGH | Architecture review |
| Vendor annotations on domain models | HIGH | Code review |
| Vendor lock-in in deployment config | MEDIUM | IaC review |

---

## Cloud Provider Neutrality

### Section 1 — Abstraction Required For

| Service | Abstraction Required | Fallback Implementation |
|---------|---------------------|----------------------|
| Object Storage | StorageBackend interface | MinIO (self-hosted) |
| Database | SQLAlchemy (already abstracted) | PostgreSQL |
| Cache | RedisInterface | In-process memory |
| Queue | MessageQueue interface | RabbitMQ, in-process |
| Search | SearchEngine interface | OpenSearch, in-memory |
| Email | EmailProvider interface | Self-hosted SMTP |
| SMS | SMSProvider interface | Self-hosted gateway |
| Push Notifications | PushProvider interface | WebSocket fallback |
| AI Inference | AIModel interface | Ollama, local models |
| Identity | IdentityProvider interface | Keycloak, Authentik |
| DNS | Cloudflare Free (standard) | Self-hosted DNS |
| CDN | CDNProvider interface | Nginx + MinIO |

### Section 2 — Provider-Specific Features

Provider-specific features (AWS Lambda, Google Cloud Functions, Azure Logic Apps)
MUST NOT be used. Equivalent functionality MUST be implemented using portable
technologies:
- Background tasks: Python asyncio / Celery / RQ
- Scheduled jobs: cron / APScheduler
- Workflows: Temporal / Prefect (self-hosted)
- Event processing: Kafka / RabbitMQ (self-hosted)

---

## Migration Strategy

### Section 1 — Every Dependency Must Have a Migration Plan

Every dependency MUST document:
1. How to migrate away from this dependency
2. Alternative implementations available
3. Estimated migration effort
4. Data migration requirements (if any)
5. Testing strategy for migration

### Section 2 — Migration Testing

- CI MUST test at least 2 implementations of every abstraction
- Integration tests MUST run against different backends
- Performance tests MUST compare implementations
- Migration smoke tests MUST run quarterly

---

## Detection and Enforcement

### Automated Detection (CI)

CI MUST scan for:
1. Direct imports of vendor SDKs without abstraction layer
2. Vendor-specific configuration patterns
3. Hardcoded vendor endpoints
4. Vendor annotations on domain models
5. Missing alternative implementations

### Architecture Review

Every architecture decision MUST address:
1. Vendor lock-in risk assessment
2. Abstraction layer design
3. Alternative implementations
4. Migration strategy

### Quarterly Audit

Every quarter:
1. Review all dependencies for lock-in risk
2. Verify abstraction layers are maintained
3. Test migrations between implementations
4. Update migration plans for any new dependencies

---

## Compliance

### PR Requirements

Every PR that introduces a new external dependency MUST include:
- [ ] Abstraction layer interface defined
- [ ] At least 2 implementations (or migration plan)
- [ ] No vendor types in interface
- [ ] Tests with both implementations
- [ ] Architecture review sign-off

### CI Enforcement

CI will:
- BLOCK any PR with vendor SDK in core domain
- WARN on any PR with vendor SDK without abstraction
- FAIL if any abstraction layer has only 1 implementation

---

## Exceptions

Exceptions to No Vendor Lock-In policy require:
1. Architecture Decision Record (ADR) documenting rationale
2. Architecture Review Board approval (supermajority)
3. Technical justification why abstraction is impossible
4. Time-bounded exception with mandatory migration date
5. Annual re-evaluation
