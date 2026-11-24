# Resumption Status — Controlled Resumption

**Program:** GULA final remediation & release-blocker closure
**Branch:** `integration/gula-unification-v1`
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Resumed:** 2026-11-16 (session restart after operator-initiated interruption)
**Verdict of `GOVERNANCE/FINAL_DECISION.md`:** unchanged — **HOLD**

> Purpose: make the last written state sufficient to resume **without repeating
> completed phases**. Evidence artifacts live outside tracked files in
> `/tmp/opencode/remediation/`.

---

## 1. Proven cause of the stop

| Candidate cause | Verdict | Evidence |
|---|---|---|
| Process termination | **RULED OUT** | Background job **still alive** at inspection: PID `72596`/`72597`, started `Mon Nov 16 22:12:10 2026`, `etimes` 616 s and counting |
| Git operation interrupted | **RULED OUT** | `git diff --cached --numstat` → **0 staged content changes**; 20 pre-existing `R100` renames untouched; HEAD still `2827c1ff` |
| Database connection failure | **RULED OUT** | No DB job in flight during Phase 1; PG16 reachable (`172.18.0.3:5432`, 7 databases enumerated) |
| Dependency resolution failure | **PARTIAL — contributing** | First fresh-resolution attempt **did** fail: `pip._vendor.urllib3.exceptions.ReadTimeoutError` → `RESOLVE_EXIT=2`. Retry launched 22:12:10 and is progressing (78 wheels cached, 132 MB cache) |
| **Network throttling** | **CONFIRMED contributing cause** | Sustained **~19–20 kB/s** (`sqlalchemy-2.1.8` 4.7 MB at 19.1 kB/s). This is what turned a routine resolution into a read timeout |
| **Session interruption (operator)** | **PRIMARY cause of the stop** | Work stopped mid-flight while the job was running; a new operator directive arrived. No crash signature, no partial writes |

**Stated cause:** the OpenCode session was interrupted at operator level while a
background dependency-resolution job was in flight. The job itself survived and
continues. The technical impediment behind the single recorded failure is
**network throttling (~19 kB/s) causing a pip `ReadTimeoutError`**.

### Evidence-preservation lapse (declared, not hidden)

The first failed attempt's log was **overwritten** by the retry (both used `>`
on the same `resolve.log`), so `ReadTimeoutError` / `RESOLVE_EXIT=2` now exist
only in the session transcript, not on disk. The retry writes to the same path.
**Correction for all future long jobs:** timestamp the log file before
redirecting. Tracked in §6.

---

## 2. Last phase fully completed

**Phase 1 (dependency vulnerabilities) — core remediation and verification.**

| Deliverable | Result |
|---|---|
| Re-scan (prior result not trusted) | `pip-audit -r requirements-lock.txt --no-deps --disable-pip` → **exit 1, 55 findings / 6 packages** (54 unique advisories) — `dep_audit_before.log` |
| Upgrades executed | `pillow 13.0.0`, `joserfc 1.7.6`, `certifi 2026.10.18`, `dnspython 2.9.2`, `pyasn1 0.6.5`, `urllib3 2.8.0` + `idna 3.20` — all **minimum fix versions**, nothing floated to "latest" |
| Lock re-scan | **exit 0 — "No known vulnerabilities found"** — `dep_audit_after_lock.log` |
| Installed-set re-scan | `pip-audit --path /tmp/opencode/upgraded` → **exit 0** |
| Compat tests (new) | `backend/tests/test_dependency_upgrade_compat.py` → **33/33 on the upgraded set AND 33/33 on the untouched baseline** (behavioural equivalence, no version assertions) |
| Targeted regression | **225 passed / 0 failed, 124.33 s, exit 0** — `upgrade_targeted.log` |
| Full backend suite | **3480 passed / 27 skipped / 0 failed, 506.93 s, exit 0** — `full_suite_upgraded.log` (baseline 3447 + 33 new = 3480 → **0 regressions**) |
| Defect found & fixed | `shared/qr/generator.py::generate_qr_svg` had **always** raised `AttributeError` (PIL factory has no `to_string()`); zero callers; fixed with `image_factory=SvgPathImage` |
| Reports | `GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md` (new, §1–§8 complete); `GOVERNANCE/UNIFICATION_BLOCKERS.md` `DEP-AUDIT-BACKEND` row rewritten with before/after evidence |

**Phase 2 preliminary (read-only only, no writes):** database inventory,
hospital-family ORM↔migration coverage, prior-snapshot discovery (§4).

---

## 3. Last phase not complete

**Phase 1 supplementary — CI/Docker-equivalent fresh dependency resolution on Python 3.12.**

This is the **only** open item of Phase 1. It is required by release condition 1
("dependency audit clean on lock **and** fresh CI/Docker resolution").

