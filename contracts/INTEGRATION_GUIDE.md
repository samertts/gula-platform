# GULA Platform Integration Guide

**Version:** 2.1.0 | **Status:** FROZEN | **Date:** 2026-07-14

Arabic-first healthcare platform for Iraqi medical laboratories. This guide documents every API, event, protocol, and SDK contract consumed by external developers.

---

## Table of Contents

1. [Platform Overview](#1-platform-overview)
2. [Getting Started](#2-getting-started)
3. [API Conventions](#3-api-conventions)
4. [Domain API Guide](#4-domain-api-guide)
5. [FHIR R4 Integration](#5-fhir-r4-integration)
6. [HL7 v2.x Integration](#6-hl7-v2x-integration)
7. [ASTM E1381/E1394 Integration](#7-astm-e1381e1394-integration)
8. [Events & Webhooks](#8-events--webhooks)
9. [SDK Usage](#9-sdk-usage)
10. [Offline Sync Pattern](#10-offline-sync-pattern)
11. [Rate Limits](#11-rate-limits)
12. [Error Catalog](#12-error-catalog)
13. [v1.x → v2.x Migration](#13-v1x--v2x-migration)
14. [Security Model](#14-security-model)

---

## 1. Platform Overview

GULA is a **medical laboratory information system (LIS)** built for the Iraqi healthcare system. It manages the full laboratory workflow: patient registration, order placement, specimen tracking, result entry (manual and instrument-driven), quality control, clinical validation, reporting, and national health data submission.

### Core Capabilities

| Capability | Description |
|---|---|
| Patient Management | Master Patient Index (MPI), deduplication, QR card system |
| Lab Orders | Test ordering, batch import, priority (routine/urgent/stat) |
| Sample Tracking | Full lifecycle from collection through disposal |
| Instrument Integration | ASTM E1394, HL7 v2.5.1, vendor-specific adapters |
| Quality Control | IQC, EQA, Levey-Jennings, Westgard rules |
| Clinical AI | Interpretation suggestions, anomaly detection |
| Citizen Portal | Test result access, consent management |
| National Reporting | SNDHS-lite data submission to Ministry of Health |
| Edge Computing | Offline-capable agent for remote sites |
| Financial Engine | Insurance claims, billing (Phase A schema) |

### Base URL

**Production:** `https://api.gula-platform.org`
**Staging:** `https://staging.gula-platform.org`
**Local:** `http://localhost:8000`

### Architecture Overview

```
Internet → nginx (TLS) → api-gateway (127.0.0.1:8080) → gula-backend (FastAPI, :8000) → PostgreSQL 16 + Redis 7
                                                                   ↓
                                                            Outbox Worker → Webhooks → External Systems
                                                                   ↓
                                                            Edge Agent ←→ Device Bridge (ASTM/HL7)
```

### Stack

- **Runtime:** Python 3.10+, FastAPI, gunicorn + uvicorn workers
- **Database:** PostgreSQL 16 (primary), Redis 7 (cache, rate-limiter, JWT blacklist)
- **Frontend:** React 19 + TypeScript + Firebase (citizen portal)
- **Events:** Transactional outbox pattern (`outbox_events` table, at-least-once delivery)
- **Deployment:** Docker Compose (primary), Kubernetes overlays available

---

## 2. Getting Started

### Authentication

GULA uses **JWT Bearer tokens** (HS256) for API authentication.

**Obtain token:**

```bash
curl -X POST https://api.gula-platform.org/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@lab.example.com", "password": "your-password"}'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Use token:**

```bash
curl https://api.gula-platform.org/patients \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Refresh token:**

```bash
curl -X POST https://api.gula-platform.org/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

### Token Payload

```json
{
  "user_id": 42,
  "lab_id": 7,
  "role": "lab_admin",
  "perm_ver": 3,
  "type": "access",
  "jti": "uuid-v4",
  "exp": 1700000000
}
```

### Token Lifetimes

- **Access token:** 60 minutes (configurable via `JWT_EXPIRE_MINUTES`)
- **Refresh token:** 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)

### Required Headers

| Header | Required | Description |
|---|---|---|
| `Authorization` | Yes | `Bearer <token>` |
| `Content-Type` | Yes | `application/json` |
| `X-Request-ID` | Recommended | UUID for request tracing |
| `Idempotency-Key` | For mutations | UUID for idempotent writes |
| `X-Device-ID` | For device endpoints | Instrument/device identifier |
| `X-App-Version` | Recommended | Client application version |

### Actor Types & Registration Endpoints

| Actor | Register Endpoint | Notes |
|---|---|---|
| Lab | `POST /register` | Creates lab + admin, pending approval |
| Citizen | `POST /register/citizen` | Self-registration with optional national_id |
| Doctor | `POST /register/doctor` | Self-registration with license number |
| Staff | `POST /register/staff` | By lab admin |
| Mobile | `POST /mobile/register-device` | FCM/APNS push notification token |

---

## 3. API Conventions

### Versioning

API version is indicated via the `X-API-Version` response header and the `APP_VERSION` environment variable. URL path versioning (`/v1/`, `/v2/`) is **not used** — the API is forward-compatible within the same major version. Breaking changes trigger a new major version announcement with a migration window.

### Pagination

List endpoints use cursor-based pagination:

**Request:**
```
GET /patients?cursor=eyJpZCI6MTAwLCJjcmVhdGVkX2F0IjoiMjAyNi0wMS0wMVQwMDowMDowMFoifQ==&limit=50
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTUwLCJjcmVhdGVkX2F0IjoiMjAyNi0wMS0wMVQwMDowMDowMFoifQ==",
    "has_more": true,
    "limit": 50
  }
}
```

| Parameter | Type | Default | Max |
|---|---|---|---|
| `cursor` | string (base64) | — | — |
| `limit` | integer | 20 | 200 |
| `page` (legacy) | integer | 1 | N/A |

Legacy offset-based pagination (`?page=1&per_page=20`) is supported but **deprecated**.

### Filtering

```http
GET /orders?status=pending&lab_id=7&patient_id=42
GET /results?test_code=GLU&is_critical=true&date_from=2026-01-01&date_to=2026-06-30
```

| Pattern | Example |
|---|---|
| Exact match | `?status=pending` |
| Date range | `?date_from=2026-01-01&date_to=2026-06-30` |
| Nested filter | `?patient__name=محمد` (double underscore for relationship traversal) |
| Multiple values | `?status__in=pending,completed` |

### Sorting

```http
GET /patients?sort=-created_at
GET /orders?sort=+priority,-created_at
```

Prefix with `-` for descending, `+` or no prefix for ascending.

### Error Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "detail_ar": "رسالة الخطأ بالعربية",
  "request_id": "uuid",
  "code": "ERROR_CODE",
  "field": "field_name",
  "violations": [
    {"field": "email", "reason": "already_registered", "reason_ar": "البريد الإلكتروني مسجل مسبقاً"}
  ]
}
```

### Idempotency

Mutation endpoints support idempotent writes via the `Idempotency-Key` header. Keys are UUID v4 strings stored for 24 hours.

```bash
curl -X POST https://api.gula-platform.org/orders \
  -H "Authorization: Bearer <token>" \
  -H "Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 42, "results": [...]}'
```

- Same key + same request body → same response (idempotent)
- Same key + different body → `409 Conflict`
- Expired keys (24h) are treated as new requests

### ETags / Conditional Requests

List endpoints return `ETag` headers. Use `If-None-Match` to skip unchanged responses:

```bash
curl -H "Authorization: Bearer <token>" \
  -H "If-None-Match: \"33a64df551425fcc55e4d42a148795d9f25f89d4\"" \
  https://api.gula-platform.org/patients
```

Returns `304 Not Modified` when data is unchanged.

---

## 4. Domain API Guide

### 4.1 Authentication (`/login`, `/auth/*`, `/register`)

| Method | Path | Description |
|---|---|---|
| POST | `/login` | Authenticate and receive JWT |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/change-password` | Change password (authenticated) |
| POST | `/auth/logout` | Revoke token (adds to Redis blacklist) |
| POST | `/register` | Register a new lab |
| POST | `/register/citizen` | Citizen self-registration |
| POST | `/register/doctor` | Doctor self-registration |
| POST | `/register/staff` | Lab admin adds staff |
| POST | `/mobile/register-device` | Register FCM/APNS push token |

**Example — Login:**
```bash
curl -X POST https://api.gula-platform.org/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@lab.com", "password": "secret123"}'
```

**Example — Logout:**
```bash
curl -X POST https://api.gula-platform.org/auth/logout \
  -H "Authorization: Bearer <token>"
```

### 4.2 Labs (`/labs`)

| Method | Path | Description |
|---|---|---|
| GET | `/labs/me` | Get current lab profile |
| PUT | `/labs/me` | Update lab profile |
| GET | `/labs/me/employees` | List lab employees |
| POST | `/labs/me/employees` | Add employee |
| PATCH | `/labs/me/employees/{id}` | Update employee |
| DELETE | `/labs/me/employees/{id}` | Deactivate employee |

**Example — Get Lab Profile:**
```bash
curl https://api.gula-platform.org/labs/me \
  -H "Authorization: Bearer <token>"
```

### 4.3 Patients (`/patients`)

| Method | Path | Description |
|---|---|---|
| GET | `/patients` | List patients (paginated) |
| POST | `/patients` | Create patient |
| GET | `/patients/{id}` | Get patient |
| PUT | `/patients/{id}` | Update patient |
| DELETE | `/patients/{id}` | Soft-delete patient |
| GET | `/patients/search?q=` | Search patients by name/phone |
| POST | `/patients/{id}/merge` | Merge duplicate patient (admin) |

**Example — Create Patient:**
```bash
curl -X POST https://api.gula-platform.org/patients \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "محمد علي حسن",
    "phone": "07701234567",
    "birth_date": "1985-03-15",
    "gender": "male"
  }'
```

**Example — Search:**
```bash
GET /patients/search?q=محمد&phone=0770
```

### 4.4 Orders (`/orders`)

| Method | Path | Description |
|---|---|---|
| GET | `/orders` | List orders |
| POST | `/orders` | Create order with results |
| GET | `/orders/{id}` | Get order details |
| PATCH | `/orders/{id}` | Update order |
| DELETE | `/orders/{id}` | Cancel order |
| POST | `/batch/orders` | Batch create (max 50) |
| GET | `/orders/by-barcode/{barcode}` | Lookup by sample barcode |

**Example — Create Order:**
```bash
curl -X POST https://api.gula-platform.org/orders \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": 42,
    "doctor_name": "د. أحمد",
    "results": [
      {"test_name": "Glucose", "value": 95.3, "unit": "mg/dL"}
    ]
  }'
```

**Order States:**

```
pending → completed → validated → released
  ↓
cancelled
```

### 4.5 Results (`/results`, `/test-results`)

| Method | Path | Description |
|---|---|---|
| GET | `/results` | List results (staff) |
| POST | `/test-results` | Create test result (citizen-centric) |
| GET | `/test-results/{id}` | Get result detail |
| GET | `/test-results/citizen/{health_id}` | Citizen's results |
| POST | `/test-results/validate` | Pre-save validation |
| GET | `/results/by-order/{order_id}` | Results for an order |

**Example — Get Citizen Results:**
```bash
curl https://api.gula-platform.org/test-results/citizen/HN-98765 \
  -H "Authorization: Bearer <token>"
```

### 4.6 Samples (`/samples`)

| Method | Path | Description |
|---|---|---|
| GET | `/samples` | List samples |
| POST | `/samples` | Create sample |
| GET | `/samples/{barcode}` | Get sample by barcode |
| PATCH | `/samples/{barcode}` | Update sample status |
| GET | `/samples/tracking/{barcode}` | Full tracking history |

**Sample States:**

```
ordered → registered → collected → transporting → received → accepted → analysis_started → analyzed → verified → validated → released → archived → disposed
                                                                                                                          ↓
                                                                                                                       rejected
```

### 4.7 Quality Control (`/quality-control`)

| Method | Path | Description |
|---|---|---|
| GET | `/quality-control` | List QC runs |
| POST | `/quality-control/iqc` | Run internal QC |
| GET | `/quality-control/iqc/{id}` | Get IQC details |
| GET | `/quality-control/levey-jennings/{test_code}` | Levey-Jennings chart data |
| POST | `/quality-control/eqa` | Submit EQA result |

### 4.8 Clinical AI (`/ai`)

| Method | Path | Description |
|---|---|---|
| POST | `/ai/analyze` | Clinical interpretation analysis |
| POST | `/ai/suggest` | Get AI interpretation suggestion |
| POST | `/ai/suggest/{id}/reject` | Reject AI suggestion |
| POST | `/ai/chat` | AI assistant chat (Gemini 2.0 Flash) |

**Example — Clinical Analysis:**
```bash
curl -X POST https://api.gula-platform.org/ai/analyze \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "results": [
      {"test_name": "Glucose", "value": 185, "unit": "mg/dL", "normal_range_high": 110}
    ]
  }'
```

### 4.9 Statistics (`/stats`)

| Method | Path | Description |
|---|---|---|
| GET | `/stats/dashboard` | Lab dashboard statistics |
| GET | `/stats/trends` | Trend analysis |
| GET | `/stats/abnormal-rate` | Abnormal result rate |
| GET | `/stats/turnaround-time` | TAT analysis |

### 4.10 Patient Card (`/patient-card`)

| Method | Path | Description |
|---|---|---|
| POST | `/patient-card/generate` | Generate QR card |
| GET | `/patient-card/{patient_id}` | Get patient card (HTML) |
| POST | `/patient-card/scan` | Scan QR code (verify HMAC token) |

**Example — Generate Card:**
```bash
curl -X POST https://api.gula-platform.org/patient-card/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": 42}'
```

### 4.11 Consent (`/consent`)

| Method | Path | Description |
|---|---|---|
| POST | `/consent/grant` | Grant time-bounded consent |
| POST | `/consent/revoke` | Revoke consent |
| GET | `/consent/check?gpid=&grantee_id=&scope=` | Check consent |

**Example — Grant Consent:**
```bash
curl -X POST https://api.gula-platform.org/consent/grant \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "gpid": "01HABCDEFGHIJKLMNOPQRSTUVWX",
    "grantee_id": "user:42",
    "scope": "view:results",
    "expires_in_hours": 24
  }'
```

### 4.12 Edge Devices (`/edge`)

| Method | Path | Description |
|---|---|---|
| POST | `/edge/devices/register` | Register edge device |
| GET | `/edge/devices` | List devices |
| GET | `/edge/devices/{device_id}` | Get device detail |
| DELETE | `/edge/devices/{device_id}` | Revoke device |
| POST | `/edge/tasks` | Submit edge task |
| GET | `/edge/tasks/{task_id}` | Get task status |
| POST | `/edge/heartbeat` | Device heartbeat |

### 4.13 Claims (`/claims`)

| Method | Path | Description |
|---|---|---|
| GET | `/claims` | List insurance claims |
| POST | `/claims` | Create claim (draft) |
| GET | `/claims/{id}` | Get claim detail |
| PATCH | `/claims/{id}` | Update claim |
| POST | `/claims/{id}/submit` | Submit claim to insurer |

### 4.14 National ID / Identity (`/national-id`, `/identity`)

| Method | Path | Description |
|---|---|---|
| POST | `/national-id/verify` | Verify national ID |
| POST | `/identity/link` | Link national ID to patient |

### 4.15 Admin (`/admin`)

| Method | Path | Description |
|---|---|---|
| GET | `/admin/labs` | List all labs (master_admin) |
| POST | `/admin/labs` | Create lab |
| GET | `/admin/users` | List platform users |
| POST | `/admin/users` | Create platform user |
| PATCH | `/admin/users/{id}/role` | Change user role |
| POST | `/admin/kill-switch` | Toggle kill switch |
| GET | `/admin/audit-log` | View audit log |

### 4.16 Device Integration (`/device`, `/lims/integration`)

| Method | Path | Description |
|---|---|---|
| POST | `/device/results` | Submit device results |
| POST | `/lims/integration/astm/receive` | Receive ASTM message |
| POST | `/lims/integration/hl7/receive` | Receive HL7 message |
| POST | `/lims/integration/simulate` | Generate test message |

### 4.17 Compliance / FHIR (`/compliance`)

| Method | Path | Description |
|---|---|---|
| GET | `/compliance/fhir/Patient/{id}` | FHIR Patient resource |
| GET | `/compliance/fhir/Observation/{id}` | FHIR Observation resource |
| GET | `/compliance/fhir/DiagnosticReport/{id}` | FHIR DiagnosticReport |
| GET | `/compliance/fhir/ServiceRequest/{id}` | FHIR ServiceRequest |

### 4.18 Health (`/health`)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/health/live` | Liveness |
| GET | `/health/ready` | Readiness (Docker healthcheck) |
| GET | `/health/status` | Startup diagnostic |
| GET | `/health/deep` | Full diagnostic (grade, latency, memory) |
| GET | `/health/kernel` | Kernel health |

---

## 5. FHIR R4 Integration

### Base URLs

| Endpoint Family | Base Path | Resources |
|---|---|---|
| Government Compliance | `/compliance/fhir/{resource}/{id}` | Patient, Observation, DiagnosticReport, ServiceRequest |
| LIMS | `/lims/{resource}s/{id}/fhir` | Device, Specimen, ServiceRequest, Observation, DiagnosticReport |
| National Data Layer | `/national/fhir/{resource}/{id}` | Patient, Practitioner, Organization, Encounter, Observation |

### Supported Resources (10 types)

| Resource | Family | FHIR Profile |
|---|---|---|
| Patient | Compliance, National | `https://gula-platform.org/fhir/profiles/gula-patient` |
| Practitioner | National | `https://gula-platform.org/fhir/profiles/gula-practitioner` |
| Organization | National | `https://gula-platform.org/fhir/profiles/gula-organization` |
| Encounter | National | `https://gula-platform.org/fhir/profiles/gula-encounter` |
| Observation | Compliance, LIMS, National | `https://gula-platform.org/fhir/profiles/gula-observation` |
| DiagnosticReport | Compliance, LIMS | `https://gula-platform.org/fhir/profiles/gula-diagnostic-report` |
| Specimen | LIMS | `https://gula-platform.org/fhir/profiles/gula-specimen` |
| ServiceRequest | Compliance, LIMS | `https://gula-platform.org/fhir/profiles/gula-service-request` |
| Device | LIMS | `https://gula-platform.org/fhir/profiles/gula-device` |
| Bundle | All | Standard FHIR Bundle |

### Terminology Bindings

| System | Usage |
|---|---|
| `http://loinc.org` | Laboratory test identification |
| `http://snomed.info/sct` | Clinical terminology |
| `http://unitsofmeasure.org` | UCUM units of measure |
| `http://terminology.hl7.org/CodeSystem/v2-0203` | Identifier type codes |
| `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation` | Observation interpretation (H, L, HH, LL, N, A) |
| `http://terminology.hl7.org/CodeSystem/observation-category` | Observation category codes |
| `http://gula.iq/CodeSystem/specimen-type` | GULA specimen types (custom) |

### Identifier Systems

| System | Resource | Description |
|---|---|---|
| `https://gula.health/identifier/health-number` | Patient | Health Number (primary identifier) |
| `https://gula.health/identifier/national-id` | Patient | HMAC-hashed national ID (first 16 chars only) |
| `https://gula.health/identifier/license` | Practitioner | Medical license number |
| `https://gula.health/identifier/org` | Organization | Organization identifier |
| `https://gula-platform.org/fhir/patient-id` | Patient | Internal Patient ID |
| `https://gula-platform.org/fhir/order-id` | ServiceRequest | Internal Order ID |
| `urn:gula:lims:specimen` | Specimen | Specimen barcode |

### Capability Statement

Full FHIR CapabilityStatement available at:
```
GET /compliance/fhir/metadata
```

### Example — Retrieve Patient as FHIR Resource

```bash
curl https://api.gula-platform.org/compliance/fhir/Patient/C-12345 \
  -H "Authorization: Bearer <token>" \
  -H "Accept: application/fhir+json"
```

Response:
```json
{
  "resourceType": "Patient",
  "id": "C-12345",
  "identifier": [
    {
      "use": "usual",
      "type": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]
      },
      "system": "https://gula.health/identifier/health-number",
      "value": "HN-98765"
    }
  ],
  "name": [{"use": "official", "family": "حسن", "given": ["محمد", "علي"]}],
  "gender": "male",
  "birthDate": "1985-03-15",
  "active": true,
  "managingOrganization": {"reference": "Organization/LAB-7"}
}
```

### Example — Search Observations

```bash
GET /compliance/fhir/Observation?patient=C-12345&code=http://loinc.org|2345-7&_count=50
```

---

## 6. HL7 v2.x Integration

### Supported Version: 2.5.1

### Message Types

| Type | Status | Description |
|---|---|---|
| `ORU^R01` | **Active** | Unsolicited observation result (instrument → LIS) |
| `ACK` | **Active** | General acknowledgment (LIS → instrument) |
| `ADT^A01` | Planned | Admit/visit notification |
| `ADT^A04` | Planned | Patient registration |
| `ORM^O01` | Planned | Lab order placement |
| `QBP^Q22` | Not planned | Patient demographics query |

### Transport

HL7 messages are transported over **HTTP POST** to the GULA backend:

```
POST /lims/integration/hl7/receive
Authorization: Bearer <token>
Content-Type: application/json

{
  "instrument_id": 5,
  "raw_message": "MSH|^~\\&|SIMULATOR|SIMLAB|LIS|LAB|20260714143000||ORU^R01|A1B2C3D4|P|2.5.1\rPID|||PAT-A1B2C3||SIM^PATIENT||19800101|M\rSPM|1|SMP-A1B2C3D4||SER^Serum\rOBR|1|SMP-A1B2C3D4^SIM|A1B2C3D4^SIM|GLU^Glucose|||20260714143000\rOBX|1|NM|GLU^Glucose||95.3|mg/dL|70.0-110.0|N|||F\r"
}
```

### Encoding

| Property | Value |
|---|---|
| Format | ER7 (pipe-delimited) |
| Segment terminator | `\r` (0x0D, CR) |
| Field separator | `|` |
| Component separator | `^` |
| Subcomponent separator | `&` |
| Repetition separator | `~` |
| Escape character | `\\` |
| Character encoding | UTF-8, ASCII |

### ORU^R01 Message Structure

```
MSH  — Message Header (R)
PID  — Patient Identification (R)
PV1  — Patient Visit (O)
ORC  — Common Order (O)
OBR  — Observation Request (R)
SPM  — Specimen Details (O)
NTE  — Notes (O, 0+)
OBX  — Observation/Result (R, 1+)
NTE  — Result Notes (O, 0+ per OBX)
```

### Key Field Mappings

| HL7 Field | GULA Field |
|---|---|
| PID-3 (Patient Identifier List) | `patient_id` |
| SPM-2 (Specimen ID) | `specimen_id` / barcode |
| OBR-3 (Filler Order Number) | `instrument_result_id` |
| OBX-3.1 (Observation Identifier - code) | `test_code` |
| OBX-3.2 (Observation Identifier - name) | `test_name` |
| OBX-5 (Observation Value) | `value` |
| OBX-6 (Units) | `unit` |
| OBX-7 (Reference Range) | `ref_range` |
| OBX-8 (Abnormal Flags) | `abnormal_flag` (N/H/L/LL/HH) |
| OBX-11 (Result Status) | `result_status` (F/P/C/X/D) |

### ACK Response

```hl7
MSH|^~\&|LIS|LAB|SENDING_APP|SENDING_FAC|20260714143000||ACK|MSGID123|P|2.5.1
MSA|AA|A1B2C3D4
```

| Code | Meaning | HTTP |
|---|---|---|
| AA | Application Accept — processed successfully | 200 |
| AE | Application Error — valid message, processing failed | 500 |
| AR | Application Reject — message rejected | 400 |

### Vendor Profiles

| Vendor | Instruments | Notes |
|---|---|---|
| Roche | Cobas c 311/501/502, e 411/601 | Patient IDs in PID-2 or PID-3 |
| Abbott | Architect c8000/i1000SR, Alinity | Specimen barcode in OBR-2/OBR-3 |
| Siemens | Dimension EXL 200/500, Atellica | NTE segments for remarks |
| GULA Simulator | Test only | Codes: GLU, CRE, BUN, NA, K |

### Test Profiles

| Code | Name | Unit | Ref Range |
|---|---|---|---|
| GLU | Glucose | mg/dL | 70.0–110.0 |
| CRE | Creatinine | mg/dL | 0.6–1.2 |
| BUN | Blood Urea Nitrogen | mg/dL | 7–20 |
| NA | Sodium | mmol/L | 136–145 |
| K | Potassium | mmol/L | 3.5–5.1 |
| CL | Chloride | mmol/L | 98–107 |
| CA | Calcium | mg/dL | 8.5–10.5 |
| TP | Total Protein | g/dL | 6.0–8.3 |
| ALB | Albumin | g/dL | 3.5–5.0 |
| TBIL | Total Bilirubin | mg/dL | 0.1–1.2 |
| ALP | Alkaline Phosphatase | U/L | 44–147 |
| ALT | ALT (SGPT) | U/L | 10–40 |
| AST | AST (SGOT) | U/L | 10–40 |

---

## 7. ASTM E1381/E1394 Integration

### Standard: E1394-97 (E1381-02 serial transport)

### Frame Format

```
STX (0x02) + payload + ETX (0x03) + checksum (2 hex chars)
```

### Message Structure

Result Upload (instrument → LIS):
```
H  — Header (R)
P  — Patient/Specimen (R)
O  — Order/Test (R)
R  — Result (R)
C  — Comment (O)
L  — Terminator (R)
```

Host Query (LIS → instrument):
```
ENQ → ACK → Q frame → ACK → H/P/O/R/L frames → ACK → EOT
```

### Frame Types

| Frame | Required | Description |
|---|---|---|
| H | Yes | Header — sender, receiver, protocol version |
| P | Yes | Patient — specimen ID, patient name |
| O | Yes | Order — test code, specimen barcode |
| R | Yes | Result — value, unit, ref range, flag |
| C | No | Comment — free-text notes |
| L | Yes | Terminator — ends transmission |
| Q | No | Query — LIS requests data from instrument |

### Key Field Mappings

| ASTM Field | GULA Field |
|---|---|
| P-2 | `specimen_id` |
| O-4 | `test_code` |
| R-5 | `value` |
| R-6 | `unit` |
| R-7 | `ref_range` |
| R-8 | `flag` (N/H/L) |
| R-2 | `instrument_result_id` |

### Example ASTM Message

```
H|\^&|||SIMULATOR|||||ASTM_E1394|0001|
P|1|SMP-A1B2C3D4|||SIM^PATIENT|||M|19800101
O|1|SMP-A1B2C3D4|WBC|White Blood Cell Count|||
R|1|A1B2C3D4|WBC|White Blood Cell Count|7.5|10^3/uL|4.0-11.0|N
L|1|N
```

### Connection Parameters

| Parameter | Serial | TCP/IP |
|---|---|---|
| Baud | 9600 (default), up to 115200 | — |
| Data bits | 8 | — |
| Parity | none, even | — |
| Stop bits | 1 | — |
| Port | — | 5000 (default) |
| Encoding | ASCII | ASCII |

### Vendor Support

| Vendor | Models | Adapter |
|---|---|---|
| Sysmex | XS-1000i, XT-2000i, XN-350/550/1000/2000 | SysmexAdapter (maps HGB→HB) |
| Mindray | BC-2600/3600/5000/6000/6800, BS-200/400/800 | MindrayAdapter (UNKNOWN→UNMATCHED) |
| Roche | Cobas c 311/501/502, e 411/601, 8000 | RocheAdapter (normalizes units) |
| Generic | Any ASTM E1394 device | GenericASTMAdapter (passthrough) |

### Data Pipeline (Device Bridge)

```
Raw bytes → ASTMBuffer → Frame extraction → Checksum validation
    → ASTMParser → MessageBuilder → AdapterRegistry transforms
    → TestMappingEngine → PatientMatcher → Normalizer
    → ResultRepository → GulaClient (REST) → RetryQueue / EdgeBuffer
```

---

## 8. Events & Webhooks

### Event System

All domain events use the **transactional outbox pattern**. Events are written atomically to the `outbox_events` table within the same database transaction as the business operation, ensuring at-least-once delivery.

| Property | Value |
|---|---|
| Table | `outbox_events` |
| Delivery guarantee | At-least-once |
| Max attempts | 5 |
| Poll interval | 10 seconds |
| Batch size | 50 |
| Purge after | 30 days |
| Backoff | Exponential (1s → 2s → 4s → 8s → 16s) |

### Event Catalog (85+ events)

**Specimen Lifecycle (14 events):**
`lims.specimen.ordered`, `lims.specimen.registered`, `lims.specimen.collected`, `lims.specimen.transporting`, `lims.specimen.received`, `lims.specimen.accepted`, `lims.specimen.rejected`, `lims.specimen.aliquoted`, `lims.specimen.analysis_started`, `lims.specimen.analyzed`, `lims.specimen.verified`, `lims.specimen.validated`, `lims.specimen.released`, `lims.specimen.archived`, `lims.specimen.disposed`

**Order Lifecycle (5 events):**
`lims.order.accessioned`, `lims.order.completed`, `lims.order.validated`, `lims.order.released`, `lims.order.cancelled`, `lims.order.corrected`

**Result Lifecycle (6 events):**
`lims.result.created`, `lims.result.updated`, `lims.result.auto_validated`, `lims.result.validated`, `lims.result.flagged`, `lims.result.critical`, `lims.result.delta_check_failed`

**QC Events:**
`lims.qc.iqc_run` (with Westgard rule violations, z-scores)

**National Identity Events:**
`identity.citizen.registered`, `identity.citizen.merged`, `identity.citizen.linked`

**Audit Events:**
`audit.access_granted`, `audit.access_revoked`, `audit.break_glass_activated`

### Event Schema Structure

```json
{
  "aggregate_id": 123,
  "lab_id": 7,
  "user_id": 42,
  "payload": {
    "barcode": "SMP-A1B2C3D4",
    "specimen_type": "serum",
    "test_code": "GLU",
    "value": 95.3,
    "unit": "mg/dL"
  }
}
```

### Webhook Registration

Webhook endpoints are configured per-lab. Contact platform support to register a webhook receiver.

Webhook payload:
```http
POST /your-webhook-endpoint HTTP/1.1
Content-Type: application/json
X-GULA-Event: lims.result.critical
X-GULA-Delivery: uuid-v4
X-GULA-Signature: sha256=...

{
  "event_id": "lims.result.critical",
  "aggregate_id": 456,
  "lab_id": 7,
  "timestamp": "2026-07-14T14:30:00Z",
  "payload": {
    "result_id": 456,
    "test_code": "GLU",
    "value": 485,
    "unit": "mg/dL",
    "is_panic": true,
    "notification_window": "15 minutes"
  }
}
```

---

## 9. SDK Usage

### Python SDK

**Installation:**
```bash
pip install gula-platform-sdk
```

**Usage:**
```python
from gula import GulaClient, Role, OrderStatus
from gula.exceptions import AuthenticationError, RateLimitError

client = GulaClient(
    base_url="https://api.gula-platform.org",
    api_key="your-jwt-token"
)

# List patients
patients = client.patients.list(limit=20)
for patient in patients.data:
    print(patient.full_name, patient.phone)

# Create order
order = client.orders.create(
    patient_id=42,
    results=[
        {"test_name": "Glucose", "value": 95.3, "unit": "mg/dL"}
    ]
)
print(order.id, order.status)

# Batch create
batch = client.orders.create_batch(
    orders=[
        {"patient_id": 42, "results": [...]},
        {"patient_id": 43, "results": [...]},
    ]
)

# Search patients
results = client.patients.search(q="محمد")

# Handle errors
try:
    result = client.results.get(result_id=999)
except NotFoundError:
    print("Result not found")
except RateLimitError:
    print("Slow down!")
```

**Available Clients:**

| Attribute | API Domain |
|---|---|
| `client.auth` | Login, refresh, logout |
| `client.labs` | Lab profile, employees |
| `client.patients` | Patient CRUD, search, merge |
| `client.orders` | Orders CRUD, batch |
| `client.results` | Results CRUD, validate |
| `client.test_results` | Citizen-centric results |
| `client.samples` | Sample lifecycle |
| `client.quality_control` | QC operations |
| `client.ai` | Clinical analysis, chat |
| `client.consent` | Consent grant/revoke/check |
| `client.claims` | Insurance claims |
| `client.edge` | Edge device management |
| `client.admin` | Platform admin operations |
| `client.stats` | Dashboard statistics |
| `client.health` | Health checks |

### TypeScript SDK

**Installation:**
```bash
npm install @gula-platform/sdk
# or
yarn add @gula-platform/sdk
```

**Usage:**
```typescript
import { GulaClient, Role } from '@gula-platform/sdk';

const client = new GulaClient({
  baseUrl: 'https://api.gula-platform.org',
  apiKey: 'your-jwt-token',
});

// List patients
const patients = await client.patients.list({ limit: 20 });

// Create order
const order = await client.orders.create({
  patientId: 42,
  results: [{ testName: 'Glucose', value: 95.3, unit: 'mg/dL' }],
});

// Search
const results = await client.patients.search({ q: 'محمد' });

// Error handling
try {
  await client.results.get(999);
} catch (error) {
  if (error instanceof NotFoundError) {
    console.log('Not found');
  }
}
```

### CLI

```bash
gula patients list --limit 20
gula patients get 42
gula orders create --patient-id 42 --results '[{"test_name":"Glucose","value":95.3,"unit":"mg/dL"}]'
gula search محمد
```

---

## 10. Offline Sync Pattern

Edge devices and mobile apps support offline operation with eventual consistency.

### Synchronization Flow

```
Offline writes → Local SQLite/IndexedDB → Network available → Sync API → Server
                                                          ↓
                                                  Conflict resolution
                                                          ↓
                                                  Server response → Local merge
```

### Sync Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/sync/push` | Push local changes to server |
| POST | `/sync/pull` | Pull server changes since last sync |
| GET | `/sync/status` | Get sync status and pending count |

### Conflict Resolution

Conflict resolution follows **last-write-wins** with the server as authoritative. The SDK's `ConflictResolver` handles:
- **Create conflicts:** Server insert wins; client receives server-generated ID
- **Update conflicts:** Server version wins; client receives the merged state
- **Delete conflicts:** Server delete wins; client receives tombstone marker

### Sync SDK Usage

```python
from gula.sync import SyncQueue, SyncEngine, ConflictResolver

engine = SyncEngine(
    client=gula_client,
    local_db="path/to/local.db",
    conflict_resolver=ConflictResolver()
)

# Enable offline mode
engine.start_background_sync(interval_seconds=30)

# Queue operations offline
engine.queue_create("patients", {"full_name": "محمد"})
engine.queue_update("orders", 42, {"status": "completed"})

# All changes sync when network available
```

---

## 11. Rate Limits

| Limit Type | Default | Clinical Write Exemption |
|---|---|---|
| Requests per second (burst) | 100/s | Exempt (`/results`, `/orders`, `/samples`, `/critical-alerts`) |
| Requests per minute (sustained) | 3000/min | Exempt |
| Concurrent requests per worker | 200 | Exempt for clinical paths |
| Max request body size | 10 MB | N/A |
| Batch order max | 50 orders | N/A |
| Idempotency key TTL | 24 hours | N/A |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1700000100
Retry-After: 12
```

### Rate Limit Error

```json
{
  "detail": "Rate limit exceeded. Retry after 12 seconds.",
  "detail_ar": "تم تجاوز حد الطلبات. يرجى المحاولة بعد 12 ثانية.",
  "code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 12
}
```

---

## 12. Error Catalog

| Code | HTTP | Meaning | Action |
|---|---|---|---|
| `AUTH_INVALID_CREDENTIALS` | 401 | Email or password incorrect | Retry with correct credentials |
| `AUTH_TOKEN_EXPIRED` | 401 | JWT access token expired | Refresh token |
| `AUTH_TOKEN_INVALID` | 401 | JWT malformed or invalid signature | Obtain new token |
| `AUTH_TOKEN_BLACKLISTED` | 401 | Token has been revoked | Obtain new token |
| `AUTH_INSUFFICIENT_PERMISSIONS` | 403 | Role lacks required permission | Contact admin |
| `AUTH_CROSS_LAB_ACCESS_DENIED` | 403 | Attempted cross-lab resource access | Verify lab_id |
| `AUTH_DOCS_ACCESS_DENIED` | 403 | Non-admin trying to access API docs | Login as admin |
| `NOT_FOUND` | 404 | Resource not found | Check resource ID |
| `PATIENT_NOT_FOUND` | 404 | Patient does not exist | Create patient first |
| `ORDER_NOT_FOUND` | 404 | Order does not exist | Check order ID |
| `VALIDATION_ERROR` | 422 | Request body validation failed | Check field constraints |
| `FIELD_REQUIRED` | 422 | Missing required field | Include the field |
| `INVALID_EMAIL` | 422 | Email format invalid | Use valid email |
| `INVALID_PHONE` | 422 | Phone format invalid | Use Iraqi format (07xx or 9647xx) |
| `INVALID_NATIONAL_ID` | 422 | National ID format invalid | Must be 12-13 digits |
| `INVALID_DATE_FORMAT` | 422 | Date format incorrect | Use YYYY-MM-DD |
| `WEAK_PASSWORD` | 422 | Password does not meet strength requirements | Min 8 chars |
| `CONFLICT` | 409 | Resource already exists | Check for duplicates |
| `EMAIL_ALREADY_REGISTERED` | 409 | Email already in use | Use different email or login |
| `DUPLICATE_PATIENT` | 409 | Patient with matching attributes exists | Use force_create or merge |
| `IDEMPOTENCY_CONFLICT` | 409 | Same key, different request body | Use new idempotency key |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Retry after `Retry-After` header |
| `PAYLOAD_TOO_LARGE` | 413 | Request body exceeds 10 MB limit | Reduce payload size |
| `SERVICE_UNAVAILABLE` | 503 | System not ready (startup) | Retry in a moment |
| `DEGRADED_MODE` | 503 | Database circuit breaker open (read-only) | Retry later |
| `SERVER_ERROR` | 500 | Unexpected server error | Retry with exponential backoff |
| `DB_CONNECTION_ERROR` | 500 | Database unreachable | Check DB health |
| `INTEGRATION_ERROR` | 500 | External integration failed | Check instrument config |
| `HL7_PARSE_ERROR` | 422 | HL7 message malformed | Check message format |
| `ASTM_PARSE_ERROR` | 422 | ASTM message malformed | Check frame format |
| `ASTM_CHECKSUM_ERROR` | 422 | ASTM checksum mismatch | Check frame integrity |
| `CONSENT_EXPIRED` | 403 | Patient consent has expired | Request new consent |
| `CONSENT_NOT_GRANTED` | 403 | No active consent for this scope | Grant consent first |
| `BREAK_GLASS_REQUIRED` | 403 | Emergency access protocol must be initiated | Use break-glass endpoint |
| `INSTRUMENT_OFFLINE` | 503 | Instrument not reachable | Check connection |
| `EDGE_DEVICE_REVOKED` | 403 | Edge device has been revoked | Re-register device |
| `MPI_MERGE_CONFLICT` | 409 | Patient merge operation conflicts | Review merge proposal |
| `FEATURE_NOT_ENABLED` | 403 | Feature flag disabled for tenant | Check subscription |

---

## 13. v1.x → v2.x Migration

### Summary

v2.x is a **backward-compatible** superset of v1.x. No breaking changes have been introduced. All v1.x endpoints remain functional.

### What Changed

| Category | v1.x | v2.x |
|---|---|---|
| Runtime | Python 3.9 | Python 3.10+ |
| Auth | Simple JWT | JWT + Redis blacklist + perm_version |
| Pagination | Offset-based only | Cursor-based (offset deprecated) |
| Events | None | Full transactional outbox (85+ events) |
| FHIR | Not supported | FHIR R4 (10 resource types) |
| HL7 | Basic parsing | Full ORU^R01 + vendor profiles |
| ASTM | Basic parsing | Full E1394 + device bridge pipeline |
| Edge | Not supported | Full edge device platform |
| SDK | None | Python + TypeScript SDKs |
| AI | None | Clinical AI (analyze, suggest, chat) |
| Consent | None | Full consent management |
| Financial | None | Phase A schema + claims |
| National ID | None | SNDHS-lite integration |

### Migration Checklist

1. **Update SDK:** Migrate from any custom HTTP client to the official SDK
2. **Cursor pagination:** Replace `?page=N` with cursor-based pagination (offset-based still works)
3. **Idempotency:** Add `Idempotency-Key` header to mutation requests
4. **X-Request-ID:** Add request tracing header for debuggability
5. **Event consumers:** Subscribe to outbox events instead of polling for changes
6. **Error handling:** Update error parsers for the bilingual `detail_ar` field

### Deprecated Endpoints

| v1.x Endpoint | v2.x Replacement | Sunset |
|---|---|---|
| `GET /api/patients` | `GET /patients` | v3.0 |
| `POST /api/orders` | `POST /orders` | v3.0 |
| `GET /api/results` | `GET /results` | v3.0 |
| `GET /results?page=N` | `GET /results?cursor=...` | v2.5 |

---

## 14. Security Model

### Authentication

- **JWT HS256** with 60-minute access tokens and 30-day refresh tokens
- **Redis-backed token blacklist** for immediate revocation on logout
- **Dummy hash verification** prevents user enumeration (timing-safe login)
- **`perm_version` claim** invalidates all tokens for a user when their permissions change

### Authorization (RBAC + ABAC)

**9 roles × 13 permissions:**

| Role | Level | Key Permissions |
|---|---|---|
| `master_admin` | 100 | Full system access, kill-switch |
| `ministry_admin` | 90 | Cross-lab read, national reporting |
| `province_admin` | 80 | Province-scoped management |
| `lab_admin` | 70 | Lab configuration, employee mgmt |
| `doctor` | 50 | View patient data, order tests |
| `technician` | 40 | Enter results, run QC |
| `pathologist` | 45 | Validate results, sign off |
| `receptionist` | 30 | Register patients, collect samples |
| `citizen` | 10 | View own results, manage consent |

**ABAC** extends RBAC with attribute-based rules (conditions, priority, deny-overrides).

### Tenant Isolation

- Every patient-data query **must** filter by `lab_id = current_user.lab_id`
- Platform roles (`master_admin`, `ministry_admin`, `province_admin`) can cross lab boundaries
- `require_own_lab()` helper enforces tenant isolation in all endpoints

### Data Encryption

| Data | Encryption |
|---|---|
| Passwords | bcrypt (via passlib) |
| National ID (Iraqi) | HMAC-SHA256 hash, only first 16 chars exposed |
| JWT tokens | HS256 |
| Transport | TLS (nginx termination) |
| At rest | PostgreSQL TDE (filesystem-level) |

### Consent

- Citizens grant/revoke time-bounded consent for specific scopes
- Scopes: `view:results`, `view:profile`, `view:history`
- Maximum duration configurable per deployment
- All consent operations logged to audit trail

### Break-Glass Emergency Access

Healthcare providers can escalate in emergencies:

```
POST /security/break-glass
{
  "patient_id": 42,
  "reason": "Emergency — patient unresponsive",
  "duration_minutes": 60
}
```

- Requires documented emergency reason
- Creates audit log entry
- Notifies lab admin
- Automatically expires after configured duration

### Audit Log

Every mutation is logged to the `audit_log` table:

| Field | Description |
|---|---|
| actor_id | User who performed the action |
| action | CREATE/READ/UPDATE/DELETE/VERIFY/etc. |
| resource_type | e.g., `patient`, `order`, `result` |
| resource_id | ID of affected resource |
| details | JSON payload with before/after state |
| ip_address | Client IP |
| user_agent | Client user-agent |
| lab_id | Tenant isolation |
| timestamp | ISO 8601 |

### Security Headers (Applied to Every Response)

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Cross-Origin-Opener-Policy: same-origin
Content-Security-Policy: default-src 'self'; ...
Strict-Transport-Security: max-age=31536000; includeSubDomains (production only)
```

### API Documentation Protection

In production, `/docs`, `/redoc`, and `/openapi.json` require a valid admin JWT token.

---

## Contract Tag

This integration contract is frozen under tag `integration-contracts-v1.0`.
Any changes require version bump and stakeholder notification.
