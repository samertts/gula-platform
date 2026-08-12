# GULA Platform — Database Analysis
**Date:** 2026-07-17

---

## 1. Database Technology

| Component | Technology | Version |
|-----------|------------|---------|
| Primary DB | PostgreSQL | 16 (MVP), 14.11 (full.yml) |
| ORM | SQLAlchemy | 2.0.51 |
| Migration | Alembic | 1.18.5 |
| Connection Pool | SQLAlchemy QueuePool | pool_size=5, max_overflow=10 |
| Analytics | ClickHouse | 23.8 (full.yml) |
| Cache | Redis | 7-alpine |
| Object Storage | MinIO | RELEASE.2024-01 (full.yml) |
| Message Queue | RabbitMQ | 3.12-management (full.yml) |
| Stream Processing | Kafka | 7.5.0 (full.yml) |

---

## 2. Migration Inventory (48 files)

### Phase 1: Core LIMS Bootstrap (8 migrations)
| File | Date | Tables Created |
|------|------|----------------|
| `20250322_0000_create_base_schema.py` | 2025-03-22 | labs, lab_users, users, patients, lab_orders, lab_results, samples, test_types, audit_logs, outbox_events — **IMMUTABLE** |
| `20250322_0001_add_roles_hierarchy.py` | 2025-03-22 | Roles hierarchy |
| `20250322_0002_perf_indexes_audit_protection.py` | 2025-03-22 | Performance indexes |
| `20250322_0003_order_validation_state.py` | 2025-03-22 | Order validation |
| `20250323_0004_core_enforcement.py` | 2025-03-23 | Core constraints |
| `20250323_0005_citizen_email_nullable.py` | 2025-03-23 | Citizen email nullable |
| `20260324_0006_patient_family_guardian.py` | 2026-03-24 | Family/guardian fields |
| `20260324_0007_lab_type_director_website.py` | 2026-03-24 | Lab metadata |

### Phase 2: Production Hardening (7 migrations)
| File | Date | Purpose |
|------|------|---------|
| `0008_lab_result_test_type_fk_set_null` | 2026-03-24 | FK on delete set null |
| `0009_audit_chain_hash_result_engine_version` | 2026-03-24 | Audit chain hash |
| `0010_production_indexes` | 2026-03-24 | Production indexes |
| `0011_subscription_tiers_feature_flags` | 2026-03-29 | Subscriptions |
| `0012_lab_result_version_citizen_indexes` | 2026-03-29 | Version + indexes |

### Phase 3: Domain Expansion (7 migrations)
| File | Date | Purpose |
|------|------|---------|
| `20260407_0001_claims_tables` | 2026-04-07 | Insurance claims |
| `20260413_0001_mpi_citizen_registry` | 2026-04-13 | Master Patient Index |
| `20260417_0001_consent_table` | 2026-04-17 | Patient consent |
| `20260428_0001_edge_platform` | 2026-04-28 | Edge AI devices |
| `20260503_0001_stats_trends_perf_indexes` | 2026-05-03 | Analytics indexes |

### Phase 4: SNDHS-lite Integration (6 migrations)
| File | Date | Purpose |
|------|------|---------|
| `20260505_0001_sndhs_phase1_extend_patients` | 2026-05-05 | national_id, sndhs_health_id |
| `20260505_0002_sndhs_phase1_index_national_id` | 2026-05-05 | National ID indexes |
| `20260505_0003_sndhs_phase1_visits_table` | 2026-05-05 | Visits table |
| `20260505_0004_sndhs_phase1_lab_orders_visit_id` | 2026-05-05 | visit_id FK |
| `20260505_0005_sndhs_phase1_audit_logs_v2` | 2026-05-05 | Enhanced audit |
| `20260505_0006_sndhs_phase1_constraints` | 2026-05-05 | Constraints |

### Phase 5: Financial + AI (3 migrations)
| File | Date | Purpose |
|------|------|---------|
| `20260506_0001_financial_engine_phase_a` | 2026-05-06 | Financial tables (Phase A) |
| `20260511_0001_ai_interactions_dataset` | 2026-05-11 | AI interaction tracking |
| `20260511_0002_ai_safety_hallucination_columns` | 2026-05-11 | AI safety columns |

### Phase 6: National Platform (17 migrations — largest)
| File | Date | Size | Purpose |
|------|------|------|---------|
| `20260714_0001_national_lims_tables` | 2026-07-14 | **76,502 bytes** — LIMS with 35 tables |
| `20260715_0001_national_ecosystem_partners` | 2026-07-15 | Ecosystem partners |
| `20260716_0001_nhdw_platform` | 2026-07-16 | Health data warehouse |
| `20260716_0002_nursing_platform` | 2026-07-16 | Nursing (15+ tables) |
| `20260716_0003_pharmacy_platform` | 2026-07-16 | Pharmacy (23+ tables) |
| `20260716_0004_radiology_platform` | 2026-07-16 | Radiology (19+ tables) |
| `20260716_0005_national_ems` | 2026-07-16 | Emergency services |
| `20260716_0006_blood_bank` | 2026-07-16 | Blood bank |
| `20260716_0007_critical_care` | 2026-07-16 | Critical care |
| `20260716_0008_biomedical_engineering` | 2026-07-16 | Biomedical |
| `20260716_0009_public_health` | 2026-07-16 | Public health |
| `20260716_0010_command_center` | 2026-07-16 | Command center |
| `20260716_0011_pilot_deployment` | 2026-07-16 | Pilot deployment |
| `20260716_0012_lifecycle_governance` | 2026-07-16 | Lifecycle |
| `20260716_0013_trust_platform` | 2026-07-16 | Trust platform |
| `20260716_0014_governance_identity` | 2026-07-16 | Identity governance |
| `20260716_0015_auth_security_tables` | 2026-07-16 | Auth/security |
| `20260716_0016_canonical_patient_unification` | 2026-07-16 | Patient unification |

