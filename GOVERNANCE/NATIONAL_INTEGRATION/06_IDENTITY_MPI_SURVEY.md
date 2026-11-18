# WS-01 Survey — Identity & MPI

**Document:** 06 · **Status:** `TESTED` (synthetic) / `BLOCKED` (owner decisions).

## Surface
`backend/app/identity/**`; `backend/app/services/mpi/{matcher,resolver,api,canonical_service,reliability,models,schemas}.py`; `backend/app/services/identity_matching.py`; `backend/app/routes/canonical_patient.py`; `backend/app/routes/compliance.py`; `backend/app/health_core/identity/` (3 modules, 1 test file).

## Verified evidence (prior cycle, unchanged)
- MPI regression suite: **127 passed / 0 failed**.
- Final independent audit: **REJECT** — 13 PASS + 1 documented PASS; 3 open: AUD-02 HIGH (DB UNIQUE / MP-001), AUD-07 MEDIUM (D-MPI-5 / ODR-002), AUD-16 INFO (D-MPI-3/4 / ODR-003).
- Wrong-patient linkage paths AUD-01/02 app-layer remediated; lost-reference paths AUD-04/06/13 remediated.
- Concurrency proof: 6/6 HTTP 200 on 2-connection pool, 0 pool-timeout 503s; 10/10 idempotent NID registration, single ULID/row.
- Compliance audit verifier wired into `GET /compliance/audit-integrity` (admin-only, fail-closed).

## Gaps and classification
| Gap | Classification | Route |
|---|---|---|
| DB `UNIQUE(patient_id)` / `UNIQUE(citizen_id)` not applied | `BLOCKED` | MP-001 package (`05` §2) |
| Re-resolution of corrected identity payloads | `BLOCKED` | ODR-002 (`05` §3) |
| Fork-response policy | `BLOCKED` | ODR-003 (`05` §3) |
| National NHID canonicalization / government interface | `BLOCKED` | §1 legal package |
| Real patient data validation | `NOT IMPLEMENTED` | forbidden by boundary |

## Program action
Synthetic-safe regressions and decision-package linkage only. `REJECT` verdict remains effective; no status escalation.
