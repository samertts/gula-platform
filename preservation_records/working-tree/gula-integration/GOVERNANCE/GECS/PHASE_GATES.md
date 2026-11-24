# GECS — PHASE GATES

**Purpose (canonical):** the enforceable definition of each gate that must pass before the
programme may progress. **A gate is never complete because documentation exists** — it must satisfy
its acceptance criteria with identified evidence. `FINAL_DECISION.md` remains **HOLD** until the
release gate (G-12) and every prerequisite are satisfied.
**Created:** 2026-11-17 · **Status vocabulary:** `NOT_MET / PARTIAL / MET (pending sign-off) /
FAILED / NOT_APPLICABLE`. Reopening conditions apply even after a gate is MET.

Each gate: preconditions · required evidence · required tests · acceptance criteria · approval
authority · failure conditions · reopening conditions · **current status**.

---

### G-01 — Architecture approval
- **Preconditions:** decision package complete (E-023); option analysis with evidence per recommendation.
- **Required evidence:** E-021 (ADR request), E-023 (package §A11 approval matrix).
- **Required tests:** none (decision gate) — but no implementation test may run before it passes.
- **Acceptance criteria:** D-001 (ADR-A), D-002 (ADR-B), D-003 (NR-011), D-004 (rollback) each
  approved in writing by the named authority.
- **Approval authority:** Program Director / Architecture (D-001, D-002); Architecture (D-003);
  Database/Operations owner (D-004).
- **Failure conditions:** any recommendation implemented without approval; approval inferred from analysis.
- **Reopening conditions:** new evidence materially changes an option's risk/reversibility.
- **Current status:** **MET — 2026-11-17**: all four approved in writing by the project owner
  (task §1; `DECISION_REGISTRY.md` §A1; package §A11.1). Reopens if new evidence materially
  changes an option's risk/reversibility, or if evidence conflicts with an approved decision.

### G-02 — Database and migration readiness
- **Preconditions:** G-01 approvals for D-001/D-003; single Alembic head maintained.
- **Required evidence:** E-008 (340 gap), E-009 (82/664), E-010 (573/485/88 FK topology),
  E-017 (probes), E-019, E-024.
- **Required tests:** fresh-clone `alembic upgrade head`; per-wave strict subset; `alembic check`
  completes; `alembic heads -v` single head.
- **Acceptance criteria:** 0 unexplained missing tables on shipping surfaces; drift 0 on shipping
  surfaces; fingerprint delta equals approved migrations only (`3b2d9499…` baseline + approved delta).
- **Approval authority:** Migration Owner + Architecture.
- **Failure conditions:** DDL outside an approved revision; `create_all()`-synthesized schema used
  as proof (rejected — F-063); partial downgrade used as rollback (F-012).
- **Reopening conditions:** any new table/column/type divergence discovered; head count > 1.
- **Current status:** **NOT MET** — 340 missing, 82/664 drift remain (B-007…B-009). *Partial
  progress 2026-11-17:* NR-011 (D-003, W-024) **verified** — `alembic check` now completes without
  `NoReferencedTableError` and reaches the ADR-A diff (E-042, E-045); gate reopens-check on the
  next wave, but the missing-table/drift criteria are still unmet.

### G-03 — PostgreSQL compatibility
- **Preconditions:** disposable clones only; never an operational DB.
- **Required evidence:** E-024 (T1 forward upgrade PASS, T2 determinism PASS, T4 full teardown
  VERIFIED, T3 partial = defect), E-001…E-004 (strict vs control), E-015 fingerprint.
- **Required tests:** forward upgrade from prior snapshot with checksum reconciliation; full
  `downgrade base` → `upgrade head`; strict suite.
- **Acceptance criteria:** forward + full round trip PASS (already true); **and** strict suite 872/872.
- **Approval authority:** DBA + QA Lead.
- **Failure conditions:** exit-0 claimed as state equivalence (T3 counter-example); operational DB touched.
- **Reopening conditions:** new migration revisions; snapshot from a different base revision.
- **Current status:** **PARTIAL** — upgrade/round-trip PASS, strict suite FAILED (B-007); partial
  downgrade documented unsafe (B-010).

### G-04 — Identity and authorization
- **Preconditions:** security remediation in tree; independent review scheduled.
- **Required evidence:** E-027 (S-01…S-13), E-029 (69/69 classification), E-033 walk,
  8 regression files (115 tests) + S-13 7/7 + kill-switch 9/9.
- **Required tests:** `test_control_plane_authorization` 21, `test_niam_registry_authorization` 21,
  `test_national_governance_authorization` 29, `test_governance_audit_authorization` 11,
  `test_governance_anonymous_access` 8, `test_security_store_policy` 12,
  `test_ai_platform_authorization` 8, `test_lims_quality_authorization` 5,
  `test_professional_verification_authorization` 7, `test_kill_switch_fail_closed` 9 —
  **plus** isolation tests against migration-built schema (absent — B-019).
