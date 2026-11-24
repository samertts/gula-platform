# Wave 0 — Fresh Repository Baseline

**Directive:** GULA AUTONOMOUS MASTER EXECUTION (2026-11-19) §3 FIRST ACTION / §5 Wave 0
**Method:** read-only examination. No source, test, config, index or ref was modified to produce this report.
**Captured:** 2026-11-19 (UTC), pinned interpreter `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (3.12.13).

## 1. Git state (observed this pass)

| Item | Observed | Note |
|---|---|---|
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | matches prior checkpoint |
| Branch | `integration/gula-unification-v1` | — |
| Upstream | `origin/main` | — |
| Remote | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` (fetch+push) | single remote `origin` |
| Recent commits | `2206654d` (Phase B evidence tranche), `0cb067ae` (Phase A baseline), `2827c1ff` (`origin/main`) | no new commit this pass |
| Staged | 20 paths, all `R100` renames under `archive/legacy/workflow_runtime/` | preserved untouched |
| Unstaged (modified) | 149 tracked files | includes prior auth/DB/CI work + this directive's Python 3.12 pin edits |
| Untracked | 596 paths | predominantly governance reports, health_core/domain_platform/identity security modules, tests, new migrations — never committed |
| Worktrees | 5 active + 1 prunable; sibling `gula-platform` @ `f478676b` `[remediate-security-001]` | sibling is protected/read-only |
| Protected MD5s | `effdfeaf…` / `1a02c015…` / `ea3969d0…` | all identical |
| `production_ready_items` | 0 | intact |

## 2. Reconciliation of the previous execution record (evidence-backed)

- HEAD, branch, protected MD5s and 20 staged renames **match** the checkpoint — no external rewrite detected.
- **NR-011 is FIXED in code but the governing doc is stale.** `backend/migrations/env.py` already registers all 17 declarative bases, imports `app.national.domain`, and merges metadata into one `MetaData` (BEGIN/END NR-011 markers). Verification: `pytest tests/unit/test_nr011_metadata_discovery.py tests/unit/test_fk_target_integrity.py -q` → **19 passed, EXIT=0**; cross-metadata `ehr_allergies → national_patients` FKs resolve. Yet `DATABASE_MIGRATION_READINESS.md` (dated 2026-11-19) still lists NR-011 as `BLOCKED`. Status now: **resolved in code, documentation correction required**.
- Full-suite log `/tmp/opencode/final_tree_full_suite_b5_fixed.log` → **5117 passed / 27 skipped / 0 failed, EXIT=0** (authoritative post-fix tree at time of run; not re-run in this pass).
- Team C engineering-scope `INDEPENDENTLY VERIFIED` awards exist for B4, B1, B2, B3, B5 and NIAM step-up (reports in `GOVERNANCE/ADVERSARIAL_ASSURANCE/`). No self-award.
- Live OpenAPI (`app.main.app`) → **1817 paths / 2130 operations**; `/niam/delegations` present.
- Waves 0–7 evidence recorded in `GOVERNANCE/EXECUTION_LEDGER.md` §§8–15 at static/safe-lane scope.

## 3. Baseline inventories

| Inventory | Measurement |
|---|---|
| Alembic migrations | 110 files; single head `20261119_0002`; linear chain to first base |
| care_continuum models | **45 `cc_*` tables**, 0 covering migrations (confirmed pre-existing gap) |
| Declarative bases | 17 registered in `env.py`; merged `MetaData` ≥450 tables |
| API surface | 1817 paths / 2130 operations |
| CI | 32 workflow YAML files, all parse; 3.12 pins enforced (prior wave); `architecture-check`/brain gates absent |
| Tests | full suite 5117 passed (last authoritative run); focused NR-011 19 passed this pass |
| Security findings | B4/Tier B residuals (R-1…R-4, B1 catalog gap, B2 category mismatch, B3 flag/audit sink, B5 forged-DB-row defense-in-depth) recorded; no real API-reachable bypass outstanding |
| Governance decisions | `HOLD`, MPI `REJECT`, MP-001, ODR-001…004, D-020/D-021, ADR-A…J remain as recorded; ADR-A/J pending implementation scope |

## 4. Concurrent activity / provenance warning

Live processes observed in **isolated** `/tmp/opencode/` directories (NOT the working tree):
- `pytest /tmp/opencode/audit008/test_bola_repro.py` — adversarial BOLA repro.
- Vite preview server on `127.0.0.1:4173` from an isolated eval copy.

No git write process active. Because 149 modified + 596 untracked paths exist from prior/concurrent sessions, **per-file provenance must be established before any commit** (directive §8 mandatory pre-commit procedure). History rewrite / force-push / push to protected branch / sibling modification remain prohibited.

## 5. Highest-priority unfinished task (directive priority order)

P0 identity/security work is independently verified; do not repeat. The highest-priority genuinely unfinished item is **Wave 2 / database integrity**: the **45-table `care_continuum` migration gap** (ADR-C: keep as permanent cross-cutting host — C1), plus correction of the stale NR-011 status in `DATABASE_MIGRATION_READINESS.md`. This directive §5 explicitly authorizes "additive, reversible database migrations" as priority 1–3 and supersedes the prior "PENDING" gate for the engineering work. Next action: investigate each `cc_*` model (ownership, FKs, dependencies, operational usage), then author one additive reversible migration and test fresh-install / upgrade / downgrade / re-upgrade on disposable PostgreSQL with synthetic data. No `create_all()`, no fake stamps, no operational DB.

## 6. Post-baseline progression (same session, appended — baseline above unchanged)

The §5 Wave 2 task was executed. NR-011's stale `BLOCKED` text in `DATABASE_MIGRATION_READINESS.md`
was corrected to resolved-in-code (19/19 focused tests). The care-continuum gap was closed at the
migration level by uncommitted revision `20261119_0003` (62-table FK closure, single head) plus 8
regression tests: full-chain fresh upgrade → downgrade → re-upgrade PASS on disposable PG16
(`45 cc + 17 national` targets, 24 enum types), synthetic FK/UNIQUE/enum constraint probes PASS,
Ruff/hygiene/secret-PHI scans clean. A first fresh-context Team C review found one P1 defect
(`use_alter=True` FK silently omitted by Alembic's `create_table`); it was fixed with an explicit
`create_foreign_key`/`drop_constraint` pair and strengthened FK-parity regression tests. A second
fresh-context Team C re-verification awarded the migration **`INDEPENDENTLY VERIFIED`** (engineering
scope; checks A–G PASS, falsification proof — `/tmp/opencode/teamc_cc_reverify_report.md`); the award
was issued by Team C, not self-awarded, and `PRODUCTION READY` was not awarded. Post-fix full suite
`5124 passed / 28 skipped / EXIT=0`. See `GOVERNANCE/EXECUTION_LEDGER.md` §16/§16.1 and
`DATABASE_MIGRATION_READINESS.md` §4. No commit was made; git HEAD, the 20 staged `R100` renames and
the 3 protected MD5s remain unchanged.
