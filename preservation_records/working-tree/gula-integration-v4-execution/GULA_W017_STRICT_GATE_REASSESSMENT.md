# GULA W-017 Strict Quality Gate — Read-Only Reassessment

| Field | Value |
|---|---|
| **Directive ID** | `W017-STRICT-GATE-READONLY-REASSESSMENT-001` (subagent read-only reassessment deliverable — **not** an authorized gate re-run) |
| **Repository** | `/home/samertts/workspace/projects/gula-integration` |
| **Branch** | `integration/gula-unification-v1` |
| **HEAD** (`git rev-parse HEAD`) | `2206654dc713ea2de8c564a3207dfe05fde23549` |
| **Date** | 2026-11-19 |
| **Scope** | Reassess the W-017 strict quality gate from static evidence only; produce this one file and nothing else |

## Method statement

Read-only reassessment. Tools used: `git rev-parse` / `git status` / `git ls-files`, `grep`, `glob`, `find`, `sed`/`cat`, in-file reads, and one pure-arithmetic `python3 -c` (integer addition of documented classification counts). **No** pytest, Alembic, psql, docker, DB connection, staging, commit, push, merge, PR, or worktree operation was performed. A full backend pytest suite is running on this 2-CPU host; no competing process was started. No threshold was lowered, no gate altered, no test edited, no missing evidence fabricated, and the blocked PostgreSQL execution was not attempted.

## Strict-status summary

| Object | Status (strict vocabulary) | Basis |
|---|---|---|
| W-017 gate as a whole | **FAILED** (historical, E-001 2026-11-17) and **BLOCKED** for fresh re-execution | No trigger, no PG16 clone/artifact, no authorization for live re-run |
| Fresh re-execution of the gate | **BLOCKED** | Missing external harness, missing PG16 disposable clone, missing documented trigger; A07/owner authorization required (QA_AUDIT A09-004) |
| Deterministic read-only recomputation of the score from in-repo artifacts | **TESTED** — current score from existing artifacts = **119 failures** | Classification sum 43+33+20+4+4+4+4+4+2+1 = 119 (§3) |
| Raw gate artifact under QA_AUDIT A09-004 P1 | **BLOCKED** (absent) | All referenced `/tmp/opencode/...` paths missing; no XML/log/manifest anywhere in repo (§5) |
| Independent verification of the historical 753/119 result | **BLOCKED** | Raw per-test artifacts unavailable; only summarized documentation remains |
| This reassessment | **BLOCKED** (fully concluded as a read-only assessment; cannot promote to verified) | Evidence gap + authorization boundary |

**Never claimed here:** `INDEPENDENTLY VERIFIED`, `PRODUCTION READY`, a fresh pass/fail number, or any release/deployment action.

## Explicit non-claims

1. **No PRODUCTION READY** and **no INDEPENDENTLY VERIFIED** status is awarded to W-017 or to this reassessment.
2. **No release, deployment, gate re-run, or PostgreSQL execution** was performed or authorized by this work.
3. **No owner approval is invented.** D-001/D-003 are recorded as approved (project owner, 2026-11-17); D-020/D-021 remain `PENDING_APPROVAL`; no new approval is asserted.
4. **Standing decision HOLD** (`GOVERNANCE/FINAL_DECISION.md`, md5 `effdfeaf10234678d83b2668c4489552`) is unchanged. W-017 remains `FAILED`; HOLD must not become GO on the strength of this report.
5. Historical numbers are preserved verbatim and are **not** treated as current/fresh evidence.

---

## 1. Exact gate definition

**Work item:** `W-017` — "GULA-017 W1 strict-schema functional validation" (workstream `W1-GATE`), owner **QA Lead**, priority **P0**.
Source: `GOVERNANCE/GECS/WORK_REGISTRY.md:40`; execution record `GOVERNANCE/EXECUTION_LEDGER.md:30`; alternate ledger row `GOVERNANCE/EXECUTION_LEDGER.md:113`.