- **Acceptance criteria:** 0 real unguarded gaps (met in tree); human sign-off on report **and**
  diff; isolation tests pass on migration schema.
- **Approval authority:** Security lead + Program Director.
- **Failure conditions:** guard weakened to make tests pass; approval inferred from green tests.
- **Reopening conditions:** new endpoints/routes; role model changes; residuals R-01…R-11 accepted/rejected.
- **Current status:** **PARTIAL** — remediated (uncommitted, unreviewed); criterion 7 NOT MET (B-005).

### G-05 — Audit integrity
- **Preconditions:** append-only enforcement understood as working (not a defect to remove).
- **Required evidence:** E-005 (4 trigger failures = enforcement working), hash-chain tests,
  `test_compliance_integrity` / `test_disaster_recovery` status.
- **Required tests:** tamper tests green **with** trigger active; audit-forgery tests (S-05) green;
  no cross-test row leakage (B-013 fixed).
- **Acceptance criteria:** trigger-aware test strategy recorded; audit tests green without
  disabling the trigger; fixture leak fixed for repeatability.
- **Approval authority:** QA Lead + Security lead (test-strategy change = category B).
- **Failure conditions:** trigger disabled/dropped; tamper tests deleted.
- **Reopening conditions:** audit schema changes; new audit actions added.
- **Current status:** **PARTIAL** — enforcement verified; 4 test mismatches open (F-008);
  isolation leak open (B-013).

### G-06 — Patient data integrity
- **Preconditions:** D-001/D-002 approved (write paths and owners defined).
- **Required evidence:** E-009 (82/664), E-011 (1,114 NOT NULL w/o default; 70 insert-breaking),
  E-012 categories, dual-definition record E-014.
- **Required tests:** insert/update paths against migrated schema for shipping surfaces; checksum
  reconciliation on upgrade (Phase C method); no column drops.
- **Acceptance criteria:** 0 insert-breaking drift columns on shipping surfaces; backfill plan
  reviewed for any NOT-NULL addition; single owner per master-data entity.
- **Approval authority:** Migration Owner + Database owner.
- **Failure conditions:** NOT-NULL column added without default/backfill plan; dual writers retained.
- **Reopening conditions:** any new NOT-NULL column; master-data entity added.
- **Current status:** **NOT MET** — 70 insert-breaking columns + 340 tables absent (B-008, B-009).

### G-07 — Service integration
- **Preconditions:** route↔service wiring decision (criterion 9) and frontend drift disposition (criterion 8).
- **Required evidence:** E-025 (5/9 wired, 4 inline), `FRONTEND_INTEGRATION_REPORT.md` §4–§5,
  E-035 frontend gates, D-013 (CR-1) evidence.
- **Required tests:** OpenAPI diff before/after each wiring change (no contract change);
  frontend typecheck/lint/vitest/build/audit exit 0 (currently true).
- **Acceptance criteria:** all 9 service routes delegate or inline bodies deleted with OpenAPI
  unchanged; 101 drifts accepted/scheduled/rejected per page.
- **Approval authority:** Architecture (contract) + Frontend owner (drift).
- **Failure conditions:** route changed without OpenAPI diff; drift page silently rewritten.
- **Reopening conditions:** new endpoints; contract version bump.
- **Current status:** **PARTIAL** — 5/9 wired (W-010), drift classified not dispositioned (W-041).

### G-08 — Patient workflow validation
- **Preconditions:** G-02 waves for clinical/operational contexts; coverage tests exist.
- **Required evidence:** E-001 (4 P0 modules failing), E-024 §13.4 (green under control),
  F-007 coverage holes.
- **Required tests:** `test_icu_lab_workflow_p0`, `test_emergency_surgery_workflow_p0`,
  `test_pharmacy_radiology_workflow_p0`, `test_pharmacy_pos`, `test_national_bootstrap` — all green
  on migration-built schema; **new** functional tests for referrals, `care_continuum`, hospital.
- **Acceptance criteria:** every P0 workflow module green twice (repeatability); coverage holes
  closed; no test skipped/weakened/rewritten to obtain the pass.
- **Approval authority:** Clinical Safety Owner + QA Lead.
- **Failure conditions:** skipping/xfailing workflow tests; claiming pass from SQLite control.
- **Reopening conditions:** any workflow logic change; new P0 workflow added.
- **Current status:** **FAILED** — 4 P0 modules fail strict; referrals/`care_continuum` untested
  (B-018, D-021 pending).

