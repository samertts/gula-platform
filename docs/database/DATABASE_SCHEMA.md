# GULA Platform — Database Schema Reference

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Database Overview](#1-database-overview)
2. [Schema Diagram (ASCII)](#2-schema-diagram-ascii)
3. [Core Tables](#3-core-tables)
   - 3.1 [labs](#31-labs)
   - 3.2 [lab_users](#32-lab_users)
   - 3.3 [patients](#33-patients)
   - 3.4 [lab_orders](#34-lab_orders)
   - 3.5 [lab_results](#35-lab_results)
   - 3.6 [samples](#36-samples)
   - 3.7 [test_types](#37-test_types)
   - 3.8 [test_results](#38-test_results)
   - 3.9 [audit_logs](#39-audit_logs)
   - 3.10 [outbox_events](#310-outbox_events)
   - 3.11 [users](#311-users)
   - 3.12 [tenants](#312-tenants)
   - 3.13 [organizations / facilities](#313-organizations--facilities)
   - 3.14 [visits](#314-visits)
   - 3.15 [subscriptions](#315-subscriptions)
   - 3.16 [mfa_devices / mfa_sessions](#316-mfa_devices--mfa_sessions)
   - 3.17 [oauth2_clients / oauth2_tokens](#317-oauth2_clients--oauth2_tokens)
   - 3.18 [service_accounts](#318-service_accounts)
   - 3.19 [quality_controls](#319-quality_controls)
   - 3.20 [consents](#320-consents)
   - 3.21 [edge platform tables](#321-edge-platform-tables)
   - 3.22 [authorization tables](#322-authorization-tables)
   - 3.23 [canonical patient tables](#323-canonical-patient-tables)
   - 3.24 [AI interaction tables](#324-ai-interaction-tables)
   - 3.25 [claims tables](#325-claims-tables)
   - 3.26 [financial engine (Phase A)](#326-financial-engine-phase-a)
4. [Indexes](#4-indexes)
5. [Constraints and Foreign Keys](#5-constraints-and-foreign-keys)
6. [Partitioning](#6-partitioning)
7. [Retention Policy](#7-retention-policy)
8. [Connection Pool Configuration](#8-connection-pool-configuration)
9. [Migration Policy](#9-migration-policy)

---

## 1. Database Overview

- **RDBMS:** PostgreSQL 16 (production), SQLite (test/in-memory fallback)
- **ORM:** SQLAlchemy 2.0 (async-ready, `declarative_base()` pattern)
- **Connection Library:** `psycopg2` (via SQLAlchemy engine)
- **Migrations:** Alembic (48 migration files as of 2026-07-23)

The GULA Platform uses a single-database monolith pattern. All clinical, financial, identity, and audit data lives in one PostgreSQL database. A read-replica engine is optional (`READ_REPLICA_URL`) for distributing read-only queries.

**Key architectural invariants:**
- Multi-tenant isolation via `lab_id` on every clinical table — all queries MUST filter by `lab_id = current_user.lab_id`
- All mutations MUST write to the `audit_logs` table
- Optimistic locking (`version` column) on `lab_orders` and `lab_results`
- SHA-256 hash chain on `audit_logs` for tamper detection
- Context variables (`request_id`, `endpoint`, `user_id`, `lab_id`) correlate every DB error log

---

## 2. Schema Diagram (ASCII)

```
                          ┌───────────────────────────┐
                          │         tenants            │
                          │  (multi-tenant hierarchy)  │
                          └──────────┬────────────────┘
                                     │ 1
                                     │
                                     ▼
                          ┌───────────────────────────┐
                          │       organizations        │
                          │  (health directorates)     │
                          └──────────┬────────────────┘
                                     │ 1
                                     │
                                     ▼
                          ┌───────────────────────────┐
                          │        facilities          │
                          │  (hospitals, labs, PHCs)   │
                          └──────────┬────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│      labs        │     │      users        │     │  lab_subscriptions│
│ (lab orgs)       │     │ (platform users)  │     │ (tier per lab)    │
└───┬───┬───┬───┬──┘     └────────┬─────────┘     └──────────────────┘
    │   │   │   │                 │
    │   │   │   │                 │
    ▼   ▼   ▼   ▼                 │
┌──────────────┐                  │
│  lab_users   │                  │
│ (staff accts)│                  │
└──────┬───────┘                  │
       │                          │
       ▼                          ▼
┌─────────────────────────────────────────────────────┐
│                    patients                          │
│          (patient records, lab-scoped)               │
└───┬──────────────────────────────┬──────────────────┘
    │ 1                            │ 1
    │                              │
    ▼                              ▼
┌──────────────────┐     ┌──────────────────┐
│   lab_orders     │     │     visits       │
│ (test requests)  │     │ (SNDHS episodes) │
└───┬───────┬──────┘     └──────────────────┘
    │ 1     │ 0..1
    │       │
    ▼       ▼
┌──────────────────┐
│   lab_results    │──── test_types (FK→id)
│ (test values)    │
└──────────────────┘
    │
    ▼
┌──────────────────┐
│    samples       │
│ (specimens)      │
└──────────────────┘

┌─────────────────────────────────────────────┐
│            test_results                      │
│ (national LIMS — citize-scoped)             │
│ lab_id FK → labs.id                         │
│ citizen_id FK → citizens.id                 │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│         canonical_patients                   │
│  (MPI golden record via patient_links       │
│   and citizen_links)                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│            audit_logs                        │
│  (SHA-256 hash chain — tamper-evident)      │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│           outbox_events                      │
│  (transactional outbox pattern)             │
└─────────────────────────────────────────────┘
```

---

## 3. Core Tables

### 3.1 `labs`

Multi-tenant lab organizations — the top-level tenant boundary for all clinical data. Every patient, order, result, and sample belongs to exactly one lab.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `name` | `String(200)` | NOT NULL | — | Lab name |
| `license_number` | `String(100)` | YES | — | Unique license number |
| `lab_type` | `String(50)` | YES | — | `private`, `government`, `hospital`, `clinic` |
| `director_name` | `String(200)` | YES | — | Lab director / manager |
| `website` | `String(300)` | YES | — | Lab website |
| `city` | `String(100)` | YES | — | City location |
| `address` | `String(500)` | YES | — | Full address |
| `phone` | `String(20)` | YES | — | Contact phone |
| `is_active` | `Boolean` | YES | `true` | Active status flag |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `lab_type`, `is_active`

**Relationships:**
- `users` → `LabUser` (1:N, cascade delete)
- `patients` → `Patient` (1:N, cascade delete)
- `orders` → `LabOrder` (1:N, cascade delete)
- `subscription` → `LabSubscription` (1:1, cascade delete)
- `staff_users` → `User` (1:N)

---

### 3.2 `lab_users`

Lab staff accounts — the primary identity provider for lab-side operations. Each user belongs to exactly one lab.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `name` | `String(200)` | NOT NULL | — | Full name |
| `email` | `String(100)` | NOT NULL | — | Unique email (login) |
| `password_hash` | `String(255)` | NOT NULL | — | bcrypt/argon2 hash |
| `role` | `String(50)` | YES | `staff` | `staff`, `admin`, `doctor`, `technician`, `MASTER_ADMIN`, `PROVINCE_ADMIN` |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `perm_version` | `Integer` | NOT NULL | `1` | Bumped on role/permission change |
| `national_id_hash` | `String(255)` | YES | — | HMAC-SHA256 of national ID |
| `province_id` | `Integer` | YES | — | Province scope restriction |
| `created_by` | `Integer` FK | YES | — | → `lab_users.id` ON DELETE SET NULL |
| `reset_token` | `String(255)` | YES | — | Password reset token |
| `reset_token_expires` | `DateTime(tz)` | YES | — | Token expiry |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `lab_id`, `email` (unique), `role`, `is_active`, `national_id_hash` (unique), `province_id`, `reset_token`

---

### 3.3 `patients`

Patient records. Scoped by `lab_id` for multi-tenant isolation. Supports national ID (encrypted at rest, HMAC-hashed for lookup) and SNDHS phase 1 extensions.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `health_id` | `String(20)` | YES | — | Unique health ID |
| `national_id_hash` | `String(255)` | YES | — | HMAC-SHA256 of national ID |
| `family_id_hash` | `String(255)` | YES | — | HMAC-SHA256 of family registry number (prefix `fam:`) |
| `guardian_id` | `Integer` FK | YES | — | → `patients.id` ON DELETE SET NULL (for minors) |
| `full_name` | `String(200)` | NOT NULL | — | Full name |
| `phone` | `String(20)` | NOT NULL | — | Contact phone |
| `birth_date` | `Date` | YES | — | Date of birth |
| `gender` | `String(1)` | YES | — | `M` or `F` |
| `email` | `String(100)` | YES | — | Email address |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Table constraints:** `ix_patients_lab_id` (lab_id), `ix_patients_lab_phone` (lab_id, phone), `ix_patients_lab_nid` (lab_id, national_id_hash)

**Indexes:** `id` (PK), `health_id` (unique), `national_id_hash`, `family_id_hash`, `guardian_id`, `phone`, plus the composite indexes above.

**SNDHS Phase 1 columns (added via migration):** `national_id_hash`, `sndhs_health_id` — both nullable. The dual-read rule: code must handle `None` gracefully.

**Relationships:**
- `lab` → `Lab` (N:1)
- `orders` → `LabOrder` (1:N, cascade delete)
- `dependents` → `Patient` (1:N, self-referential via `guardian_id`)
- `guardian` → `Patient` (N:1, self-referential)

---

### 3.4 `lab_orders`

Lab test orders with state machine. Tracks the lifecycle of a diagnostic request.

**Status state machine:**
```
pending ──→ completed ──→ validated  (immutable after validated)
pending ──→ cancelled
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `patient_id` | `Integer` FK | NOT NULL | — | → `patients.id` ON DELETE CASCADE |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `doctor_name` | `String(200)` | YES | — | Ordering doctor name |
| `doctor_user_id` | `Integer` FK | YES | — | → `lab_users.id` ON DELETE SET NULL |
| `status` | `String(20)` | YES | `pending` | `pending`, `completed`, `validated`, `cancelled` |
| `validated_by` | `Integer` FK | YES | — | → `lab_users.id` ON DELETE SET NULL |
| `validated_at` | `DateTime(tz)` | YES | — | Validation timestamp |
| `locked_at` | `DateTime(tz)` | YES | — | Finalization timestamp (= validated_at when finalized) |
| `version` | `Integer` | NOT NULL | `1` | Optimistic lock — incremented on every mutation |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `patient_id`, `lab_id`, `doctor_user_id`, `status`, `validated_by`, `created_at`

**Relationships:**
- `patient` → `Patient` (N:1)
- `lab` → `Lab` (N:1)
- `results` → `LabResult` (1:N, cascade delete)
- `samples` → `Sample` (0..1:N, backref)

**Visit association (SNDHS Phase 1):** Column `visit_id` → `visits.id` added by migration `20260505_0004`.

---

### 3.5 `lab_results`

Individual test results within an order. Supports both numeric (`value`) and text (`value_text`) results. Includes optimistic locking and clinical engine version tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `order_id` | `Integer` FK | NOT NULL | — | → `lab_orders.id` ON DELETE CASCADE |
| `test_type_id` | `Integer` FK | YES | — | → `test_types.id` ON DELETE SET NULL |
| `test_name` | `String(200)` | NOT NULL | — | Name of test |
| `value` | `Float` | YES | — | Numeric result value |
| `value_text` | `String(200)` | YES | — | Non-numeric result text |
| `unit` | `String(20)` | YES | — | Measurement unit |
| `normal_range_low` | `Float` | YES | — | Lower reference range |
| `normal_range_high` | `Float` | YES | — | Upper reference range |
| `flag` | `String(10)` | YES | — | `H`, `L`, `normal`, `critical` |
| `token` | `String(64)` | NOT NULL | `generate_token()` | Secure access token (unique) |
| `token_hash` | `String(64)` | YES | — | SHA-256 of token for lookup |
| `expires_at` | `DateTime(tz)` | YES | `now() + 90d` | Token expiry |
| `clinical_engine_version` | `String(20)` | YES | — | Clinical engine version that last evaluated this result |
| `version` | `Integer` | NOT NULL | `1` | Optimistic lock — incremented on every mutation |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `order_id`, `flag`, `token` (unique), `token_hash` (unique), `expires_at`

**Relationships:**
- `order` → `LabOrder` (N:1)
- `test_type` → `TestType` (N:1)

---

### 3.6 `samples`

Physical specimens collected for lab testing. Linked to orders with barcode tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `order_id` | `Integer` FK | NOT NULL | — | → `lab_orders.id` ON DELETE CASCADE |
| `barcode` | `String(20)` | NOT NULL | `SMP-{hex}` | Unique barcode |
| `sample_type` | `String(50)` | NOT NULL | — | `blood`, `urine`, `stool`, `swab`, `serum`, `plasma` |
| `collection_time` | `DateTime(tz)` | YES | `now()` | Time collected |
| `collected_by` | `String(200)` | YES | — | Collector name |
| `status` | `String(30)` | YES | `collected` | `collected`, `received`, `processing`, `analyzed`, `rejected` |
| `rejection_reason` | `Text` | YES | — | Reason if rejected |
| `notes` | `Text` | YES | — | Additional notes |
| `storage_location` | `String(100)` | YES | — | Storage location |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `order_id`, `barcode` (unique), `status`

**Relationships:**
- `order` → `LabOrder` (N:1, backref `samples`)

---

### 3.7 `test_types`

Test catalog definitions. Stores reference ranges and clinical interpretations in both English and Arabic.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `test_code` | `String(50)` | NOT NULL | — | Unique test code |
| `test_name` | `String(200)` | NOT NULL | — | Test name (English) |
| `test_name_ar` | `String(200)` | YES | — | Test name (Arabic) |
| `category` | `String(50)` | YES | — | `CBC`, `Chemistry`, `Lipid`, etc. |
| `unit` | `String(20)` | YES | — | Default unit |
| `normal_range_low` | `Float` | YES | — | Default lower bound |
| `normal_range_high` | `Float` | YES | — | Default upper bound |
| `interpretation_low` | `String(500)` | YES | — | Low-value interpretation (EN) |
| `interpretation_normal` | `String(500)` | YES | — | Normal interpretation (EN) |
| `interpretation_high` | `String(500)` | YES | — | High-value interpretation (EN) |
| `interpretation_low_ar` | `String(500)` | YES | — | Low-value interpretation (AR) |
| `interpretation_normal_ar` | `String(500)` | YES | — | Normal interpretation (AR) |
| `interpretation_high_ar` | `String(500)` | YES | — | High-value interpretation (AR) |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `test_code` (unique)

---

### 3.8 `test_results`

National LIMS — citizen-scoped test results from the MPI integration layer. Uses `BigInteger` PK and references `citizens` table (from the national citizen registry / NHOP platform), not the per-lab `patients` table. This is the canonical result store for the cross-lab/national view.

**NOTE:** This model is NOT yet re-exported from `app/models/__init__.py`. The FK to `lab_devices` is currently a plain Integer column (the `lab_devices` table does not exist yet in the schema).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `BigInteger` PK | NOT NULL | auto-increment | Primary key |
| `citizen_id` | `BigInteger` FK | NOT NULL | — | → `citizens.id` ON DELETE RESTRICT |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `device_id` | `Integer` | YES | — | Instrument device ID (no FK yet) |
| `test_code` | `String(30)` | NOT NULL | — | LOINC-style test code |
| `test_name_en` | `String(200)` | NOT NULL | — | Test name (English) |
| `test_name_ar` | `String(200)` | NOT NULL | — | Test name (Arabic) |
| `category` | `String(50)` | YES | — | `hematology`, `chemistry`, `hormones`… |
| `result_value` | `Float` | YES | — | Numeric result |
| `result_text` | `String(200)` | YES | — | Text result (positive/negative) |
| `unit` | `String(20)` | YES | — | Unit |
| `reference_min` | `Float` | YES | — | Min reference range |
| `reference_max` | `Float` | YES | — | Max reference range |
| `status` | `String(20)` | NOT NULL | `pending` | `pending`, `completed`, `verified`, `rejected` |
| `is_critical` | `Boolean` | NOT NULL | `false` | Critical flag |
| `is_abnormal` | `Boolean` | NOT NULL | `false` | Abnormal flag |
| `abnormality_direction` | `String(10)` | YES | — | `high`, `low`, `normal` |
| `sample_collected_at` | `DateTime(tz)` | NOT NULL | — | Sample collection time |
| `result_completed_at` | `DateTime(tz)` | YES | — | Result completion time |
| `verified_at` | `DateTime(tz)` | YES | — | Verification time |
| `verified_by` | `String(200)` | YES | — | Verifier name |
| `sample_barcode` | `String(64)` | NOT NULL | — | Unique barcode |
| `ordering_physician` | `String(200)` | YES | — | Ordering doctor |
| `clinical_notes` | `Text` | YES | — | Clinical notes |
| `created_at` | `DateTime(tz)` | NOT NULL | `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | NOT NULL | `now()` | Last update timestamp |

**Indexes (table args):**
- `ix_test_results_citizen_lab` (`citizen_id`, `lab_id`)
- `ix_test_results_lab_status` (`lab_id`, `status`)
- `ix_test_results_lab_collected` (`lab_id`, `sample_collected_at`)
- `ix_test_results_test_code` (`test_code`)

---

### 3.9 `audit_logs`

Tamper-evident audit trail using SHA-256 hash chain. Every mutation to clinical data writes an entry.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `user_id` | `Integer` | YES | — | Actor user ID |
| `user_role` | `String(50)` | YES | — | Actor role |
| `action` | `String(50)` | NOT NULL | — | `view`, `create`, `update`, `delete` |
| `resource_type` | `String(50)` | NOT NULL | — | `patient`, `test`, `result`, `order` |
| `resource_id` | `Integer` | YES | — | ID of the resource acted upon |
| `details` | `Text` | YES | — | JSON or human-readable details |
| `ip_address` | `String(45)` | YES | — | Client IP address |
| `chain_hash` | `String(64)` | YES | — | SHA-256 hash of (prev_chain_hash + record data) |
| `created_at` | `DateTime(tz)` | YES | `now()` | Audit timestamp |

**Indexes:** `id` (PK), `user_id`, `action`, `chain_hash`, `created_at`

**Hash chain integrity:** Each entry's `chain_hash` = SHA-256 of (previous entry's `chain_hash` + current record data). Any modification to a past entry breaks the chain for all subsequent entries. NULL on legacy rows pre-dating the hash chain migration.

**SNDHS Phase 1 v2 audit:** Migration `20260505_0005` adds enhanced SNDHS correlation fields.

---

### 3.10 `outbox_events`

Transactional outbox pattern for guaranteed at-least-once event delivery. Events are written in the same DB transaction as the triggering business operation.

**Status lifecycle:**
```
pending → processing → done
              ↓
            failed  (retried up to 5 times)
```

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `event_type` | `String(100)` | NOT NULL | — | Event type identifier |
| `aggregate_type` | `String(100)` | YES | — | `order`, `result`, etc. |
| `aggregate_id` | `Integer` | YES | — | ID of associated aggregate |
| `payload` | `Text` | NOT NULL | — | JSON payload |
| `status` | `String(20)` | NOT NULL | `pending` | `pending`, `processing`, `done`, `failed` |
| `attempts` | `Integer` | NOT NULL | `0` | Delivery attempt count |
| `last_error` | `Text` | YES | — | Last error message |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `processed_at` | `DateTime(tz)` | YES | — | Processing timestamp |

**Indexes:** `id` (PK), `event_type`, `aggregate_id`, `created_at`

**Config:** `MAX_ATTEMPTS = 5` — after this, event stays in `failed` state and alerts operations.

---

### 3.11 `users`

Platform users — a broader user model for citizens, doctors, ministry personnel, and system accounts. Separate from `lab_users` which are lab-staff specific.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `email` | `String(100)` | YES | — | Unique email |
| `phone` | `String(20)` | YES | — | Unique phone |
| `password_hash` | `String(255)` | NOT NULL | — | Password hash |
| `full_name` | `String(200)` | NOT NULL | — | Full name |
| `role` | `String(50)` | NOT NULL | `citizen` | User role |
| `lab_id` | `Integer` FK | YES | — | → `labs.id` ON DELETE SET NULL |
| `user_type` | `String(50)` | YES | — | Extended type classification |
| `organization_id` | `Integer` FK | YES | — | → `organizations.id` ON DELETE SET NULL |
| `facility_id` | `Integer` FK | YES | — | → `facilities.id` ON DELETE SET NULL |
| `tenant_id` | `Integer` FK | YES | — | → `tenants.id` ON DELETE SET NULL |
| `governorate_id` | `String(50)` | YES | — | Governorate code |
| `directorate_id` | `String(50)` | YES | — | Directorate code |
| `department_id` | `String(100)` | YES | — | Department |
| `specialty` | `String(200)` | YES | — | Clinical specialty |
| `license_number` | `String(100)` | YES | — | Professional license |
| `national_id_hash` | `String(255)` | YES | — | HMAC-SHA256 of national ID |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `is_verified` | `Boolean` | YES | `false` | Email/phone verified |
| `mfa_enabled` | `Boolean` | YES | `false` | MFA enabled |
| `perm_version` | `Integer` | YES | `1` | Permission version |
| `preferences` | `JSON` | YES | — | User preferences |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `last_login` | `DateTime(tz)` | YES | — | Last login timestamp |

**Indexes:** `id` (PK), `email` (unique), `phone` (unique), `user_type`, `organization_id`, `tenant_id`, `governorate_id`, `directorate_id`, `national_id_hash`

---

### 3.12 `tenants`

Multi-tenant hierarchy. Supports a tree structure (national → governorate → facility) via `parent_tenant_id` self-reference.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `tenant_id` | `String(100)` | NOT NULL | — | Unique tenant identifier |
| `name_en` | `String(200)` | NOT NULL | — | English name |
| `name_ar` | `String(200)` | NOT NULL | — | Arabic name |
| `domain` | `String(200)` | YES | — | Domain (unique) |
| `tenant_type` | `String(50)` | NOT NULL | `governorate` | Tenant classification |
| `parent_tenant_id` | `Integer` | YES | — | → `tenants.id` (self-ref) |
| `phone` | `String(30)` | YES | — | Contact phone |
| `address` | `Text` | YES | — | Address |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `max_users` | `Integer` | YES | — | User limit |
| `feature_flags` | `JSON` | YES | — | Feature override flags |
| `settings` | `JSON` | YES | — | Tenant settings |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `tenant_id` (unique), `domain` (unique), `parent_tenant_id`

**Relationships:**
- `organizations` → `Organization` (1:N)

---

### 3.13 `organizations` / `facilities`

Organization and facility hierarchy under tenants. Maps to Iraqi health directorates and their facilities.

#### `organizations` (Health Directorates)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `org_id` | `String(100)` | NOT NULL | — | Unique org identifier |
| `name_en` | `String(200)` | NOT NULL | — | English name |
| `name_ar` | `String(200)` | NOT NULL | — | Arabic name |
| `org_type` | `String(50)` | NOT NULL | — | Organization type |
| `parent_org_id` | `String(100)` | YES | — | Parent org reference |
| `tenant_id` | `Integer` FK | YES | — | → `tenants.id` ON DELETE SET NULL |
| `governorate_id` | `String(50)` | YES | — | Governorate code |
| `directorate_id` | `String(50)` | YES | — | Directorate code |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `contact_email` | `String(200)` | YES | — | Contact email |
| `contact_phone` | `String(30)` | YES | — | Contact phone |
| `address` | `Text` | YES | — | Address |
| `extra_metadata` | `JSON` | YES | — | Additional metadata |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | YES | `now()` | Last update |

**Indexes:** `id` (PK), `org_id` (unique), `org_type`, `parent_org_id`, `tenant_id`, `governorate_id`, `directorate_id`

#### `facilities` (Hospitals, Labs, PHCs)

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `facility_id` | `String(100)` | NOT NULL | — | Unique facility identifier |
| `name_en` | `String(200)` | NOT NULL | — | English name |
| `name_ar` | `String(200)` | NOT NULL | — | Arabic name |
| `facility_type` | `String(50)` | NOT NULL | — | Facility type |
| `organization_id` | `Integer` FK | NOT NULL | — | → `organizations.id` ON DELETE CASCADE |
| `contact_email` | `String(200)` | YES | — | Contact email |
| `contact_phone` | `String(30)` | YES | — | Contact phone |
| `address` | `Text` | YES | — | Address |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

**Indexes:** `id` (PK), `facility_id` (unique), `facility_type`, `organization_id`

**Relationships:** `organization` → `Organization` (N:1)

---

### 3.14 `visits`

SNDHS Phase 1 visit tracking. Created by migration `20260505_0003`. Feature-gated by `SNDHS_ENABLE_VISITS` (default: false).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `UUID` PK | NOT NULL | `gen_random_uuid()` | Primary key |
| `patient_id` | `Integer` FK | NOT NULL | — | → `patients.id` ON DELETE CASCADE |
| `visit_type` | `String(40)` | NOT NULL | `lab` | Type of visit |
| `status` | `String(20)` | NOT NULL | `open` | `open`, `closed` |
| `created_at` | `DateTime(tz)` | NOT NULL | `now()` | Visit creation timestamp |
| `closed_at` | `DateTime(tz)` | YES | — | Visit closure timestamp |

**Indexes:** `ix_visits_patient_id`, `ix_visits_status`, `ix_visits_created_at`

**Note:** `patient_id` is INT (not UUID) to match the existing `patients.id` PK type.

---

### 3.15 `subscriptions`

Multi-tier SaaS subscription model with three orthogonal dimensions: Subscription Tier (`starter` / `growth` / `enterprise`), Deployment Mode (`single` / `multi_branch` / `government`), and Security Level (`standard` / `high_security` / `air_gapped`).

#### `lab_subscriptions`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE (unique) |
| `tier` | `String(30)` | NOT NULL | `starter` | `starter`, `growth`, `enterprise` |
| `deployment_mode` | `String(30)` | NOT NULL | `single` | `single`, `multi_branch`, `government` |
| `security_level` | `String(30)` | NOT NULL | `standard` | `standard`, `high_security`, `air_gapped` |
| `is_active` | `Boolean` | NOT NULL | `true` | Active status |
| `trial_ends_at` | `DateTime(tz)` | YES | — | Trial expiry |
| `billing_cycle` | `String(20)` | YES | `monthly` | `monthly`, `yearly` |
| `monthly_price_usd` | `Float` | YES | `0.0` | Monthly price |
| `max_patients` | `Integer` | YES | `500` | Patient limit |
| `max_staff` | `Integer` | YES | `5` | Staff limit |
| `max_branches` | `Integer` | YES | `1` | Branch limit |
| `max_orders_per_day` | `Integer` | YES | `100` | Daily order limit |
| `max_ai_calls_per_day` | `Integer` | YES | `0` | Daily AI call limit |
| `notes` | `Text` | YES | — | Notes |
| `activated_at` | `DateTime(tz)` | YES | `now()` | Activation timestamp |
| `expires_at` | `DateTime(tz)` | YES | — | Expiry timestamp |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | YES | `now()` | Last update |

**Indexes:** `lab_id` (unique), `tier`

#### `upgrade_requests` / `upgrade_demand_scores` / `feature_flags`

Supporting tables for demand-driven upgrades and per-lab feature overrides. See `backend/app/models/subscription.py` for full column definitions.

---

### 3.16 `mfa_devices` / `mfa_sessions`

Multi-factor authentication device registry and session tracking.

#### `mfa_devices`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `user_id` | `Integer` FK | NOT NULL | — | → `lab_users.id` |
| `device_type` | `String(30)` | NOT NULL | — | TOTP, WebAuthn, backup_code |
| `device_name` | `String(100)` | YES | — | Human-readable name |
| `secret` | `String(500)` | YES | — | TOTP secret |
| `credential_id` | `String(500)` | YES | — | WebAuthn credential ID |
| `public_key` | `Text` | YES | — | WebAuthn public key |
| `sign_count` | `Integer` | YES | `0` | WebAuthn signature counter |
| `transports` | `String(500)` | YES | — | WebAuthn transports |
| `backup_codes` | `Text` | YES | — | Backup codes (hashed) |
| `is_active` | `Boolean` | YES | `true` | Active status |
| `is_primary` | `Boolean` | YES | `false` | Primary device flag |
| `last_used_at` | `DateTime(tz)` | YES | — | Last use timestamp |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | YES | `now()` | Last update |

#### `mfa_sessions`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `user_id` | `Integer` FK | NOT NULL | — | → `lab_users.id` |
| `session_token` | `String(255)` | NOT NULL | — | Unique session token |
| `mfa_method` | `String(30)` | NOT NULL | — | Method used |
| `is_verified` | `Boolean` | YES | `false` | Verification status |
| `expires_at` | `DateTime(tz)` | NOT NULL | — | Session expiry |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

---

### 3.17 `oauth2_clients` / `oauth2_tokens`

OAuth2 authorization server tables for third-party integrations.

#### `oauth2_clients`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `client_id` | `String(100)` | NOT NULL | — | Unique client ID |
| `client_secret_hash` | `String(255)` | NOT NULL | — | Hashed client secret |
| `redirect_uris` | `Text` | YES | — | Allowed redirect URIs |
| `allowed_scopes` | `Text` | YES | — | Allowed OAuth scopes |
| `grant_types` | `Text` | YES | — | Allowed grant types |
| `response_types` | `Text` | YES | — | Allowed response types |
| `is_confidential` | `Integer` | YES | `1` | Confidential client flag |
| `is_active` | `Integer` | YES | `1` | Active status |
| `token_endpoint_auth_method` | `String(50)` | YES | `client_secret_basic` | Auth method |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `updated_at` | `DateTime(tz)` | YES | `now()` | Last update |

#### `oauth2_tokens`

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `client_id` | `String(100)` | NOT NULL | — | → `oauth2_clients.client_id` |
| `user_id` | `Integer` | YES | — | Resource owner user ID |
| `token_type` | `String(20)` | NOT NULL | — | `access_token`, `refresh_token`, `authorization_code` |
| `token_hash` | `String(255)` | NOT NULL | — | SHA-256 of token value |
| `scope` | `Text` | YES | — | Granted scopes |
| `expires_at` | `DateTime(tz)` | NOT NULL | — | Token expiry |
| `code_challenge` | `String(255)` | YES | — | PKCE code challenge |
| `code_challenge_method` | `String(10)` | YES | — | PKCE method (`S256`, `plain`) |
| `is_revoked` | `Integer` | YES | `0` | Revocation flag |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

---

### 3.18 `service_accounts`

API service accounts for machine-to-machine integration.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `name` | `String(200)` | NOT NULL | — | Account name |
| `description` | `Text` | YES | — | Description |
| `api_key_hash` | `String(255)` | NOT NULL | — | Hashed API key |
| `roles` | `Text` | YES | — | Assigned roles |
| `scopes` | `Text` | YES | — | Authorized scopes |
| `is_active` | `Integer` | YES | `1` | Active status |
| `last_used_at` | `DateTime(tz)` | YES | — | Last usage timestamp |
| `created_by` | `Integer` | YES | — | Creator user ID |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `expires_at` | `DateTime(tz)` | YES | — | Account expiry |

---

### 3.19 `quality_controls`

Lab instrument QC tracking with Westgard rule violations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `test_code` | `String(50)` | NOT NULL | — | Test code (glucose, hemoglobin, etc.) |
| `instrument_name` | `String(200)` | YES | — | Instrument name |
| `lot_number` | `String(100)` | YES | — | Control lot number |
| `level` | `String(20)` | NOT NULL | — | `low`, `normal`, `high` |
| `expected_value` | `Float` | NOT NULL | — | Expected value |
| `measured_value` | `Float` | NOT NULL | — | Measured value |
| `sd` | `Float` | YES | — | Standard deviation |
| `unit` | `String(30)` | YES | — | Unit |
| `status` | `String(20)` | YES | `pass` | `pass`, `warning`, `fail` |
| `violation` | `String(50)` | YES | — | Westgard rule: `1-2s`, `1-3s`, `2-2s`, `R-4s`, `4-1s`, `10-x` |
| `notes` | `Text` | YES | — | Notes |
| `performed_by` | `String(200)` | YES | — | Technician name |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |

---

### 3.20 `consents`

Patient consent management for data access grants. Uses ULID primary keys.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `String(26)` PK | NOT NULL | — | ULID |
| `gpid` | `String(26)` | NOT NULL | — | Subject (citizen ULID) |
| `grantee_id` | `String(64)` | NOT NULL | — | Actor identifier |
| `scope` | `String(64)` | NOT NULL | — | Namespaced scope |
| `status` | `String(16)` | NOT NULL | `active` | `active`, `revoked`, `expired` |
| `expires_at` | `DateTime(tz)` | NOT NULL | — | Expiry (API caps at 72h) |
| `created_at` | `DateTime(tz)` | YES | `now()` | Creation timestamp |
| `revoked_at` | `DateTime(tz)` | YES | — | Revocation timestamp |
| `created_by_user_id` | `Integer` FK | YES | — | → `lab_users.id` ON DELETE SET NULL |

**Design invariants:** No PII stored. No open-ended consents. No wildcard scopes. Status transitions are one-way: `active` → `revoked` / `expired`. Active tuple (gpid, grantee_id, scope, status) is unique.

---

### 3.21 Edge Platform Tables

Seven tables powering the Managed Distributed Edge AI Platform.

#### `edge_devices`

Edge nodes (user devices) registered for distributed AI inference.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | `Integer` PK | NOT NULL | auto-increment | Primary key |
| `device_id` | `String(64)` | NOT NULL | — | Unique device ID |
| `lab_id` | `Integer` FK | NOT NULL | — | → `labs.id` ON DELETE CASCADE |
| `owner_user_id` | `Integer` FK | YES | — | → `lab_users.id` ON DELETE SET NULL |
| `display_name` | `String(200)` | YES | — | Human-readable name |
| `role_mode` | `String(32)` | NOT NULL | `personal` | `personal`, `clinic`, `enterprise` |
| `status` | `String(32)` | NOT NULL | `pending` | `pending`, `active`, `quarantined`, `revoked`, `offline` |
| `trust_score` | `Float` | NOT NULL | `50.0` | Trust score (0–100) |
| `public_key_pem` | `Text` | YES | — | Public key |
| `cert_fingerprint` | `String(128)` | YES | — | Certificate fingerprint (unique) |
| `attestation_blob` | `Text` | YES | — | Attestation data |
| `agent_version` | `String(32)` | YES | — | Agent software version |
| `os_platform` | `String(64)` | YES | — | OS/platform |
| `capabilities` | `JSON` | YES | — | Device capabilities |
| `last_seen_at` | `DateTime(tz)` | YES | — | Last heartbeat |
| `registered_at` | `DateTime(tz)` | NOT NULL | `now()` | Registration timestamp |
| `revoked_at` | `DateTime(tz)` | YES | — | Revocation timestamp |
| `quarantined_at` | `DateTime(tz)` | YES | — | Quarantine timestamp |
| `kill_switched` | `Boolean` | NOT NULL | `false` | Kill switch flag |
| `notes` | `Text` | YES | — | Notes |

#### Other edge tables: `edge_tasks`, `edge_telemetry`, `edge_models`, `edge_model_assignments`, `edge_policies`, `edge_events`

Each scoped by `lab_id` with appropriate indexes. See `backend/app/models/edge.py` for full definitions.

---

### 3.22 Authorization Tables

Extended RBAC/ABAC authorization model with 45+ user types, roles, permissions, policies, delegations, and break-glass sessions.

#### Key tables:
- **`roles`** (46 types including citizen, physician, nurse, lab_technician, pathologist, radiologist, ministry_director, etc.)
- **`permissions`** — Fine-grained permission definitions with domain/resource/action tuples
- **`role_permissions`** — Many-to-many role ↔ permission mapping
- **`role_assignments`** — User role assignments with optional facility/department scope
- **`role_groups`** / **`role_group_members`** — Role grouping
- **`abac_policies`** — Attribute-based access control policies with JSON conditions
- **`field_security`** — Field-level security classifications
- **`delegations`** — Role delegation with time bounds
- **`break_glass_sessions`** — Emergency access sessions with audit
- **`authorization_audit`** — Authorization decision audit trail

Full column definitions in `backend/app/models/authorization.py`.

---

### 3.23 Canonical Patient Tables

MPI (Master Patient Index) golden record system using probabilistic matching (Fellegi-Sunter).

- **`canonical_patients`** — Golden patient records with `BigInteger` PK, national_id_hash, health_id, blood_type, mpi_score
- **`patient_links`** — Links per-lab `patients` → `canonical_patients` with linkage method and confidence
- **`citizen_links`** — Links national `citizens` → `canonical_patients` with linkage method and confidence

---

### 3.24 AI Interaction Tables

Clinical AI interaction logging with safety, hallucination control, and feedback.

- **`ai_interactions`** — Prompt/response pairs with latency, risk_level, confidence_score, retrieval_used, unsupported_claims
- **`ai_retrieval_refs`** — RAG retrieval references per interaction
- **`ai_feedback`** — User feedback (signal + notes)
- **`ai_unresolved_questions`** — Questions AI couldn't answer
- **`medical_terminology_normalized`** — EN/AR/AR-IQ terminology normalization

---

### 3.25 Claims Tables

Insurance and billing claims integration (migration `20260407_0001`).

- **`claims`** — Insurance claims with `lab_id`, `patient_id`, `order_id`, status, total_amount, currency (IQD), idempotency_key
- **`claim_items`** — Line items with test_code, quantity, unit_price, amount

---

### 3.26 Financial Engine (Phase A)

Phase A is schema-only (gated by `ENABLE_FINANCIAL_ENGINE` = false). Nine `fin_*` tables created by migration `20260506_0001`:

| Table | Purpose |
|-------|---------|
| `fin_providers` | Billable entity (lab/clinic/doctor/institution) |
| `fin_subscriptions` | Provider plan + status + expiry |
| `fin_transactions` | Pricing-engine ledger (per-test fees, ad spend, refunds) |
| `fin_ads_campaigns` | Sponsored-listing bids and daily caps |
| `fin_ads_clicks` | Raw click stream for CPC accounting + fraud scoring |
| `fin_ads_conversions` | Attributed orders for CPA accounting |
| `fin_fraud_logs` | Provider-level integrity flags |
| `fin_market_benchmarks` | Per-test-type market reference (price + TAT) |
| `fin_clinical_behavior` | Doctor-level over-testing / deviation profile |

All columns nullable (except PKs). No FK constraints in Phase A.

---

## 4. Indexes

### Primary Key Strategies

| Strategy | Tables |
|----------|--------|
| `Integer` auto-increment | Most tables: `labs`, `lab_users`, `patients`, `lab_orders`, `lab_results`, `samples`, `test_types`, `audit_logs`, `users`, `tenants`, `organizations`, `facilities`, `subscriptions`, `quality_controls`, `service_accounts`, `oauth2_clients`, `oauth2_tokens`, `mfa_devices`, `mfa_sessions` |
| `BigInteger` auto-increment | `test_results`, `canonical_patients`, `patient_links`, `citizen_links` |
| `UUID` (server-generated) | `visits`, `ai_interactions`, `ai_retrieval_refs`, `ai_feedback`, `ai_unresolved_questions`, `medical_terminology_normalized`, financial engine tables |
| `String(26)` (ULID) | `consents` |
| `String(36)` | `gov_identity_records`, `gov_break_glass_accesses` |

### Critical Indexes

| Table | Index | Type | Purpose |
|-------|-------|------|---------|
| `patients` | `ix_patients_lab_id` | Composite | Multi-tenant lookups |
| `patients` | `ix_patients_lab_phone` | Composite | Phone lookup within lab |
| `patients` | `ix_patients_lab_nid` | Composite | National ID lookup within lab |
| `patients` | `health_id` | Unique | Health ID lookup |
| `patients` | `family_id_hash` | B-tree | Family grouping |
| `lab_orders` | `patient_id` | B-tree | Patient order history |
| `lab_orders` | `lab_id` | B-tree | Lab order queries |
| `lab_orders` | `status` | B-tree | Status filtering |
| `lab_orders` | `version` | B-tree | Optimistic lock |
| `lab_results` | `token` | Unique | Patient card access |
| `lab_results` | `order_id` | B-tree | Order result lookup |
| `lab_results` | `flag` | B-tree | Critical result filtering |
| `audit_logs` | `chain_hash` | B-tree | Hash chain integrity |
| `audit_logs` | `action` | B-tree | Action-type queries |
| `test_results` | `ix_test_results_citizen_lab` | Composite | Citizen+lab scope |
| `test_results` | `ix_test_results_lab_status` | Composite | Lab status queries |
| `consents` | `idx_consents_lookup` | Composite | Consent lookup |
| `edge_devices` | `idx_edge_devices_lab` | Composite | Lab device queries |
| `feature_flags` | `ix_feature_flags_lab_key` | Unique | Per-lab feature key |
| `outbox_events` | `status, created_at` | B-tree | Pending event polling |

### Partial / Special Indexes

- `upgrade_demand_scores.lab_id` — unique per lab
- `lab_subscriptions.lab_id` — unique per lab (one subscription)
- `mfa_sessions.session_token` — unique
- `claims.idempotency_key` — unique
- `edge_devices.cert_fingerprint` — unique constraint

---

## 5. Constraints and Foreign Keys

### Cascade Rules

| Parent | Child | On Delete | Business Rationale |
|--------|-------|-----------|--------------------|
| `labs` | `lab_users` | CASCADE | Lab deletion removes all staff |
| `labs` | `patients` | CASCADE | Lab deletion removes all patients |
| `labs` | `lab_orders` | CASCADE | Lab deletion removes all orders |
| `labs` | `quality_controls` | CASCADE | Lab deletion removes QC records |
| `labs` | `lab_subscriptions` | CASCADE | Lab deletion removes subscription |
| `labs` | `edge_devices` | CASCADE | Lab deletion revokes edge devices |
| `patients` | `lab_orders` | CASCADE | Patient deletion removes orders |
| `patients` | `visits` | CASCADE | Patient deletion removes visits |
| `lab_orders` | `lab_results` | CASCADE | Order deletion removes results |
| `lab_orders` | `samples` | CASCADE | Order deletion removes samples |
| `organizations` | `facilities` | CASCADE | Org deletion removes facilities |
| `users` | `role_assignments` | CASCADE | User deletion removes assignments |
| `citizens` | `test_results` | RESTRICT | Cannot delete citizen with results |

### Nullifying Rules

| Parent | Child | On Delete | Rationale |
|--------|-------|-----------|-----------|
| `lab_users` | `lab_orders.doctor_user_id` | SET NULL | Preserve order when doctor deleted |
| `lab_users` | `lab_orders.validated_by` | SET NULL | Preserve order when validator deleted |
| `lab_users` | `mfa_devices` | CASCADE | User deletion removes MFA |
| `patients` | `patients.guardian_id` | SET NULL | Minor becomes orphaned but data preserved |
| `labs` | `users` | SET NULL | User exists independently of lab |

### Unique Constraints

| Table | Constraint | Columns |
|-------|-----------|---------|
| `lab_users` | `uq_lab_users_email` | `email` |
| `lab_users` | `uq_lab_users_national_id` | `national_id_hash` |
| `labs` | `uq_labs_license` | `license_number` |
| `patients` | `uq_patients_health_id` | `health_id` |
| `patients` | `uq_patients_nid_hash` | `national_id_hash` |
| `lab_results` | `uq_lab_results_token` | `token` |
| `lab_results` | `uq_lab_results_token_hash` | `token_hash` |
| `samples` | `uq_samples_barcode` | `barcode` |
| `test_types` | `uq_test_types_code` | `test_code` |
| `tenants` | `uq_tenants_id` | `tenant_id` |
| `tenants` | `uq_tenants_domain` | `domain` |
| `organizations` | `uq_orgs_id` | `org_id` |
| `facilities` | `uq_facilities_id` | `facility_id` |
| `oauth2_clients` | `uq_oauth2_client_id` | `client_id` |
| `service_accounts` | `uq_service_account_name` | (docs say unique, model uses Integer PK with `name` unique) |
| `edge_devices` | `uq_edge_devices_device_id` | `device_id` |
| `edge_devices` | `uq_edge_devices_cert_fp` | `cert_fingerprint` |
| `edge_models` | `uq_edge_models_name_version` | `name`, `version` |
| `consents` | `uq_consents_active_tuple` | `gpid`, `grantee_id`, `scope`, `status` |
| `feature_flags` | `ix_feature_flags_lab_key` | `lab_id`, `feature_key` |

---

## 6. Partitioning

**No table-level partitioning is currently implemented.** All tables are unpartitioned.

**Growth targets and future considerations:**

| Table | Estimated Row Growth | Partition Strategy |
|-------|---------------------|--------------------|
| `audit_logs` | 100M+ rows/year | Range partition by `created_at` (quarterly) |
| `test_results` | 50M+ rows/year | Range partition by `sample_collected_at` |
| `outbox_events` | 10M+ rows/year | Range partition by `created_at` (monthly) |
| `lab_results` | 5M+ rows/year | Range partition by `created_at` |
| `edge_telemetry` | 500M+ rows/year | Range partition by `ts` (daily) |
| `ai_interactions` | 10M+ rows/year | Range partition by `created_at` |

**When partition thresholds would trigger implementation:**
- Any table exceeding 100M rows
- Query performance degradation on time-range scans
- Vacuum/autovacuum unable to keep up with write-heavy tables

Partitioning will be implemented as new Alembic migrations using PostgreSQL declarative partition syntax (`PARTITION BY RANGE`).

---

## 7. Retention Policy

| Data | Retention | Archival/Deletion Rule |
|------|-----------|----------------------|
| Clinical orders & results | Indefinite | Never deleted — clinical record |
| Patient records | Indefinite | Never deleted — clinical record |
| Audit logs | Indefinite | Never deleted — legal/regulatory |
| Outbox events | 90 days after `done` status | Archived, then deleted |
| Lab result tokens | 90 days | Auto-expire via `expires_at` |
| Edge telemetry | 90 days | Archived, then deleted |
| Edge tasks | 30 days after completion | Archived, then deleted |
| AI interactions | 1 year | Anonymised (prompt_redacted=true), then deleted |
| AI retrieval refs | 1 year | Cascade from `ai_interactions` |
| MFA sessions | Session lifetime + 24h | Hard delete after expiry |
| OAuth2 tokens | Token lifetime + 30d | Archived, then deleted |
| Service accounts | Account lifetime | Deactivated, archived after 90d |
| Upgrade requests | Indefinite | Never deleted — demand signal history |
| Claims | 7 years (Iraqi law) | Archived after 7 years |
| Financial engine data | Indefinite | Never deleted — audit trail |
| QC records | 2 years | Archived, then deleted |

**Archival mechanism:** Not yet automated. Future implementation will use a background worker that moves old rows to a `*_archive` schema or separate archive database before hard-deleting.

---

## 8. Connection Pool Configuration

### Production Formula

```
Total connections = WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
Must be < postgres.max_connections (default: 100)
```

### Current Defaults (from `backend/app/database.py`)

| Parameter | Env Variable | Default | Description |
|-----------|-------------|---------|-------------|
| `WEB_CONCURRENCY` | `WEB_CONCURRENCY` | `2` | Gunicorn worker count |
| `DB_POOL_SIZE` | `DB_POOL_SIZE` | `5` | Base pool size per worker |
| `DB_MAX_OVERFLOW` | `DB_MAX_OVERFLOW` | `10` | Overflow per worker |
| `DB_POOL_TIMEOUT` | `DB_POOL_TIMEOUT` | `10s` | Pool checkout timeout |
| `DB_POOL_RECYCLE` | `DB_POOL_RECYCLE` | `1800s` | Connection recycle interval |
| `DB_STMT_TIMEOUT` | `DB_STMT_TIMEOUT` | `30s` | Per-statement timeout |

**Budget calculation (default):** 2 × (5 + 10) = **30 connections** (well under PostgreSQL's default 100, leaving headroom for superuser + monitoring).

**Read-replica pool:** When `READ_REPLICA_URL` is configured, a separate engine with `REPLICA_POOL_SIZE=10` and `REPLICA_MAX_OVERFLOW=20` is created for read-only queries.

### Per-Connection Session Settings

Set via `SET` statements on every new connection:
- `statement_timeout = '30s'`
- `work_mem = '16MB'`
- `idle_in_transaction_session_timeout = '60s'`

### Pool Monitoring

The `get_pool_status()` function exposes live pool metrics:
- `pool_size`, `checked_out`, `overflow`, `checked_in`
- `read_replica_enabled` boolean
- Replica pool metrics if active

### Circuit Breaker Thresholds

| Metric | Env Variable | Default | Action |
|--------|-------------|---------|--------|
| Refused count (5min) | `DB_CIRCUIT_OPEN_THRESHOLD` | 20 | Open circuit → L2 READ_ONLY |
| Refused count (5min) | `DB_SYSTEM_DEGRADE_THRESHOLD` | 50 | System degrade → L3 CRITICAL_ONLY |
| Timeout count (5min) | `DB_TIMEOUT_L1_THRESHOLD` | 5 | L1 CACHE_HEAVY (slow DB) |
| Timeout count (5min) | `DB_TIMEOUT_L2_THRESHOLD` | 15 | L2 READ_ONLY (same as circuit open) |

---

## 9. Migration Policy

### Rules (MANDATORY — from CLAUDE.md)

| Rule | Why |
|------|-----|
| **Never modify an existing migration** | Existing DBs have already run it |
| **All schema changes = new revision** | `alembic revision --autogenerate -m "describe"` |
| **`20250322_0000_create_base_schema.py` is immutable** | It is the bootstrap snapshot |
| **Every migration must be idempotent** | Use `_has_column()`, `_table_exists()`, `_index_exists()` guards |
| **New columns must be nullable or have a `server_default`** | Non-nullable columns break existing rows |
| **Test on a clean DB before PR** | The CI migration-gate does this; do it locally first |

### Migration Workflow

```bash
# Create a migration
cd backend && alembic revision --autogenerate -m "add_foo_column"

# Test on clean DB
docker compose down -v && docker compose up -d postgres
docker compose run --rm gula-backend alembic upgrade head

# Round-trip test
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

### Migration History (48 files)

| Revision | Description |
|----------|-------------|
| `20250322_0000` | Create base schema (bootstrap snapshot — immutable) |
| `20250322_0001` | Add roles hierarchy |
| `20250322_0002` | Performance indexes, audit protection |
| `20250322_0003` | Order validation state (validated_by, validated_at, locked_at) |
| `20250323_0004` | Core enforcement |
| `20250323_0005` | Citizen email nullable |
| `20260324_0006` | Patient family/guardian fields |
| `20260324_0007` | Lab type, director, website |
| `20260324_0008` | Lab result test_type FK set null |
| `20260324_0009` | Audit chain_hash, result engine version |
| `20260324_0010` | Production indexes |
| `20260329_0011` | Subscription tiers, feature flags |
| `20260329_0012` | Lab result version, citizen indexes |
| `20260407_0001` | Claims tables (claims, claim_items) |
| `20260413_0001` | MPI citizen registry |
| `20260417_0001` | Consent table |
| `20260428_0001` | Edge platform |
| `20260503_0001` | Stats/trends performance indexes |
| `20260505_0001` | SNDHS Phase 1 — extend patients |
| `20260505_0002` | SNDHS Phase 1 — index national_id |
| `20260505_0003` | SNDHS Phase 1 — visits table |
| `20260505_0004` | SNDHS Phase 1 — lab_orders.visit_id |
| `20260505_0005` | SNDHS Phase 1 — audit_logs v2 |
| `20260505_0006` | SNDHS Phase 1 — constraints |
| `20260506_0001` | Financial Engine Phase A (fin_* tables) |
| `20260511_0001` | AI interactions dataset |
| `20260511_0002` | AI safety/hallucination columns |
| `20260714_0001` | National LIMS tables |
| `20260715_0001` | National ecosystem partners |
| `20260716_0001` | NHDW platform |
| `20260716_0002` | Nursing platform |
| `20260716_0003` | Pharmacy platform |
| `20260716_0004` | Radiology platform |
| `20260716_0005` | National EMS and disaster response platform |
| `20260716_0006` | National blood bank and transfusion platform |
| `20260716_0007` | National critical care platform |
| `20260716_0008` | National biomedical engineering platform |
| `20260716_0009` | National public health and disease surveillance platform |
| `20260716_0010` | National health command center |
| `20260716_0011` | National pilot deployment and readiness platform |
| `20260716_0012` | National platform lifecycle and governance tables |
| `20260716_0013` | National trust platform |
| `20260716_0014` | Governance identity persistence |
| `20260716_0015` | Auth security tables |
| `20260716_0016` | Canonical patient unification |
| `20260719_0001` | AI platform tables |
| `20260720_0001` | Gap closure composite indexes |
| `20260722_0001` | Authorization expansion |

### CI Migration Gate

The CI pipeline's `migration-check` job:
1. Creates a fresh PostgreSQL 17 container
2. Runs `alembic upgrade head`
3. Verifies required tables exist: `labs`, `lab_users`, `patients`, `lab_orders`, `lab_results`, `outbox_events`, `audit_logs`
4. Runs `downgrade -1` then `upgrade head` to verify round-trip compatibility

### Schema Enforcement

- `backend/app/core/startup_guard.py` blocks readiness until migrations are checked
- `system_ready` stays `False` until DB is confirmed reachable and migrations pass
- The `ReadinessMiddleware` returns 503 for every path (except health endpoints) until ready

### Model File Summary

| File | Models |
|------|--------|
| `models/lab.py` | `Lab` |
| `models/lab_user.py` | `LabUser` |
| `models/patient.py` | `Patient` |
| `models/lab_order.py` | `LabOrder` |
| `models/lab_result.py` | `LabResult` |
| `models/sample.py` | `Sample` |
| `models/test_type.py` | `TestType` |
| `models/test_result.py` | `TestResult` (+ Pydantic schemas) |
| `models/audit_log.py` | `AuditLog` |
| `models/outbox.py` | `OutboxEvent` |
| `models/user.py` | `User` |
| `models/tenant.py` | `Tenant` |
| `models/organization.py` | `Organization`, `Facility` |
| `models/subscription.py` | `LabSubscription`, `UpgradeRequest`, `UpgradeDemandScore`, `FeatureFlag` |
| `models/mfa_device.py` | `MFADevice`, `MFASession` |
| `models/oauth2_client.py` | `OAuth2Client` |
| `models/oauth2_token.py` | `OAuth2Token` |
| `models/service_account.py` | `ServiceAccount` |
| `models/quality_control.py` | `QualityControl` |
| `models/consent.py` | `Consent` |
| `models/edge.py` | `EdgeDevice`, `EdgeTask`, `EdgeTelemetry`, `EdgeModel`, `EdgeModelAssignment`, `EdgePolicy`, `EdgeEvent` |
| `models/authorization.py` | `Permission`, `Role`, `RolePermission`, `RoleAssignment`, `RoleGroup`, `RoleGroupMember`, `Policy`, `FieldSecurity`, `Delegation`, `BreakGlassSession`, `AuthorizationAudit`, `UserTypeEnum` |
| `models/canonical_patient.py` | `CanonicalPatient`, `PatientLink`, `CitizenLink` |
| `models/ai_interaction.py` | `AIInteraction`, `AIRetrievalRef`, `AIFeedback`, `AIUnresolvedQuestion`, `MedicalTerminologyNormalized` |
| `models/base.py` | `AuditMixin`, `BaseEntityMixin`, `OptimisticLockMixin`, `SoftDeleteMixin`, `TenantMixin`, `TimestampMixin` |

---

*End of Database Schema Reference — GULA Platform v2.5.0*
