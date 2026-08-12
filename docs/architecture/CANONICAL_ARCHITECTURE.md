# GULA Canonical Architecture

## One Unified Platform Architecture

### Architecture Principles

1. **Single Source of Truth** — Every concern has exactly one canonical implementation in `shared/`
2. **Repository Consolidation** — All code from Platform-Core, LabLink-Core, Receipt-and-delivery, OGLG, Front-end, govlab-platform, INWP, and identity-credential is unified
3. **Layered Design** — Presentation → Application → Domain → Infrastructure
4. **Arabic-First** — RTL support at every layer
5. **Event-Driven** — Asynchronous communication via the canonical EventBus
6. **Tenant-Isolated** — Every query scoped by `lab_id`
7. **Audit-Everywhere** — Every mutation logged through the canonical AuditService

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Presentation                       │
│  (frontend-v2 / client / frontend / REST APIs)      │
├─────────────────────────────────────────────────────┤
│                   Application                        │
│  (routes / use-cases / commands / queries)          │
├─────────────────────────────────────────────────────┤
│                    Domain                            │
│  (entities / value-objects / domain-services)       │
├─────────────────────────────────────────────────────┤
│                 Infrastructure                       │
│  (shared/ library / DB / cache / storage / MQ)      │
└─────────────────────────────────────────────────────┘
```

---

## Canonical Component Map

| Concern | Canonical Module | Source Repository |
|---------|-----------------|-------------------|
| **Authentication** | `shared/auth/` | Platform-Core (`security/auth.py`) |
| **Authorization / RBAC** | `shared/rbac/` | Platform-Core (`security/rbac.py`) |
| **Password Hashing** | `shared/auth/passwords.py` | Platform-Core (`security/auth.py`) |
| **JWT Token Management** | `shared/auth/jwt.py` | Platform-Core (`security/auth.py`) |
| **Configuration** | `shared/config/` | Platform-Core (`config.py`) |
| **Event Bus** | `shared/events/` | Platform-Core (`core/events.py`) |
| **Message Broker** | `shared/messaging.py` | Platform-Core + Services |
| **Logging** | `shared/logging/` | Platform-Core (`core/logging_config.py`) |
| **Audit Trail** | `shared/audit/` | Platform-Core + Services/shared |
| **Metrics** | `shared/metrics/` | Platform-Core (`routes/metrics.py`) |
| **Caching** | `shared/cache/` | Platform-Core (`security/redis_client.py`) |
| **Retry / Resilience** | `shared/retry/` | Platform-Core (`core/resilience.py`) |
| **Circuit Breaker** | `shared/circuit_breaker.py` | Services/shared |
| **Health Check** | `shared/health/` | Platform-Core (`main.py`) |
| **QR Code** | `shared/qr/` | Platform-Core (`routes/qr.py`, `services/patient_card.py`, `services/pdf_report.py`) |
| **Barcode** | `shared/barcode/` | Platform-Core (`models/sample.py`) |
| **PDF Generation** | `shared/pdf/` | Platform-Core (`services/pdf_report.py`) |
| **Encryption** | `shared/security/encryption.py` | Platform-Core (`security/encryption.py`) |
| **Storage** | `shared/storage/` | Platform-Core + Gateways |
| **Notifications** | `shared/notifications/` | Platform-Core + NHOP |
| **Backup / Restore** | `shared/backup/` | Scripts + Operations |
| **Workflow Engine** | `shared/workflow/` | Platform-Core (`workflows/`) |
| **Policy Engine** | `shared/policies/` | Platform-Core (`policies/`) |
| **Validation** | `shared/validators/` | Platform-Core (`validation/`) |
| **Observability** | `shared/observability/` | Platform-Core |
| **Tracing** | `shared/tracing/` | Platform-Core (`main.py` RequestIDMiddleware) |
| **Device Integration** | `shared/device/` | LabLink-Core (services/device_bridge) |
| **Design System** | `shared/design_system/` | frontend-v2 + client |
| **Middleware** | `shared/middleware/` | Platform-Core (`main.py`) |
| **Schemas** | `shared/schemas/` | Platform-Core |
| **Models** | `shared/models/` | Platform-Core |
| **Utilities** | `shared/utilities/` | All repos |
| **Printing** | `shared/printing/` | Platform-Core |

---

## One Authentication Flow

```
Client → shared/auth/jwt.py (create_access_token)
       → shared/auth/passwords.py (hash_password / verify_password)
       → shared/middleware/base.py (RequestIDMiddleware)
       → shared/rbac/permissions.py (has_permission)
       → shared/audit/service.py (create_audit_entry)
```

## One Audit Trail

```
Any mutation → shared/audit/service.py
             → audit_logs table (SHA-256 chain)
             → shared/events/bus.py (event emission)
             → shared/messaging.py (message broker)
```

## One Event Bus

```
shared/events/bus.py (in-process)
shared/messaging.py (RabbitMQ for cross-service)
Both use shared/events/constants.py for event names
```

---

## Security Invariants

1. All patient data queries filter by `lab_id`
2. All mutations write to audit log
3. National IDs encrypted with Fernet + HMAC-signed
4. JWT verified with required `exp` and `iat` claims
5. Rate limiting on auth endpoints (10 req/min default)
6. Security headers on every response (CSP, HSTS, X-Frame-Options)
7. Circuit breaker prevents cascading failures
8. Retry with exponential backoff for external calls
9. Request IDs for end-to-end tracing

---

## Migration Path

| From | To | Status |
|------|----|--------|
| `services/shared/audit.py` | `shared/audit/` | ✅ Bridged |
| `services/shared/circuit_breaker.py` | `shared/circuit_breaker.py` | ✅ Bridged |
| `services/shared/messaging.py` | `shared/messaging.py` | ✅ Bridged |
| `backend/app/security/auth.py` (auth funcs) | `shared/auth/` | ✅ Extracted |
| `backend/app/core/events.py` | `shared/events/` | ✅ Extracted |
| `backend/app/core/logging_config.py` | `shared/logging/` | ✅ Extracted |
| `backend/app/core/resilience.py` | `shared/retry/` | ✅ Extracted |
| `backend/app/security/redis_client.py` | `shared/cache/` | ✅ Extracted |
| `backend/app/routes/qr.py` | `shared/qr/` | ✅ Consolidated |
| `backend/app/models/sample.py` | `shared/barcode/` | ✅ Consolidated |
| `backend/app/services/pdf_report.py` | `shared/pdf/` | ✅ Consolidated |
| `backend/app/services/audit_service.py` | `shared/audit/` | ✅ Extracted |
| `backend/app/security/encryption.py` | `shared/security/` | ✅ Extracted |
| `backend/app/security/rbac.py` | `shared/rbac/` | ✅ Extracted |
