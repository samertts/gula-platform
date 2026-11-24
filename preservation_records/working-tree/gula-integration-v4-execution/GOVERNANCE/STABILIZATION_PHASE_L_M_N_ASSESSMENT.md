# Stabilization Phases L / M / N — Bounded Read-Only Assessment

**Date:** 2026-11-17 · **Repository:** `gula-integration` · **Owner authorization:** post-GECS stabilization (D-023)
**Work items:** W-060 (Phase L — multi-level test strategy), W-061 (Phase M — data integrity & migration readiness, **no operational DDL**), W-062 (Phase N — backup/DR plan + RPO/RTO honesty).

## 1. Header — purpose, scope, verdict

**Purpose.** Produce one bounded, evidence-based assessment of the three work items so the stabilization cycle can proceed without repeating closed GECS work, inventing measurements, or touching operational surfaces.

**Scope — READ-ONLY / ASSESSMENT ONLY.** This document is a plan-and-evidence index. **No code / config / DB / test / migration change** was made. No test was run (pytest / vitest / any test command not executed by this task). No SQL, no DDL, no `alembic` command, no `alembic stamp`, no connection to the operational `gula` database. No commit, add, push, merge, PR, deploy, or destructive git operation. No real patient data used or opened. No synthetic run was executed here; all cited results are pre-existing records.

**Verdict:** `GOVERNANCE/FINAL_DECISION.md` remains **HOLD** (criteria 5, 7, 8, 9 NOT MET). **D-020 and D-021 remain PENDING_APPROVAL.** No gate status changes. All findings/registries unchanged. Historical evidence is preserved, never re-run or overwritten.

**Verification method:** read/grep/glob only. Paths below were confirmed to exist on disk; figures were confirmed in the named canonical registry/report. Anything not confirmed is labelled **NOT VERIFIED**.

---

## 2. Phase L — Multi-level test strategy (W-060)

**Strategy source alignment:** `docs/constitution/20_TESTING_POLICY.md` (test pyramid, deterministic tests, every migration round-trip tested, CD rules tested) and `FRONTEND_BACKEND_INTEGRATION_TEST_PLAN_AR.md` §2 (layer → proof → tool → environment). This document maps that policy to **paths that actually exist in this repo**; it does not restate them as achieved coverage.

**Governing rule R (applies to every level below):** **no skip / xfail / deletion / weakening is used to hide a failure.** A skip is permitted only if pre-existing, justified and tracked (e.g. the 27 skips in E-030/E-031); it is never a path to a green gate. Gate G-08 explicitly lists "skipping/xfailing workflow tests" and "claiming pass from SQLite control" as failure conditions (`PHASE_GATES.md:124-126`); `W1_CHECKPOINT.md` §11 records that no test was deleted, skipped, weakened or rewritten.

