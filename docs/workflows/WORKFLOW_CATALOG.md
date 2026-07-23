# GULA Platform — Lab Domain Workflow Catalog

**Version:** 1.0 | **Last Updated:** 2026-07-23

This catalog documents the **lab-domain workflows** implemented in the GULA platform
monolith (`backend/app/`). These are distinct from the national healthcare workflows
documented in `docs/national/WORKFLOW_CATALOG.md` — this catalog covers the actual
day-to-day laboratory operations: order processing, sample tracking, QC, result
verification, critical alerts, device integration, and patient card generation.

**Workflow Constitution:** `docs/constitution/18_WORKFLOW_CONSTITUTION.md`
**Order State Machine:** `backend/app/domain/order_state.py`

---

## Table of Contents

- [1. Lab Order Processing Workflow](#1-lab-order-processing-workflow)
- [2. Patient Registration Workflow](#2-patient-registration-workflow)
- [3. Sample Tracking Workflow](#3-sample-tracking-workflow)
- [4. Result Entry & Validation Workflow](#4-result-entry--validation-workflow)
- [5. Quality Control Workflow](#5-quality-control-workflow)
- [6. Critical Value Alert Workflow](#6-critical-value-alert-workflow)
- [7. Patient Card Generation Workflow](#7-patient-card-generation-workflow)
- [8. Device Bridge Integration Workflow](#8-device-bridge-integration-workflow)
- [9. Clinical Interpretation Workflow](#9-clinical-interpretation-workflow)
- [10. Authentication & Authorization Workflow](#10-authentication--authorization-workflow)
- [11. Public Result Access Workflow](#11-public-result-access-workflow)
- [12. Related Documents](#12-related-documents)

---

## 1. Lab Order Processing Workflow

**Domain:** LIMS | **Route:** `routes/results.py` | **Service:** `services/order_service.py`
**State Machine:** `domain/order_state.py` — single source of truth

The primary workflow — from order creation through sample tracking to verified result.
This is the core value stream of the platform.

### Actors

| Actor | Role | Entry Point |
|-------|------|-------------|
| Clinician | Orders lab tests | `POST /orders` (routes) |
| Lab Technician | Collects samples, runs tests | `POST /samples`, device bridge |
| Lab Director / Doctor | Validates final results | `POST /orders/{id}/validate` |

### Preconditions

- Patient is registered in the system
- Test types exist (test profiles available via `GET /test-profiles`)
- Lab is active
- Current user has appropriate role (staff/technician/admin/master_admin/doctor)

### Order State Machine

The canonical state machine is defined in `order_state.py` with four states:

```
                 ┌──────────┐
                 │  PENDING  │
                 └────┬─────┘
                      │
            ┌─────────┴─────────┐
            │                   │
            ▼                   ▼
      ┌──────────┐       ┌───────────┐
      │ COMPLETED │       │ CANCELLED │  (terminal)
      └─────┬─────┘       └───────────┘
            │
            ▼
      ┌───────────┐
      │ VALIDATED  │  (terminal — locked, immutable)
      └───────────┘
```

| State | Meaning | Mutability |
|-------|---------|------------|
| `pending` | Order created, awaiting results | Results can be added/edited |
| `completed` | All results recorded | No new results; can still cancel |
| `validated` | Locked by lab director | Completely immutable |
| `cancelled` | Order voided (terminal) | No mutations allowed |

### Physical Workflow Steps

The state machine maps to a physical lab workflow:

```
ORDER_REQUESTED → SAMPLE_COLLECTED → SAMPLE_RECEIVED → TEST_IN_PROGRESS →
RESULT_RECORDED → RESULT_VERIFIED
                        │                 │
                        ▼                 ▼
                   CANCELLED (any     ENTERED_IN_ERROR
                   state before        (result correction
                   validation)         before validation)
```

| Step | Physical State | System Action | Data Created |
|------|---------------|---------------|--------------|
| 1. ORDER_REQUESTED | Clinician places order | `POST /orders` with test list | `LabOrder` (status=pending) |
| 2. SAMPLE_COLLECTED | Phlebotomist collects specimen | `POST /samples` | `Sample` (status=collected), barcode |
| 3. SAMPLE_RECEIVED | Lab receives and logs sample | `PATCH /samples/{id}` | Sample (status=received) |
| 4. TEST_IN_PROGRESS | Analysis on instrument | Device bridge or manual entry | Sample (status=processing) |
| 5. RESULT_RECORDED | Results entered into system | `POST /orders` with results or device bridge | `LabResult` entries; order → completed |
| 6. RESULT_VERIFIED | Lab director approves | `POST /orders/{id}/validate` | Order status=validated, locked_at set |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `order.created` | Order placed | order_id, patient_id, lab_id, tests |
| `sample.collected` | Sample registered | sample_id, order_id, barcode, sample_type |
| `sample.received` | Sample logged at lab | sample_id, order_id, status |
| `result.recorded` | Results entered | order_id, test_name, value, flag |
| `result.verified` | Order validated | order_id, validated_by, validated_at |
| `order.cancelled` | Order voided | order_id, reason |

### Exceptions

- **CANCELLED** — order can be cancelled at any state before validation (pending → cancelled, completed → cancelled)
- **ENTERED_IN_ERROR** — result correction handled before validation by editing/removing individual `LabResult` records
- **Race condition guard** — atomic `UPDATE WHERE locked_at IS NULL` prevents double-validation

### Enforcement

```python
# order_state.py — guards applied in routes/results.py, routes/samples.py, routes/device_results.py
enforce_transition(order.status, "completed")   # before adding results
enforce_transition(order.status, "validated")   # before locking
assert_not_locked(order)                        # before any mutation
assert_not_cancelled(order)                     # before any mutation
```

---

## 2. Patient Registration Workflow

**Domain:** MPI (Master Patient Index) | **Route:** `routes/patients.py`
**Service:** `services/patient_service.py` | **Models:** `models/patient.py`

### Actors

| Actor | Entry Point |
|-------|------------|
| Front desk staff | `POST /patients` |
| Clinician | `POST /patients` (during order creation) |
| Citizen self-service | Citizen portal (via `routes/citizen_portal.py`) |

### States

Patients are not state-machine driven. The lifecycle is:

```
DRAFT (pre-registration) → ACTIVE → MERGED (into another record)
                                                  ↓
                                           INACTIVE (soft-deleted)
```

### Steps

| Step | Action | Detail |
|------|--------|--------|
| 1. IDENTITY_VERIFICATION | Collect full_name, phone, birth_date, gender | Phone validated as Iraqi number (07xxxxxxxxx or 9647xxxxxxxxx) |
| 2. DUPLICATE_CHECK | MPI matches against existing records | Probabilistic matching (Fellegi-Sunter) via `services/mpi/` |
| 3. DOCUMENT_COLLECTION | Optional: national_id, family_id | national_id hashed before storage |
| 4. RECORD_CREATION | Insert patient record | `Patient` created with lab_id tenant isolation |
| 5. NOTIFICATION | Patient notified | Confirmation via SMS/portal |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `patient.registered` | New patient created | patient_id, lab_id, full_name, phone |
| `patient.updated` | Patient edited | patient_id, changed_fields |
| `patient.merged` | Duplicate records merged | survivor_id, merged_id, confidence_score |

### Exceptions

- **Duplicate detection** — `force_create` flag bypasses MPI check; otherwise 409 on probable match
- **SNDHS integration** — when `SNDHS_ENABLE_NATIONAL_ID` is enabled, additional fields (`national_id`, `sndhs_health_id`) are populated and encrypted at rest

---

## 3. Sample Tracking Workflow

**Domain:** LIMS | **Route:** `routes/samples.py` | **Model:** `models/sample.py`

### Actors

| Actor | Action |
|-------|--------|
| Phlebotomist | Collects sample, registers in system |
| Lab Technician | Receives sample, processes it |
| Lab Director | Reviews rejected samples |

### Sample Status Lifecycle

```
COLLECTED → RECEIVED → PROCESSING → ANALYZED
    │          │                        │
    │          │                        │
    └──────────┴────────→ REJECTED (terminal at any point)
```

| Status | Meaning | Data |
|--------|---------|------|
| `collected` | Sample taken from patient, initial state | barcode, collection_time, collected_by |
| `received` | Sample logged at lab receiving area | — |
| `processing` | Analysis in progress on instrument | — |
| `analyzed` | Results produced and linked to order | Links to `LabResult` entries |
| `rejected` | Sample compromised (hemolyzed, clotted, insufficient, etc.) | rejection_reason recorded |

### Steps

| Step | Action | API | Data |
|------|--------|-----|------|
| 1. COLLECT | Phlebotomist collects specimen | `POST /samples` | barcode (auto-generated: `SMP-{12-hex}`), sample_type, collected_by |
| 2. LABEL | Barcode label affixed to container | Auto | Unique barcode on `Sample` |
| 3. TRANSPORT | Sample transported to lab | — | — |
| 4. RECEIVE | Lab logs receipt | `PATCH /samples/{id}` → status=received | — |
| 5. PROCESS | Instrument or technician runs test | `PATCH /samples/{id}` → status=processing | — |
| 6. ANALYZE | Results generated | Device bridge or `POST /orders/{id}/analyze` | status=analyzed |
| 7. STORE | Sample stored for retention | storage_location field | — |
| 8. DISPOSE | Sample discarded per policy | — | — |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `sample.collected` | Sample created | sample_id, order_id, barcode, sample_type |
| `sample.received` | Status → received | sample_id, order_id |
| `sample.compromised` | Status → rejected | sample_id, rejection_reason |

### Enforcement

- Sample creation is blocked on validated (locked) orders via `assert_not_locked()`
- Results cannot be added to a rejected sample (`device_results.py:68`)

### Sample Types

`blood`, `urine`, `stool`, `swab`, `serum`, `plasma`, `csf`, `spum`, `other`

---

## 4. Result Entry & Validation Workflow

**Domain:** LIMS | **Route:** `routes/results.py` | **Services:** `services/order_service.py`, `services/clinical_intelligence.py`

### Actors

| Actor | Permission | Action |
|-------|-----------|--------|
| Lab Technician | `staff` / `technician` | Enter and edit results |
| Lab Director / Doctor | `admin` / `master_admin` / `doctor` | Validate and lock results |

### States

```
PENDING → COMPLETED → VALIDATED
              │
              ▼
          CANCELLED
```

### Steps

| Step | Actor | Action | API |
|------|-------|--------|-----|
| 1. RESULTS_PENDING | System | Order created with no results | `POST /orders` → status=pending |
| 2. RESULTS_ENTERED | Technician | Manual or device entry of results | Device bridge or `POST /orders` with results |
| 3. CLINICAL_REVIEW | System (auto) | Clinical intelligence analysis | `POST /orders/{id}/intelligence` — pattern detection |
| 4. VERIFY | Lab Director | Review and validate results | `POST /orders/{id}/validate` → status=validated, locked_at set |
| 5. NOTIFY | System | Notify ordering clinician | Notification sent |

### Validation Guards

```python
# Only admin/master_admin/doctor may validate
# Atomic UPDATE prevents double-validation:
UPDATE lab_orders
SET status = 'validated', validated_by = :uid, validated_at = NOW(),
    locked_at = NOW(), version = version + 1
WHERE id = :oid AND lab_id = :lid AND locked_at IS NULL AND status = 'completed'
```

### Clinical Intelligence

At verification time, the system optionally runs multi-test pattern detection:

| Pattern | Severity | Tests Considered |
|---------|----------|-----------------|
| Sepsis | critical | WBC, neutrophils, CRP, procalcitonin, lactate |
| DKA | critical | Glucose, pH, bicarbonate, ketones |
| Renal failure | high | Creatinine, BUN, potassium, eGFR |
| Hepatic failure | high | ALT, AST, bilirubin, INR, albumin |
| Anemia | moderate | Hemoglobin, MCV, ferritin, iron |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `result.recorded` | Results entered | order_id, test_name, value, flag |
| `result.verified` | Order validated | order_id, validated_by, validated_at |
| `result.rejected` | Result flagged as error | order_id, test_name, reason |
| `result.amended` | Result corrected before validation | order_id, test_name, old_value, new_value |

---

## 5. Quality Control Workflow

**Domain:** Lab Operations | **Route:** `routes/quality_control.py`
**Model:** `models/quality_control.py`

### Actors

| Actor | Action |
|-------|--------|
| Lab Technician | Runs QC samples, records results |
| Lab Director | Reviews QC failures, authorizes corrective action |

### Preconditions

- Instrument is configured and active
- QC materials (control sera) are available with assigned lot numbers
- Expected values and SD are established per test/level/instrument

### Steps

| Step | Action | Detail |
|------|--------|--------|
| 1. QC_SCHEDULED | QC scheduled per frequency | Daily, per instrument, per test, per level (low/normal/high) |
| 2. QC_SAMPLE_RUN | Control material analyzed | Instrument runs control alongside patient samples |
| 3. RESULT_RECORDED | QC result submitted | `POST /qc/submit` with test_code, level, expected_value, measured_value, sd |
| 4. WESTGARD_EVALUATION | Multi-rule analysis | `evaluate_westgard_full()` applies rules: 1-3s, 1-2s, 2-2s, R-4s, 4-1s, 10-x |
| 5. RESULT_LOGGED | QC result persisted | `QualityControl` record with status (pass/warning/fail) and violation type |
| 6. CORRECTIVE_ACTION | If failed — troubleshoot | Instrument maintenance, recalibration, repeat QC |

### Westgard Multi-Rule Evaluation

```python
# From routes/quality_control.py evaluate_westgard_full()
# Uses historical QC data from last 48 hours for same test/level/instrument/lot
```

| Rule | Criteria | Result |
|------|----------|--------|
| 1-3s | One measurement >3σ | FAIL |
| 1-2s | One measurement >2σ | WARNING |
| 2-2s | Two consecutive >2σ (same side) | FAIL |
| R-4s | Two consecutive differ by >4σ | FAIL |
| 4-1s | Four consecutive >1σ (same side) | FAIL |
| 10-x | Ten consecutive same side of mean | FAIL |

### Batch Submission

Technicians can submit multiple QC results at once via `POST /qc/batch-submit`.

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `qc.result.recorded` | QC result saved | id, test_code, level, measured_value, status |
| `qc.rule.failure` | Westgard rule violated | id, violation, instrument_name, lot_number |
| `qc.corrective.action` | Corrective action taken | qc_id, action_description, resolved_by |

---

## 6. Critical Value Alert Workflow

**Domain:** Patient Safety | **Route:** `routes/critical_alerts.py`
**Service:** `services/critical_alerts.py`

### Actors

| Actor | Action |
|-------|--------|
| System (auto) | Detects critical values via `CRITICAL_THRESHOLDS` |
| Lab Technician | Verifies result, calls clinician |
| Clinician | Receives notification, provides readback |

### Critical Thresholds

35+ tests monitored across chemistry, haematology, coagulation, cardiac, endocrine,
liver, inflammation, pancreas, iron studies, and metabolic panels. Defined in
`services/critical_alerts.py:CRITICAL_THRESHOLDS`.

Examples:

| Test | Critical Low | Critical High | Unit |
|------|-------------|--------------|------|
| Glucose | 40 | 500 | mg/dL |
| Potassium | 2.5 | 6.5 | mEq/L |
| Hemoglobin | 5.0 | 20.0 | g/dL |
| Platelets | 20 | 1000 | ×10³/µL |
| INR | — | 4.0 | — |
| Troponin | — | 0.4 | ng/mL |

### Steps

| Step | Actor | Action |
|------|-------|--------|
| 1. RESULT_RECORDED | Technician / Device | Result value entered that exceeds critical threshold |
| 2. ALERT_GENERATED | System | `check_critical()` returns alert with severity (critical_low/critical_high), Arabic + English messages |
| 3. LAB_CONFIRMS | Lab Technician | Verify result is not a lab error (re-run if needed) |
| 4. CLINICIAN_NOTIFIED | Lab Technician | Call ordering clinician with critical value |
| 5. READBACK_CONFIRMED | Clinician | Read back the value verbatim to confirm receipt |
| 6. DOCUMENTED | System | Alert acknowledged in system |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `critical.alert.raised` | Result exceeds threshold | test_name, value, threshold, severity, order_id |
| `critical.alert.acknowledged` | Lab confirms result | alert_id, confirmed_by |
| `critical.alert.notified` | Clinician notified | alert_id, clinician_name, notification_channel |

---

## 7. Patient Card Generation Workflow

**Domain:** Patient Engagement | **Route:** `routes/patient_card.py`
**Service:** `services/patient_card.py`

### Security Invariants

- All reads filter by `current_user.lab_id` (tenant isolation)
- Scan tokens are HMAC-signed and bound to the issuing lab
- Every card view, scan, and history fetch is audit-logged
- Rate limited: 60 req/min for cards, 30 req/min for history

### Steps

| Step | Action | API | Detail |
|------|--------|-----|--------|
| 1. REQUEST_CARD | User requests patient card | `GET /patient-card/{patient_id}` | Returns card payload + signed QR token |
| 2. GENERATE_TOKEN | System issues HMAC-signed token | `issue_card_token()` | Token bound to patient_id + lab_id |
| 3. ENCODE_QR | Token encoded in QR image | `GET /patient-card/{patient_id}/qr.png` | PNG image, fresh token each request |
| 4. RENDER_HTML | Printable Arabic-first card | `GET /patient-card/{patient_id}/print` | HTML response with clinical history |
| 5. SCAN_CARD | Provider scans QR at visit | `POST /patient-card/scan` | Verifies HMAC signature → returns patient |
| 6. VIEW_HISTORY | Longitudinal history | `GET /patient-card/{patient_id}/history` | Full order/result history for patient |

### Card Token Format

```
HMAC-SHA256({
    "patient_id": 123,
    "lab_id": 5,
    "issued_at": "2026-07-23T10:00:00Z"
}, lab_signing_key)
```

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `patient.card.generated` | Card requested | patient_id, lab_id |
| `patient.card.scanned` | QR code scanned | patient_id, scanning_user_id |
| `patient.card.history.viewed` | History fetched | patient_id, user_id |

---

## 8. Device Bridge Integration Workflow

**Domain:** Lab Instrument Integration | **Repository:** `services/device_bridge/`
**Protocols:** ASTM (primary), HL7 (secondary)

The Device Bridge (LabLink-Core) is an independent service that connects lab
analyzers (Sysmex, Roche, Mindray, generic) to the GULA platform. It lives in
`services/device_bridge/` and communicates with the monolith via the API
at `POST /device/results`.

### Actors

| Actor | Role |
|-------|------|
| Lab Instrument | Sysmex, Roche, Mindray, or generic analyzer |
| Device Bridge | ASTM/HL7 parser, adapter, router |
| GULA Backend | Receives normalized results via `routes/device_results.py` |

### Steps

| Step | Actor | Action |
|------|-------|--------|
| 1. INSTRUMENT_SENDS | Lab Instrument | Transmits ASTM frame (STX + H/P/R/L records + ETX + checksum) over serial/TCP |
| 2. CONNECTOR_RECEIVES | Device Bridge | `SerialConnector` or `TCPConnector` receives raw bytes |
| 3. ASTM_PARSE | Device Bridge | `ASTMBuffer` handles STX/ETX framing, checksum validation, record parsing |
| 4. VENDOR_ADAPT | Device Bridge | `SysmexAdapter` / `RocheAdapter` / `MindrayAdapter` / `GenericAdapter` normalizes test names |
| 5. PATIENT_MATCH | Device Bridge | `PatientMatcher` resolves patient ID via barcode map or fallback |
| 6. TEST_MAPPING | Device Bridge | `TestMappingEngine` unifies aliases (e.g. Hb/HGB → HEMOGLOBIN) |
| 7. SMART_ROUTE | Device Bridge | `SmartRoutingEngine` decides: GULA, offline, or both |
| 8. FORWARD_TO_API | Device Bridge | `POST /device/results` with barcode + results payload |
| 9. BACKEND_PROCESS | GULA Backend | `receive_device_results()` — find sample by barcode, enforce order state, create LabResult entries, update sample status to analyzed |
| 10. ACKNOWLEDGE | GULA Backend | Return success → Device Bridge logs to audit |

### Device Bridge Endpoints (in bridge service)

| Endpoint | Purpose |
|----------|---------|
| `POST /ingest` | Receive raw instrument data |
| `POST /devices/register` | Register a new instrument |
| `POST /devices/onboarding/scan` | Discover and score new devices |
| `POST /edge/sync` | Sync offline-buffered results |

### GULA Backend Endpoint

| Endpoint | Purpose |
|----------|---------|
| `POST /device/results` | Receive normalized results from bridge |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `device.result.received` | Bridge receives ASTM frame | device_id, frame_size |
| `device.result.parsed` | Bridge parses frame | device_id, test_count, patient_id |
| `device.result.forwarded` | Bridge sends to GULA API | device_id, barcode, test_count, status |

---

## 9. Clinical Interpretation Workflow

**Domain:** Clinical Decision Support | **Service:** `services/interpretation.py`
**Route:** `routes/results.py` (via `/analyze` and `/orders/{id}/intelligence`)

### Actors

| Actor | Action |
|-------|--------|
| System (auto) | Generates interpretations for lab results |
| Clinician | Reviews interpretation flags |
| Patient | Views public result with interpretation |

### Interpretation Engine

The Smart Interpretation Engine (`services/interpretation.py`) provides bilingual
(Arabic/English) interpretations for 100+ lab tests. Each test has:

- **Thresholds** for low, normal, high, and critical_high ranges
- **Interpretation text** in English and Arabic
- **Clinical advice** in English and Arabic

```python
# Example interpretation structure
INTERPRETATIONS = {
    "glucose": {
        "unit": "mg/dL",
        "low": { "threshold": 70, "text": "...", "text_ar": "...", "advice": "...", "advice_ar": "..." },
        "normal": { "text": "...", "text_ar": "..." },
        "high": { "threshold": 100, "text": "...", "text_ar": "..." },
        "critical_high": { "threshold": 200, "text": "...", "text_ar": "..." },
    },
    ...
}
```

### Steps

| Step | Action | Detail |
|------|--------|--------|
| 1. RESULT_ENTERED | Result recorded for a test | `LabResult` created with value, unit, normal ranges |
| 2. FLAG_ASSIGNMENT | `get_flag()` computes H/L/normal/critical | Based on value vs. normal_range_low/high |
| 3. INTERPRETATION | Look up test in INTERPRETATIONS | Arabic + English text + advice |
| 4. PATTERN_DETECTION | Multi-test clinical pattern analysis | Sepsis, DKA, renal failure, hepatic failure, anemia detection |
| 5. PRESENTATION | Flags and interpretations returned to UI | `GET /orders/{id}/intelligence` |

### Clinical Pattern Detection

| Pattern | Tests | Severity |
|---------|-------|----------|
| Sepsis | WBC ↑, neutrophils ↑, CRP ↑, procalcitonin ↑, lactate ↑ | critical |
| DKA | Glucose ↑↑, pH ↓, bicarbonate ↓ | critical |
| Renal failure | Creatinine ↑, BUN ↑, potassium ↑, eGFR ↓ | high |
| Hepatic failure | ALT ↑, AST ↑, bilirubin ↑, INR ↑, albumin ↓ | high |
| Anemia | Hemoglobin ↓, MCV ↓, ferritin ↓ | moderate |

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `result.flag.assigned` | Flag computed | test_name, value, flag, normal_range |
| `pattern.detected` | Clinical pattern identified | order_id, pattern_name, severity, affected_tests |

---

## 10. Authentication & Authorization Workflow

**Domain:** Security | **Routes:** `routes/login.py`, `routes/authorization.py`, `routes/service_accounts.py`
**Services:** `security/auth.py`, `services/authorization_service.py`

While not unique to the lab domain, auth/z is foundational to every workflow.

### Actors

| Actor | Authentication | Authorization Model |
|-------|---------------|---------------------|
| Lab User (staff/technician/admin/doctor) | JWT (email + password) | RBAC (10 roles, 16 permissions) + ABAC |
| API Client / Service Account | API key or JWT | Scoped to specific resources |
| Public User | Token-based (result token) | Single-result access only |

### Authentication Flow

```
LOGIN → JWT_ISSUED → TOKEN_IN_REQUEST → CURRENT_USER_EXTRACTED
                       │
                    EXPIRED → 401 → LOGIN_AGAIN
```

### Authorization Checks (common across all workflows)

1. **JWT extraction** — `security/dependencies.py::get_current_user()`
2. **Lab tenant isolation** — all queries filter `WHERE lab_id = current_user.lab_id`
3. **Role-based access** — route-level checks using `current_user.role`
4. **Break-glass** — `routes/authorization.py` provides emergency access escalation

---

## 11. Public Result Access Workflow

**Domain:** Patient Engagement | **Route:** `routes/results.py`
**Endpoints:** `GET /r/{token}`, `GET /r/{token}/pdf`, `GET /history/{phone}`

### Steps

| Step | Action | API | Detail |
|------|--------|-----|--------|
| 1. PATIENT_RECEIVES_TOKEN | Token shared via SMS/print | Created at order creation, set on `LabResult.token` | SHA-256 hashed for storage |
| 2. VIEW_RESULT | Patient views result | `GET /r/{token}` | Rate limited: 30 req/min |
| 3. DOWNLOAD_PDF | Download professional PDF | `GET /r/{token}/pdf` | Includes QR code, rate limited: 10 req/min |
| 4. HISTORY_BY_PHONE | Patient's full history | `GET /history/{phone}?name=...` | Multi-lab aggregation, rate limited: 5 req/min |

### Security

- Tokens are SHA-256 hashed before storage (`token_hash` column)
- Tokens expire after 90 days (`expires_at` default)
- Token verification via `hash_token(token) == row.token_hash`
- Phone history requires name match as verification factor
- Phone lookups use exact match (never LIKE with user input)

### Result Token Lifecycle

```
ORDER_CREATED → TOKEN_GENERATED → TOKEN_HASHED → STORED
                                                      │
                                              ┌───────┴────────┐
                                              │                │
                                         TOKEN_USED        TOKEN_EXPIRED
                                         (view/PDF)     (after 90 days)
```

---

## 12. Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| National Workflow Catalog | `docs/national/WORKFLOW_CATALOG.md` | National healthcare workflows (admission, referral, medication, discharge, transfer) |
| Workflow Constitution | `docs/constitution/18_WORKFLOW_CONSTITUTION.md` | Design principles for all GULA workflows |
| Order State Machine | `backend/app/domain/order_state.py` | Canonical state transitions for lab orders |
| ADR-007 (Device Bridge) | `services/device_bridge/docs/` | Architecture Decision Record for lab instrument integration |
| Event Constitution | `docs/constitution/16_EVENT_CONSTITUTION.md` | Event schema and delivery guarantees |
| Patient Card System | `backend/app/routes/patient_card.py` | QR-backed digital patient card implementation |
| CLAUDE.md | Root-level | Repository overview and workflow descriptions |
