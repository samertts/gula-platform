# APPLICATION ARCHITECTURE — PI-003 National Applications Suite

## 1. Overview

The GULA National Applications Suite (PI-003) delivers a unified healthcare platform
across four form factors — Desktop, Mobile, Web, and PWA — all backed by a single
FastAPI monolith. The architecture follows the **One Backend, One SDK, One Auth**
pattern: every application shares the same API surface, the same authentication
platform, and the same core SDK irrespective of the client platform.

```
                          ┌─────────────────────────────────┐
                          │     National API Gateway         │
                          │     (Docker nginx, TLS 1.3)      │
                          └────────────┬────────────────────┘
                                       │
                          ┌────────────┴────────────────────┐
                          │      gula-backend (FastAPI)       │
                          │   backend/app/main.py:276-297     │
                          │   Postgres 16 + Redis 7           │
                          │   Gunicorn + Uvicorn workers      │
                          └────────────┬────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
   ┌────────┴────────┐       ┌────────┴────────┐       ┌────────┴────────┐
   │   Desktop (Qt)  │       │  Mobile Native  │       │  Web / PWA       │
   │   PySide6       │       │  Flutter/Kotlin │       │  React/Vite      │
   │   Offline DB    │       │  Background Sync│       │  Service Worker  │
   │   Windows/Linux │       │  Android/iOS    │       │  frontend-v2/    │
   └─────────────────┘       └─────────────────┘       └─────────────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                          ┌────────────┴────────────┐
                          │   shared/ SDK & Auth     │
                          │   shared/sdk/client.py   │
                          │   shared/auth/jwt.py     │
                          │   shared/design_system/  │
                          └─────────────────────────┘
```

## 2. Shared Backend Architecture

All applications consume a single backend (`backend/app/main.py`). The monolith
exposes ~60 route modules covering:

| Domain | Routes | Module |
|--------|--------|--------|
| Auth & Identity | login, register, mfa, oauth2, saml, password_reset | `routes/login.py`, `routes/oauth2.py` |
| Patient Management | patients, national_identity, canonical_patient, mpi | `routes/patients.py`, `services/mpi/` |
| Laboratory | results, test_results, samples, quality_control | `routes/results.py` |
| Clinical | clinical, clinical_orders, clinical_documentation | `routes/clinical*.py` |
| National Platforms | national_data, care_continuum, citizen_platform | `routes/national_data.py` |
| Hospital | hospital, nhdw, nursing, pharmacy, radiology | `routes/hospital.py` |
| Intelligence | ai, intelligence, rules_engine, workflow_runtime | `routes/ai.py` |

### 2.1 Middleware Stack (order matters — `backend/app/main.py`)

1. **MaxBodySizeMiddleware** (line 350) — 413 above 10MB
2. **RequestIDMiddleware** (line 374) — X-Request-ID tracing
3. **CORSMiddleware** (line 467) — configured origins
4. **RequestTimingMiddleware** (line 489) — per-request access log
5. **SecurityHeadersMiddleware** (line 518) — CSP, HSTS, XFO
6. **GZipMiddleware** (line 557) — minimum 1KB
7. **ReadinessMiddleware** (line 576) — 503 until `system_ready`
8. **DegradedModeMiddleware** (`core/self_healing.py`) — circuit breaker
9. **KernelMiddleware** (line 611) — kernel runtime bootstrap
10. **ConcurrencyLimitMiddleware** (line 644) — per-worker backpressure

### 2.2 Database Layer (`backend/app/database.py`)

- **Engine:** SQLAlchemy 2.0 with connection pooling
- **Pool sizing:** `WORKERS × (POOL_SIZE + MAX_OVERFLOW)` = `2 × (5 + 10)` = 30 connections
- **Read replicas:** Optional `READ_REPLICA_URL` for read scaling
- **Circuit breaker:** Escalation from L1 (cache-heavy) → L2 (read-only) → L3 (critical-only)
- **Sliding window:** 5-minute event tracker for DB failure rate analysis
- **Statement timeout:** 30s default, `work_mem = 16MB`

### 2.3 Caching (`core/cache_manager.py`)

```
L1 (in-memory dict) → TTL 60s, max 10,000 entries
L2 (Redis 7)        → TTL 300s, shared across workers
```

## 3. Desktop Application Architecture

The National Laboratory Desktop Professional (Mission 024) is a native Windows
application built with **PySide6**.

### 3.1 Architecture

```
┌─────────────────────────────────────────┐
│           Desktop Shell (PySide6)        │
├─────────────────────────────────────────┤
│  UI Layer: Qt Widgets + QML             │
│  State: Redux-style stores              │
│  Offline: SQLite local cache (AES-256)  │
│  Sync: Background sync engine           │
│  Printing: Thermal + Laser + PDF        │
│  Scanner: Barcode/QR (USB + camera)     │
│  Device: ASTM E1394, HL7 ORU^R01       │
├─────────────────────────────────────────┤
│  Transport: HTTPS + mTLS                │
│  Auth: JWT (access + refresh)           │
│  SDK: shared/sdk/client.py              │
└─────────────────────────────────────────┘
```

### 3.2 Offline-First Design

- Local SQLite database encrypted with AES-256-GCM
- Full specimen lifecycle works offline
- Background sync engine with conflict resolution (last-write-wins + manual override)
- Delta sync for bandwidth efficiency