| Element | Exact value (source) |
|---|---|
| Question answered | Does the backend suite pass against a PostgreSQL DB whose schema was created **exclusively by Alembic migrations** — no `create_all()`, no test-side DDL, no `alembic stamp`? (`GOVERNANCE/W1_CHECKPOINT.md:15-21`) |
| Acceptance criterion / threshold | **872/872 on a migration-built schema** (`WORK_REGISTRY.md:40`, `BLOCKER_REGISTRY.md:26`); repeat twice with fingerprint delta = approved migrations only (`W1_CHECKPOINT.md:179-180`) |
| Result at last execution | **753 passed / 119 failed / 0 skipped (872)** — exit 1 — `FAILED` (E-001, 2026-11-17) |
| Executable | **No in-repo executable exists.** The gate was an external harness at `/tmp/opencode/strict-w1/` (`W1_CHECKPOINT.md:30`, `DATABASE_COMPATIBILITY_REPORT.md:323-326`). Command recorded: `STRICT_DATABASE_URL=<clone> pytest tests -q` (`EXECUTION_LEDGER.md:113`); run #2 with `--junitxml` (`:114`). |
| Config / conftest | Strict `conftest.py`: PostgreSQL only, asserts revision `20261114_0006` and table count **433**, savepoint-only isolation, **no DDL** (`W1_CHECKPOINT.md:29-36`). `pytest.ini` at harness root (`:201`). |
| Input files | **53 test modules / 872 tests**, byte-identical copies verified by `sha256_manifest_full.txt` (`:32`, `:199`); selection rule at `:33`; source-fingerprint `3b2d9499…6f973568` before/after (`:35`). |
| Target DB | Disposable PG 16.14 clone `gula_w1_strict_20261117` from `gula_unify_full`, 433 tables (`W1_CHECKPOINT.md:29`). |
| Ownership of method | D-018 **VERIFIED (DECIDED + EXECUTED)**: validate only against a disposable migration-built clone with byte-identical test copies outside the repo; no test/fixture/migration/production edit to obtain a pass; never rerun without trigger (`DECISION_REGISTRY.md:68`). |
| In-repo reference to the harness | Only a comment: `backend/migrations/env.py:53` ("probe C baseline: /tmp/opencode/strict-w1/alembic_probe_c"). No runnable script, no gate config, no thresholds file in the repository. |

**Conclusion (task 1):** The gate is defined entirely in governance markdown; its executable, conftest, manifest, and raw results lived **outside the repository** under `/tmp/opencode/` and are not reproducible from the checkout alone.

## 2. Can the gate be re-executed read-only? — **BLOCKED**

No. Re-execution requires all of the following, none of which is available under this read-only mandate:

1. **Environment (PG16 artifact):** a disposable PostgreSQL 16 clone with `STRICT_DATABASE_URL` set and revision `20261114_0006`/433-table schema built by Alembic only (§1). That clone no longer exists in this session; provisioning it is a DB operation, explicitly forbidden (and "provisioning a disposable DB is explicitly constrained by program control" — `QA_AUDIT.md:259`, A09-013).
2. **Authorization:** QA_AUDIT **A09-004 P1** states "Approval required? **Yes** — A07 + owner decision; Wave D must re-run an approved gate and capture artifacts" (`docs/parallel-program/qa/QA_AUDIT.md:196`). A09 is forbidden from executing gates (Wave A) — `SR-A09-06` (`:300`). No such authorization is present in this task.
3. **Documented trigger:** GECS hard rule — "Do not rerun a completed test without a documented trigger (new evidence, changed files, failed acceptance criterion, newly discovered dependency)" (`DUPLICATE_PREVENTION.md:32-33`); "FAILED results are evidence, not invitations to re-run" (`:37-38`); "Re-run the 872-test suite to see current state" → `BLOCKED_PENDING_APPROVAL` (`:45`). No trigger is recorded.
4. **The harness itself:** `/tmp/opencode/strict-w1/` (conftest, pytest.ini, 53 copied modules) is missing from this host (§5). Even with authorization and a clone, the byte-identical harness would have to be reconstructed, which is itself a change to the evidence basis.

Marking precisely: **fresh re-execution = BLOCKED** (missing A07/owner authorization, missing PG16 disposable clone artifact, missing documented trigger, missing external harness). No number is invented for a run that was not performed.

## 3. Deterministic read-only recomputation from existing artifacts — current score = **119 failures** (from artifacts; NOT a fresh execution)

The raw per-test artifacts (JUnit XML, classification JSON) are absent, so a from-scratch recount of individual test node IDs is impossible. A **deterministic arithmetic recomputation** is possible from the classification counts preserved in three independent in-repo governance documents.

Command (pure file parsing / arithmetic only):

```
python3 -c "print(43+33+20+4+4+4+4+4+2+1)"
# -> 119
```

Sources of the ten counts — all agree exactly:
- `GOVERNANCE/W1_CHECKPOINT.md:60-71` (table "Remaining failures by class (run #1 = 119)")
- `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md:360-371` (§11.3 "Authoritative failure classification")
- `GOVERNANCE/EXECUTION_LEDGER.md:117`

