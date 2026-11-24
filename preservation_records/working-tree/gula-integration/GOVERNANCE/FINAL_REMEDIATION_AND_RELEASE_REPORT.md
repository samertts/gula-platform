# Final Remediation and Release Report

**Program:** GULA Stable v1.0.0 — Repository Unification
**Repository (worktree):** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2827c1ff` (= `origin/main`, 0/0)
**Report date:** 2026-11-17
**Release verdict:** **HOLD — do not release to production.**
**Commits / pushes / merges / PRs / deploys performed:** **0 / 0 / 0 / 0 / 0**

---

## 1. Executive summary

This cycle closed the one release blocker that had a deterministic fix (the backend dependency
audit), proved the existing-database upgrade path in both directions on disposable clones, and
converted a partly-unknown national surface into an evidence-based inventory, contract set and
wave-planned roadmap. It did **not** close the release hold.

| Area | Verdict |
|---|---|
| Backend dependency security (criterion 11) | **CLOSED — 0 known advisories, three independent audits exit 0, 72-pin fresh resolution reproducible** |
| Existing-database upgrade (criterion 5) | **PARTIAL — forward upgrade and full-teardown rollback proven; still NOT MET on four items** |
| Backend unification (services, routes, tests) | **PASS — 1 measured wiring gap (4 routes not delegating, 2 216 LOC duplicated)** |
| Frontend unification | **PASS with classified drift (101 unresolved calls, 28 verb mismatches)** |
| Security remediation (S-01…S-13) | **REMEDIATED in working tree — UNREVIEWED; 11 residuals (R-01…R-11) open** |
| Security certification | **NOT CERTIFIED** (no human sign-off, no pen test) |
| National service inventory (18 services) | **COMPLETE — 0 STABLE, 5 DRAFT, 11 BLOCKED, 3 NOT IMPLEMENTED/ANALYTICS** |
| National contracts | **COMPLETE as a gate — no service may be unified until its contract leaves DRAFT** |
| Integration roadmap | **COMPLETE — W0…W7 with entry gates, exit evidence, rollback** |
| Database portability (fresh install) | **PASS (433 tables, deterministic)** |
| Database portability (existing install) | **PARTIAL** |
| **Release candidate** | **HOLD** |

**The single most important new finding:** `alembic check` / autogenerate **cannot run at all**
(`NR-011`). `ehr_allergies.encounter_id` references `national_encounters`, a table that is defined in
the ORM, imported by no migration env, created by no revision and absent from every migrated
database. Until that is repaired, the **426 unmigrated ORM tables** (407 of 833 migrated; 18 of 40
contexts fully covered) cannot be closed with the tool that is supposed to close them.

---

## 2. Work performed, phase by phase

### Phase 0 — Resumption and baseline (`GOVERNANCE/RESUMPTION_STATUS.md`)

The prior session stopped because the operator session was interrupted, not because of a failure;
the residual network throttling (~13–33 kB/s) was recorded as the environmental constraint. Baseline
state was re-measured before any change: HEAD `2827c1ff`, 0/0 vs `origin/main`, full suite
**3 447 passed / 27 skipped / 0 failed**.

### Phase 1 — Dependency remediation (criterion 11) — **CLOSED**

| Item | Evidence |
|---|---|
| Starting position | **55 known vulnerabilities in 6 runtime packages** — `pillow` 12.3.0 (42), `pyasn1` 0.6.4 (4), `urllib3` 2.7.0 (3), `joserfc` 1.7.4 (2), `dnspython` 2.8.0 (2), `certifi` 2026.6.17 (2) |
| Policy applied | **Minimum safe fix** per package (`pillow==13.0.0`, `joserfc==1.7.6`, `certifi==2026.10.18`, `dnspython==2.9.2`, `pyasn1==0.6.5`, `urllib3==2.8.0`, `idna==3.20`) plus security **floors** in `requirements.txt`. `cryptography` deliberately **not** shadowed (out of scope; collides with the venv's `pyopenssl`) |
| Fresh resolution | `uv 0.11.26 pip compile` on the **same manifests, same index, same interpreter (3.12.13)** → **exit 0, 72 pins, byte-identically reproducible** |
| Audits | Lock audit **exit 0**, fresh-resolution audit **exit 0**, installed-set audit **exit 0** — all *"No known vulnerabilities found"* |
| Behaviour compatibility | **33/33** behaviour-only tests (no version assertions) pass on **both** the old and the new set |
| Regulation | Targeted **225 passed**; full suite **3 480 passed / 27 skipped / 0 failed** (506.93 s) — **+33 vs baseline** (the new compat tests), **0 regressions** |
| Method disclosure | Two `pip` wheel-download attempts failed **only** at the network layer (`ReadTimeoutError`, exit 2, process terminated). Recorded as **BLOCKED by network throttling**, **not** as a resolution failure. A `pip`-based install was never claimed |

`DEP-AUDIT-BACKEND` is **VERIFIED**; `FINAL_DECISION.md` criterion 11 is **MET**.

### Phase A — National service inventory — **COMPLETE**

`GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (432+ lines): all **18 services** with per-service
verdicts, evidence, shared dependencies, duplicates, missing APIs/migrations/tests, authorization and
audit gaps, a dependency map, 7 user journeys, and ADR candidates A–J. Evidence rule applied: a
directory or keyword match alone is **not** proof of a live service.