| Level | What actually exists (verified paths) | Evidence (existing record) | Gap / honest boundary | Rule |
|---|---|---|---|---|
| **L0 static / lint** | `pyproject.toml` (`[tool.mypy]` at :49, ruff config), `backend/pyproject.toml` (`requires-python >=3.12`), `frontend-v3/eslint.config.js`; governance scripts `frontend-v3/scripts/verify-{integration-boundary,frontend-unification,contract-governance,data-source-governance}.mjs`, `frontend-v3/scripts/data-source-inventory.mjs` | E-020: scoped ruff 35, mypy 71 (tracked, not masked); FINAL_DECISION §2 E-7…E-11 all exit 0; E-032/F-055: 0 dependency advisories | Static debt is *recorded*, not eliminated (F-058); frontend gates in E-035 are typecheck/lint/vitest/build/audit, **not** a Phase-L rerun | R |
| **L1 unit** | `backend/tests/unit/` — `test_{lab,sample,dashboard,quality_control,metrics,mobile,admin}_service.py`, `test_nr011_metadata_discovery.py`; broad `backend/tests/test_*.py` | E-044: 36 passed / 0 failed (22 adjacent + 14 new NR-011 regressions); FINAL_DECISION §3 service tests | Unit green proves the *unit*, not the deployed route (F-061: 4 routes still inline, 2,216 LOC duplicated) | R |
| **L2 service / integration** | `backend/tests/integration/` — `test_identity_bundle.py`, `test_integration_inbox.py`, `test_connector_sdk.py`, `test_connector_registry.py`, `test_reference_services.py`; `backend/tests/test_pricing_service.py`, `test_financial_phase_b.py`, `test_comprehensive.py` | E-030 3,447/0/27; E-031 3,480/0/27 (current count record); both on suite-configured SQLite | Full-suite green is not migration compatibility (F-063); no Phase-L rerun performed here | R |
| **L3 API / contract** | `backend/tests/contracts/test_integration_envelope.py`, `backend/tests/test_error_contract.py`, `test_clinical_gateway_contracts.py`, `backend/tests/blood_bank/test_http_idempotency_contract.py`; `frontend-v3/scripts/verify-contract-governance.mjs` | FINAL_DECISION §2 E-9 exit 0; criterion 9 requires OpenAPI diffed before/after each wiring change | 101 unresolved frontend calls + 28 verb mismatches classified but not dispositioned (F-057/W-041); criterion 9 NOT MET | R |
| **L4 security** | `backend/tests/test_{security,abac,tenant_isolation_matrix,control_plane_authorization,niam_registry_authorization,national_governance_authorization,governance_audit_authorization,governance_anonymous_access,security_store_policy,ai_platform_authorization,lims_quality_authorization,professional_verification_authorization,kill_switch_fail_closed}.py`; `backend/tests/security/test_security_headers.py` | E-027/E-029/E-033: 115 regression tests, 69/69 partition, 0 real gaps; E-057 engineering regression | **D-020 PENDING_APPROVAL** — human review + PD sign-off absent (B-005/W-033); 11 residuals R-01…R-11 open; fixes uncommitted/unreviewed | R |
| **L5 clinical safety** | `backend/tests/test_{clinical_safety,chronic_care_safety,clinical_command_guard_p0,icu_lab_workflow_p0,emergency_surgery_workflow_p0,pharmacy_radiology_workflow_p0,pharmacy_pos}.py`, `test_cds_failsafe_synthetic.py`, `test_mdm_patient_identity_synthetic.py` | E-001 §clinical verdicts; E-054 11/11 synthetic CDS fail-safe; `clinical_safety` 33/33, `patient_card` 15/15, `command_guard_p0` 5/5 under control | **D-021 PENDING_APPROVAL** — 4 P0 modules fail strict (F-003); referrals/`care_continuum` untested (F-007); national CDS route unmounted (F-068); synthetic ≠ clinical certification | R |
| **L6 migration / schema** | `backend/tests/test_migrations.py`, `test_migration_resilience.py`, `backend/tests/migrations/test_migration_graph_integrity.py`, `backend/tests/unit/test_nr011_metadata_discovery.py`; disposable rehearsal only | E-042/E-044/E-045 (NR-011: `alembic check` reaches ADR-A diff, 36/36, autogen == probe C); E-024 T1–T5; single head `20261114_0006` | 340 missing tables / 664 drift columns / 70 insert-breaking remain (§3); no operational DDL here; drift tests not green | R |
| **L7 E2E / journey** | `backend/tests/blood_bank/test_wave1_lifecycle_e2e.py`, `backend/tests/test_national_bootstrap.py`, `test_pharmacy_pos.py`; `frontend-v3/e2e/` — `auth, patients, orders, results, samples, billing-insurance, financial-governance, fhir, navigation, mobile-layout, dark-mode, reports-safe-empty .spec.ts` (12 specs verified); `mobile/android/app/src/androidTest/` (`NavigationTest.kt`, `SyncIntegrationTest.kt`, `PatientDaoTest.kt`) | E-048 (65/65 workflow batch, synthetic); E-024 §13.4 strict P0 verdicts | Specs exist on disk; **no Phase-L E2E execution evidence verified** for them. Strict P0 journeys still fail; 7-journey synthetic suite W-058 NOT_STARTED | R |
| **L8 resilience / performance** | `backend/tests/test_{stress,resilience,chaos_survival,performance_budgets,disaster_recovery,resilience_smoke,break_scenarios,hard_scenarios}.py`; `backend/tests/kernel_hardening/test_{stress,performance_baseline,recovery,memory_leaks,chaos_engineering,observability}.py` | E-049 11/11 kernel batch; FINAL_DECISION §6: "Performance / load / soak — not in scope; no benchmarks were taken" | No SLO exists and none is invented here; W-059 bounded reliability tests NOT_STARTED; no production load | R |
| **L9 governance / AI-governance** | `backend/tests/test_{governance,persisted_identity_governance,national_governance_authorization,governance_audit_authorization,governance_anonymous_access}.py`, `backend/tests/identity/test_identity_governance.py`; GECS registries under `GOVERNANCE/GECS/`; synthetic engine suites `test_engines_rules_policy_expression_synthetic.py`, `test_certification_engine_synthetic.py` | E-046…E-052 (740 passed / 0 failed, 7 synthetic batches); E-058 34/34; E-059 30+4; W-043 CLOSED | Evidence indexed against gates is **not** a gate closure; 5 engine artifacts made 0 runtime/production claims; certification output never used as release evidence (F-072) | R |