The written arithmetic in `DATABASE_COMPATIBILITY_REPORT.md:373-377` independently reconciles to the same figure: 76 direct table/column + 4 cascade + 2 type + 1 FK = 83; +20 runtime-guard + 4 trigger = 107 schema-dependent; +4 harness + 4 id-assumption + 4 downstream assertions = 119.

**Result: current score reconstructed from existing artifacts = 753 passed / 119 failed / 0 skipped (872).** This is a recomputation of the *historical* E-001 result from preserved summaries, **not** a fresh execution and **not** independent verification (raw node-level evidence is unavailable).

## 4. Failure classification (119 from run #1) with representative evidence

| Category | Count | Examples / file:line evidence |
|---|---:|---|
| **Real defects (schema/migration parity)** — `MIGRATION_COLUMN_DRIFT` 43 + `MIGRATION_MISSING_TABLE` 33 + `PG_TYPE_OVERFLOW` 2 + `FK_ENFORCEMENT` 1 + `CASCADE_FAILURE` 4 | **83** | `fin_providers.provider_type` ×29, `radiology_exams.exam_code` ×4, `pharmacy_drug_catalog.code` ×3 (`DATABASE_COMPATIBILITY_REPORT.md:362`); `gov_national_audit_events` ×10, `fin_pricing_rules` ×7, `fin_invoices` ×5, `national_patients` ×3, `ehr_conditions` ×3 (`:363`). Hottest files: `test_pricing_service.py` 22 failures (`ARCHITECTURE_DECISION_PACKAGE_W1.md:1158`), `test_financial_phase_b.py` 21 = 16 drift + 5 missing (`:896`). `disk_free_bytes` migrated as `integer` (`:370`); ICU/LIMS FK correction (`:371`). `national_encounters`, `ehr_conditions`, `exam_code` appear in **no migration file** (`W1_CHECKPOINT.md:97-98`). Schema gap: 756 ORM tables per base / 416 present / **340 missing**; **82 tables / 664 columns** missing (`:82-86`). |
| **Dependencies on unavailable runtime / schema-dependent behaviors** — `RUNTIME_GUARD` 20 + `AUDIT_APPEND_ONLY_TRIGGER` 4 | **24** | All 20 `tests/test_edge_platform` cases raise `RuntimeIsolationError` on the migrated schema (`DATABASE_COMPATIBILITY_REPORT.md:364`); 4 audit-hash-chain tamper tests hit the migrated append-only `audit_logs` trigger, absent from the `create_all()` control (`:365`). The append-only trigger is a **required** design property, so this is a control/schema-behavior mismatch, not a defect to "fix" by weakening the guard (`W1_CHECKPOINT.md:149-150`). |
| **Invalid / outdated rules or test/harness assumptions** — `HARNESS_PATH_ARTEFACT` 4 + `ID_SEQUENCE_ASSUMPTION` 4 + `OTHER` 4 | **12** | 4 failures are `FileNotFoundError` from source reads relative to the external harness root — explicitly "classified, not hidden" (`W1_CHECKPOINT.md:67`, `DATABASE_COMPATIBILITY_REPORT.md:339-341`); 4 `test_communication_experience` cases assume sequential ids (`:367`); 4 downstream placeholder-style assertions (`assert 404 == 200` ×2, `assert False is True`, `assert 0 > 0`) (`:369`). Every one passes under the SQLite control. |
| **Dependencies on owner decisions** (not failure counts, but why the 119 persist) | — | ADR-A migration strategy (D-001, approved but **not implemented**), NR-011 two-part fix (D-003, approved but **not implemented**) (`DECISION_REGISTRY.md:17,19`); ADR-B table ownership (`W1_CHECKPOINT.md:161`); rollback-procedure choice (`:162`); D-020/D-021 human sign-off `PENDING_APPROVAL` (`DECISION_REGISTRY.md:70-71`). |

Arithmetic: 83 + 24 + 12 = 119. Reconciles with §3 and with the "107/119 schema-dependent" statement in `DATABASE_COMPATIBILITY_REPORT.md:375`.

Four P0 patient-workflow modules fail on the migrated schema (all green under control): ICU/LIMS 6/7, emergency surgery 2/4, pharmacy/radiology 1/3, pharmacy POS 0/3 (`W1_CHECKPOINT.md:50-53`; `DATABASE_COMPATIBILITY_REPORT.md:383-389`). These are **not** a subset that can be waved through; every one of the 119 passes under the control, proving the failures are schema-induced, not pre-existing test defects (`:355-356`).