---

## 3. Core Tables (~20 core tables)

| Table | Domain | Key Columns |
|-------|--------|-------------|
| `labs` | Core | id, name, license_number, lab_type, city, is_active |
| `lab_users` | Core | id, lab_id, name, email, password_hash, role, perm_version |
| `users` | Identity | id, email, phone, password_hash, role, lab_id, national_id_hash |
| `patients` | Clinical | id, lab_id, health_id, national_id_hash, full_name, guardian_id |
| `lab_orders` | Clinical | id, patient_id, lab_id, status (FSM), doctor_name, version |
| `lab_results` | Clinical | id, order_id, test_type_id, value, flag, token_hash, version |
| `samples` | Clinical | id, order_id, barcode, sample_type, status, rejection_reason |
| `test_types` | Reference | id, test_code, test_name, test_name_ar, category, unit, normal_range |
| `audit_logs` | Security | id, user_id, action, resource_type, chain_hash |
| `outbox_events` | Infrastructure | id, event_type, aggregate_type, payload, status |

---

## 4. Domain-Specific Tables (~230 additional tables)

| Domain | Approx. Tables | Migration |
|--------|---------------|-----------|
| National LIMS | 35 | `20260714_0001` |
| Clinical Terminology | 15 | Clinical sub-packages |
| Clinical Knowledge | 8 | Clinical sub-packages |
| Clinical Quality | 8 | Clinical sub-packages |
| Clinical CDS | 12 | Clinical sub-packages |
| NHDW (Hospital) | 15 | `20260716_0001` |
| Nursing | 15 | `20260716_0002` |
| Pharmacy | 23 | `20260716_0003` |
| Radiology | 19 | `20260716_0004` |
| EMS | 12 | `20260716_0005` |
| Blood Bank | 11 | `20260716_0006` |
| Critical Care | 13 | `20260716_0007` |
| Biomedical | 11 | `20260716_0008` |
| Public Health | 7 | `20260716_0009` |
| Command Center | 4 | `20260716_0010` |
| Pilot Platform | 5 | `20260716_0011` |
| Lifecycle | 5 | `20260716_0012` |
| Trust Platform | 5 | `20260716_0013` |
| Governance | 3 | `20260716_0014` |
| Auth/Security | 4 | `20260716_0015` |
| MPI / Citizen | 4 | `20260413_0001` |
| Edge Platform | 9 | `20260428_0001` |
| AI Interactions | 5 | `20260511_0001/0002` |
| Financial | 5 | `20260506_0001` |
| SNDHS | 3 | `20260505_0001-0006` |
| Health Data (Warehouse/ODS/MDM) | 15+ | National |

---

## 5. Migration Policy Compliance

| Rule | Status | Evidence |
|------|--------|----------|
| Never modify existing migrations | ✅ | All 48 files are additive |
| All schema changes = new revision | ✅ | Sequential timestamps |
| Base schema immutable | ✅ | `20250322_0000` unchanged |
| Idempotent migrations | ✅ | Uses _has_column(), _table_exists() guards |
| Nullable new columns | ✅ | All new columns nullable |

---

## 6. Key Database Patterns

### Tenant Isolation
- Every patient-data table has `lab_id` foreign key
- All queries MUST filter by `current_user.lab_id`
- No cross-lab access possible

### Optimistic Locking
- `lab_orders.version` — checked on every mutation
- `lab_results.version` — checked on every mutation
- HTTP 409 on conflict

### Hash Chain Audit
- `audit_logs.chain_hash` = SHA-256(prev_hash + JSON(entry))
- PostgreSQL trigger prevents UPDATE/DELETE
- HMAC-anchored checkpoint files every 100 entries

### Encryption at Rest
- `patients.national_id` → `national_id_hash` (encrypted + HMAC-signed)
- Format: `{encrypted_data}.{hmac_signature}`
- Fernet AES-256 + HMAC-SHA256

### Dual-Read Rule
- `patients.national_id` and `sndhs_health_id` must handle None
- Pre-backfill rows have null values

---

## 7. Critical Findings

| Finding | Impact |
|---------|--------|
| 17 migrations dated 2026-07-16 (same day) | Schema changes are very recent — stability unknown |
| Largest migration 76KB (national LIMS) | Single migration creates 35 tables — high risk |
| Health Data Warehouse models exist but no routes | Schema without endpoints |
| Financial Engine schema exists (Phase A) but routes deferred to Phase B+ | Schema-only gap |
| National platform tables lack corresponding route handlers | Dead schema |
| No evidence of regular VACUUM/ANALYZE | Performance risk at scale |
