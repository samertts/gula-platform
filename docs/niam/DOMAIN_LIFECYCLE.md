# DOMAIN_LIFECYCLE.md

> **PROGRAM-STABLE-004** — Domain Lifecycle (Phase 5).
> Generated: 2026-08-06T04:28:40+00:00

## Supported Operations

Every Domain supports: **Installation, Activation, Suspension, Upgrade, Rollback, Backup, Restore, Health Check, Metrics, Independent Versioning, and Independent Certification.**

## State Machine

| State | Transitions |
|---|---|
| installed | active, retired |
| active | suspended, upgrading, failed |
| suspended | active, retired, upgrading |
| upgrading | active, suspended, failed |
| failed | installed, retired |
| retired | — |

## Operations

- **install** — register the Domain blueprint, create the initial version, record the install audit event.
- **activate** — make the Domain operational (only from installed/suspended/upgrading).
- **suspend** — halt the Domain while preserving all data (from active).
- **upgrade** — publish a newer SemVer; backward-compatibility is enforced.
- **rollback** — restore the previous certified version.
- **backup / restore** — point-in-time snapshots with a restore operation.
- **health check** — state, version, backups, health status.
- **metrics** — state, version, transition count, backup count.
- **certification** — run the Phase 7 certification for this Domain.

## Audit Trail

Every lifecycle transition is recorded in `niam_domain_lifecycle_events` (immutable audit). No transition happens without an audit record.

## Current Domain States

| Domain | State | Version |
|---|---|---|
| laboratory | installed | 1.0.0 |
| pharmacy | installed | 1.0.0 |
| radiology | installed | 1.0.0 |
| hospital | installed | 1.0.0 |
| blood_bank | installed | 1.0.0 |
| public_health | installed | 1.0.0 |
| insurance | installed | 1.0.0 |
| emergency | installed | 1.0.0 |
| research | installed | 1.0.0 |
| citizen_portal | installed | 1.0.0 |
| provider_portal | installed | 1.0.0 |
