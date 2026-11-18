# Phase A — Verified Baseline & Environment Recovery

**Document:** 01 · **Program:** National Integration · **Date:** 2026-11-18
**Status:** `TESTED` (re-executed this program; prior-cycle evidence is labelled in §4). `INDEPENDENTLY VERIFIED` is used only for the protected md5s/HEADs that the independent reviewer re-checked — see `ADVERSARIAL_REVIEW_RECORD.md`.

---

## 1. Repository state (captured before any program write)

| Item | Observed | Expected | Result |
|---|---|---|---|
| `gula-integration` branch | `integration/gula-unification-v1` | same | PASS |
| `gula-integration` HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | unchanged | PASS |
| `gula-integration` status entries | **262** (20 staged renames, 109 modified, 133 untracked, **0 deletions**) | preserve exactly | PASS — no git operation performed in Phase A |
| `gula-platform` branch | `remediate-security-001` | same | PASS |
| `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | unchanged | PASS |
| `gula-platform` status | 0 entries | clean | PASS |

> **Discrepancy note:** the pre-reset checkpoint recorded 606 status entries (20 staged, 477 untracked). After the environment reset the tree shows 262 (20 staged, 109 modified, 133 untracked). HEAD is identical and **0 deletions** are present. This is recorded, not "corrected" — no `add`/`reset`/`clean`/`checkout` was run, and all pre-existing modified and untracked files remain in place.

## 2. Environment recovery

The pinned toolchain `/tmp/opencode/mpi-venv` and all `/tmp/opencode/prodready/{integration_gate.sh,verify_final.sh,demo_production_readiness.py}` artifacts were destroyed by an environment reset before this phase.

**First recovered equivalent:** `/home/samertts/workspace/projects/gula-platform/.venv/bin/python` — Python 3.12.13, pytest 9.1.1 — used for the first 773 re-run (11.54 s).

**Complete recovered toolchain (used for all final evidence):** `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin` — Python **3.12.13**, pytest **9.1.1**, ruff **0.16.0**, mypy **2.3.0**, alembic **1.18.5**, `signxml` present. All mandated quality gates were re-executed with this toolchain.

**Re-executed gate commands:**

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
V=/home/samertts/workspace/projects/gula-platform/backend/.venv/bin
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  $V/python -m pytest tests/health_core -q --tb=short
# → 773 passed, 1 warning in 13.41s  [exit=0]
$V/ruff check app/health_core tests/health_core
# → All checks passed!  [exit=0]
ENV=test RUNTIME_MODE=test PYTHONPATH=.:.. $V/mypy app/health_core --ignore-missing-imports
# → Success: no issues found in 75 source files  [exit=0]
ENV=test RUNTIME_MODE=test PYTHONPATH=.:.. $V/python -m pytest tests/ --collect-only -q
# → 4675 tests collected in 22.55s  [0 errors — missing signxml resolved; +31 from new registry-integrity tests (20 at round 1, +11 negative cases)]
```

The single pytest warning is the pre-existing third-party `StarletteDeprecationWarning` from `fastapi/testclient.py` (httpx/starlette), not a Health Core warning. With the earlier incomplete venv, 12 collection errors occurred, all `ModuleNotFoundError: signxml` — an **environmental** dependency gap, not a code defect; the complete toolchain resolves all 12.

## 3. Governance evidence integrity (md5, unchanged)

| File | md5 | Verdict | Status |
|---|---|---|---|
| `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` | HOLD (md5 unchanged) | `INDEPENDENTLY VERIFIED` |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` | REJECT (md5 unchanged) | `INDEPENDENTLY VERIFIED` |
| `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` | REJECT source (md5 unchanged) | `INDEPENDENTLY VERIFIED` |

Basis: md5s re-read this program and independently re-checked by the adversarial reviewer, 2026-11-18 (`ADVERSARIAL_REVIEW_RECORD.md`). No original file was edited; the verdicts remain HOLD / REJECT.

## 4. Carried evidence from the completed Production Readiness Acceleration Program

| Evidence | Result | Classification |
|---|---|---|
| 10/10 adversarial findings remediated and re-verified (F-01…F-05, L-1…L-3, I-1, I-2) | all closed with strict regressions | `TESTED` (carried prior-cycle evidence) |
| Preservation / ownership gate | 24/24 PASS — `VERDICT: PASS` | `TESTED` (carried prior-cycle evidence) |
| Reproducible six-workstream synthetic demo | all assertions passed | `TESTED` (carried prior-cycle evidence) |
| Eight classified final reports `FINAL_00`…`FINAL_07` | complete in `GOVERNANCE/PRODUCTION_READINESS/` | `IMPLEMENTED` (carried prior-cycle evidence) |
| `factory.py` / `main.py` Health Core references | 0 / 0 — no production activation | `TESTED` (carried prior-cycle evidence) |

## 5. Source-surface inventory (direct survey, this phase)

### 5.1 Health Core implementation (Python modules per surface)

| Surface | Modules | Test file count |
|---|---:|---:|
| authorization | 6 | 3 |
| clinical | 8 | 5 |
| lab | 7 | 5 |
| fhir | 6 | 3 |
| terminology | 8 | 2 |
| reliability | 11 | 6 |
| client_integration | 6 | 3 |
| integration | 6 | 6 |
| identity | 3 | 1 |
| contracts | 8 | 6 |
| common | 5 | — |

Total Health Core test files: **44**; executed tests: **773**.

### 5.2 National surfaces located (for WS-01…WS-07)

- Identity/MPI: `backend/app/identity/`, `backend/app/services/mpi/{matcher,resolver,api,canonical_service,reliability,models,schemas}.py`, `backend/app/services/identity_matching.py`, `backend/app/routes/canonical_patient.py`, `backend/app/routes/compliance.py`.
- FHIR: `backend/app/health_core/fhir/`, `backend/app/capabilities/fhir_interoperability/`, `backend/app/national/fhir/`, `backend/app/fhir/`.
- Terminology: `backend/app/health_core/terminology/`, `backend/app/national/reference/` (ICD/LOINC/SNOMED/UCUM).
- Reliability/offline: `backend/app/health_core/reliability/`, offline sync engine (`tests/test_offline_sync.py`).
- Client: `backend/app/health_core/client_integration/`; frontend `frontend-v3/` contracts.
- National domains: `backend/app/domain_platform/`, `backend/app/national/`; inventory `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (18 services).

## 6. Phase A verdict

Baseline is **reproducible and preserved**. The suite is green at 773 and all protected governance md5s are unchanged. No repository write was performed before this document set. Phase A is eligible to close once the remaining documents (`02`…`14` + registry) are recorded — which this document set does.

**No production claim is made.** Phase A status: `IMPLEMENTED`; the baseline results are `TESTED`. Program phases C and E are `NOT IMPLEMENTED`; B and D are `TESTED` (see `status_registry.json`).
