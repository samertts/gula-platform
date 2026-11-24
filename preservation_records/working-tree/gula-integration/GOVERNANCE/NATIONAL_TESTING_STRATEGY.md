# NATIONAL PLATFORM TESTING STRATEGY (unified)

**Repository:** `gula-integration` · **Branch / HEAD:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged) · **Date:** 2026-11-17
**Work item:** W-079 (NAT-P) · **Change control:** CC-010 · **Evidence:** E-062 (new), E-053…E-061 (preserved) · **Status:** strategy delivered; gate closure **BLOCKED / NOT VERIFIED** where evidence is absent.

---

## 0. Governing rule and non-claims

**Rule R (non-negotiable):** no skip, xfail, deletion, suppression or weakening of a test to hide a failure. A skip is permitted only if pre-existing, justified and tracked; it is never a path to a green gate. No full strict-suite rerun without a documented trigger. No test expectation was changed to force a pass in this program.

This strategy maps the required test classes to **paths that actually exist in this repository** and to **records that actually exist**. Presence of a test file is not a pass; a documented pass is not a gate closure; synthetic evidence is not runtime, clinical, security-certified or production evidence. `FINAL_DECISION.md` stays **HOLD**; D-020/D-021 stay **PENDING**.

**Approved command (targeted runs only):**
`cd /home/samertts/workspace/projects/gula-integration/backend && ENV=test PYTHONPATH=.. /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m pytest -q --no-header -p no:cacheprovider <specific_test_files>`

---

## 1. Required test classes → on-disk path → current evidence

| Required class | Existing on-disk path (verified) | Evidence / status | Honest boundary |
|---|---|---|---|
| **Unit** | `backend/tests/unit/test_{lab,sample,dashboard,quality_control,metrics,mobile,admin}_service.py`, `test_nr011_metadata_discovery.py` | E-044 36/0; service suites | unit green ≠ deployed route |
| **Integration** | `backend/tests/integration/test_{identity_bundle,integration_inbox,connector_sdk,connector_registry,reference_services}.py`; `test_comprehensive.py` | E-030 3,447/0/27; E-031 3,480/0/27 | SQLite suite control ≠ migration compatibility (F-063) |
| **Contract / API** | `backend/tests/contracts/test_integration_envelope.py`, `test_error_contract.py`, `test_clinical_gateway_contracts.py`, `blood_bank/test_http_idempotency_contract.py`; `frontend-v3/scripts/verify-contract-governance.mjs` | E-9 exit 0 (prior); 101 frontend calls + 28 verb mismatches classified (F-057/W-041) | criterion 9 NOT MET |
| **Authorization** | `backend/tests/test_{abac,control_plane_authorization,niam_registry_authorization,national_governance_authorization,governance_audit_authorization,governance_anonymous_access,security_store_policy,ai_platform_authorization,lims_quality_authorization,professional_verification_authorization,kill_switch_fail_closed}.py` | E-027/E-029/E-033 115 regressions, 69/69 partition, 0 real gaps; E-057 engineering regression | **D-020 PENDING** — human review absent; 11 residuals R-01…R-11 |
| **Tenant isolation** | `backend/tests/test_tenant_isolation_matrix.py`, `test_lims_tenant_isolation.py`, `test_security_merge_regression_synthetic.py` | E-046 21; E-057 8+4 | F-073 (broader canonical GET/search/link tenant gaps) remains OPEN |
| **Data integrity / migration** | `backend/tests/test_migrations.py`, `test_migration_resilience.py`, `migrations/test_migration_graph_integrity.py`, `unit/test_nr011_metadata_discovery.py` | E-042/E-044/E-045; E-063 (new unregistered-base finding F-085) | 340/664/70 drift; no operational DDL; G-02/G-06 NOT MET |
| **Workflow** | `backend/tests/test_national_bootstrap.py`, `test_identity_workflows_canonical.py`, `test_*_workflow_p0.py`, E-048 batch | E-048 65/65 synthetic | 4 P0 modules fail strict (F-003); strict gate FAILED |
| **Journey E2E** | `backend/tests/test_journey_contract_reliability_synthetic.py` (envelope class) + `frontend-v3/e2e/*.spec.ts` (12 specs) + android `androidTest/` | E-060 23/0 **contract envelope only**; specs exist but no Phase-L/P e2e execution evidence | **Contract-envelope ≠ E2E.** True 7-journey E2E **BLOCKED** — no test integration environment, migration/audit/event gaps |
| **Offline** | `backend/tests/test_offline_sync.py`, `test_offline_conflict_synthetic.py` | E-055 31/0 | crash durability **NOT VERIFIED** (in-memory, F-028/D-012); `CONFLICT_QUARANTINE`, not CRDT |
| **Security regression** | `backend/tests/test_security*.py`, `test_sql_injection*.py`, `test_*authorization*.py`, E-057 merge suite | E-027/E-029/E-033/E-057 | engineering regressions only; not human security certification |
| **Performance** | `backend/tests/test_{stress,performance_budgets}.py`, `kernel_hardening/test_performance_baseline.py` | FINAL_DECISION §6: "not in scope; no benchmarks taken" | **No SLO invented; no production load** |
| **Resilience** | `backend/tests/test_{resilience,chaos_survival,resilience_smoke,break_scenarios,hard_scenarios}.py`, `kernel_hardening/test_{stress,recovery,memory_leaks,chaos_engineering,observability}.py`; E-061 composition | E-049 11/11; E-061 7/0 | bounded primitives only; no SLO/RPO/RTO |
| **Backup restore / DR** | `scripts/backup.sh`, `validate-restore.sh`, `pitr-recover.sh`; `PHASE_C_DATABASE_REHEARSAL_REPORT.md` | E-024 T1–T7 (disposable clones); D-004 policy | **No restore/PITR drill**; RPO/RTO **UNMEASURED**; B-016/B-017 |
| **New this program** | `backend/tests/test_national_capability_registry_reference.py` + `scripts/verify_national_capability_registry.py` | **E-062: 12/0 pytest + 20/20 verifier checks**, 3 negative controls | reference-only index guard; no runtime/engine verification |