### G-09 — Backup and recovery
- **Preconditions:** D-004 rollback policy approved.
- **Required evidence:** E-024 (T4 verified, T3 unsafe), scripts existence
  (`backup.sh`, `validate-restore.sh`, `pitr-recover.sh` — existence ≠ drill), F-017 (RPO/RTO unmeasured).
- **Required tests:** restore drill into scratch DB with table-count/fingerprint comparison
  (433 tables, rev `20261114_0006`); PITR drill; measured RPO/RTO.
- **Acceptance criteria:** one successful documented drill; RPO/RTO measured **or** explicitly
  recorded as unmeasured (no invented numbers); partial downgrade prohibited in runbook.
- **Approval authority:** Database / Operations owner.
- **Failure conditions:** RPO/RTO claimed without a drill; partial downgrade in runbook; exit-0
  treated as state equivalence.
- **Reopening conditions:** backup schedule/topology change; recovery incident.
- **Current status:** **NOT MET** — policy pending (B-004), drills unrun (B-016).

### G-10 — Offline durability
- **Preconditions:** D-012 (ADR-J) decided.
- **Required evidence:** ADR-J record (in-memory engine confirmed — F-028).
- **Required tests:** durability test (queue survives restart) **or** proof the feature is gated off.
- **Acceptance criteria:** durable queue implemented + tested, or feature verifiably non-shipping.
- **Approval authority:** Architecture.
- **Failure conditions:** offline-first claimed with in-memory engine; dormant service enabled
  without approval.
- **Reopening conditions:** offline feature activated; sync protocol change.
- **Current status:** **NOT MET** — engine in memory, ADR-J PENDING (D-012).

### G-11 — Security validation
- **Preconditions:** G-04 human review; dependency audit clean (already VERIFIED — F-055).
- **Required evidence:** E-027, E-029 (R-01…R-11), E-032 (0 advisories), E-033 walk.
- **Required tests:** regression files green; `npm audit` 0; `pip-audit` exit 0 (lock + fresh + installed).
- **Acceptance criteria:** criterion 7 MET (human sign-off); every residual fixed or explicitly
  accepted by owner; no new advisory.
- **Approval authority:** Security lead + Program Director.
- **Failure conditions:** residual accepted by silence; remediation claimed closed while unreviewed.
- **Reopening conditions:** new dependency; new endpoint; residual accepted then regressed.
- **Current status:** **NOT MET** — sign-off absent (B-005), 11 residuals open (F-044…F-054).

### G-12 — Release readiness (final gate)
- **Preconditions:** G-01…G-11 satisfied with evidence; criteria 1–11 of `FINAL_DECISION.md` re-evaluated.
- **Required evidence:** all gates above + E-022 criteria table + commit authorization (B-006).
- **Required tests:** full backend suite green post-change; frontend gates green; strict suite 872/872.
- **Acceptance criteria:** criteria **5, 7, 8, 9** (currently NOT MET) become MET with evidence;
  PD accepts HOLD→RC promotion in writing.
- **Approval authority:** Program Director (sole).
- **Failure conditions:** HOLD lifted without criteria re-evaluation; any gate marked complete on
  documentation alone.
- **Reopening conditions:** any regression in G-01…G-11 after promotion.
- **Current status:** **NOT MET — `FINAL_DECISION.md` remains HOLD** (E-022, D-019).

---

**Gate summary:** MET 1 (G-01, 2026-11-17) · PARTIAL 4 (G-03, G-04, G-05, G-07) · NOT MET 6
(G-02, G-06, G-09, G-10, G-11, G-12) · FAILED 1 (G-08). **No gate may be marked complete by
documentation existence; every gate above requires its acceptance criteria with evidence.**

---

## Phase 3–8 evidence cross-references (additive — NO gate status changed)

| Gate | Phase 3–8 evidence now indexed | Why the gate status is unchanged |
|---|---|---|
| G-08 (strict gate, FAILED) | E-046…E-052: 740 passed / 0 failed across 7 bounded batches | Different corpus (SQLite synthetic harness, existing tests); W1 strict remains 119/872 FAILED (E-001); no rerun trigger |
| G-10 (offline durability, NOT MET) | E-046 `test_offline_sync` 20; F-028 in-memory queue; F-069 first-wins `CRDT_MERGE` | Durability still unproven; W-047/D-012 PENDING; offline-first remains unsatisfied |
| G-11 (security validation, NOT MET) | E-047 authorization/audit evidence indexed in `DECISION_REGISTRY.md` §D; E-046 ABAC/tenant | D-020 human sign-off absent (B-005/W-033); residual findings R-01…R-11 unchanged |
| G-04 / clinical review chain (PARTIAL) | E-048/050 workflow evidence; F-068 national CDS unverifiable | D-021 Clinical Safety Owner sign-off absent; 4 P0 modules still fail strict; no clinical behavior verified |
| G-12 (release, NOT MET) | `GOVERNANCE/ACTIVATION_FINAL_REPORT.md` (Phases 0–8 complete) | Final report explicitly keeps **HOLD**; criteria 5/7/8/9 NOT MET; no gate may close on documentation |

