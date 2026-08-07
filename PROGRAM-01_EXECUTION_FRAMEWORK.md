# PROGRAM-01 Execution Framework

**Authoritative execution model for every structural migration.**
**Status:** Adopted — mandatory for all remaining Commit 1.x migrations.
**Date:** 2026-08-07
**Authority chain:** `AI_OPERATING_CONSTITUTION.md` (supreme) →
`PROGRAM-CONSTITUTION-001` → `33_STRUCTURAL_MIGRATION_CONSTITUTION.md` →
ADR-028 → ADR-029 → this framework.
**Supersedes:** all ad-hoc per-commit execution in Commits 1.1–1.6 (retroactively
covered; future commits MUST follow this model exactly).

---

## Purpose

Every remaining migration runs through **exactly one execution model** with zero
ambiguity. This document fixes: the lifecycle, the verification matrix, exit
criteria, rollback standards, architecture decision rules, risk escalation
rules, the program dashboard, wave execution rules, the certification model,
and PROGRAM-02 readiness.

The framework governs **all** migrations of the 48 acknowledged findings
(`.ai/core/architecture/constitution_baseline.json`) plus any NEW finding the
architecture gate reports.

---

## 1. Migration Lifecycle

Every migration is a 13-stage lifecycle. Stages are sequential and blocking —
a migration NEVER advances past a gate that has not passed. Stages 1–6 are
**documentation-only** (no production code touched); stage 7 is the single
implementation commit; stages 8–11 verify; stage 12 certifies; stage 13
starts the next migration.

```
Discovery
    ↓
Evidence Collection
    ↓
Consumer Analysis
    ↓
Architecture Analysis
    ↓
Migration Classification
    ↓
Risk Classification
    ↓
ADR Decision (if required)
    ↓
Implementation
    ↓
Verification
    ↓
Metrics
    ↓
Independent Review
    ↓
Certification
    ↓
Next Migration
```

### Stage definitions

| Stage | Deliverable | Exit condition | Production code touched? |
|---|---|---|---|
| **1. Discovery** | Finding ID, signal, current impl, canonical provider, file/line | Candidate identified and mapped to exactly one `SHARED_CORE_CATALOG` service | No |
| **2. Evidence Collection** | Objective proof: unused / superseded / duplicated / deprecated | Evidence recorded in the Migration Impact Report (ADR-028 R2) | No |
| **3. Consumer Analysis** | Complete importer graph: backend, tests, scripts, frontend, dynamic imports | Every consumer classified (re-point / archive / delete / untouched) | No |
| **4. Architecture Analysis** | Behavioral-equivalence assessment vs canonical provider; canonical completeness; orphan-risk check | Equivalence verdict + canonical-provider consumer list | No |
| **5. Migration Classification** | One of the 5 classes (§5) — exactly one, never mixed | Class assigned with justification | No |
| **6. Risk Classification** | Risk (L/M/H), effort (S/M/L), rollback (L/M/H) per the classification legend | Risk entry + escalation decision (§6) | No |
| **7. ADR Decision** | ADR created/updated if class requires it (see §5 matrix) | ADR accepted before implementation begins | No |
| **8. Implementation** | The single atomic migration commit | Commit satisfies R1–R7; pre-commit hook green | **Yes** |
| **9. Verification** | Full verification cycle (§2) executed | All mandatory matrix rows PASS | No |
| **10. Metrics** | Dashboard metrics updated (§7); baseline re-run if findings removed | Baseline shrinks; count never grows | No (baseline file) |
| **11. Independent Review** | Reviewer or human approval of the change-set (R7 stop) | Independent verdict PASS | No |
| **12. Certification** | Wave/Program certification (§9) updated | Certified wave/program markers set | No |
| **13. Next Migration** | Next Wave-ordered finding selected (§8) | Explicit approval granted; R7 satisfied | No |