Notable corrections produced by this phase:

* **Insurance is UNSERVED/BLOCKED** — 5 live operations, while `backend/app/insurance/api/*`
  (**84 endpoints**) is imported by nothing. Two competing claims implementations exist
  (`routes/claims.py` live vs `insurance/api/claims.py` unserved) → **ADR-I**.
* **`care_continuum` is a cross-cutting host**, not a service (primary care, maternal/child,
  immunization, chronic, referral, home care, public health). Dental/rehab/mental-health are signals
  only → **ADR-C**.
* **Offline durability is in-memory only** (`services/offline_sync_service.py`) → **ADR-J**.

### Phase B — National service contracts — **COMPLETE (as a gate)**

`GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md` (469 lines): cross-cutting primitives, DB ownership rules
(R-DB-1/2: **no shared DB ownership**, no uncontrolled cross-service writes), per-service contract
rows, the unification gate, journeys J1–J7, binding rules **R-UNI-1…8**, ADR-A…J.

**Gate result: 0 STABLE · 5 DRAFT (01, 04, 05, 06, 18) · 11 BLOCKED · 3 NOT IMPLEMENTED/ANALYTICS.**
No service may be unified before its contract document exists and leaves DRAFT — this is why the four
`admin`/`test_result`/`lab`/`sample` services were **not** unified this cycle.

### Phase D — Integration roadmap — **COMPLETE**

`GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md`: deterministic 6-axis score (M/P/R/C/D/T), a 19-row
priority table, waves **W0…W7** with entry gates, exit evidence and rollback per wave, a
journey→wave map, and a parallel remediation track. W1's exit evidence explicitly requires the **full
suite against a migrated clone with `create_all` disabled** — that run has **not** been executed and
is the honest gate on the strict-schema claim.

### Phase C — Existing-database rehearsal — **PARTIAL (forward + rollback proven)**

Full detail: `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md`; summary appended to
`DATABASE_COMPATIBILITY_REPORT.md` §10. **Disposable clones only** (`CREATE DATABASE … TEMPLATE`); the
operational database `gula` was never migrated, stamped, dropped or written.

| Test | Result |
|---|---|
| **T1 Forward upgrade** from `20260815_0022` (405 tables, 51 rows) | **PASS** — exit 0, 17 s, **20 revisions across 3 branches**, rev `20261114_0006`, **433 tables**; **all 50 business rows identical with identical per-table MD5** (only `alembic_version` changed) |
| Structural delta vs fresh build | **Exactly 2 lines** — `pharmacy_drug_catalog.id` keeps a legacy `DEFAULT nextval(...)` inherited from `0022`. No table/column/type/index/constraint difference → **NR-012** |
| **T2 Determinism** | fresh build ≡ `downgrade base` → `upgrade head`: fingerprint `3b2d9499…6f973568`, **0 diff lines** |
| **T3 Partial/block rewind** to `20260815_0022` | **FAILURE MODE** — exit **0** but **2 `alembic_version` rows** and **7 residual tables** (`blood_bank_*` ×6 + `clinical_command_receipts`), 412 tables instead of 405. `0022` is not an ancestor of the blood-bank branch, so Alembic unwinds only part of the graph. **Exit 0 does not mean "restored"** |
| **T4 Full-teardown rollback** | **VERIFIED** — `downgrade base` exit 0 (25 s, 0 version rows, 4 residual tables = `alembic_version` + the 3 documented reference tables) → `upgrade head` exit 0 (81 s, 433 tables, fingerprint **identical to fresh**) |
| **T5 `alembic check`** | **FAIL (9 s)** — `NoReferencedTableError: ehr_allergies.encounter_id → national_encounters` → **NR-011** |
| **T6 ORM↔migration coverage** | **407 / 833** tables (48.9 %), **426 missing**, **18 / 40** contexts covered |

