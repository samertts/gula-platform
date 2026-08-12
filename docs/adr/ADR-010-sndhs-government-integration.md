# ADR-010: SNDHS-lite Government Integration

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, Product Manager, Compliance Officer

## Context

The Iraqi Ministry of Health requires healthcare providers to integrate with the National Health Data System (SNDHS — النظام الوطني للبيانات الصحية). GULA must support national ID collection, health ID assignment, visit tracking, and enhanced audit logging while maintaining tenant isolation and data security.

## Decision

Implement SNDHS-lite integration in phased approach, with feature flags controlling rollout and data backfill required before enabling on existing deployments.

### Phase 1 (Complete)
- **National ID:** `patients.national_id` — AES-256 encrypted at rest, indexed
- **Health ID:** `patients.sndhs_health_id` — SNDHS-assigned health identifier
- **Visits:** `visits` table for clinical episode tracking
- **Order-Link:** `lab_orders.visit_id` linking orders to visits
- **Enhanced Audit:** Audit log v2 with SNDHS correlation fields
- **Dual-Read:** All code gracefully handles `None` for pre-backfill rows

### Feature Flag Control
- `SNDHS_ENABLE_VISITS` (default: false) — Visit tracking
- `SNDHS_ENABLE_NATIONAL_ID` (default: false) — National ID fields
- Both require backfill before enabling on existing data

### Backfill
- Script: `scripts/sndhs_phase1_backfill.py`
- Rollback: `scripts/sndhs_phase1_rollback.sql` + `scripts/sndhs_phase1_disable_flags.sh`

## Alternatives Considered

### 1. Full SNDHS Integration in One Release

**Pros:** Single deployment, immediate compliance.
**Cons:** Higher risk, complex migration, cannot be rolled back easily.
**Rejected because:** Phased approach allows incremental validation and reduces risk.

### 2. Separate SNDHS Service

**Pros:** Independent deployment, decoupled from main platform.
**Cons:** Network overhead, data synchronisation complexity, dual storage.
**Rejected because:** National ID and health ID are core patient data that belong in the primary database.

### 3. External Identity Provider

**Pros:** SNDHS-managed identity, reduced liability.
**Cons:** Network dependency for every patient lookup, offline complications.
**Rejected because:** Laboratories need offline capability and local ID management.

## Consequences

### Positive
- Iraqi Ministry of Health compliance achieved
- National IDs encrypted at rest (AES-256) — not stored in plaintext
- Feature flags allow safe, gradual rollout across tenants
- Rollback scripts provide safety net
- Dual-read pattern ensures backward compatibility

### Negative
- Additional schema complexity (visits table, nullable columns)
- Backfill required before enabling on existing deployments
- Enhanced audit log increases storage requirements
- Dual-read `None` handling adds boilerplate

### Neutral
- SNDHS integration follows existing patterns (encryption, audit, feature flags)
- Government APIs can be added in Phase 2 without architectural changes
- Compliance documentation needed for certification

## References
- `docs/sndhs/` — SNDHS-lite documentation (22 files)
- `docs/sndhs/phase1/RUNBOOK.md` — Production deployment guide
- `scripts/sndhs_phase1_backfill.py` — Data backfill
- `scripts/sndhs_phase1_rollback.sql` — Rollback SQL
- `backend/migrations/versions/20260505_0001_sndhs_phase1_extend_patients.py` — Migration
- `backend/app/core/sndhs_flags.py` — SNDHS deployment flags
- `backend/app/core/feature_flags.py` — Per-tenant feature flags
- ADR-003: Multi-Tenant Isolation via lab_id