**Stop rule:** after Stage 8/9 (implementation + verification), the executor
STOPS and awaits explicit approval before Stage 13 (ADR-028 R7). A single
migration = a single implementation commit + a single
`docs/baselines/COMMIT_X_Y_VERIFICATION_REPORT.md`.

---

## 2. Standard Verification Matrix

Every migration MUST run the full matrix below. Rows are **mandatory** unless
marked *advisory*. A row is PASS only when the stated criterion is objectively
met. The matrix is executed **after** every implementation commit (Stage 9).

| # | Verification | Tool / command | PASS criterion | Severity |
|---|---|---|---|---|
| 1 | **Architecture Constitution** | `scripts/architecture.py check` | Shared Core scan: 0 NEW findings (acknowledged count ≤ previous); constitution PASS | **Mandatory (HARD)** |
| 2 | **Policy Engine** | `scripts/architecture.py check` (policy component) | All enabled policies evaluated; policy engine PASS | **Mandatory (HARD)** |
| 3 | **Domain Certification** | `scripts/architecture.py check` (domain component) + `scripts/domains.py check` | Domain certification 11/11; isolation PASS | **Mandatory (HARD)** |
| 4 | **OpenAPI** | Regenerate schema; `cmp` against committed baseline | **Byte-identical** (unless the migration deliberately changes the contract — requires an ADR + explicit approval) | **Mandatory (HARD)** |
| 5 | **Generated Clients** | OpenAPI byte-compat + frontend contract check | No generated client model changed unless backend contract required it | **Mandatory (HARD)** |
| 6 | **Frontend Compatibility** | `npx tsc --noEmit`, `npx eslint .`, `npx vitest run`, `npx vite build` | tsc 0 errors; eslint 0 errors (baseline warnings allowed); vitest all pass; build succeeds | **Mandatory (HARD)** |
| 7 | **Permissions** | Review of changed request/response paths + authorization gates | No permission touched unless ADR-approved; authorization gates PASS | **Mandatory (HARD)** |
| 8 | **Database Compatibility** | Migration chain check + schema review | No DDL change unless the finding is DB-coupled and ADR-approved; 56-migration chain intact | **Mandatory (HARD)** |
| 9 | **Behavior Preservation** | Before/after equivalence evidence in the report | Runtime/API/business/security/authorization/audit/DB behavior preserved (ADR-028 R1) | **Mandatory (HARD)** |
| 10 | **Performance** | Budget tests + p95 + query counts (`make validate` performance scope) | No new bottleneck; p95 within budget; query counts ≤ budget | **Mandatory** |
| 11 | **Regression Tests** | `ENV=test PYTHONPATH=.. .venv/bin/python -m pytest tests/ -q` + policy/unit scope | Full suite **0 failures** (≥ 4993 baseline); affected-file tests pass | **Mandatory (HARD)** |
| 12 | **Build Validation** | `backend` import/boot smoke + `compileall` gate | App boots; module parses; no import-time I/O regressions | **Mandatory (HARD)** |
| 13 | **CI** | `ai-governance.yml` gates (architecture-check HARD) | CI gates PASS on the migration commit | **Mandatory (HARD)** |
| 14 | **Repository Health** | ruff baseline, brain freshness, tsc baseline | ruff == 379 (no new); brain fresh (`make brain-check`); tsc 0 | **Mandatory** |
| 15 | **Canonical-Provider Orphan Check** | Post-migration consumer scan of the affected canonical provider | Canonical provider keeps ≥ 1 active consumer or carries explicit justification | **Mandatory** |
| 16 | *Ruff on changed scope* | `ruff check <touched files>` | 0 violations on changed scope | Advisory (turned mandatory on failure) |

### Execution order

1. Regression Tests → 2. Architecture Constitution → 3. Policy Engine →
4. Domain Certification → 5. OpenAPI + Generated Clients → 6. Frontend →
7. Permissions → 8. Database → 9. Behavior Preservation → 10. Performance →
11. Build Validation → 12. CI → 13. Repository Health →
14. Canonical-Provider Orphan Check.