Hospital correction (additive, supersedes arithmetic only): **13 of 14** hospital tables are
unmigrated — the only migrated one is `hospital_surgical_safety_checklists` (`20260820_0004`); the
earlier "12" **omitted `bed_assignments`**; `hospital_operation_theaters` is **never created**, it is
only a conditional-FK target.

---

## 3. Release conditions — independent verdicts

`FINAL_DECISION.md` defines 11 exit criteria; the program charter adds 3 release conditions
(12–14). **Three of fourteen are MET.**

| # | Condition | Verdict |
|---:|---|---|
| 1 | S-01/S-02 closed — control-plane authorization, token-derived actor/approver, two-person rule | **MET in working tree (UNREVIEWED)** |
| 2 | S-03…S-05 closed — identity store, lifecycle/pilot/governance writes, audit actor | **MET in working tree (UNREVIEWED)** |
| 3 | Unguarded endpoints reduced to public-by-design, remainder allow-listed and reviewed | **MET in working tree (UNREVIEWED)** — 69/69 classified, 0 residual gaps |
| 4 | S-06/S-07 closed — fail-closed on Redis loss, `Secure` cookies on HTTPS | **MET in working tree (UNREVIEWED)**; residual R-06 open |
| 5 | `MIG-EXISTING` with row/checksum reconciliation + ambiguous-table owner | **NOT MET** — (a) ADR-B ownership, (b) rollback procedure not a recorded decision, (c) 51-row snapshot ≠ production-like, (d) NR-011 |
| 6 | Full backend suite green after the security changes | **MET** — 3 480 / 27 / 0 |
| 7 | Human security review sign-off against report **and** remediation diff | **NOT MET** |
| 8 | Frontend drift reduced or formally accepted per page | **NOT MET** (classified; product decision) |
| 9 | Four unwired extractions connected (or duplicated bodies deleted) with OpenAPI diffed | **NOT MET** — gated on contract/exception mapping (`DomainError`→`build_error_payload` vs `HTTPException`→`public_http_detail`) |
| 10 | S-13 closed, no privilege path to a professional role, R-01…R-11 fixed or accepted | **MET in working tree (UNREVIEWED)**; **residuals open** → acceptance belongs to 7/9 |
| 11 | Backend dependency audit with 0 advisories | **MET — CLOSED this cycle** |
| 12 | All 18 services inventoried and contracted with evidence | **MET (documents)** — inventory + contracts + gate produced; **0 services contract-STABLE** |
| 13 | No shared DB ownership / no uncontrolled cross-service writes | **MET as a rule** (R-DB-1/2 written and enforced by the gate); **not yet met in code** for services that share tables |
| 14 | Final report + change manifest + Git readiness produced, nothing committed | **MET** by this report, `CHANGE_MANIFEST.md`, `GIT_READINESS_REPORT.md` |

Verdict: **HOLD**. Conditions 5, 7, 8 and 9 are **NOT MET**, and conditions 1–4 and 10 are
*remediated but unreviewed* — by the program's own rule, unreviewed remediation is not closure.

---

## 4. Blocker register after this cycle

Full register: `GOVERNANCE/UNIFICATION_BLOCKERS.md` (**30 tracked rows**).

**Closed / verified this cycle**