| Attribute | Value |
|---|---|
| PID | `72596` (bash) / `72597` (pip) |
| Started | `Mon Nov 16 22:12:10 2026` |
| Log file | `/tmp/opencode/remediation/resolve.log` (truncated in place — see §1 lapse) |
| Report target | `/tmp/opencode/remediation/resolve_report.json` (not yet produced) |
| Isolated env | `/tmp/opencode/resolve-venv` — **fresh Python 3.12.13 venv**, created precisely so the protected venv is never touched |
| Command | `pip install --dry-run --ignore-installed --timeout 180 --retries 20 --report … -r reqs_combined.txt` |
| Inputs | `requirements.txt` + `requirements-dev.txt` concatenated — **the exact manifests CI (`ci.yml:145,245`) and Docker (`Dockerfile:11,14`) install** |
| Prior attempt | exit **2**, `ReadTimeoutError` (network) |
| State at inspection | in progress — 78 wheels cached/downloading, currently `psycopg2_binary` 4.3 MB, cache 132 MB |

**Why it must use Python 3.12:** the original attempt ran on the Python 3.10
audit venv and failed with `Pillow>=13.0.0 … Requires-Python >=3.11`. That was a
**tooling artifact, not a repo defect** — the repo pins `requires-python = ">=3.12"`.

---

## 4. Phase 2 findings already gathered (read-only — do not re-derive)

### 4.1 Database inventory (PG16 `172.18.0.3:5432`, inspected read-only)

| Database | alembic revision | tables | role |
|---|---|---|---|
| `gula_unify_scratch` | **`20260815_0022`** (prior) | **405** | **the prior-version snapshot for MIG-EXISTING rehearsal** |
| `gula_unify_full` | `20261114_0006` (head) | 433 | fresh full-chain reference |
| `gula_unify_downgrade` | `20261114_0006` (head) | 433 | downgrade round-trip reference |
| `gula` (test-suite DB) | `20260805_0002` | 351 | **operational for tests — do not migrate** |
| `gula_unify_tail` | none | 26 | partial |

→ **MIG-EXISTING is NOT blocked**: a supported prior snapshot exists and can be
cloned with `CREATE DATABASE … TEMPLATE gula_unify_scratch`, so the rehearsal
runs on a copy and touches no operational database.

### 4.2 Hospital-family ORM↔migration coverage (reproducible)

Method: `__tablename__` scan over `app/**/*.py` vs `create_table` scan over
`migrations/versions/*.py`. Evidence: `/tmp/opencode/remediation/hospital_coverage.txt`

- Total distinct ORM tables: **832**; total distinct migration-created: **421**
- `hospital_*` prefix tables: **12** → **1 migrated** (`hospital_surgical_safety_checklists`
  via `20260820_0004`), **11 unmigrated**
- `hospitals` (parent): **unmigrated**
- **Reproducible uncovered count for the hospital family = 12**

⚠️ **The previously recorded "13 `hospital_*` tables unmigrated" does not
reproduce** and must not be repeated. Correct it with the reason stated
(§12 of the mandate: correct contradictions, explain the correction).

### 4.3 Open ownership question (architectural — escalate, do not guess)

`facilities`, `organizations`, `national_facilities` survive `downgrade base`
with ambiguous ownership (`NR-010-RESIDUAL`, `NR-006`). Disposition requires a
Program Director decision — **not decided here**.

---

## 5. Changes that must be preserved

### 5.1 Working-tree delta vs. session baseline

Baseline at session start: **170 entries (73 M / 77 ?? / 20 R)** → now
**178 entries (79 M / 79 ?? / 20 R)**. Delta **+6 M, +2 ?? = exactly Phase 1**.
Staged content changes: **0** (both then and now).

| # | File | State | Change |
|---|---|---|---|
| 1 | `backend/requirements.txt` | M | `Pillow>=13.0.0`, `joserfc>=1.7.6` + labelled transitive security-floor block (certifi/dnspython/idna/pyasn1/urllib3) |
| 2 | `backend/requirements-lock.txt` | M | 7 pins raised to fix versions |
| 3 | `backend/pyproject.toml` | M | `Pillow>=13.0.0`, `joserfc>=1.7.6` |
| 4 | `shared/pyproject.toml` | M | `pillow>=13.0.0`, `joserfc>=1.7.6` (was a real gap) |
| 5 | `services/lab/Dockerfile` | M | `joserfc` was **unpinned** → `"joserfc>=1.7.6"` |
| 6 | `shared/qr/generator.py` | M | `generate_qr_svg` factory fix (pre-existing defect) |
| 7 | `backend/tests/test_dependency_upgrade_compat.py` | ?? | new — 33 behaviour-only tests |
| 8 | `GOVERNANCE/DEPENDENCY_VULNERABILITY_REPORT.md` | ?? | new — Phase 1 report |
| 9 | `GOVERNANCE/UNIFICATION_BLOCKERS.md` | ?? *(already untracked in baseline)* | `DEP-AUDIT-BACKEND` row rewritten |

