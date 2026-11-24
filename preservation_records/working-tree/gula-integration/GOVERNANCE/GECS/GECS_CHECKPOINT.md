# GECS — CHECKPOINT

**Program:** GULA execution-control foundation (governance phase, not product development)
**Date:** 2026-11-17 · **Branch:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Verdict of `GOVERNANCE/FINAL_DECISION.md`:** unchanged — **HOLD** (lines 13, 361)
**Commits / pushes / merges / PRs / deploys:** none. **Implementation:** none.

---

## 1. State verified before creating GECS (read-only)

| Check | Result |
|---|---|
| HEAD / branch | `2827c1ff…` / `integration/gula-unification-v1` — unchanged |
| Working tree | 80 modified · 20 renamed (R100 staged) · 90 untracked — preserved as found |
| `GOVERNANCE/GECS/` | NOT PRESENT before this phase |
| Evidence md5s (re-checked) | `W1_CHECKPOINT` `ab863d68…` · DCR `e7b13d17…` · `UNIFICATION_BLOCKERS` `04c02279…` · `ADR_DECISION_REQUEST` `0b533cc4…` · `FINAL_DECISION` `effdfeaf…` · decision package `9b466620…` — all identical |
| HOLD | `HOLD — do not release` present at `FINAL_DECISION.md` lines 13 and 361 (2 occurrences) |
| Sources read in full | `W1_CHECKPOINT.md` (217 lines), `FINAL_DECISION.md` (365), `EXECUTION_LEDGER.md` (150), `RESUMPTION_STATUS.md` (228), `UNIFICATION_BLOCKERS.md` (§1, §2, §3A, §4, §5), `ADR_DECISION_REQUEST.md` decision table (ADR-A…J all PENDING), `PHASE_C_DATABASE_REHEARSAL_REPORT.md` (§1–§13 structure + T1–T7 results), `SECURITY_REVIEW_REPORT.md` (S-01…S-13), `SECURITY_COVERAGE_MATRIX.md`, `PUBLIC_ENDPOINT_REGISTER.md` (69 endpoints, R-01…R-11), decision package (own prior deliverable) |
| New tests / scans run | **NONE** — all state reconstructed from existing evidence (mandate §2) |

## 2. Files created (10, category A only, under `GOVERNANCE/GECS/`)

| # | File | Purpose (canonical for) |
|---|---|---|
| 1 | `MASTER_CONTROL.md` | single source of truth: phase, scope, HOLD, blockers, approvals, next action, prohibitions, registry links |
| 2 | `WORK_REGISTRY.md` | 42 work items with 11 required fields + reopening rules |
| 3 | `FINDINGS_REGISTRY.md` | 64 findings with root cause, type, severity, closure criteria |
| 4 | `DECISION_REGISTRY.md` | 22 decisions with unchanged approval status + named authority |
| 5 | `EVIDENCE_REGISTRY.md` | 40 evidence records: path, integrity, currency (current/historical/superseded) |
| 6 | `BLOCKER_REGISTRY.md` | 36 blockers typed approval/technical/evidence/external with exit criteria |
| 7 | `PHASE_GATES.md` | 12 gates with preconditions, evidence, tests, criteria, authority, failure + reopening conditions |
| 8 | `CHANGE_CONTROL.md` | categories A–E, authorization boundaries, CC-001/CC-002 records |
| 9 | `DUPLICATE_PREVENTION.md` | mandatory 7-step pre-execution protocol, 5 outcomes, 9 worked resolutions |
| 10 | `GECS_CHECKPOINT.md` | this file |

No database, dashboard, service, script, dependency or runtime artifact was created.

## 3. Import counts

| Registry | Imported from existing evidence | Created new in this phase | Total |
|---|---:|---:|---:|
| Work items | 23 (GULA-001…017, GLOSI-001…006) | 19 (W-024…W-042, bounded-context grouped) | **42** |
| Findings | 55 (W1 ×9, NR ×2, X-series ×12, S-01…S-13 ×13, R-01…R-11 ×11, programme ×8) | 9 reconciliations/aliases (F-015, F-018, F-024, F-055…F-064 set) | **64** |
| Blockers | 15 canonical source rows (NR-*, SEC-*, CR-*, CODE-MERGE, DEP-*, …) + MIG-EXISTING | 21 typed (B-001…B-021) | **36** |
| Decisions | 20 (ADR-A…ADR-J ×10, CR-1/CR-2, NR-003/009/010, W1 method, HOLD, security verdict) | 2 (D-021 clinical safety posture, D-022 GECS adoption) | **22** |
| Evidence | 40 (all pre-existing runs/reports/hashes) | 0 (no test re-run — index only) | **40** |
| Phase gates | 12 (mandate §10) | 12 definitions with current status | **12** |