| ID | Result |
|---|---|
| `DEP-AUDIT-BACKEND` | **VERIFIED** — three audits exit 0, 72-pin reproducible resolution |
| `NR-010` (full round trip) | **FIXED** — `downgrade base` → `upgrade head` verified byte-identical on a disposable clone; **partial rewind is a documented failure mode** |
| `TEST-SUITE-FULL` | **PASS** — 3 480 / 27 / 0 |
| `MIG-TAIL` | **RESOLVED** — full fresh chain validated |

**New this cycle**

| ID | Sev | Finding |
|---|---|---|
| **NR-011** | **P0** | `alembic check`/autogenerate abort — `ehr_allergies.encounter_id → national_encounters` (defined `backend/app/national/domain/encounter.py:9`; `migrations/env.py:38` imports only `app.national.base`; in no migration, no migrated DB). Mechanical blocker for the 426-table gap |
| **NR-012** | P2 | Legacy `DEFAULT nextval('pharmacy_drug_catalog_id_seq')` preserved on `pharmacy_drug_catalog.id` (varchar after `0023`); 2-line structural delta; not an upgrade defect (ORM supplies ULIDs) |

**Still open (unchanged or refined)**

`MIG-EXISTING` (PARTIAL), `NR-010-RESIDUAL` (3 reference tables, ADR-B), `NR-006`, `NR-007`,
`LINT-MYPY-PORTED` (71 errors), `CI-RUN-EVIDENCE`, `AUDIT-COVERAGE`, `SECURITY-PRIVACY`
(PARTIAL — NOT CERTIFIED), `SEC-AUTHZ`/`SEC-NIAM`/`SEC-CTRL` and the rest of the P0 security rows
(REMEDIATED — **unreviewed**), `FRONTEND-DRIFT`, `NR-006-dupe` (PARTIAL — 4 routes unwired).

---

## 5. Architectural decisions required before further work

None of these has been implemented; each is a schema/ownership/activation change that needs approval.

| ADR | Decision needed | Blocks |
|---|---|---|
| **ADR-A** | Migration strategy for **426 unmigrated tables** (833 ORM / 407 migrated / 18 of 40 contexts). Ordering prerequisite: fix **NR-011** (`env.py` national imports + a revision creating `national_encounters`) | Any strict-schema release, W1 exit evidence |
| **ADR-B** | Ownership of `facilities` / `organizations` / `national_facilities` (downgrade residuals, two ORM packages map `national_facilities` → `NR-006`) | Criterion 5 |
| **ADR-C** | `care_continuum` decomposition vs permanent cross-cutting host | Contract 07, W2 |
| **ADR-D** | Audit coverage + replacement for blanket `system:admin` actors | Criteria 7, 10 |
| **ADR-E** | Public token/phone access model | Contract 04 |
| **ADR-F** | Lab duplication (`lab_service` vs inline `routes/labs.py`) | Criterion 9 |
| **ADR-G** | Insurance provisioning (5 live ops vs 84 unserved endpoints) | Contracts 05/06 |
| **ADR-H** | Shared Core boundary (what may be imported across domains) | All contracts |
| **ADR-I** | Register or archive the unserved `backend/app/insurance/api/*` | Insurance verdict |
| **ADR-J** | Offline durability (in-memory engine cannot survive restart) | Offline-first guarantee |

A recorded rollback procedure is also required: **snapshot restore**, or **`downgrade base` +
`upgrade head`** in a maintenance window. A partial rewind to a prior release revision is **unsafe**
and must never enter a runbook.

---

## 6. Residual risk

| Risk | Severity | Mitigation state |
|---|---|---|
| Strict-schema deployments fail because 426 ORM tables have no migration | **Critical** | Unmitigated; `conftest.py:104-148` `create_all()` **masks** the gap in tests |
| Rollback runbook error (partial rewind looks successful, exit 0) | **Critical** | Known and documented; not yet enforced by a gate |
| Security remediation is unreviewed | **Critical** | 10 regression files pass; human sign-off absent |
| Production-sized upgrade never rehearsed (51-row snapshot) | High | Phase C proves mechanics only |
| `national_encounters` metadata gap | High | NR-011 recorded; not repaired |
| 2 216 LOC of live duplicated business logic in 4 routes | High | Criterion 9 open |
| MyPy 71 scoped errors, ruff 35 pre-existing | Medium | Baseline maintained, not improved |
| Insurance API surface (84 endpoints) drifting unserved | Medium | ADR-I pending |