---

## 2. New synthetic suite design (E-062 — deterministic, isolated, reproducible, auditable)

- **Deterministic:** `verify()` re-derives counts and compares to a frozen baseline; two consecutive calls return identical dicts (idempotency test).
- **Isolated:** stdlib-only verifier; no DB, no network, no app imports; `tmp_path` for tampered copies.
- **Synthetic:** operating on a checked-in static index of source pointers — no patient data, no device, no clinical environment.
- **Reproducible:** single approved pytest command; 12 tests / 0 failures in 0.69 s.
- **Auditable:** E-062 log contains pytest output + full verifier JSON + exit codes; negative controls prove the checks detect `executing=true`, invented `RUNTIME_VERIFIED`, and dormant activation.
- **Non-claim:** verifies the *registry's honesty invariants*, not any engine's runtime behavior.

---

## 3. Immutable historical gate numbers (preserve verbatim — never rerun/overwrite)

| Evidence | Run | Immutable result |
|---|---|---|
| **E-001** | strict #1, authoritative, migration-only PG16 clone | **753 passed / 119 failed / 0 skipped** (53 modules / 872 tests, exit 1) |
| **E-003** | SQLite `create_all()` control (same 53 byte-identical modules) | **872 passed / 0 failed** (exit 0) — control only, not migration compatibility (F-063) |
| **E-002** | strict #2, repeatability | **750 / 122** (119 reproduced + 3 self-poisoned, F-005) |
| Prior stabilization (E-053…E-061) | 9 synthetic suites | **194 passed / 0 failed** — preserved unchanged |
| This program (E-062) | capability-registry guard | **12 passed / 0 failed** + 20/20 verifier checks |

**Status:** strategy **delivered**; closure of the engineering gaps remains with the owning work items (W-031 fixture leak, W-033 security sign-off, W-034 DR drill, W-041 frontend drift, W-026…W-030 ADR-A waves, F-085 registration decision). No gate was closed and no historical number was altered by this work item.

---

## 4. Rollback (CC-010)

Delete this document and E-062's test/verifier/index/log. No existing test, fixture, conftest, gate or configuration was modified by this program; the prior suites (E-053…E-061) remain byte-stable and unchanged. `FINAL_DECISION.md` stays **HOLD**.