### 2.1 Immutable historical gate numbers — preserve verbatim

These are historical records. **Never re-run, never overwrite, never substitute a different corpus** (`EVIDENCE_REGISTRY.md` rules; `DUPLICATE_PREVENTION.md`; F-060 declared lapse).

| Evidence ID | Run | Immutable result |
|---|---|---|
| **E-001** | strict #1, authoritative, migration-only PG16 clone | **753 passed / 119 failed / 0 skipped** (53 modules / 872 tests; exit 1) |
| **E-003** | SQLite `create_all()` **control** (same 53 byte-identical modules) | **872 passed / 0 failed** (exit 0) — control only, **not** migration compatibility (F-063) |
| **E-002** | strict #2, repeatability on same clone | **750 / 122** — 119 reproduced + 3 self-poisoned (F-005 fixture leak) |

*Label-integrity note:* the W-060 work-item shorthand attaches "872/0" to E-003 (correct — control) and calls "750/122" the control; the canonical `EVIDENCE_REGISTRY.md` records **750/122 as E-002 (strict repeatability)** and E-003 as the 872/0 control. All three numbers are preserved exactly; this assessment keeps the registry's ID-to-result mapping rather than silently relabelling a mis-stated shorthand.

**Status — W-060:** **BLOCKED / NOT VERIFIED except as documentation.** The 10-level strategy and its on-disk mappings are delivered by this document, but no new test, gate result, or coverage claim is produced, and no skip/xfail policy change is authorized here. Historical numbers retained; no run performed. Closure of the *engineering* gaps listed above remains with the owning work items (W-031…W-035, W-040, W-041, W-058, W-059, W-033).

---

## 3. Phase M — Data integrity & migration readiness (W-061)

**Constraint:** **NO operational DDL. NO `alembic stamp`. No DB connection to `gula`.** Readiness is documentation of existing evidence only. Per `CHANGE_CONTROL.md:44-48`, ADR-A is approved *as a strategy* but individual migration revisions are wave work (W-026…W-030), explicitly **not** part of this task.

### 3.1 Drift / gap summary (figures matched to canonical sources)

| Measure | Value | Source |
|---|---|---|
| Missing ORM tables (per-base sum) | **340** (756 ORM / 416 present) | E-008, E-013, `W1_CHECKPOINT.md` §5 |
| Column drift | **82 tables / 664 columns** missing | E-009, `W1_CHECKPOINT.md` §5 |
| Insert-breaking drift columns | **70** of the 664 (ORM NOT NULL, no default) | E-011, F-001 |
| NOT NULL without default | **1,114** columns across **339 of 340** missing tables | E-011 |
| Migrated public tables | **433** at revision **`20261114_0006`** | E-024, E-043, `W1_CHECKPOINT.md` §2 |
| Migration graph | **single head `20261114_0006`**, 107 revisions, 0 missing parents, 0 cycles | `MIGRATION_RECONCILIATION_MATRIX.md` §5.2; `UNIFICATION_BLOCKERS.md` §3 |
| Schema fingerprint | **`3b2d9499d019503bf1ff5644f713cd5f272705f544862d8022887a516f973568`** — identical ×3 (before / after / rerun) ⇒ **zero DDL executed** | E-015, E-043 |
| FK topology | 573 declared edges = 485 → missing tables + 88 → present | E-010 |
| Strict functional result | **753/119**; 4 P0 workflow modules fail on migrated schema (all green under control) | E-001, F-003, `W1_CHECKPOINT.md` §3 |
| Discovery debt | 5 of 17 registered bases contribute **0 tables** (`NursingBase`, `PharmacyBase`, `RadiologyBase`, `NHDWBase`, `CitizenPlatformBase`) | F-065, E-045 |
| Ownership | dual `national_facilities`: 6-col `clinical_scope` (DB-matching) vs 28-col dormant; 3 downgrade-residual tables unowned | F-014, F-013, ADR-B (W-038) |
| Successful rehearsals (disposable clones only) | forward upgrade 405→433 tables (17 s, 50 rows checksum-identical); full teardown `downgrade base`→`upgrade head` 25 s/81 s, identical fingerprint; determinism PASS | E-024 T1/T2/T4; `PHASE_C_DATABASE_REHEARSAL_REPORT.md` |
| Unsafe path | partial rewind to `20260815_0022`: exit 0 but 2 version rows + 7 residual tables (412 vs 405) — **must never be a rollback runbook** | E-024 T3, F-012, B-010, D-004 |

