# Database Certification Report

**Date:** 2026-07-22
**Engine:** PostgreSQL 16 (primary), SQLite (test)

## Schema Overview

| Metric | Value |
|--------|-------|
| ORM Models | 26 |
| Migration files | 47 |
| Base migration | `20250322_0000_create_base_schema.py` (immutable) |
| Idempotent migrations | 47/47 (100%) |
| Migration guard functions | `_has_column()`, `_table_exists()`, `_index_exists()` |

## Model Inventory

| Model | Key Fields | Tenant Isolation |
|-------|-----------|-----------------|
| Lab | id, name, subscription_tier | N/A (root tenant) |
| LabUser | id, lab_id, role, email | `lab_id` |
| Patient | id, lab_id, full_name, phone | `lab_id` |
| LabOrder | id, lab_id, patient_id, status | `lab_id` |
| LabResult | id, order_id, version (optimistic lock) | via order |
| Sample | id, barcode, lab_id | `lab_id` |
| AuditLog | id, action, hash_chain | `lab_id` |
| QualityControl | id, lab_id, test_code | `lab_id` |
| OutboxEvent | id, event_type, payload | N/A |
| Subscription | id, lab_id, tier | `lab_id` |
| +16 more | | |

## Key Features

| Feature | Status |
|---------|--------|
| Alembic migrations | ✅ 47 files, all idempotent |
| Base schema immutable | ✅ `20250322_0000_create_base_schema.py` |
| Optimistic locking | ✅ LabResult has `version` column |
| Audit hash chain | ✅ AuditLog uses SHA-256 chain |
| Soft delete | ✅ Via `is_active` flag on users/labs |
| Tenant isolation | ✅ `lab_id` on all patient-data tables |
| Foreign keys | ✅ All relationships enforced |
| Indexes | ✅ 13 production indexes |
| Migration safety | ✅ IF NOT EXISTS / guard functions |
| Connection pooling | ✅ 18 conn (3 workers × 6 pool) |

## Migration Round-Trip

CI validates: `alembic upgrade head` → verify tables → `alembic downgrade -1` → `alembic upgrade head`

## Status: PASS ✅