---

## 7. Deliverables produced

| Artifact | Purpose |
|---|---|
| `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md` | **new** — full Phase C evidence, reproduction commands, evidence index |
| `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` | 18 services, evidence, §15.1–§15.4 (hospital 13/14, Phase C impact) |
| `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md` | contract gate, DB ownership, R-UNI-1…8, ADR-A…J |
| `GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md` | scored priority table, waves W0–W7 |
| `GOVERNANCE/CHANGE_MANIFEST.md` | **new** — 188 working-tree entries, 0 commits, 20 `R100` renames |
| `GOVERNANCE/GIT_READINESS_REPORT.md` | **new** — topology, upstream state, hygiene, staging sequence |
| `GOVERNANCE/ADR_DECISION_REQUEST.md` | **new** — ADR-A…J submitted for approval (options, recommendation, unblocks, reversibility); **nothing implemented** |
| `GOVERNANCE/UNIFICATION_BLOCKERS.md` | NR-010/MIG-EXISTING re-stated, NR-011/NR-012 added, `DEP-AUDIT-BACKEND` VERIFIED |
| `GOVERNANCE/FINAL_DECISION.md` | criteria 5/11 updated, §6 unverified table corrected — **verdict still HOLD** |
| `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md` | §10 appended (append-only; §1–§9 untouched) |
| `GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md` | §6.1 fresh-resolution + audit evidence |
| `SECURITY_REMEDIATION_REPORT.md` (repo root) | addendum A1–A3; path discrepancy noted (the tracked security record is at repo root, not under `GOVERNANCE/`) |
| `GOVERNANCE/EXECUTION_LEDGER.md` | §3.1 Phase 1 and §3.2 Phase C command/exit tables; §4 blockers 1/2/2a/2b/15 rewritten |

---

## 8. What is **not** claimed

* **Not production ready.** Not clinically certified. Not security certified. Not released.
* **Not "MIG-EXISTING verified"** — forward and rollback mechanics are proven; criterion 5 remains
  NOT MET on four explicit items.
* **Not "426 tables fixed"** — the gap is measured, not closed, and **cannot** be closed by
  autogenerate until NR-011 is repaired.
* **Not "partial downgrade works"** — it is proven to be a silent partial reversal.
* **Not "rollback runbook defined"** — the supported paths are identified; the decision is not recorded.
* **Not "dependency install verified via pip"** — that path is **BLOCKED by network throttling**;
  resolution and audit were proven with `uv` metadata and three independent audits.
* **Not "services unified"** — 0 contracts are STABLE; the four route extractions are still unwired.
* **Not "security closed"** — remediation is unreviewed and residuals R-01…R-11 are open.
* **Nothing was committed, pushed, merged, opened as a PR, or deployed.** No operational database was
  written to. `gula-platform` and `Platform-Core` were not modified. No test was deleted, skipped or
  weakened.

---

## 9. Required next actions (in order)

1. **Program Director:** review the security remediation diff and authorise commit (criterion 7),
   then record the rollback-procedure decision (snapshot restore, or `downgrade base` + `upgrade head`).
2. **Database owner:** assign ownership of `facilities` / `organizations` / `national_facilities`
   (**ADR-B**) and approve **ADR-A** with **NR-011** as its first task.
3. **Architecture:** decide ADR-C, ADR-D, ADR-G, ADR-I, ADR-J; ADR-E/F/H as their waves open. All ten
   are submitted with options, recommendation, impact and reversibility in
   **`GOVERNANCE/ADR_DECISION_REQUEST.md`** — none is implemented.
4. **Engineering:** wire the four route extractions against the contract mapping (criterion 9) — only
   after ADR-F/contracts exist.
5. **QA:** execute the strict-schema suite (migrated clone, `create_all` disabled) as W1 exit evidence.
6. **Product:** formally accept or fix the frontend drift per page (criterion 8).

Only when conditions 1–14 are independently proven may `FINAL_DECISION.md` move off **HOLD**.