Denominator discipline (F-024): **426** (per-context union), **340** (per-base), **284** (probe-C add_table) are different measurements; they are never summed or substituted. Historical/corrected figures retained: hospital "13" → 12 (F-015/E-034) and the §8.1 correction in E-024; auth walk 2,066/67 → 2,064/69 (F-062).

**Status — W-061:** **BLOCKED / NOT VERIFIED.** Drift and gaps are documented, not remediated. Readiness cannot be claimed pending (a) ADR-A waves W-026…W-030 adding/verifying tables and columns with per-wave strict subsets, (b) ADR-B ownership record W-038, (c) W-036 type reconciliation, (d) a production-like snapshot (B-017/W-039 — only 51 rows exist), (e) repeatable strict suite at 872/872. Release criterion 5 (`MIG-EXISTING`) stays **NOT MET**; G-02/G-06 stay NOT MET. **No table was dropped, no column added, no revision authored, no stamp applied by this task.**

---

## 4. Phase N — Backup / disaster-recovery plan and RPO/RTO honesty (W-062)

### 4.1 Evidence that exists

| Item | Verified record | Honest reading |
|---|---|---|
| Rehearsal report | E-024 = `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md` (T1–T7) | Migration rehearsal on **disposable clones**, not a backup/restore/PITR drill |
| Rollback tooling present | `scripts/backup.sh`, `scripts/validate-restore.sh`, `scripts/pitr-recover.sh` (all confirmed on disk) | **Existence ≠ drill** (G-09); ADR §A7: "Tooling exists, not verified here" / "untested here" |
| Verified closest equivalent | `downgrade base` (25 s) → `upgrade head` (81 s), 433 tables, identical fingerprint (E-024 T4) | Schema reversibility, **not** measured recovery time or data-loss bound |
| Readiness decision | D-004 **APPROVED 2026-11-17** (`DECISION_REGISTRY.md` §A): snapshot restore (once drilled) or `downgrade base`+`upgrade head`; partial downgrade **prohibited**; **no RPO/RTO claim without measurement** | Policy exists; drill does not |
| Blockers | **B-016** RPO/RTO unmeasured — "restore/PITR drills never run here"; **B-017** no production-like snapshot (51 rows) | Both OPEN (`BLOCKER_REGISTRY.md` §C) |
| Work item | **W-034** restore drill + RPO/RTO measurement, NOT_STARTED, needs separate operational authorization, disposable clones only | W-062 cannot self-authorize a drill |

### 4.2 RPO / RTO — UNMEASURED / NOT VERIFIED. No numbers published.

No restore or PITR drill in this repository produced a figure. Sources agree: F-017 ("RPO and RTO **not measured** — no drill in this repository produced a figure"); B-016; E-022/FINAL_DECISION §6 ("Disaster recovery — Not re-run in this cycle"); `ARCHITECTURE_DECISION_PACKAGE_W1.md` §A7 — RPO **NOT MEASURED**, RTO **NOT MEASURED**, and "**no RPO/RTO number may be published until a drill measures it**"; `CHANGE_CONTROL.md:50` — "RPO/RTO numbers still may not be published (unmeasured)".

