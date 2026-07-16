# Identity Platform — Architecture

## Overview

The GULA Identity Platform provides production-grade national identity services
for tens of millions of Iraqi citizens. It is designed for online and offline
operation, supporting all identity types through a unified canonical model.

## Core Components

### Identity Governance Service
- **File**: `backend/app/services/governance/identity_governance.py`
- **Persistence**: `backend/app/governance/models/identity.py` → `gov_identity_records` table
- **Repository**: `backend/app/governance/repositories/identity_repository.py`
- Supports: citizen, foreigner, visitor, newborn, unknown patient, resident

### Break Glass Service
- **File**: `backend/app/national/security/break_glass.py`
- **Persistence**: `backend/app/governance/models/identity.py` → `gov_break_glass_accesses`
- **Repository**: `backend/app/governance/repositories/break_glass_repository.py`
- Emergency access with audit trail and automatic expiry

### Identity Merge Engine
- **File**: `backend/app/services/governance/merge_engine.py`
- **Persistence**: `backend/app/governance/models/identity.py` → `gov_merge_proposals`
- **Repository**: `backend/app/governance/repositories/merge_repository.py`
- Confidence scoring, proposal workflow, approval/rejection

### Citizen Model (MPI)
- **File**: `backend/app/services/mpi/models.py` → `citizens` table
- **File**: `backend/app/models/canonical_patient.py` → `canonical_patients` table
- Identity claims bridge LIMS patients to national citizens

### Offline Sync Engine
- **File**: `backend/app/services/offline_sync_service.py`
- CRDT-compatible vector clocks
- Conflict detection and configurable resolution strategies
- Encrypted local cache with `EncryptedSyncStore`

### Patient Matcher (Fellegi-Sunter)
- **File**: `backend/app/services/mpi/matcher.py`
- Deterministic: NID hash exact match → score 1.0
- Probabilistic: phone, DOB, name Jaro-Winkler, gender, family ID
- Thresholds: auto-match ≥ 0.90, review ≥ 0.70

## Identity Types

| Type | Method | Documents |
|------|--------|-----------|
| Citizen | `register_citizen()` | National ID |
| Foreigner | `register_foreigner()` | Passport, Visa |
| Visitor | `register_visitor()` | Passport, Visa |
| Newborn | `register_newborn()` | Birth Certificate |
| Unknown | `register_unknown_patient()` | None (emergency) |
| Resident | `register_resident()` | Residency |

## Data Flow

1. Patient registers → MPI resolver blocks against citizens table
2. Matcher scores → auto-claim, review, or new citizen
3. CanonicalPatient bridges LIMS Patient ↔ National Citizen
4. Offline sync queues operations, resolves conflicts via vector clocks
5. All mutations emit hash-chained audit events

## Database Tables

- `citizens` — Canonical national identity (48M scale)
- `identity_claims` — Lab→Citizen bridge
- `mpi_merge_audit` — Append-only merge ledger
- `canonical_patients` — Unified patient view
- `patient_links` — LIMS patient to canonical
- `citizen_links` — Citizen to canonical
- `gov_identity_records` — Governance identity records
- `gov_break_glass_accesses` — Emergency access log
- `gov_merge_proposals` — Merge workflow proposals
- `consents` — Patient consent grants

## Migrations

47 Alembic migrations covering identity, security, clinical, and governance:
- `20260716_0014_governance_identity_persistence.py`
- `20260716_0015_auth_security_tables.py`
- `20260716_0016_canonical_patient_unification.py`
- `20260413_0001_mpi_citizen_registry.py`
