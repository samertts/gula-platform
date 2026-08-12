# GULA Platform — Platform Stability Assessment
**Date:** 2026-07-17

---

## 1. Stability Zones

```
┌─────────────────────────────────────────────────────────────────┐
│                    PLATFORM STABILITY MAP                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CRITICAL — MUST NOT CHANGE                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • 20250322_0000_create_base_schema.py (immutable)           │ │
│  │ • Audit log hash chain + PG trigger                         │ │
│  │ • Patient data tenant isolation (lab_id filter)             │ │
│  │ • JWT auth + refresh token rotation                         │ │
│  │ • Encryption: Fernet AES-256 + HMAC for NIDs                │ │
│  │ • Config secrets validation (SECRET_KEY, ENCRYPTION_KEY)    │ │
│  │ • Optimistic locking on LabResult/LabOrder                  │ │
│  │ • system_ready flag + startup guard                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  STABLE — Change with Migration                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • Core routes: labs, patients, orders, results, samples     │ │
│  │ • Core models: Lab, LabUser, Patient, LabOrder, LabResult   │ │
│  │ • Service layer: interpretation, outbox, audit              │ │
│  │ • Security: RBAC, ABAC, rate limiting, MFA                  │ │
│  │ • Database: core tables (labs, patients, lab_orders, etc.)  │ │
│  │ • API response shapes (mobile clients depend on them)       │ │
│  │ • FHIR resource endpoints                                   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  REPLACEABLE — Can Be Refactored                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • Large route files (ehr.py 73KB, compliance.py 47KB)       │ │
│  │ • 6 microservice stubs (lab, order, patient, sample, etc.)  │ │
│  │ • frontend (static PWA)                                     │ │
│  │ • firewall/ directory                                       │ │
│  │ • Duplicate AI engines (services/ai)                        │ │
│  │ • services/shared (deprecated bridge)                       │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  EXPERIMENTAL — Not Yet Stable                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ • National platform domains (pharmacy, radiology, nursing)  │ │
│  │ • Clinical decision support (schema-only)                   │ │
│  │ • All tables from 2026-07-16 migrations (17 migrations)     │ │
│  │ • Financial Engine (Phase A — schema only)                  │ │
│  │ • frontend-v2 (Firebase bypass)                             │ │
│  │ • hospital_desktop                                          │ │
│  │ • SNDHS Phase 1 features (behind flags)                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Critical Components (Must Not Change Without Review)

| Component | Reason | Penalty for Breaking |
|-----------|--------|---------------------|
| Base migration (20250322_0000) | Fresh deploy bootstrap | NoSuchTableError |
| Audit hash chain trigger | Tamper evidence | Compliance failure |
| Tenant isolation (lab_id filter) | Data leakage | Patient data exposure |
| JWT auth flow | Access control | Auth bypass |
| Encryption pipeline | Data protection | Plaintext NIDs |
| Optimistic locking | Data integrity | Lost updates |
| Startup guard | System integrity | Premature traffic |
| Config secrets validation | Credential safety | Weak secrets |

---

## 3. Stable APIs (Consumer Contracts)

### REST API
- `GET/POST /api/v1/labs` — Lab management
- `GET/POST /api/v1/patients` — Patient management
- `GET/POST /api/v1/orders` — Lab orders
- `GET/POST /api/v1/results` — Lab results
- `GET/POST /api/v1/samples` — Sample tracking
- `POST /api/v1/auth/login` — Authentication
- `POST /api/v1/auth/refresh` — Token refresh

### FHIR API
- `GET /api/v1/fhir/Patient/{id}`
- `GET /api/v1/fhir/Observation/{id}`
- `GET /api/v1/fhir/Encounter/{id}`

### Internal Contracts
- `emit_to_outbox()` — Transactional outbox
- `get_current_user()` — Auth dependency
- `require_permission()` — RBAC check
- `require_own_lab()` — Tenant isolation

---

## 4. Stable Database Structures

### Core Tables (DO NOT ALTER without migration)
| Table | Immutable Since | Reason |
|-------|----------------|--------|
| `labs` | 2025-03-22 | Core tenant |
| `lab_users` | 2025-03-22 | Auth dependency |
| `patients` | 2025-03-22 | Clinical core |
| `lab_orders` | 2025-03-22 | Workflow core |
| `lab_results` | 2025-03-22 | Clinical data |
| `samples` | 2025-03-22 | Workflow |
| `test_types` | 2025-03-22 | Reference data |
| `audit_logs` | 2025-03-22 | Compliance |
| `outbox_events` | 2025-03-22 | Event bus |

### Stable Indexes
- `idx_lab_orders_patient_lab` — Common query pattern
- `idx_lab_orders_lab_status` — Status filtering
- `idx_lab_results_order` — Order lookup
- `idx_patients_phone` — Phone lookup (exact match)
- `idx_audit_logs_timestamp` — Time-range queries

---

## 5. Stable Platform Core (gula-backend)

The monolith at `backend/app/` is the production stable core. The following modules are production-hardened:

```
backend/app/
├── main.py            # Lifespan, middleware, routes, health
├── config.py          # Env vars, secrets
├── database.py        # Engine, pool, contextvars
├── core/              # Startup guard, self-healing, auto-repair
│   ├── startup_guard.py
│   ├── self_healing.py
│   ├── auto_repair.py
│   ├── feature_flags.py
│   └── sndhs_flags.py
├── security/          # Auth, RBAC, encryption, rate limit
├── models/            # Core ORM models
├── routes/            # Core route modules
├── services/          # Business logic
└── domain/            # Order state machine
```

---

## 6. Replaceable Components

| Component | Replacement Strategy | Priority |
|-----------|---------------------|----------|
| `services/lab/`, `order/`, `patient/`, etc. (6 stubs) | Delete or implement properly | Medium |
| `frontend/` (static PWA) | Migrate to client/ or retire | Low |
| `services/shared/` (deprecated bridge) | Delete (canonical shared/ exists) | Low |
| `hospital_desktop/` | Investigate and decide | Unknown |
| `firewall/` | Merge into security/ | Low |

---

## 7. Experimental Components

| Component | Status | Risk | Recommendation |
|-----------|--------|------|---------------|
| National LIMS (35 tables) | Schema only | Low (no code uses it) | Stabilize or remove |
| Pharmacy platform (23 tables) | Schema only | Low | Ship or remove |
| Radiology platform (19 tables) | Schema only | Low | Ship or remove |
| Nursing platform (15 tables) | Schema only | Low | Ship or remove |
| EMS (12 tables) | Schema only | Low | Ship or remove |
| Blood bank (11 tables) | Schema only | Low | Ship or remove |
| Financial Engine | Schema only (Phase A) | Low | Keep behind flag |
| frontend-v2 (Firebase) | Active development | HIGH | Align with backend |
| Clinical CDS (schema only) | Schema only | Low | Ship or remove |

---

## 8. Stability Recommendations

| Recommendation | Priority |
|---------------|----------|
| Freeze base migrations — never modify | Critical |
| Add integration tests for critical flows | Critical |
| Document all stable API contracts | High |
| Create consumer changelog | High |
| Stabilize national platform domains one at a time | Medium |
| Remove or implement microservice stubs | Medium |
| Resolve frontend-v2 Firebase alignment | High |
| Add end-to-end smoke tests | High |