## 4. Mobile Application Architecture

Native Android (Kotlin) and iOS-ready mobile applications for the Citizen Super App
(Mission 021).

### 4.1 Architecture

```
┌─────────────────────────────────────────┐
│        Mobile Shell (Flutter/Kotlin)     │
├─────────────────────────────────────────┤
│  UI: Material Design 3 + RTL            │
│  State: Riverpod / ViewModel            │
│  Offline: Encrypted Room DB / SQLite    │
│  Sync: WorkManager + background sync    │
│  Biometrics: Fingerprint + Face ID      │
│  Push: FCM + APNS                       │
├─────────────────────────────────────────┤
│  Transport: HTTPS + certificate pinning │
│  Auth: JWT + refresh + biometric unlock │
│  SDK: shared/sdk/client.py (HTTP)       │
└─────────────────────────────────────────┘
```

### 4.2 Offline Capabilities

- Encrypted local cache for all patient-facing data
- Background sync via WorkManager (Android) / BGTaskScheduler (iOS)
- Queue-based mutation store with retry + exponential backoff
- Delta sync reduces bandwidth by ~70% for subsequent syncs

## 5. Web / PWA Architecture

The Web Application (`frontend-v2/`) serves the Citizen Portal, Doctor Workspace,
Ministry Command Centre, and Laboratory Dashboard.

### 5.1 Technology Stack

- **Framework:** React 19 with TypeScript
- **Build:** Vite 6 (`vite.config.ts`)
- **Styling:** Tailwind CSS 4 (`@tailwindcss/vite`)
- **PWA:** vite-plugin-pwa (`package.json:42`)
- **State:** React Router v7 + context
- **Charts:** recharts
- **QR:** html5-qrcode
- **Animations:** motion
- **Error tracking:** Sentry (`@sentry/react`)

### 5.2 PWA Service Worker (`frontend/sw.js`)

```
Cache Strategy:
  Static assets   → cache on install (pre-cache)
  JS/CSS          → network-first, fallback to cache
  API calls       → network-only (never cache patient data)
  Images          → stale-while-revalidate
```

### 5.3 Offline Support

- `manifest.json` with `"display": "standalone"` and `"dir": "rtl"`
- Service worker caches shell for offline rendering
- API mutations queued via Background Sync API
- IndexedDB for local encrypted cache

## 6. Code Sharing Strategy

### 6.1 The `shared/` Package

All platform code lives in `shared/` at the repo root:

| Module | Purpose | Used By |
|--------|---------|---------|
| `shared/sdk/client.py` | HTTP client, typed methods | Desktop, Mobile, Web |
| `shared/auth/` | JWT create/decode, MFA, WebAuthn, passwords | All apps + backend |
| `shared/design_system/` | Tokens, RTL, components | Desktop, Web |
| `shared/rbac/` | Role hierarchy, permissions, ABAC | All apps + backend |
| `shared/security/` | Encryption (Fernet/AES-256-GCM) | All apps + backend |
| `shared/config/` | Environment loader | Backend |
| `shared/validators/` | National ID, phone, email | All apps |
| `shared/pdf/` | Report generation | Desktop, Web |

### 6.2 SDK Client (`shared/sdk/client.py:10`)

```python
class GulaClient:
    def __init__(self, base_url, api_key=None, timeout=30.0):
    def get(self, path, params=None)
    def post(self, path, data=None)
    def create_patient(self, data)
    def get_patient(self, patient_id)
    def create_order(self, data)
    def create_result(self, data)
    def health(self)
```

Single SDK — every application uses the same `GulaClient`. Authentication is
handled at the transport layer (Bearer token), not at the SDK level.

## 7. Authentication Platform

The **One Auth Platform** serves every application through multiple protocols:

| Protocol | Route | Purpose |
|----------|-------|---------|
| JWT (access + refresh) | `/token` | All first-party apps |
| OAuth2 / OIDC | `/oauth2/*` | Third-party integrations |
| SAML 2.0 | `/saml/*` | Government SSO (Iraq e-Government) |
| MFA (TOTP) | `/mfa/totp/*` | User security (shared/auth/mfa.py) |
| WebAuthn / FIDO2 | `/mfa/webauthn/*` | Passwordless auth (shared/auth/webauthn.py) |
| Service Accounts | `/service-accounts/*` | Machine-to-machine |

### 7.1 Auth Modules (`shared/auth/`)

```python
# shared/auth/jwt.py
create_access_token(data, secret_key, expire_minutes=30)
create_refresh_token(data, refresh_secret, expire_days=30)
decode_access_token(token, secret_key)
```

All apps authenticate through the same JWT infrastructure. Tokens carry `user_id`,
`lab_id`, `role`, and `perm_version` claims. Revocation is via Redis blacklist.

## 8. Deployment Topology

```
Internet → Host nginx (TLS 1.3)
              → api-gateway (Docker nginx on 127.0.0.1:8080)
                  → gula-backend (FastAPI, port 8000)
                      → PostgreSQL 16
                      → Redis 7
```

All four application types (Desktop, Mobile, Web, PWA) connect to the same
`gula-backend` through the same API gateway. There is no separate backend per
application type.
