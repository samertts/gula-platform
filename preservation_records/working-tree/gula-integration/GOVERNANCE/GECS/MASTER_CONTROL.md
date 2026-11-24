# GECS — MASTER CONTROL (single source of truth)

**Purpose (canonical):** the concise current view of the programme. Detailed technical reports are
**not** duplicated here — every line links to its canonical registry or report.
**Snapshot:** 2026-11-17 · Repo `/home/samertts/workspace/projects/gula-integration` ·
Branch `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` ·
All work uncommitted (91 modified / 20 renamed / 108 untracked — preserved; 0 commits; grew from
81/20/91 only through this phase's new test + assessment + report files).

**Status legend:** `VERIFIED` (evidence identified) · `IN_PROGRESS` · `PENDING_APPROVAL`
(authority named, no implementation) · `BLOCKED` (explanation + dependency recorded) ·
`NOT_STARTED` · `FAILED` (evidence appended, never hidden) · `SUPERSEDED` (successor named).
**No item is VERIFIED without an evidence reference (E-ID).**

## 1. Current project phase

**Post-GECS remediation & stabilization COMPLETE (owner D-023, 2026-11-17):** full executive
delegation for F-066…F-072 treatment, synthetic tests, conservative CDS/offline fail-safe fixes,
MDM, lab gateway, certification, security hardening, engine integration, journeys, reliability,
DR and GECS consolidation. Checkpoint: `GECS_CHECKPOINT.md` §9. **Phases A–G (P0/P1/P1) VERIFIED
(W-049…W-055, E-053…E-059, 164 synthetic tests / 0 failed, 3 real defects fixed); Phases H…O
COMPLETE (W-056…W-063); total 194 synthetic tests / 0 failed.** Final report
`GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md`. Verdict remains **HOLD**; D-020/D-021
remain PENDING (engineering authorization is NOT clinical or security certification); 0 commits.

**Post-stabilization national completion program COMPLETE (owner engineering mandate, CC-010,
2026-11-17):** reference-only National Capability Registry (39 engines, 0 executing), Database
Ownership + Migration Readiness Matrix (new F-085 = 2 unregistered declarative bases), Cross-Service
Integration Matrix (F-082/083/084 re-verified), unified Testing Strategy, and the 24-section
`GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`. Work W-064…W-080; evidence E-062/063/064;
12 new synthetic tests pass / 0 fail + verifier 20/20. Pre-edit checkpoint `GECS_CHECKPOINT.md` §12.
**All append-only; HOLD unchanged; no gate closed; no approval inferred.** Prior: approval activation
Phases 0–8 COMPLETE (D-001…D-004 recorded, NR-011 verified, engine audit 740 passed / 0 failed,
GECS sync, final report).

## 2. Current authorized scope

Per **D-023** (owner executive delegation, task §0/§18): full remediation of F-066…F-072 with
synthetic tests and evidence-justified, testable, reversible fixes; MDM/patient matching; conservative
documented CDS fail-safe; reliable tested `CRDT_MERGE` replacement or honest alternative; Lab Device
Gateway; certification engine; proven security fixes; integration/reliability/performance/isolation/
recovery tests; engine de-duplication; national-service interlinking; GECS/registry updates; new
files/tests/helpers as needed. Order P0 (MDM, CDS, offline, security, lab gateway) → P1 (rules,
certification, engine integration, journeys) → P2 (performance/resilience, DR, schema, docs).
Conservative clinical default on failure: `UNAVAILABLE`/`INDETERMINATE`, stop affected recommendation,
preserve data, clear message, audit, never block emergency care.
**Still prohibited:** commit/push/merge/PR/deploy, `git add .`/`-A`, destructive git, real patient
data, weakened/hidden tests, migrations on operational DBs, `alembic stamp`, Platform-Core or
`gula-platform` edits, enabling ENG-A12/ENG-B09, unproven production-readiness claims, closing
D-020/D-021, any irreversible action. Owner approval is not a substitute for clinical testing or
professional security review.

## 3. Current release decision

**HOLD — do not release to production.** (`FINAL_DECISION.md` lines 13 and 361, md5
`effdfeaf10234678d83b2668c4489552`, unchanged.) Release criteria **5, 7, 8, 9 NOT MET**;
criterion 11 MET (F-055). W1 strengthened the hold; it did not modify it (D-019).

## 4. Current critical blockers (top 10 — full list: `BLOCKER_REGISTRY.md`)

| ID | Blocker | Sev | Type |
|---|---|---|---|
| B-005 | Human security review + PD sign-off absent (criterion 7) | P0 | approval |
| B-006 | No commit authorization — everything uncommitted | P0 | approval |
| B-007 | W1 strict gate FAILED — 119/872, 19 of 53 modules | P0 | technical |
| B-008 | 340 ORM tables absent from migrated schema | P0 | technical |
| B-009 | 82 tables / 664 columns drift (70 insert-breaking) | P0 | technical |
| B-010 | Partial downgrade falsely succeeds (unsafe rollback) | P0 | technical |
| B-015 | No shipping/non-shipping register (340 tables, live app refs) | P0 | technical/governance |

_Cleared 2026-11-17 by owner approval: B-001 (D-003), B-002 (D-001), B-003 (D-002),
B-004 (D-004) — rows retained in `BLOCKER_REGISTRY.md`._

## 5. Pending approvals (authority named — `DECISION_REGISTRY.md`)

| ID | Decision | Authority | Status |
|---|---|---|---|
| D-001 | ADR-A — incremental migration by bounded context (+ register) | Project owner (task §1, 2026-11-17) | **APPROVED** |
| D-002 | ADR-B — single authoritative owner + downgrade exclusion | Project owner (task §1, 2026-11-17) | **APPROVED** |
| D-003 | NR-011 — two-part metadata fix (zero DDL) | Project owner (task §1, 2026-11-17) | **APPROVED** |
| D-004 | Rollback policy — snapshot-restore (once drilled) or full downgrade; partial prohibited | Project owner (task §1, 2026-11-17) | **APPROVED** |
| D-020 | Security certification (S-01…S-13 diff + R-01…R-11 acceptance) | Security lead + Program Director | **PENDING** |
| D-021 | Clinical safety certification (4 P0 modules fail; coverage holes) | Clinical Safety Owner | **PENDING — no approval record exists** |
| D-005…D-012 | ADR-C…ADR-J | per `ADR_DECISION_REQUEST.md` | all **PENDING** (unchanged) |

**A recommendation or "continue analysis" is never approval.** The 2026-11-17 approval covers
**only** D-001…D-004 (conditions: `DECISION_REGISTRY.md` §A1; package §A11.1) — D-020, D-021 and
ADR-C…ADR-J remain PENDING; HOLD unchanged.

## 6. Active work (open items — `WORK_REGISTRY.md`)

- **Blocked (7):** W-009 (snapshot evidence), W-026…W-030 (ADR-A waves — depend on W-024/W-025
  execution, approvals cleared), W-039 (production-like snapshot absent).
- **Pending approval (3 — D-023 authorizes the other four):** W-031 (fixture-leak fix),
  W-032 (coverage tests), W-033 (security sign-off — D-020, independent, still needs the named
  professional authority). W-044/W-045/W-046/W-047 are now **authorized via D-023** and executed
  as W-049…W-052 (synthetic tests + conservative fail-safe fixes; no clinical/security certification).
- **In progress (7):** W-003, W-010 (4 routes unwired), W-013/W-015/W-016 (security review chain),
  W-021/W-022 (GLOSI, P4/P3 — cannot bypass P0/P1). **W-024 (NR-011) → VERIFIED/closed
  2026-11-17** (E-041…E-045; 10/10 criteria).
- **Failed (1):** W-017 strict gate — evidence complete (E-001…E-017); never rerun without trigger.
- **Verified/closed in this task:** **W-043** (Phase 3 engine audit — 5 artifacts, 740 tests,
  E-046…E-052) and **W-048** (Phases 4–8 sync + final report).
- **Not started (10):** W-014 (RC), W-025 (register), W-034 (drill), W-035, W-036, W-037,
  W-038 (ADR-B record), W-040, W-041, W-042.
- **Verified/closed (D-023 remediation):** **W-049** (Phase A MDM, E-053), **W-050** (Phase B CDS,
  E-054), **W-051** (Phase C offline, E-055), **W-052** (Phase D gateway, E-056), **W-053** (Phase E
  rules/policy, E-058), **W-054** (Phase F certification, E-059), **W-055** (Phase G security merge,
  E-057), **W-058** (Phase J contract envelope, E-060, 23 tests), **W-059** (Phase K reliability,
  E-061, 7 tests) — 9 phases, 194 synthetic tests / 0 failed.
- **Assessments delivered (no status/gate upgraded):** W-056/W-057 (Phase H/I read-only, PARTIAL;
  F-082…F-084), W-060/W-061/W-062 (Phase L/M/N read-only, BLOCKED/NOT VERIFIED).
- **Complete (Phase O):** W-063 — final report `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md`
  delivered; all 17 acceptance criteria mapped; GECS synced; final integrity check PASS.
- **Counts (post-CC-010):** **80 work items** (23 imported · 25 earlier new · 15 remediation
  W-049…W-063 · 17 completion W-064…W-080). PENDING_APPROVAL 3 (W-031/032/033); remediation
  W-049…W-055 + W-058/W-059 VERIFIED/CLOSED (9), W-056/W-057/W-060/W-061/W-062 assessments delivered,
  W-063 VERIFIED; completion W-064…W-080 closed as source/doc assessment + evidence (no gate upgraded).

**Progress measurement:** completion percentage **UNKNOWN** — gates are evidence-based, not
count-based; report gate statuses (1 MET / 4 PARTIAL / 6 NOT MET / 1 FAILED), not invented totals.

## 7. Next authorized action

**D-023 remediation COMPLETE — all 15 phases A–O delivered (W-049…W-063).** A–G + J/K VERIFIED
via E-053…E-061 (194 synthetic tests / 0 failed; 3 real defects FIXED); assessments H/I/L/M/N
delivered (PARTIAL / BLOCKED). Final report `GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md`
maps all 17 acceptance criteria to evidence and passes final integrity verification. Each
remediation carries: root cause · fix · synthetic regression tests · before/after · risks ·
rollback · unique E-ID evidence · VERIFIED/PARTIAL/BLOCKED/FAILED/NOT VERIFIED status, and a GECS
record. **No further work authorized without a new change record. HOLD unchanged; D-020/D-021 PENDING.**
**Post-stabilization completion program (CC-010) now COMPLETE:** reference-only capability registry,
ownership/integration/test matrices and the 24-section completion report delivered under W-064…W-080,
with E-062/063/064 (12 new synthetic tests pass / 0 fail + verifier 20/20). One new finding **F-085**
(unregistered `DocIntelBase`/`InsBase`) recorded OPEN with blocker B-022; no `env.py` edit, no DDL, no
app/DB/contract change, no gate closed, no repeated work, no strict-suite rerun. Each change carried a
pre-edit checkpoint (`GECS_CHECKPOINT.md` §12), evidence and a rollback path. **No further work
authorized without a new change record.**

**Still outstanding professional authorities (owner approval is not a substitute):** D-020 human
security review + Program Director (B-005/W-033); D-021 Clinical Safety Owner sign-off (F-003/F-007);
national release needs met release criteria + professional security review + clinical testing.
Keep **HOLD**, D-020/D-021 PENDING, W-017 FAILED 119/872, ENG-A12 dormant, ENG-B09 unmounted;
no strict-suite rerun without trigger; no commit. **HOLD must not become GO** — in particular, not on
the strength of `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`.

## 8. Explicitly prohibited actions

1. ~~Implementing D-001…D-004 before written approval~~ — **now approved (2026-11-17)**, but
   only within their recorded scope/constraints; implementing **ADR-C…ADR-J, D-020, D-021** or
   any architecture change beyond the four decisions without approval remains prohibited.
2. Changing `FINAL_DECISION.md` from HOLD; approving ADRs by inference.
3. Editing tests, fixtures, conftest, migrations, `env.py`, schemas or production modules —
   *exception: the single NR-011 edit to `backend/migrations/env.py` + its new regression test
   was authorized by D-003/CC-004 and executed 2026-11-17; any further `env.py` edit needs new
   approval*; enabling dormant services; adding dependencies; building a dashboard.
4. Re-running the 872-test strict suite or the full backend suite (no documented trigger);
   starting a new QA campaign; obtaining a "pass" by weakening a gate.
5. Commit, push, merge, PR, deploy; destructive Git; `git add .` / `git add -A`; touching
   `gula-platform` or Platform-Core; modifying operational DB `gula` (351 tables, do not migrate).
6. Publishing RPO/RTO numbers; claiming Ministry endorsement; dropping `facilities` /
   `organizations` / `national_facilities`; partial downgrade as rollback; enabling non-shipping
   surfaces outside an approved register; secrets or patient data in any governance record.

## 9. Canonical registries

| Registry | Canonical for |
|---|---|
| `GOVERNANCE/GECS/WORK_REGISTRY.md` | work items (**80**) — status, acceptance, next action |
| `GOVERNANCE/GECS/FINDINGS_REGISTRY.md` | findings (**85**) — root cause, severity, closure |
| `GOVERNANCE/GECS/DECISION_REGISTRY.md` | decisions (**23** — D-001…D-023; D-023 uses a vertical block) — approval status + authority |
| `GOVERNANCE/GECS/EVIDENCE_REGISTRY.md` | evidence (**64**) — paths, integrity, currency |
| `GOVERNANCE/GECS/BLOCKER_REGISTRY.md` | blockers (**22** canonical B-IDs B-001…B-022; imported source-ID rows in §D counted separately) — type, exit criteria |
| `GOVERNANCE/GECS/PHASE_GATES.md` | 12 gates — acceptance criteria + current status |
| `GOVERNANCE/GECS/CHANGE_CONTROL.md` | authorization categories + change records |
| `GOVERNANCE/GECS/DUPLICATE_PREVENTION.md` | pre-execution protocol (5 outcomes) |
| `GOVERNANCE/GECS/GECS_CHECKPOINT.md` | this phase's record + control-system audit (§8.6 Phase 3–8) |
| `GOVERNANCE/ACTIVATION_FINAL_REPORT.md` | Phase 8 final report — engines, services, journeys, blockers, approvals, risks |
| `GOVERNANCE/AUTONOMOUS_ENGINES_*.md` (5 files) | engine inventory, verification, findings, remediation plan, dependency map |
| `GOVERNANCE/FINAL_DECISION.md` | release verdict (HOLD) + criteria 1–11 |
| `GOVERNANCE/UNIFICATION_BLOCKERS.md` | canonical blocker detail (source IDs) |
| `GOVERNANCE/W1_CHECKPOINT.md` | canonical W1 state and evidence index |
| `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md` | the four recommendations + approval matrix |

_GECS snapshot ends. Registries are canonical for status; reports are canonical for detail;
evidence is append-only; no approval status changed by GECS creation._