Plus **pre-existing, unrelated** baseline state that must not be disturbed:
79 M / 77 ?? / 20 staged `R100` renames carried from before this session.

### 5.2 Invariants verified at inspection

- **Protected repo `gula-platform`: 0 changes, 0 staged content, `f478676b`** — untouched.
- **Protected venv: 98 packages, byte-identical to `venv_freeze_before.txt`** — `VENV_UNCHANGED=YES`.
- **Shadow set intact:** `/tmp/opencode/upgraded` = 15 entries.
- **All 6 Phase-1 evidence files present** (audit before/after, full suite, targeted, runner, coverage).
- **No commits, no pushes, no merges, no PRs, no deploys** — HEAD `2827c1ff` = `origin/main`, 0/0.
- **`FINAL_DECISION.md` = HOLD** (line 13, line 40).

---

## 6. Processes restarted

| Process | Action |
|---|---|
| Fresh dependency resolution (Python 3.12) | **Relaunched** 2026-11-16 22:12:10 — PID `72597`, log `/tmp/opencode/remediation/resolve.log`, after the first attempt died with `ReadTimeoutError` (exit 2) |
| Test suites / installs / other background jobs | **None left running** — inspected and confirmed idle before any new work |
| Protected venv / original repository | **Never modified** — no process was permitted to write to either |

---

## 7. Resume plan

Sequential; do not skip ahead or re-run completed phases.

1. **Collect the in-flight resolution** (PID `72597`). If it fails again on the
   network, retry **at most once more** with `--timeout 180 --retries 20` and a
   **timestamped** log; if it still fails, record the item as **BLOCKED (network)**
   and do **not** describe it as VERIFIED (mandate §4.9).
2. On success: `pip-audit` the freshly resolved set → record exit code, then
   confirm no dependency conflicts and that neither Docker nor CI can resolve
   below the updated floors.
3. **Correct `DEP-AUDIT-BACKEND` honestly** — release condition 1 needs *both*
   lock **and** fresh resolution. Until step 2 passes, the row must read
   **REMEDIATED_UNVERIFIED (lock VERIFIED / fresh resolution pending)**, not VERIFIED.
4. Update `SECURITY_REMEDIATION_REPORT.md` — **path discrepancy:** the mandate
   says `GOVERNANCE/SECURITY_REMEDIATION_REPORT.md`, but that file **does not
   exist**; the real, tracked record is at repo root
   (`/SECURITY_REMEDIATION_REPORT.md`, Nov 14, 9214 B). Update the existing
   record; do not create a duplicate; note the discrepancy in the final report.
5. Phase 2 — clone `gula_unify_scratch`, rehearse `upgrade head` on the clone,
   compare tables/columns/indexes/constraints/FKs, update
   `DATABASE_COMPATIBILITY_REPORT.md` with the corrected **12** figure.
6. Then Phase 3 (MyPy) → 4 (API contracts) → 5 (Pilot readiness) → 6 (service
   contracts) → 7 (R-01…R-11) → 8 (comprehensive verification) → 9 (governance)
   → 10 (architecture gate) → final report.

**Long-job protocol going forward:** record PID, start time and a
**timestamped** log path before launching; never re-point `>` at a live log;
never leave a job unmonitored.

---

## 8. Blocking questions for the Program Director

1. **Table ownership** of `facilities`, `organizations`, `national_facilities`
   (`NR-010-RESIDUAL` / `NR-006`) — architectural decision, not guessed here.
2. **Disposition of the 12 uncovered hospital-family tables** — whether to add
   migrations (risk: affects existing databases) or accept as legacy.
3. **Original `gula-platform` still declares the vulnerable floors**
   (`backend/requirements.txt`, `backend/pyproject.toml`,
   `security/pyproject.toml`, `backend/requirements-lock.txt`) — out of
   authorisation, reported only, never fixed here.

---

## 9. W1 strict-schema gate (appended 2026-11-17)

The W1 gate has now been executed: 53 modules / 872 tests against a migration-only PG16 clone →
**753 passed / 119 failed**, versus **872 passed / 0 failed** for the same modules under the SQLite
`create_all()` control. Schema gap: **340** ORM table slots absent and **664** ORM columns missing
from 82 migrated tables. NR-011's root cause is corrected to a **two-part fix** (metadata registration
**and** merged `MetaData`). Full state, evidence index and the exact post-approval sequence are in
**`GOVERNANCE/W1_CHECKPOINT.md`**; the approval boundary is `GOVERNANCE/ADR_DECISION_REQUEST.md`
(ADR-A, ADR-B still **PENDING**).

---

**Nothing was committed, pushed, merged, deployed, or turned into a PR.
`FINAL_DECISION.md` remains HOLD.**