**340-table handling:** grouped into 8 bounded-context categories (E-012) → **5 wave work items**
(W-026…W-030), never 340 tasks. Denominators kept separate: **426** (833 tables / 40 contexts),
**340** (756 per-base / 17 bases), **284** (probe-C import surface) — never summed or substituted.

## 4. Control-system audit (read-only, mandate §15)

| Check | Method | Result |
|---|---|---|
| No duplicate work IDs | table-row scan, `W-\d{3}` | **PASS** — 42 unique |
| No duplicate finding IDs | `F-\d{3}` | **PASS** — 64 unique |
| No duplicate decision/evidence/blocker/change IDs | `D/E/B/CC` scans | **PASS** — 22 / 40 / 21 B-IDs + 15 source-ID rows / 2 unique |
| No duplicate gate IDs | `### G-\d{2}` headings | **PASS** — 12 unique |
| No conflicting canonical statuses | cross-read MASTER_CONTROL vs registries (WORK tallies 13/7/11/4/6/1 recomputed = matches; FAILED W-017 ↔ OPEN F-001…F-009 consistent; BLOCKED W-009 ↔ OPEN F-016 consistent) | **PASS** — 0 conflicts |
| Every VERIFIED item has evidence | evidence-cell scan (W-007's `198/198 communication tests` flagged only by a narrow regex — evidence present on inspection) | **PASS** — 13/13 |
| Every BLOCKED item has explanation | explanation-cell scan | **PASS** — 11/11 |
| Every PENDING_APPROVAL identifies an authority | D-001…D-004, D-020, D-021, D-005…D-012 all name authority; W-031…W-033, W-038 name approver | **PASS** |
| Every open P0/P1 finding has a next action | action-text scan on severity cells | **PASS** — 0 without action |
| Every completed task has acceptance evidence | VERIFIED rows carry test counts/logs/md5s | **PASS** |
| Every registry declares a clear canonical purpose | header purpose line in all 10 files | **PASS** |
| MASTER_CONTROL references correct registry entries | count spot-check 42/64/22/40/36 → each matches its registry | **PASS** |
| No historical evidence rewritten | 6 md5s re-verified identical; append-only discipline; F-062/F-064 marked SUPERSEDED with successors, originals preserved | **PASS** |
| No implementation started | git state + find-since-12:00 (below) | **PASS** |

**Corrections made during the audit (GECS documentation only):** cross-reference fixes in
`WORK_REGISTRY` (F-064→F-061 ×2, F-046…F-056→F-044…F-054, F-024→F-023, F-028→F-026, F-022→F-021)
and `FINDINGS_REGISTRY` (F-023→F-022, F-024→F-023 ×2, F-031→—), plus two count-line corrections
(WORK statuses, FINDINGS status tallies). No report outside `GECS/` was touched.

## 5. Evidence of no unauthorized changes

| Check | Result |
|---|---|
| HEAD | `2827c1ff…` — unchanged, 0 commits made |
| Working tree | 80 modified / 20 renamed / **91 untracked** — the only delta is **+1 untracked entry = `GOVERNANCE/GECS/`** (authorized category A); the prior 90 (89 pre-existing + decision package) untouched |
| Staged state | 20 staged renames preserved, 0 staged content changes added |
| Files modified since phase start (12:00) | **only the 10 files under `GOVERNANCE/GECS/`** (plus this file's siblings); **zero** outside `GOVERNANCE/` |
| Evidence md5s | all 6 identical to pre-phase values (§1) |
| `FINAL_DECISION.md` | md5 unchanged; HOLD ×2 |
| Tests / fixtures / migrations / `env.py` / schemas / production modules | **not modified**; no test executed; no DDL (fingerprint `3b2d9499…` never touched) |
| `gula-platform` / Platform-Core / operational DB `gula` | untouched |
| Commit / push / merge / PR / deploy / destructive Git / `git add` | none performed |

## 6. Known limitations of this checkpoint

- Evidence under `/tmp/opencode/**` is volatile; 28 of 40 records live there (declared lapse
  F-060 documents an earlier loss). In-repo governance files carry md5s as integrity anchors.
- Completion percentage reported as **UNKNOWN** (gate-based, not count-based).
- The 15 imported canonical blocker rows keep their original wording/status — GECS neither closed
  nor downgraded any of them.

## 7. Next authorized action (unchanged from `MASTER_CONTROL.md` §7)

**Record the four approvals (D-001 ADR-A, D-002 ADR-B, D-003 NR-011, D-004 rollback) in writing
via §A11 of `ARCHITECTURE_DECISION_PACKAGE_W1.md`.**
First implementation step after approval: **W-024 — NR-011, `backend/migrations/env.py` only,
zero DDL, single-file reversible**; then W-038 (ADR-B record); then W-026 (ADR-A context 1).
Security sign-off (W-033) proceeds in parallel. **Until each approval exists: STOP.**

---

## 8. Activation checkpoint — Phases 0–2 (appended 2026-11-17)

*Sections 1–7 above are the GECS-foundation checkpoint and are **not rewritten**; this section
records the activation task (approvals + NR-011) that superseded their "STOP" next-action.*

**Commits / pushes / merges / PRs / deploys:** none. **Verdict:** `FINAL_DECISION.md` still
**HOLD** (md5 `effdfeaf…` unchanged).

### 8.1 Phase 0 — baseline (before any modification)

`ACTIVATION_BASELINE.md` (new file) captures HEAD `2827c1ff…`, branch, 80 modified / 20 staged
renames / 91 untracked, all 10 registry md5s, and the 6 historical evidence md5s — all re-verified
identical to section 1. No file was cleaned or reordered.

### 8.2 Phase 1 — D-001…D-004 approval recording (CC-003, EXECUTED)

| Check | Result |
|---|---|
| Approval source | explicit project-owner approval in the OpenCode task §1 — **not** attributed to the security or clinical reviewer |
| Recorded in | `DECISION_REGISTRY.md` §A1 (per-decision scope/constraints/risks/evidence/reversal), package §A11 + §A11.1, `ACTIVATION_BASELINE.md` §6 |
| D-020 / D-021 | **untouched — remain PENDING_APPROVAL** |
| B-001…B-004 | **CLEARED**, rows retained with exit criteria |
| G-01 | **MET** (gate summary now MET 1 · PARTIAL 4 · NOT MET 6 · FAILED 1) |
| Scope limits | no Platform-Core restructuring, no irreversible action, HOLD unchanged; conflict rule recorded (stop + record, do not force) |

### 8.3 Phase 2 — NR-011 (D-003, CC-004, EXECUTED) — 10/10 acceptance criteria MET

| # | Criterion | Result |
|---:|---|---|
| 1 | no DDL | zero DDL statements; `env.py` diff = 49 insertions, 0 deletions |
| 2 | no DB change | fingerprint before/after/after-rerun **`3b2d9499…` ×3 identical** (E-043) |
| 3 | no unjustified migration-history change | `alembic_version`=`20261114_0006` unchanged; 433 tables; single head `20261114_0006` |
| 4 | schema fingerprint unchanged | as above |
| 5 | no dual ownership | merged `MetaData` is a read-only view; each table keeps its owning base; duplicate `national_facilities` resolves deterministically first-wins → 6-col `Base` owner (consistent with D-002) |
| 6 | no new circular imports | all 17 base imports + `app.national.domain` import OK (probe_discovery.log); ruff clean |
| 7 | no import side effects | merge block is pure metadata bookkeeping — no engine, no connection, no DDL |
| 8 | regression test | `backend/tests/unit/test_nr011_metadata_discovery.py` — **14 tests, all pass**; no existing test modified |
| 9 | alembic discovery check | `alembic check` before: `NoReferencedTableError` (ehr_allergies.citizen_id → national_citizens); after: **0** occurrences, reaches `FAILED: New upgrade operations detected` (the ADR-A diff) (E-042) |
| 10 | no unintended autogenerate change | all 12 op-class counts identical to validated probe C (568/474/68/70/3752/2312/16/14/2/186/90/56); 284 distinct `add_table` names identical list (E-045) |

**Scope respected:** only `backend/migrations/env.py` + 1 new test file. Targeted regression run
`tests/test_migrations.py` + `tests/test_migration_resilience.py` +
`tests/migrations/test_migration_graph_integrity.py` + the new file = **36 passed / 0 failed**
(E-044). Git delta vs baseline: modified 80→81 (only `env.py`), renames 20, untracked 91
(test file inside already-untracked `backend/tests/unit/`). **0 commits.**

**Recorded, not done:** `F-065` — 5 of the 17 registered bases contribute 0 tables (their model
modules are outside `env.py`'s import surface); expanding it now would break criterion 10, so it
belongs to ADR-A waves (W-027, W-030).

### 8.4 Registry sync after Phases 0–2

Work 42 (VERIFIED 14 · IN_PROGRESS 7 · BLOCKED 7 · PENDING_APPROVAL 3 · NOT_STARTED 10 · FAILED 1) ·
Findings **65** (F-010 **CLOSED**, F-065 added) · Evidence **45** (E-041…E-045) ·
Blockers 36 (B-001…B-004 CLEARED) · Decisions 22 (4 APPROVED, D-020/D-021 still PENDING) ·
Gates 12 (G-01 MET, G-02 still NOT MET with NR-011 partial-progress note) ·
Change control CC-003/CC-004 EXECUTED.

### 8.5 Next authorized action (supersedes §7)

**Phase 3 — autonomous-engines audit** (discovery from source/routes/workers/tests/CI/docs,
isolated synthetic verification, classification, 5 `GOVERNANCE/AUTONOMOUS_ENGINES_*.md`
artifacts) → Phase 4 national-service audit → Phase 5 security/clinical evidence (D-020/D-021
**stay open**) → Phase 6 targeted tests → Phase 7 full GECS sync → Phase 8 final report.
**Never flip HOLD to GO.**

---

### 8.6 Phase 3–8 completion record (2026-11-17) — supersedes §8.5 as next action

| Phase | Delivered | Evidence / record |
|---|---|---|
| 3 | 39 engines inventoried (A 12 / B 12 / C 9 / D 6); 5 engine artifacts; fixed 10-status taxonomy | E-046…E-052; `AUTONOMOUS_ENGINES_{INVENTORY,VERIFICATION,FINDINGS,REMEDIATION_PLAN,DEPENDENCY_MAP}.md`; CC-005; W-043 CLOSED |
| 4 | 18 services + J1–J7 re-verified additively; §15.4 NR-011 tooling statement superseded | `NATIONAL_SERVICE_INVENTORY.md` §16, `NATIONAL_SERVICE_CONTRACTS.md` §11; no verdict changed |
| 5 | D-020/D-021 evidence-only refresh across 7 checks | `DECISION_REGISTRY.md` §D; both decisions still PENDING_APPROVAL |
| 6 | 7 bounded targeted batches, **740 passed / 0 failed**, all exit 0; no BLOCKED batch | E-046…E-052 (logs in `/tmp/opencode/nr011_activation/`); no new/edited test |
| 7 | All GECS registries synced (72 findings / 52 evidence / 48 work / 22 decisions) | CC-005/CC-006; `FINDINGS_REGISTRY.md`, `EVIDENCE_REGISTRY.md`, `WORK_REGISTRY.md`, `CHANGE_CONTROL.md` |
| 8 | Final report with engines, repairs, services, journeys, findings, blockers, approvals, risks | `GOVERNANCE/ACTIVATION_FINAL_REPORT.md`; W-048 CLOSED |

**Engine status totals (reconciled with per-engine rows):** 9 INTEGRATION_VERIFIED ·
15 UNIT_VERIFIED · 2 PARTIAL_VERIFIED · 11 SOURCE_PRESENT · 1 DORMANT · 1 UNVERIFIABLE ·
**0 RUNTIME_VERIFIED · 0 PRODUCTION_VERIFIED**. 24 engines have isolated synthetic evidence only.

**New findings:** F-066…F-072 (6 OPEN PENDING_APPROVAL, 1 VERIFIED classification).
**New work:** W-043…W-048 (W-043/W-048 VERIFIED+CLOSED; W-044…W-047 PENDING_APPROVAL).
**New evidence:** E-046…E-052. **Change records:** CC-005 / CC-006.

**Unchanged by Phases 3–8 (re-verified):** HEAD `2827c1ff…` / branch correct · 0 commits ·
`FINAL_DECISION.md` md5 `effdfeaf10234678d83b2668c4489552` with HOLD at lines 13 and 361 ·
D-020 / D-021 PENDING · B-005…B-010/B-015 and B-016/B-017 gaps open · strict W1 gate FAILED
119/872 (E-001, not rerun) · **no code / migration / DDL / test / fixture / conftest / DB change** ·
no `gula-platform`, Platform-Core, commit, push, merge, PR or deploy.

**Next authorized action:** present the four approval requests in `ACTIVATION_FINAL_REPORT.md` §8
to the named authorities. Until granted, keep HOLD, keep D-020/D-021 PENDING, keep ENG-A12 dormant
and ENG-B09 unmounted, and do not rerun the strict suite (no trigger). **Never flip HOLD to GO.**

---

## 9. NEW CHECKPOINT — Post-GECS Remediation & Stabilization authorization (2026-11-17)

**This section is the checkpoint created BEFORE any modification in this phase.** It is the
evidence-driven baseline against which every later change is measured. Nothing below grants
release: `FINAL_DECISION.md` stays **HOLD**.

### 9.1 Owner authorization received (verbatim scope)

The project owner issued *"GULA — NATIONAL PLATFORM STABILIZATION & AUTONOMOUS CAPABILITY
REMEDIATION / OWNER'S FULL EXECUTION AUTHORIZATION"* on 2026-11-17. This is an **executive
delegation, not a preliminary plan request**. It explicitly adopts F-066…F-072 for treatment and
authorizes: synthetic tests for engines/services; limited/medium/wide technical fixes when
evidence-justified, testable, reversible and architecture-compatible; MDM patient matching;
conservative documented CDS safety policy; replacement of the incorrect `CRDT_MERGE` with a
reliable tested strategy or an honest alternative; Lab Device Gateway fix and test; Certification
engine; proven security fixes; integration/reliability/performance/isolation/recovery tests;
improvement and de-duplication of existing engines; national-service interlinking; GECS/registry
updates; and creation of new files/tests/helpers where necessary. **No further owner approval is
required for actions inside this scope.**

### 9.2 Authorization boundaries (still binding)

The authorization does **not** permit: overriding clinical-safety criteria; endangering patient
data; disabling Authorization / Tenant Isolation / Audit; real patient data in tests; hiding
failing tests; unproven production-readiness claims; irreversible operations; or undocumented
out-of-scope changes. Where a specialist clinical decision is needed, apply the most conservative
policy that prevents an untrusted recommendation, preserves data and escalates to a human without
hiding failure. Owner approval is **not** a substitute for clinical testing or professional
security review for national release. For any genuinely specialist clinical/security decision the
conservative fail-safe default is recorded and the named professional authority remains outstanding.

### 9.3 Verified baseline (re-checked this session, before edits)

| Check | Result |
|---|---|
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` |
| Branch | `integration/gula-unification-v1` |
| Git status | `M 81` · `R  20` · `?? 97` (total 198) — **not cleaned, not reordered** |
| GECS counts | F 72 · E 52 · W 48 · D 22 · CC 6 · B 21 |
| `FINAL_DECISION.md` | md5 `effdfeaf10234678d83b2668c4489552`; HOLD at lines 13 and 361 |
| NR-011 (`backend/migrations/env.py`) | `+49 / -0` only — unchanged; not re-edited |
| Historical gate numbers | E-001 `753/119`, E-003 `872/0`, control `750/122` — retained, not re-run without trigger |

**Control-file md5 baseline (pre-edit):**
`MASTER_CONTROL.md b44f7247…` · `WORK_REGISTRY.md e3f35d44…` · `FINDINGS_REGISTRY.md d0b9cc0c…` ·
`DECISION_REGISTRY.md adaa112c…` · `EVIDENCE_REGISTRY.md 3800a951…` · `BLOCKER_REGISTRY.md 4a3c428c…` ·
`PHASE_GATES.md 43abf38d…` · `CHANGE_CONTROL.md 8ecea33d…` · `DUPLICATE_PREVENTION.md 30d83a73…` ·
`GECS_CHECKPOINT.md fa143cdf…` · `FINAL_DECISION.md effdfeaf…`.

### 9.4 Execution order (owner §18)

P0: (1) MDM · (2) CDS fail-safe · (3) offline conflict resolution · (4) security · (5) Lab gateway.
P1: (6) rules/policy · (7) certification · (8) engine integration · (9) patient journeys.
P2: (10) performance/resilience · (11) backup/DR · (12) schema/migration readiness ·
(13) documentation/governance consolidation. Independent tasks may run in parallel only when they
do not share files, DBs or contracts.

### 9.5 Standing prohibitions for this phase (owner §22)

No commit/push/merge/PR/deploy · no `git add .`/`-A` · no destructive git · no `gula-platform` or
out-of-scope Platform-Core edit · no real patient data · no migration on operational DB · no
`alembic stamp` · no weakened/hidden tests · no weakened security · no HOLD → GO · no
production-readiness claim without met release criteria. All synthetic evidence only.

**Each remediation will carry: root cause · fix · tests · before/after · risks · rollback · evidence ·
status, and a GECS remediation record. FINAL_DECISION remains HOLD regardless of completion.**

---

## 10. Phase A–G completion record (appended 2026-11-17 — §9 baseline measured against this)

**Commits / pushes / merges / PRs / deploys:** none (0). **Verdict:** `FINAL_DECISION.md` still
**HOLD** (md5 `effdfeaf10234678d83b2668c4489552`, HOLD ×2 lines 13/361 — re-verified after every
task). **D-020 / D-021 still PENDING.** NR-011 `env.py` still `+49/-0`, not re-edited. No operational
DB / DDL / `alembic stamp`; no `gula-platform` or Platform-Core edit; no real patient data.

| Phase | Work | Evidence (synthetic only) | Result | Fixed / residual |
|---|---|---|---|---|
| A — MDM | W-049 | E-053 (`test_mdm_patient_identity_synthetic.py`) | **15/0** | name-only → 0.4 / `matched=False`; merge records history + source fields; ambiguous→review |
| B — CDS fail-safe | W-050 | E-054 (`test_cds_failsafe_synthetic.py`) | **11/0** | `INDETERMINATE`/`UNAVAILABLE`; 8 risk `except:pass` → fail-safe; route UNMOUNTED |
| C — offline conflict | W-051 | E-055 (`test_offline_conflict_synthetic.py` + `test_offline_sync.py`) | **31/0** | `CRDT_MERGE` → `CONFLICT_QUARANTINE`; no lost updates; idempotent; crash durability NOT VERIFIED |
| D — lab gateway | W-052 | E-056 (`test_lab_device_gateway_synthetic.py`) | **35/0** | replay store outage → fail-closed; synthetic ASTM/HL7; F-081 SPM mapping residual |
| E — rules/policy | W-053 | E-058 (`test_engines_rules_policy_expression_synthetic.py`) | **34/0** | F-077 (15/16 operators crashed) + F-078 (missing→0 false-normal) FIXED; F-074/075/076 residual |
| F — certification | W-054 | E-059 (`test_certification_engine_synthetic.py` + `test_runtime_security_guards.py`) | **30+4/0** | F-079 (all `/certification/*` → 500) FIXED; F-080 residual; scope disclaimer enforced |
| G — security merge | W-055 | E-057 (`test_security_merge_regression_synthetic.py` + `test_auth_infrastructure.py -k canonical`) | **8+4/0** | admin/same-lab/`require_own_lab`/audit; F-073 tenant gaps residual; D-020 still PENDING |

**Totals:** 164 synthetic tests / 0 failed across 7 suites; 3 real defects FIXED with regressions
(F-077, F-078, F-079); 4 findings closed with evidence (F-066…F-070, F-072) + F-069 honest
alternative; 9 new findings (F-073…F-081). Registry sync: E 52→59 · F 72→81 · W 48→63 · CC 6→8;
D-023 status → execution-in-progress. All remediation evidence is isolated/synthetic; 0 commits;
HOLD and D-020/D-021 untouched. Phases H…O completing (see final stabilization report).

---

## 11. FINAL CLOSE — Phases H–O (appended 2026-11-17)

**Deliverable:** `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md` (final, W-063). All 15
phases A–O have a recorded status; all 17 acceptance criteria (owner §20) are mapped to evidence.
**0 commits / pushes / merges / PRs / deploys. Verdict HOLD unchanged** — md5
`effdfeaf10234678d83b2668c4489552`, HOLD ×2 (lines 13/361), re-verified after every task.
**D-020 / D-021 still PENDING_APPROVAL.** HEAD `2827c1ff…`, branch unchanged; NR-011 `env.py`
`+49/-0` not re-edited; no operational DB / DDL / stamp; no `gula-platform` edit; no real patient
data; ENG-A12 dormant / ENG-B09 unmounted; no strict-suite rerun without trigger.

| Phase | Work | Record | Result |
|---|---|---|---|
| H — engine integration | W-056 | `STABILIZATION_PHASE_H_I_ASSESSMENT.md` §1 | 39 engines reconciled (0 runtime/prod); GO-for-design reference-only index; F-082; **PARTIAL** |
| I — 18 services | W-057 | same §2 | 18 rows reviewed; 70 import sites/25 pairs; F-083/F-084; **PARTIAL** |
| J — 7 journeys | W-058 | E-060 (`test_journey_contract_reliability_synthetic.py`, envelope class) | **23/0** — contract envelope only, NOT e2e readiness |
| K — reliability | W-059 | E-061 (same file, composition class) | **7/0** — bounded existing primitives; no SLO/RPO/RTO |
| L — test strategy | W-060 | `STABILIZATION_PHASE_L_M_N_ASSESSMENT.md` §2 | L0–L9 mapped; historical numbers kept; **BLOCKED/NOT VERIFIED** |
| M — migration integrity | W-061 | same §3 | 340/664/70 drift, head `20261114_0006`, fingerprint `3b2d9499…`; no DDL; **BLOCKED/NOT VERIFIED** |
| N — backup/DR | W-062 | same §4 | RPO/RTO UNMEASURED; no drill; no numbers; **BLOCKED/NOT VERIFIED** |
| O — final | W-063 | `NATIONAL_PLATFORM_STABILIZATION_REPORT.md` | GECS synced; all 17 criteria mapped; **COMPLETE** |

**Final totals:** 9 synthetic suites, **194 tests passed / 0 failed** (164 A–G + 30 J/K); 3 real
defects FIXED (F-077/F-078/F-079); F-082…F-084 added (read-only source observations).
**Final registry counts:** F **84** · E **61** · W **63** · D **23** · CC **9** · B **21** — all
append-only; no historical row rewritten. **17 acceptance criteria:** 9 VERIFIED (engineering),
3 PARTIAL, 5 BLOCKED/NOT VERIFIED. **HOLD; D-020/D-021 PENDING — HOLD must not become GO.**
This closes the owner-authorized remediation cycle; no further work is authorized without a new
change record and, for release, the outstanding professional sign-offs.

---

## 12. POST-STABILIZATION NATIONAL COMPLETION PROGRAM — PRE-EDIT CHECKPOINT (CC-010, appended 2026-11-17)

**Authority:** owner post-stabilization engineering mandate (`NATIONAL HEALTH PLATFORM COMPLETION &
INTEGRATION PROGRAM`, §5/§19/§20/§26). D-023 is **CLOSED**; D-020 and D-021 remain **PENDING**.
This checkpoint was written **before any file edit** for the new program, per §26.

### 12.1 Verified repository baseline (re-measured at program start — no edits)

| Control | Required / observed | Result |
|---|---|---|
| HEAD | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | PASS (unchanged) |
| Branch | `integration/gula-unification-v1` | PASS |
| Git status | 219 entries (108 untracked / 91 modified / 20 renamed / 0 staged adds) | PASS (preserved) |
| Commits ahead | 0 | PASS |
| `FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552`; HOLD lines 13 & 361 | PASS |
| D-020 / D-021 | `PENDING_APPROVAL` | PASS (unchanged) |
| `backend/migrations/env.py` NR-011 delta | `+49 / -0` | PASS (not re-edited) |
| Prior evidence E-053…E-061 | 8 synthetic test files + 8 `/tmp/opencode/remediation/E-05{3..9,60,61}*.log` present on disk | PASS (preserved) |
| Prior registry state | F 84 · E 61 · W 63 · D 23 · CC 9 · B 21 | PASS (append-only) |

### 12.2 Control-file md5 baseline (before new-program edits)

| File | md5 at program start |
|---|---|
| `MASTER_CONTROL.md` | `dc4f90c7e3fb74fa62f6da27aa1195c9` |
| `WORK_REGISTRY.md` | `ed11185e95e5120997447ad62370147c` |
| `FINDINGS_REGISTRY.md` | `e43c414867ae416d273e64e13213afcf` |
| `EVIDENCE_REGISTRY.md` | `03ba223a7220112da7b2953eae2fcfa3` |
| `DECISION_REGISTRY.md` | `c70a354fd9df57758901c8786199c697` |
| `CHANGE_CONTROL.md` | `53c7e65110c5126c6ba03f1255377ac4` |
| `GECS_CHECKPOINT.md` | `d9bbaa868c5c3f793c29bee4aff5a3c2` |
| `BLOCKER_REGISTRY.md` | `4a3c428c601941c8e57ebbbc264e6b6e` |
| `PHASE_GATES.md` | `c3508fb317858bc6452b9169d539cfc7` |
| `DUPLICATE_PREVENTION.md` | `d2b79486670900e890ee732eeeda6bd6` |

(These are the **pre-edit** values; CC-010 appends to these files, so their post-edit md5s will
legitimately differ. Historical rows are never rewritten — only appended.)

### 12.3 New work scopes and file ownership (A–P + final)

| Work ID | Scope | Allowed files (canonical) | Forbidden |
|---|---|---|---|
| W-064 | A — national core & patient identity | this section + report §4/§9 | no identity code, no MDM re-test (E-053 stands) |
| W-065 | B — laboratory & hospital integration | report §5 rows 01/02 + cross-service matrix | no LIMS/HIS code; F-081/F-083/F-084 stay open |
| W-066 | C — primary care & pharmacy | report §5 rows 03/04 | no app code; no contract change |
| W-067 | D — radiology, emergency, blood bank | report §5 rows 05/06/07 | no app code; no clinical claim |
| W-068 | E — public health, immunization, maternal | report §5 rows 08/09/11 | no app code; no `cc_*` DDL |
| W-069 | F — chronic disease + remaining clinical | report §5 rows 10/12/13/14 | no app code; ENG-B09 stays unmounted |
| W-070 | G — referral, insurance, home care | report §5 rows 15/16/17 | no app code; ADR-G/I pending |
| W-071 | H — equipment & maintenance | report §5 row 18 | no app code |
| W-072 | I — cross-service integration | `CROSS_SERVICE_INTEGRATION_MATRIX.md` + report §7 | no service-code change; no ownership change |
| W-073 | J — 7 patient journeys | report §6 | no e2e claim; envelope E-060 stands |
| W-074 | K — DB & migration readiness | `DATABASE_OWNERSHIP_MATRIX.md` + report §10 | **no DDL / migration / stamp / DB connection** |
| W-075 | L — security & privacy | report §11 | no D-020 closure; no security claim |
| W-076 | M — clinical safety | report §12 | no D-021 closure; no CDS mount |
| W-077 | N — reliability & infrastructure | report §17/§18 | no SLO/RPO/RTO invention; no deploy |
| W-078 | O — frontend & UX | report §15 | no frontend behavior change; no new UI |
| W-079 | P — testing & final verification | `NATIONAL_TESTING_STRATEGY.md`, verifier + test + E-062+, report §16 | no test weakened/skipped; no strict-suite rerun |
| W-080 | Final — GECS sync + completion report | `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md` + 10 GECS registries | no other file |

### 12.4 Change risks and rollback (governed by CC-010)

- **Risk:** over-claiming a service/journey as complete, or turning the reference-only index into an
  executing component. **Mitigation:** fixed status taxonomy, explicit "reference-only / not release
  evidence" language, a verifier asserting no code imports the index, and per-service verdicts carried
  from `NATIONAL_SERVICE_INVENTORY.md` (no re-certification).
- **Risk:** disturbing prior A–O evidence or user changes. **Mitigation:** append-only GECS edits, no
  cleanup, no `git add`, and a final integrity re-check against §12.1.
- **Rollback:** delete the six new docs + JSON + verifier + test; revert only CC-010's appended rows/
  sections; prior state defined by the §12.2 md5s. `git revert` is not available (0 commits) and is
  not needed; no app/DB object is created.
- **Standing prohibitions reaffirmed:** no commit/push/merge/PR/deploy, no `git add .`/`-A`, no
  destructive git, no `gula-platform`/Platform-Core edit, no operational DB/DDL/stamp, no real patient
  data, no skipped/xfailed/weakened test, no dormant activation, no ENG-B09 mount, no HOLD → GO.

### 12.5 CC-010 completion record (appended after execution — 2026-11-17)

**All 17 work items W-064…W-080 executed and closed** (16 as source/doc assessments, W-079/W-080
VERIFIED with evidence). Every change was verified before the next; no A–O work was repeated without
a trigger; no user change was cleaned or reordered.

| Deliverable | Canonical path | Evidence / result |
|---|---|---|
| Reference-only capability registry | `GOVERNANCE/NATIONAL_CAPABILITY_REGISTRY.md`, `GOVERNANCE/national_capability_index.json` | 39 engines; 9/15/2/11/1/1; 0 runtime/prod; 20/20 verifier checks |
| Read-only verifier | `scripts/verify_national_capability_registry.py` | stdlib only; app-import guard; 3 negative controls |
| Synthetic guard suite | `backend/tests/test_national_capability_registry_reference.py` | **E-062: 12 passed / 0 failed** (0.69 s) |
| Database ownership + migration readiness | `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md` | **E-063**: 19 bases/17 registered → **F-085**; `env.py` `+49/-0` |
| Cross-service integration matrix | `GOVERNANCE/CROSS_SERVICE_INTEGRATION_MATRIX.md` | **E-064**: F-082/083/084 present; 48 sites/19 pairs |
| Unified testing strategy | `GOVERNANCE/NATIONAL_TESTING_STRATEGY.md` | L0–L9 classes mapped; historical gate numbers immutable |
| 24-section completion report | `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md` | 18 services + 7 journeys; **HOLD** retained |

**Registry counts after CC-010:** F 85 · E 64 · W 80 · D 23 · CC 10 · B 22 (canonical B-IDs; one new
B-022 for F-085). D-020/D-021 unchanged `PENDING_APPROVAL`; W-017 **FAILED 119/872**; ENG-A12 dormant;
ENG-B09 unmounted; 0 commits. No finding closed, no gate upgraded, no decision changed.

**Integrity re-check** against §12.1 baseline (HEAD, branch, 0 commits, HOLD md5, D-020/D-021,
`env.py +49/-0`, evidence logs, no `gula-platform`/DB/deploy change, no lost user changes) was run as
the final step of W-080 and recorded in the completion report §2/§21. **Verdict: PASS — HOLD retained.**
