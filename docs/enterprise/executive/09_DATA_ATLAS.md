# GULA Platform — Data Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18

---

## 1. Database Architecture

| System | Version | Purpose | Deployment |
|--------|---------|---------|------------|
| PostgreSQL | 16 (MVP) / 14.11 (full) | Primary transactional database | Single instance (MVP); Patroni HA (full) |
| Redis | 7-alpine | Cache, session, rate limiting, feature flags | Single instance (MVP); Sentinel (full) |
| ClickHouse | 23.8 | Analytics (full stack only) | ❌ Not deployed |
| MinIO | RELEASE.2024-01 | Object storage (full stack only) | ❌ Not deployed |
| Kafka | 7.5.0 | Event streaming (full stack only) | ❌ Not deployed |

---

## 2. Database Scale

| Metric | Value |
|--------|-------|
| Alembic Migrations | 48 |
| Core Tables | ~20 (labs, users, patients, orders, results, samples, test_types, audit_logs, outbox_events) |
| Total Database Tables | ~250 |
| ORM Models | 31+ (70% of tables have no ORM model) |
| Migration Phases | 6 (Core LIMS → Hardening → Domain → SNDHS → Financial/AI → National Platform) |

---

## 3. Entity Relationships (Core)

```
labs (tenant root)
  ├── lab_users (staff)
  ├── patients (tenant-isolated via lab_id FK)
  │     ├── lab_orders (FK patient_id)
  │     │     └── lab_results (FK order_id, version for optimistic lock)
  │     ├── samples (FK patient_id)
  │     └── patient_cards (HMAC-signed tokens)
  ├── test_types (reference ranges, LOINC mapping)
  ├── quality_controls (Westgard rules)
  ├── audit_logs (hash-chain, PG trigger protected)
  └── outbox_events (transactional outbox, FOR UPDATE SKIP LOCKED)
```

**Tenant isolation:** Every patient-data table has `lab_id` foreign key. All queries filter by `lab_id = current_user.lab_id`.

---

## 4. Migration Inventory (6 Phases)

| Phase | Count | Date | Scope |
|-------|-------|------|-------|
| 1 — Core LIMS Bootstrap | 8 | 2025-03 → 2026-03 | Base schema, roles, indexes, validation |
| 2 — Production Hardening | 5 | 2026-03 | FK constraints, audit hash chain, indexes, subscriptions, version columns |
| 3 — Domain Expansion | 5 | 2026-04 → 2026-05 | Claims, MPI, consent, edge platform, stats |
| 4 — SNDHS-lite Integration | 6 | 2026-05-05 | national_id, sndhs_health_id, visits, audit v2, constraints |
| 5 — Financial + AI | 3 | 2026-05 | Financial Phase A, AI interactions, AI safety |
| 6 — National Platform | 17 | 2026-07-14 → 07-16 | LIMS 35 tables, pharmacy 23, radiology 19, nursing 15, EMS 12, blood bank 11, critical care 13, biomedical 11, public health 7, command center 4, auth/security 4, canonical patient, HWD, ecosystem partners |

**Total:** 48 migrations, all additive and idempotent

---

## 5. Domain Tables (~230 additional)

| Domain | Tables | Status |
|--------|--------|--------|
| National LIMS | 35 | Schema only |
| Clinical Terminology/Knowledge/Quality/CDS | 43 | Schema only |
| NHDW (Hospital) | 15 | Schema only |
| Pharmacy | 23 | Schema only |
| Radiology | 19 | Schema only |
| Nursing | 15 | Schema only |
| EMS | 12 | Schema only |
| Blood Bank | 11 | Schema only |
| Critical Care | 13 | Schema only |
| Biomedical | 11 | Schema only |
| Public Health | 7 | Schema only |
| Command Center | 4 | Schema only |
| Pilot/Lifecycle/Trust/Governance | 18 | Schema only |
| Auth/Security | 4 | Schema only |
| Health Data (Warehouse/ODS/MDM) | 15+ | Schema only |
| MPI/Citizen | 4 | ✅ Populated |
| Edge Platform | 9 | ⚠️ Partial |
| AI Interactions | 5 | ⚠️ Partial |
| Financial | 5 | ⚠️ Schema only |
| SNDHS | 3 | ✅ Deployed |

---

## 6. Data Flows

### Lab Result Ingestion
```
Lab Analyzer (ASTM)
  → device_bridge → normalizer → mapper → matcher → router
    → gula_client.py (HTTP POST)
      → device_results route → auth → validation → LabResult
        → audit_log → clinical engine → outbox → notification
```

### Patient Card
```
Patient→QR→Scan→HMAC Verify→Patient Data→Clinical History
```

### Order Lifecycle
```
Order Create → Audit → Outbox → Sample Collect → Test → Result → QC → Validate → Report
```

---

## 7. Encryption Strategy

| Data Type | Encryption | Algorithm | Key |
|-----------|-----------|-----------|-----|
| National ID | At rest (field-level) | Fernet AES-256-CBC + HMAC-SHA256 | ENCRYPTION_KEY |
| National ID HMAC | Integrity | HMAC-SHA256 | NID_HMAC_KEY |
| Patient card tokens | HMAC-signed | HMAC-SHA256 | NID_HMAC_KEY |
| Passwords | Hashed | bcrypt | N/A |
| JWT tokens | Signed | HMAC-SHA256 (HS256) | SECRET_KEY |
| Data in transit | TLS | TLS 1.2+ | Let's Encrypt |
| Audit chain | Hash chain | SHA-256 | N/A |

---

## 8. Data Retention Requirements (Mandated)

| Data Type | Retention Period | Enforcement |
|-----------|-----------------|-------------|
| Clinical records | 25 years | ❌ Not automated |
| Lab results | 10 years | ❌ Not automated |
| Audit logs | 7 years | ❌ Not automated |
| Financial records | 10 years | ❌ Not automated |

**All retention policies are currently unenforced.** The National Trust Platform mandates these periods but no automated purging or archival exists.

---

## 9. Database Connection Pool

| Parameter | Value |
|-----------|-------|
| Pool class | SQLAlchemy QueuePool |
| pool_size | 5 |
| max_overflow | 10 |
| pool_timeout | 10s |
| pool_recycle | 1800s |
| pool_pre_ping | True |
| Statement timeout | 30s |
| work_mem | 128MB |
| idle_in_transaction | 30s |

**Connection budget:** 3 workers × (5 + 10) = 45 connections (within PG max_connections=100)

---

## 10. Data Integrity Mechanisms

| Mechanism | Coverage | Description |
|-----------|----------|-------------|
| Optimistic locking | LabOrder, LabResult | version column, HTTP 409 on conflict |
| Transactional outbox | OutboxEvent | FOR UPDATE SKIP LOCKED, 10s poll |
| Hash chain audit | AuditLog (immutable) | SHA-256, PG trigger, 100-entry HMAC checkpoints |
| Tenant isolation | All patient-data tables | lab_id FK on every query |
| Dual-read rule | national_id, sndhs_health_id | Graceful None handling for pre-backfill rows |