## 5. Raw gate artifact under QA_AUDIT A09-004 P1 — **BLOCKED (absent)**

A09-004 states: "no raw artifact to verify" — "repository-wide search: 0 XML results, 0 `.log` files" (`docs/parallel-program/qa/QA_AUDIT.md:191-192`) and `TEST_RESULTS.md:55` marks the claim `CLAIM — UNVERIFIED`. Reassessment confirms this independently.

Paths searched (all confirmed **MISSING** on this host):

- `/tmp/opencode/strict-w1/logs/strict_suite_20261117_063054.log` (+ `.exit`)
- `/tmp/opencode/strict-w1/logs/strict_run2.xml`, `/tmp/opencode/strict-w1/logs/baseline_sqlite.xml`
- `/tmp/opencode/remediation/w1/strict_classification.json`, `run1_vs_run2_nodes.json`, `schema_gap_strict.json`, `schema_drift_strict.json`, `fp_strict_before.txt`
- `/tmp/opencode/strict-w1/sha256_manifest_full.txt`, `conftest.py`, `pytest.ini`

Repo-wide checks performed:

- `find … -name '*.log'` → **0** log files in the repo (excluding node_modules/.git).
- `find … -name '*.xml'` → 28 files, **all** Android resources / SBOM XML (`mobile/...`, `backend/app/capabilities/*/sbom.xml`, `assessment/brain/sbom-*.xml`); **zero JUnit/gate XML**.
- `find … -iname '*strict*'` → only `districts.py`, `subdistricts.py` (string match); **no strict-gate artifact**.
- `git ls-files | grep -iE 'junit|strict.*\\.(xml|log|json)|gula_w1|schema_fingerprint|sha256_manifest'` → **empty**.
- `GOVERNANCE/evidence/` contains only `index_target_missing.txt`, `migration_reconciliation_matrix.{tsv,json}` — **no gate artifact**. A content grep for the raw artifact filenames across `GOVERNANCE/` returns only markdown *references* (`W1_CHECKPOINT.md`, `GECS/EVIDENCE_REGISTRY.md`, `EXECUTION_LEDGER.md`, `PHASE_C_DATABASE_REHEARSAL_REPORT.md`), not the artifacts themselves.
- The five principal markdown files citing the numbers are all **untracked** in this working tree (`git ls-files --error-unmatch` fails), so no git history can supply a prior copy.

Verdict: **BLOCKED** — the raw gate artifact required to independently verify E-001/119 does not exist in the repo, in GOVERNANCE directories, among untracked files, or at any referenced `/tmp` path. Only summarized documentation survives.

## 6. The "119 vs 753" contradiction explained

