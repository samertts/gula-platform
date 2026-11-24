# MPI-06 Implementation Report — Cross-Component Reference Inventory

**Status:** `PARTIAL` (inventory completed; ownership changes require unresolved owner decision)
**Date:** 2026-11-18
**Scope:** Inventory every reference to MPI citizen/claim/merge state across components and classify ownership. **No reference was repointed; no schema was changed.**

---

## 1. Work done

Completed a deterministic, read-only inventory of merge-related references across `backend/app`, `shared`, `frontend-v3/src` and `backend/migrations/versions`. No file was changed.

Classification applied:

| Class | Definition | Examples found |
|---|---|---|
| **FK (hard reference)** | SQL FK to `citizens.id` | `backend/migrations/versions/20260413_0001_mpi_citizen_registry.py` (4 `ForeignKey("citizens.id", ondelete="RESTRICT")`), `20260716_0016_canonical_patient_unification.py` (citizen_id → citizens.id) |
| **Soft reference (in-app `merged_into_id`)** | Application column following the merge chain | `backend/app/health_data/mdm/models.py`, `mdm/service.py`, `backend/app/identity/services/citizen_relationship_service.py`, `backend/app/national/domain/citizen.py`, `shared/identity/domain.py` |
| **MPI resolver/ledger** | Owning service itself | `backend/app/services/mpi/{api,models,resolver}.py` |
| **External identifier / hash** | `national_id_hash`, `nid_hash`, `health_id` | `backend/app` (56 / 22 / 32 files respectively), `shared/identity/{domain,service}.py`, `frontend-v3/src/{api/workspaceScopedReads.ts,types/models.ts}` |
| **Canonical-bridge reference** | `canonical_id` | `backend/app/services/mpi/canonical_service.py`, `routes/canonical_patient.py`, `national/api/routes/interop.py`, `radiology/clinical_read_gate.py`, `ehr/clinical_read_gate.py`, `models/canonical_patient.py`, `health_data/canonical/models.py` |
| **Unknown / unresolved ownership** | No authoritative owner recorded | **None changed** — every observed reference mapped to a known class above |

## 2. Critical semantic boundary finding

**MPI `citizens` and national `national_citizens` are distinct semantic domains and MUST NOT be merged:**

- `backend/app/services/mpi/models.py:48` → `__tablename__ = "citizens"` (integer `id` primary key).
- `backend/app/national/domain/citizen.py:12` → `__tablename__ = "national_citizens"` (`String(26)` ULID id, `ix_national_citizens_merged` on `merged_into_id`).
- National FKs target `national_citizens.id` (e.g. `national/domain/{visit,patient,health_card,guardian}.py`, `version 20260811_0002_citizen_relationship_foundation.py`), **not** MPI `citizens.id`.

Treating these as one identity space would be a data-model corruption; no such conflation was introduced.

## 3. Reference counts (evidence)

| Token | Files (backend/app) | Files (migrations) | Other |
|---|---|---|---|
| `merged_into_id` | 7 (+ shared/identity, + migration) | 1 | 9 files total |
| `citizen_id` | 114 | 8 | 4 frontend-v3/src |
| `canonical_id` | 7 | 1 | — |
| `patient_id` | 256 | 28 | 8 frontend-v3/src, shared/sdk/domain/device/cli |
| `national_id_hash` | 56 | 8 | 2 shared/identity, 2 frontend-v3/src |
| `nid_hash` | 22 | 4 | — |
| `health_id` | 32 | 6 | 4 frontend-v3/src, shared/identity/domain |

`citizen_id` by backend module: national 38, citizen_platform 18, ehr 11, national_data 9, care_continuum 8, identity 7, services 6, routes 5, blood_bank 4, pharmacy 3, governance 3, models 2.

## 4. Commands (read-only, exit 0)

```
grep -rIl --include=*.py --include=*.ts --include=*.tsx 'merged_into_id|citizen_id|canonical_id|patient_id|national_id_hash|nid_hash|health_id' \
  backend/app shared frontend-v3/src backend/migrations
grep -rInE 'ForeignKey\("(citizens|identity_claims)|REFERENCES (citizens|identity_claims)' backend/migrations/versions
grep -rIn '__tablename__.*citizen' backend/app/services/mpi/models.py backend/app/national backend/app/citizen_platform
```

All commands were read-only; exit 0.

## 5. Residual risks / reason for `PARTIAL`

- ~90 soft references across domains still follow `merged_into_id` without a central ownership policy. Repointing them is **not** authorized under D-MPI-3 (which also requires legal review).
- Unmerge is **not implemented**: a fully reversible history model and a proven-safe rollback mechanism do not exist. This remains `BLOCKED` pending D-MPI-3.
- `verify_merge_audit_chain()` remains detection-only (MPI-08); no automatic cross-domain correction occurs on a detected fork.

## 6. Acceptance criteria

| Criterion | Result |
|---|---|
| Complete reference inventory produced | PASS |
| Each reference classified (FK / soft / ledger / external id / unknown) | PASS |
| MPI `citizens` ≠ national `national_citizens` documented | PASS |
| Unknown-ownership references changed | **NONE** (none found; none changed) |
| Cross-domain repointing implemented | **PARTIAL — not done**, blocked by D-MPI-3 |
| Production readiness claimed | **NO** — explicitly not claimed |