A prior document, **`platform/reports/national-certification/READINESS_SCORE.md`**, states **"RPO 1hr, RTO 4hr"**. This is quoted **only as a prior unverified claim** (F-018; alias F-064; package §A2.6/§A7), explicitly **not adopted** as evidence and not repeated as fact. No other measured value was found; a broader search found no drill measurement in this repository. Therefore: **RPO = UNMEASURED / NOT VERIFIED; RTO = UNMEASURED / NOT VERIFIED.** This assessment refuses to publish RPO/RTO numbers.

### 4.3 Requirements for a future disposable-environment DR drill

1. **Separate operational authorization** (W-034), owner = Platform Operations + DBA/QA; never authorized by W-062 itself.
2. **Disposable clone only** (e.g. `CREATE DATABASE … TEMPLATE …`): never the operational `gula` database, no production data.
3. **Sequence:** take/preserve backup → verify backup file exists and is restorable → **drop** the scratch DB → restore from backup → **verify** table count (**433**), revision **`20261114_0006`**, schema fingerprint vs `3b2d9499…`, and row/data checksums.
4. **PITR drill** (`scripts/pitr-recover.sh --time …`) with row-count reconciliation against the WAL archive; record outcome honestly, including failure.
5. **Measure, do not estimate:** RPO from actual backup interval / WAL segment age; RTO end-to-end from restore start to verified service. If not measured, retain the literal string **UNMEASURED**.
6. **Prohibitions:** no partial downgrade in the runbook (F-012/B-010); never treat exit-0 as state equivalence (F-012/T3 counter-example); no invented SLOs; no production load.
7. **Evidence hygiene:** results get a **new E-ID** with independent result; historical E-024/E-001/E-003/E-002 are never overwritten; record deviation/failure rather than hiding it (F-060 lesson).

**Status — W-062:** **BLOCKED / NOT VERIFIED.** The plan and the RPO/RTO honesty position are delivered by this document; no drill was run, no script executed, no backup touched, and no number published. G-09 stays **NOT MET** (B-016, B-017).

---

## 5. Risks, residual gaps, and explicit non-claims

| Risk / residual gap | Standing |
|---|---|
| Schema drift (340 tables / 664 cols / 70 insert-breaking) | OPEN P0 — F-001/F-002/B-008/B-009; ADR-A waves required |
| 4 P0 patient-workflow modules fail strict; coverage holes | OPEN — F-003/F-007/B-018; **D-021 PENDING_APPROVAL**; no clinical certification |
| Security remediation uncommitted/unreviewed; 11 residuals | OPEN — B-005/B-006; **D-020 PENDING_APPROVAL**; criterion 7 NOT MET |
| RPO/RTO unmeasured; no production-like snapshot | OPEN — B-016/B-017/F-017/F-018; no recovery claim |
| 5/9 service routes unwired; frontend drift 101+28 | OPEN — F-061/F-057; criteria 8/9 NOT MET |
| Test-isolation leak (12 audit rows) makes strict runs non-repeatable | OPEN — F-005/B-013/W-031 (test-only change, not authorized here) |
| NR-011 fixed but discovery debt / ownership remain | F-010 CLOSED; F-013/F-014/F-065 OPEN; ADR-B record W-038 pending |

**Explicit non-claims:**

- **No production-readiness claim.** `FINAL_DECISION.md` remains **HOLD**; criteria 5, 7, 8, 9 are NOT MET; G-12 NOT MET.
- **No clinical-safety claim.** D-021 is PENDING_APPROVAL with no approval record; 4 P0 modules fail strict and referrals/`care_continuum` are untested. Synthetic clinical tests (E-054/E-053) are not certification.
- **No security certification.** D-020 is PENDING_APPROVAL; E-046…E-052 and Phase A–G suites made 0 runtime/production claims.
- **No recovery/DR claim.** RPO/RTO UNMEASURED; no drill run; existence of scripts is not verification.
- **No migration/readiness verification.** No DDL, no stamp, no DB connection, no test execution by this task; readiness BLOCKED/NOT VERIFIED.
- **No approval inferred.** Documentation existence does not close a gate, a finding, a blocker, or a decision. D-020/D-021 stay PENDING; all historical evidence and gate numbers preserved unchanged.