Both figures are historical shorthands for the **same single run** (E-001, strict #1, 2026-11-17). They are not two different results, and there was no intervening re-execution.

| Notation | Where it appears | Correct meaning |
|---|---|---|
| **119/872** | `GOVERNANCE/GECS/{BLOCKER_REGISTRY.md:26,MASTER_CONTROL.md:65,PHASE_GATES.md:191,DECISION_REGISTRY.md:144}`, `NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md:7`, `AUTONOMOUS_ENGINES_VERIFICATION.md:175`, and the root `GULA_*` summary tables (`GULA_MASTER_COMPLETION_LEDGER.md:23`, `GULA_MASTER_EXECUTION_STATUS.md:36`, `GULA_RELEASE_ACCEPTANCE_REPORT.md:16`) | **119 failed of 872** (failure fraction) |
| **753/872** | `GULA_DEPENDENCY_GRAPH.md:90` ("W-017 strict gate 753/872 vs 872/872 under SQLite `create_all()`"), `GULA_SECURITY_AND_RISK_REGISTER.md:25` ("W-017 strict gate 753/872"), `UNIFICATION_BLOCKERS.md:115` ("Result 753/872 (119 failures)") | **753 passed of 872** (pass fraction); `UNIFICATION_BLOCKERS.md:115` explicitly glosses it as "(119 failures)" |

What changed between them: **only the notation and the authoring document**, not the underlying data. "753/872 failures" (if read literally) is a **misreading** — 753 is the pass count; 872 − 753 = 119 failures. The canonical spelling that removes the ambiguity is `753 passed / 119 failed / 0 skipped (872)` (`W1_CHECKPOINT.md:44`, `DATABASE_COMPATIBILITY_REPORT.md:347`, `EXECUTION_LEDGER.md:30,113`, `FINAL_DECISION.md:348`).

Neither figure is "current" in the sense of a fresh, artifact-backed run: both are historical (2026-11-17), both derive from the now-missing `/tmp/opencode/` evidence, and the current authoritative status remains **FAILED, not re-run** (`WORK_REGISTRY.md:40`: `CLOSED-AS-FAILED — never rerun without trigger`). Both values are preserved verbatim here; neither is overwritten or relabelled. A related, separately documented notation hazard exists for E-002/E-003 ("750/122" vs "872/0") in `STABILIZATION_PHASE_L_M_N_ASSESSMENT.md:47` and `TEST_RESULTS.md:51-54` — also preserved, not silently corrected.

## 7. Actionable unblock plan (not executed)

To obtain a *fresh, independently verifiable* W-017 result without lowering any threshold:

1. **Record a documented trigger** (GECS hard rule, `DUPLICATE_PREVENTION.md:32-33`): reference the new evidence that invalidates reuse — e.g. implementation of NR-011 two-part fix and/or ADR-A wave migrations, which change the schema under test. Append it to `GOVERNANCE/GECS/CHANGE_CONTROL.md` / `DUPLICATE_PREVENTION.md`.
2. **Obtain A07 + owner authorization for the re-run** (QA_AUDIT A09-004 `:196`; `SR-A09-06` `:300`), and confirm D-018 method constraints still hold (`:68`). Who owns: **QA Lead** for execution, **A07 (Backend/API/DB)** for scope, **Program Director / project owner** for the gate re-run and artifact-capture decision. D-001/D-003 are already approved (`:17,19`) but their *implementation* (NR-011 in `backend/migrations/env.py` only, zero DDL) is still required before a pass can exist.
3. **Provision the environment** (authorized owner, not this agent): a disposable PostgreSQL **16** clone with revision `20261114_0006` / 433 tables built by Alembic only; export `STRICT_DATABASE_URL=<clone>`. No operational DB; no `alembic stamp`; no test-side DDL.
4. **Reconstruct the byte-identical external harness** at `/tmp/opencode/strict-w1/` (strict `conftest.py`, `pytest.ini`, 53 byte-copied modules) and re-verify hashes against `sha256_manifest_full.txt` (which itself must be restored/regenerated under authorization). Selection rule from `W1_CHECKPOINT.md:33`.
5. **Run the exact authorized command** `STRICT_DATABASE_URL=<clone> pytest tests -q` (`EXECUTION_LEDGER.md:113`), then a second pass with `--junitxml` (`:114`), while capturing: exit code (`.exit`), full log, `strict_run2.xml`, `baseline_sqlite.xml` control, before/after schema fingerprints, and the classification JSON. Fix the fixture write leak (`W1_CHECKPOINT.md:141-143`) first or accept the known +3 self-poisoned audit-chain failures.
6. **Acceptance (unchanged):** **872/872** twice on the migration-built schema, fingerprint delta = approved migrations only, no test skipped/weakened (`WORK_REGISTRY.md:40`, `W1_CHECKPOINT.md:179-180`). Record new artifacts with new IDs under `EVIDENCE_REGISTRY.md`; never overwrite E-001…E-003.
7. **Then** revisit D-020/D-021 human sign-off and `MIG-EXISTING`/criterion 5 — a strict-gate pass alone does not grant release or certification.

## 8. Remaining owner decisions (explicitly not taken here)

- **A07 + Program Director / QA Lead:** authorize the W-017 re-run and artifact capture (A09-004 / SR-A09-06). Status: **not granted in this task**.
- **Documented trigger:** approve and record the reason for re-running (`DUPLICATE_PREVENTION.md:32-33`). Status: **absent**.
- **ADR-B** ownership of `facilities` / `organizations` / `national_facilities` (`W1_CHECKPOINT.md:161`). Status: **PENDING**.
- **Rollback procedure** choice — snapshot restore vs `downgrade base` + `upgrade head` (`:162`). Status: **PENDING**.
- **NR-011 two-part fix + ADR-A waves** — D-001/D-003 approved (`:17,19`) but not implemented; implementation authorization is a separate scope. Status: **approved-but-not-executed**.
- **D-020** security verdict (Security lead + Program Director) and **D-021** clinical safety posture (Clinical Safety Owner). Status: **`PENDING_APPROVAL`** (`DECISION_REGISTRY.md:70-71`).
- **FINAL_DECISION:** remains **HOLD**; HOLD must not become GO on the strength of this reassessment.

---

*End of reassessment. No file other than this deliverable was created or modified. No status of `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` is asserted for W-017 or for this document.*