**Rule reaffirmed:** the 740 targeted passes, 5 engine artifacts and final report are **evidence
indexed against** gates, not gate closures. No approval inferred; HOLD unchanged.

---

## D-023 remediation evidence cross-references (additive — NO gate status changed)

| Gate | Remediation evidence now indexed | Why the gate status is unchanged |
|---|---|---|
| G-08 (strict gate, FAILED) | E-053…E-059: 164 synthetic tests / 0 failed across 7 new suites (MDM, CDS, offline, gateway, rules/policy, certification, security merge) | Different corpus (synthetic, SQLite, no operational DB); W1 strict remains 119/872 FAILED (E-001), no rerun trigger; synthetic pass ≠ strict-gate closure |
| G-10 (offline durability, NOT MET) | E-055: `CONFLICT_QUARANTINE` honest alternative, 31 tests (no lost updates, conflicts preserved, idempotent) | Crash/multi-node durability still NOT VERIFIED (F-028 in-memory, W-047/D-012 PENDING); label corrected but durability gap remains |
| G-11 (security validation, NOT MET) | E-057: canonical merge admin/same-lab/audit fix, 8+4 tests (F-073) | D-020 human security review + PD sign-off still absent (B-005/W-033); broader GET/search/link tenant gaps OPEN (F-073) |
| G-04 / clinical review chain (PARTIAL) | E-054: CDS fail-safe UNAVAILABLE/INDETERMINATE, 11 tests; national CDS route stays UNMOUNTED | D-021 Clinical Safety Owner sign-off absent; conservative engineering fail-safe is not clinical certification; 4 P0 modules still fail strict |
| G-12 (release, NOT MET) | `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md` (Phases A–O final report) | Final report explicitly keeps **HOLD**; criteria 5/7/8/9 NOT MET; 3 real defects fixed (F-077/F-078/F-079) but no gate may close on synthetic evidence or documentation |

**Rule reaffirmed for D-023:** the 164 synthetic passes fix real logic defects (F-077/F-078/F-079) and
close F-066…F-072 with isolated evidence, but they are **indexed against** gates, not gate closures.
HOLD unchanged; D-020/D-021 untouched; no production-readiness or clinical-safety claim.

---

## CC-010 post-stabilization completion cross-references (additive — NO gate status changed)

| Gate | CC-010 evidence now indexed | Why the gate status is unchanged |
|---|---|---|
| G-02 / migration compatibility (NOT MET) | `DATABASE_OWNERSHIP_MATRIX.md` + E-063: 19 runtime bases vs 17 registered; **F-085** open | Ownership/mapping is documentation; drift (340 tables / 664 columns) and F-003 strict failures unchanged; no DDL/migration/stamp permitted |
| G-04 / clinical review (PARTIAL) | completion report §12: CDS fail-safe policy reaffirmed, ENG-B09 stays unmounted | D-021 Clinical Safety Owner sign-off absent; no clinical claim; no dormant activation |
| G-06 / cross-service integration (NOT MET) | `CROSS_SERVICE_INTEGRATION_MATRIX.md` + E-064: F-082/083/084 re-verified, 48 sites/19 pairs | Direct writes remain ungoverned; no ownership/contract change authorized (ADR-D/ADR-B) |
| G-08 / strict gate (FAILED) | E-062: 12/0 synthetic capability-registry guard + 20/20 verifier checks | Different corpus (reference-only index), not the W1 strict schema suite; E-001 **119/872 FAILED** unchanged, no rerun trigger |
| G-09 / recovery & RPO-RTO (NOT MET) | completion report §18: no drill; RPO/RTO UNMEASURED | No measured value; no production-like snapshot (B-016/B-017) |
| G-11 / security validation (NOT MET) | completion report §11: engineering regressions only | D-020 human review + PD sign-off absent; F-073 tenant gaps OPEN |
| G-12 / release (NOT MET) | `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md` (24 sections) | Report explicitly keeps **HOLD**; 0 services E2E/RUNTIME/PRODUCTION verified; 7 journeys contract-envelope only; criteria 5/7/8/9 NOT MET |

**Rule reaffirmed for CC-010:** the new registry, matrices, verifier and 12 synthetic tests are
**evidence indexed against** gates, not gate closures. No gate was upgraded; no test skipped/weakened;
no strict-suite rerun; no approval inferred. `FINAL_DECISION.md` **HOLD**; D-020/D-021 `PENDING`;
W-017 **FAILED 119/872**; 0 commits. **HOLD must not become GO.**