Any **HARD** row FAIL ⇒ migration does not exit; executor reverts or fixes, then
re-runs the full matrix (never a partial re-run).

---

## 3. Migration Exit Criteria

A migration is **complete** only if ALL of the following hold. There are no
exceptions unless an accepted ADR documents the deviation.

| # | Condition | Evidence |
|---|---|---|
| E1 | All **HARD** verification rows PASS (matrix #1–9, 11–14) | Verification report §6 table |
| E2 | All mandatory (non-advisory) rows PASS | Verification report §6 table |
| E3 | Acknowledged-findings count **did not grow** (48 baseline; every removal reduces it) | `.ai/core/architecture/constitution_baseline.json` + gate output |
| E4 | **0 NEW findings** reported by the gate | `scripts/architecture.py check` |
| E5 | Migration is **independently reversible** by a single `git revert` (§4) | Report rollback section |
| E6 | Migration Impact Report exists with files moved/removed/replaced, duplicate code eliminated, LOC reduction, dependency changes, API impact, frontend impact, rollback (§0) | `docs/baselines/COMMIT_X_Y_VERIFICATION_REPORT.md` |
| E7 | Dead-code/archive deletion is **evidence-based** (unused/superseded/duplicated/deprecated) | Report §3 (Dead-Code Evidence) |
| E8 | Canonical provider is **not orphaned** | Report §4 (Orphan Check) |
| E9 | Dashboard + master docs + PROJECT_BRAIN regenerated and consistent | `scripts/architecture/docs.py`, `scripts/architecture.py report`, `scripts/project_brain.py --json` |
| E10 | **One implementation commit** for the migration (R7 atomicity) | git log |
| E11 | Independent review (human or reviewer engine) approved the change-set | Review record / approval |

A migration that passes E1–E11 is **certified** and its wave progresses. Any
missing E-row blocks the next migration (Stage 13 requires the current
migration certified).

---

## 4. Rollback Standard

### Requirements

1. **Independent reversibility (ADR-028 R6):** a single
   `git revert <commit-hash>` restores the exact previous state. A migration
   must never depend on another unreverted migration.
2. **Atomicity:** one migration = one implementation commit (+ one
   documentation commit for the report). Nothing partial is merged.
3. **Archive-first (ADR-028 R5):** moved code is preserved byte-for-byte in
   `archive/platform-shared-core/` before any active-tree deletion.
4. **No destructive data action:** migrations never drop/alter data without an
   explicit approved migration + rollback plan.

### Rollback expectations by rollback class

| Rollback class | Expectation | Procedure |
|---|---|---|
| **L (Low)** | Instant; zero coordination | `git revert <hash>`; redeploy |
| **M (Medium)** | Same-commit revert; consumers re-pointed back; verify post-revert | `git revert <hash>`; re-run verification matrix; confirm canonical orphan restored |
| **H (High)** | Requires data/coordination; pre-approved plan mandatory | Documented procedure in the report; staged rollback; no silent revert |

### Rollback verification

After any revert, the full verification matrix §2 is re-run on the reverted
state. A migration is not "released" until its rollback procedure is
**demonstrated or dry-run-validated** (revert on a test branch) or carries an
explicit engineering judgment that the procedure is trivially safe (class L).

---

## 5. Architecture Decision Rules

Exactly one migration class per finding (Classification doc §1). The decision
rules below are **objective and deterministic** — the inputs are canonical
completeness, consumer activity, and behavioral equivalence, all measurable.

### 5.1 Archive and Re-point

**Allowed when:**
- Canonical provider is **complete and live**; AND
- Finding is dead code, a real duplicate, or a re-pointable live consumer.

**Actions:** archive byte-for-byte to `archive/platform-shared-core/` (Rule 5);
re-point live consumers to the canonical provider with identical observable
behavior (Rule 1); evidence the deadness (Rule 2).

**Forbidden when:** the canonical provider is incomplete, or the finding
implements behavior the canonical provider lacks.

### 5.2 Canonical Provider Promotion

**Allowed when:**
- The live implementation is the **ONLY behaviorally complete** implementation
  of the capability; AND
- The canonical path is incomplete/empty; AND
- Promotion is covered by ADR-029 (already accepted).

**Actions:** promote the live implementation into the canonical path;
re-point consumers; archive the old path.

**Forbidden when:** the canonical provider already carries live behavior, or
the live implementation is not behaviorally complete (use §5.3 instead).

### 5.3 Canonical Provider Completion

**Allowed when:**
- The canonical provider exists but is **incomplete/stub**; AND
- Completing it is lower cost than any alternative; AND
- Completion preserves behavior (Rule 1) and the ADR-032/033 precedent applies
  where referenced.

**Actions:** complete the canonical provider; then migrate findings onto it.

**Forbidden when:** the incomplete provider would require behavior changes, or
a live complete implementation exists elsewhere (§5.2 applies).

### 5.4 Retain as Domain-Owned

**Allowed when:**
- The implementation belongs inside its domain (domain sovereignty, ADR-034);
- It is NOT a Shared Core violation; OR
- The canonical provider **lacks required fields/semantics** (e.g., audit
  decision-log with policy/risk fields).

**Actions:** document in the baseline register; do NOT migrate.

**Forbidden when:** the implementation genuinely duplicates a complete canonical
provider (use §5.1).

### 5.5 Strategic Exception

**Allowed when:**
- The Constitution should not automatically apply to this finding; AND
- An ADR documents the exception (ADR-030 precedent for kernel EventBus/DI).

**Actions:** accepted ADR + baseline register entry.

**Forbidden when:** no accepted ADR (a strategic exception is never implicit).

### Decision rule summary (deterministic)

| Canonical complete & live? | Finding dead/duplicate? | Finding behaviorally unique? | Class |
|---|---|---|---|
| Yes | Yes | — | **Archive and Re-point** (5.1) |
| Yes | No | No | **Archive and Re-point** (5.1) |
| No | No | Yes | **Canonical Provider Promotion** (5.2) |
| No | No | No | **Canonical Provider Completion** (5.3) |
| n/a | Domain-owned | — | **Retain as Domain-Owned** (5.4) |
| n/a | Constitution inapplicable | — | **Strategic Exception** (5.5, ADR required) |

### ADR requirement by class

| Class | ADR required? |
|---|---|
| Archive and Re-point | Only for behavior-additive re-points (audit/notification rows begin appearing) — ADR-031/032 |
| Canonical Provider Promotion | Yes (ADR-029 accepted; per-migration ADR if scope extends) |
| Canonical Provider Completion | Yes (ADR-032/033 precedent) |
| Retain as Domain-Owned | No (document in register; ADR-034 collects them) |
| Strategic Exception | **Yes** (ADR-030 precedent) |

---

## 6. Risk Escalation Rules

Implementation **MUST STOP immediately** when any of the following triggers is
observed. Stop = freeze the working tree, record the trigger, do not commit,
escalate to the approval authority (engineering lead / program owner).

| Trigger | Detection | Stop & escalate |
|---|---|---|
| **Behavior mismatch** | Before/after equivalence evidence fails; any consumer observes different output/state | STOP before commit |
| **Canonical ambiguity** | Finding maps to > 1 canonical provider, or canonical scope unclear | STOP — resolve mapping in Discovery/Architecture stages |
| **Runtime uncertainty** | Import/boot smoke fails; lazy-init order change; import-time I/O introduced | STOP, fix or revert |
| **Unexpected dependency** | Consumer graph reveals an importer not found in Consumer Analysis | STOP — redo Consumer Analysis |
| **Performance regression** | p95 / query count / budget test fails vs baseline | STOP before commit |
| **API incompatibility** | OpenAPI schema differs from committed baseline without an approved ADR | STOP |
| **Frontend incompatibility** | tsc/eslint/vitest/build fail, or a frontend consumer breaks | STOP |
| **Security regression** | Security gate fails; authorization/audit path weakened; new risk in risk register | STOP — security is a hard constitution guarantee |
| **Baseline growth** | Acknowledged-findings count increases or any NEW finding appears | STOP — findings may never grow (ADR-028 baseline policy) |
| **Certification failure** | Any E-row in §3 unverifiable | STOP before Next Migration |

**Escalation severity model:** triggers are either **blocking** (STOP, no
commit) or **review** (record + require explicit approval). Blocking: behavior
mismatch, API/frontend incompatibility, security regression, baseline growth,
runtime uncertainty. Review: canonical ambiguity (pre-implementation),
unexpected dependency, performance regression (pre-commit).

Every STOP is recorded in the dashboard risk trend (§7) and, where applicable,
`MASTER_RISK_REGISTER.md`.

---

## 7. Program Dashboard

Permanent metrics tracked in `PROGRAM-01_DASHBOARD.md`. Updated after every
migration (Stage 10). Every metric has a **definition, owner, and trend rule**
(monotonic where applicable).

| Metric | Definition | Trend rule |
|---|---|---|
| **Architecture Health** | Gate verdict (constitution/domain/country/policy) | Always PASS |
| **Technical Debt** | Active-tree LOC, duplicate implementations, archived module count | Active LOC shrinks; duplicates shrink |
| **Remaining Findings** | Acknowledged Shared Core findings in baseline | **Monotonically non-increasing** |
| **Shared Core Progress** | Findings migrated / total (48 baseline) | Monotonically increasing |
| **Migration Progress** | Certified migrations / planned (by wave) | Monotonically increasing |
| **Production Readiness** | Quality-gate summary (tests, ruff, tsc, eslint, CI) | Always green; improving |
| **Repository Size** | Active LOC vs archived LOC vs net | Active shrinks; archive grows; net stable |
| **Duplicate Implementations** | Active-tree duplicate Shared Core implementations | Monotonically decreasing |
| **ADR Count** | Accepted ADRs governing the migration phase | Monotonically increasing |
| **Risk Trend** | Open risks, escalations, STOPs | Non-increasing open risk |
| **Certification Level** | Waves certified / total (see §9) | Monotonically increasing |

### Baseline policy (reaffirmed)

- `architecture-baseline` regenerates the acknowledged-findings list. Run it
  ONLY after a completed migration that legitimately removes findings.
- The acknowledged-findings count **must never grow**.
- Country findings (2) are tracked separately and never grow.

---

## 8. Wave Execution Rules

The migration roadmap (Classification doc §6) defines waves. Every wave SHALL
declare five attributes before execution. Wave definitions here bind the
existing Wave 1–6 plan.

| Wave | Objective | Success criteria | Verification depth | Rollback expectation | Approval point |
|---|---|---|---|---|---|
| **Wave 1 (Commits 1.4–1.8, Orders 1–11)** Low-risk archive & false-positive removals | Remove dead code / false positives with zero risk | Baseline 48 → 37; all wave items certified; 0 behavior changes | Full §2 matrix (all HARD + mandatory) | L/M — single `git revert` each | Every order (R7 stop) + wave completion |
| **Wave 2 (Commit 1.9, Order 12)** Canonical Provider Promotion | Promote the only complete impl into canonical path (ADR-029/035) | #43 promoted; canonical provider live; consumers re-pointed | Full §2 matrix + OpenAPI/client/permission re-check | M — revert + consumer re-point back | Every order + wave completion |
| **Wave 3 (Commits 1.10–1.12, Orders 13–15)** Canonical Provider Completions | Complete canonical providers (notification, search, PDF), then migrate | #24+#49, #35+#36, #46+#47 completed onto canonical; ADR-032/033 accepted | Full §2 matrix + **behavior-additive** audit (audit rows / notifications begin appearing) | M/H — staged; documented plan | ADR approval + every order + wave completion |
| **Wave 4 (Commits 1.13–1.15, Orders 16–19)** High-risk infrastructure (behavior-additive / broken-but-wired) | Archive/migrate wired-but-broken reimplementations with explicit approval | #5/#9 audit re-points, #50 fabricated-success adapters, #44 wired-but-500 removed | Full §2 matrix + frontend/API surface re-check (these change observable behavior) | M/H — documented per-migration | ADR approval + every order + wave completion |
| **Wave 5 (Commits 1.16–1.18, Orders 20–22)** National Platform migrations | Migrate national-layer findings with strategic care | #2/#1 archived; #21+#30 retained via ADR-034 | Full §2 matrix + national-platform constraints review | L/M — national-layer blast radius review | Strategic exception approval + every order |
| **Wave 6 (Commit 1.19, Orders 23–24)** Kernel exception + Retain register | Document kernel EventBus/DI exception + domain-owned register | ADR-030 + ADR-034 accepted; register complete; baseline → 0 actionable findings | Documentation + gate recognition (no code movement) | n/a (no code) | ADR approval + program certification |

**Common wave rules:**

- **Objective:** reduce acknowledged findings with behavior preservation.
- **Success criteria:** all orders certified (E1–E11); baseline target hit.
- **Verification depth:** full §2 matrix always; depth augments per wave (never
  reduces).
- **Rollback expectations:** per-wave class above; class H requires a
  documented pre-approved plan.
- **Approval point:** each order stops for approval (R7) **and** wave
  completion requires a certification review (§9).

**Wave order is fixed** by the Classification doc §6 and §7 rationale (false
positives → dead archives → promotion → completion → behavior-additive →
national → kernel). A wave MAY NOT begin before the previous wave's
certification marker is set.

---

## 9. Program Certification

PROGRAM-01 is complete only when **every wave is certified** (ADR-028 Rule 7
extended to wave scope).

### Certification process

1. **Per-migration certification** — migration passes E1–E11 (§3); the
   executor records the certification marker in the dashboard.
2. **Per-wave certification** — all orders in the wave certified; full §2
   matrix re-run on the wave's final state; `architecture-check` PASS;
   baseline target for the wave met; a wave certification review (human or
   reviewer engine) approves.
3. **Program certification** — Wave 6 complete; **0 actionable findings** in
   the baseline (48 → 0); every ADR required by §5 accepted; dashboard
   `Certification Level` = all waves; final certification review approves.

### Certification evidence artifacts

- `docs/baselines/COMMIT_X_Y_VERIFICATION_REPORT.md` per migration
- `PROGRAM-01_DASHBOARD.md` with per-wave certification markers
- `PROGRAM-01_CERTIFICATION_MODEL.md` (this model, maintained)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` (execution plan)
- Accepted ADRs: ADR-028/029/030/031/032/033/034/035/036 (as applicable)
- Final `ARCHITECTURE_CERTIFICATION.md` regenerated at program close

**Certification failure** = any wave uncertified, any E-row unmet, any
unresolved escalation, or the acknowledged-findings count failing to reach 0
actionable. The program remains open until certified.

---

## 10. PROGRAM-02 Readiness

PROGRAM-02 (**Shared Core Consolidation**) may begin ONLY when the following
**objective evidence** exists. The purpose of PROGRAM-01 is to become
**self-governing** — i.e., the execution model here is itself certified as
reproducible and unambiguous before PROGRAM-02 depends on it.

### Mandatory evidence checklist

| # | Evidence | Gate | Source |
|---|---|---|---|
| P2-1 | **PROGRAM-01 certified** — all waves certified; **0 actionable findings** in baseline | HARD | §9 certification + `architecture-check` |
| P2-2 | **Execution framework proven** — ≥ 2 consecutive certified migrations with zero escalations and identical report structure | HARD | Dashboard certification log |
| P2-3 | **Gate reproducibility** — `architecture-check` green on the certified state, deterministic across 3 consecutive runs | HARD | CI + local runs |
| P2-4 | **No NEW findings** for ≥ N consecutive migrations (N = 3) | HARD | Gate outputs history |
| P2-5 | **Canonical catalog complete** — `SHARED_CORE_CATALOG` providers all complete, live, and ≥ 1 active consumer each | HARD | Orphan checks + catalog |
| P2-6 | **Rollback exercised** — ≥ 1 real revert (or demonstrated dry-run) of a migration succeeded and re-verified | HARD | Revert record + re-run matrix |
| P2-7 | **OpenAPI contract frozen** — schema byte-identical over the last M migrations (M = 2) | HARD | `cmp` history |
| P2-8 | **Frontend contract frozen** — tsc/eslint/vitest/build green on certified state | HARD | §2 matrix history |
| P2-9 | **Risk register clean** — no open HIGH program risk; escalations closed | HARD | `MASTER_RISK_REGISTER.md` |
| P2-10 | **Self-governance demonstrated** — a fresh executor (agent/human not involved in Commits 1.1–1.6) runs one full migration lifecycle on a NEW finding using only this framework, and it passes all gates without deviation | HARD | Recorded lifecycle run |

### PROGRAM-02 scope boundary

PROGRAM-02 begins with consolidation of the (now canonical) Shared Core
providers across the platform — it does **not** re-litigate PROGRAM-01
classifications. PROGRAM-01 self-governance means: the framework + dashboard +
certification model are the permanent operating manual; no per-commit ad-hoc
decisions are required.

---

## Governance & Maintenance

- **This framework is the single source of execution truth.** It may be
  amended only by an accepted ADR (or a documented constitution amendment),
  never ad hoc.
- **Docs regenerated on any framework change:** `scripts/architecture/docs.py`,
  `scripts/architecture.py report`, `scripts/project_brain.py --json`.
- **Audit trail:** every migration's lifecycle stages are recorded in the
  dashboard + per-commit report, making Stage 11 (Independent Review) and
  Stage 12 (Certification) verifiable.

---

## Appendices

### A. Command inventory (run from repo root)

| Purpose | Command |
|---|---|
| Gate (all) | `backend/.venv/bin/python scripts/architecture.py check` |
| Baseline regen | `backend/.venv/bin/python scripts/architecture.py baseline` |
| Master docs regen | `backend/.venv/bin/python scripts/architecture/docs.py` |
| Certification docs | `backend/.venv/bin/python scripts/architecture.py report` |
| Policy | `backend/.venv/bin/python scripts/architecture.py policy` |
| Domain | `backend/.venv/bin/python scripts/domains.py check` |
| Brain | `backend/.venv/bin/python scripts/project_brain.py --json` |
| Fast validation | `backend/.venv/bin/python scripts/enterprise_validation_engine.py --scope fast` |
| Full backend suite | `ENV=test PYTHONPATH=.. backend/.venv/bin/python -m pytest tests/ -q` |
| Offline/live consumer scan | `grep -rn "<symbol>" backend/ shared/ scripts/ frontend-v3/ --include=*.py --include=*.ts --include=*.tsx` |

### B. Report template contract

Every `COMMIT_X_Y_VERIFICATION_REPORT.md` MUST contain sections §0 (Migration
Impact Report per ADR-028 R4), §1 (metrics), §2 (changes), §3 (dead-code
evidence), §4 (orphan check), §5 (behavior preservation), §6 (verification
matrix with PASS/FAIL), §7 (baseline reduction), §8 (backend-as-source-of-truth),
§9 (notes). Template: `docs/baselines/COMMIT_1_6_VERIFICATION_REPORT.md`.
