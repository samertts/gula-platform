# P-02 / AUD-F02 — implementation evidence (2026-11-24)

Status: **IMPLEMENTED + TESTED**. Independent review is pending. This record does
not grant `INDEPENDENTLY REVIEWED`, `ACCEPTED`, or `PRODUCTION READY`. HOLD remains
TRUE and `production_ready_items = 0`.

## 1. Scope and baseline

| Item | Value |
|---|---|
| Repository | `/home/samertts/workspace/projects/gula-integration` only |
| HEAD / branch | `2206654dc713ea2de8c564a3207dfe05fde23549` / `integration/gula-unification-v1` (unchanged) |
| Approved packet | `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET_REV3.md` |
| Owner directive | `GULA_OWNER_DECISION_REGISTER.md` §9 (option (a), fail closed) |
| Git mutations | none: no add, commit, push, PR, merge, reset, clean, restore, stash, checkout, force-push, history rewrite or deploy |
| Protected MD5s | `GOVERNANCE/FINAL_DECISION.md` = `effdfeaf10234678d83b2668c4489552`; `MPI_FINAL_INDEPENDENT_AUDIT.md` = `1a02c01563c93b07a7cdb92c0462bf36`; `MPI_INDEPENDENT_AUDIT_FINDINGS.md` = `ea3969d09aaf7b0b28a065838b44a594` — all unchanged |
| Sibling repo | `gula-platform` HEAD unchanged at `f478676b6fc375338648dde46fbf076c015a3f91` |
| `git diff --check` | exit 0 |

## 2. Disposable PostgreSQL 16 gate

A new throwaway environment was created; the pre-existing `gula-postgres` container
was explicitly **not** used as evidence.

| Property | Evidence |
|---|---|
| Container / network | `gula-int-pg-gate-20261124` on isolated bridge `gula-int-pg-gate-net` |
| Labels | `gula.int.scope=disposable-test`, `gula.int.nonprod=true` |
| Ports | no published ports (`5432/tcp -> null`) |
| Storage | fresh anonymous volume only; no host/bind mount |
| Credentials | random password written outside the repo to `/tmp/opencode/gula-int-pg-gate.env` (mode 0600); no value in code, evidence or shell output |
| Version | `PostgreSQL 16.14 on x86_64-pc-linux-musl` |
| Database / role | `gula_int_gate` / `gula_int_gate` (only login role) |
| Databases present | `gula_int_gate`, `postgres`, `template0`, `template1` |
| Isolation | `SHOW transaction_isolation` = `read committed` |
| Migrations | `alembic upgrade head` exit 0; `alembic_version` = `20261119_0003`; 497 user tables |
| Synthetic-only proof | before seeding: `patients=0 lab_orders=0 lab_results=0 audit_logs=0`; every test row prefixed `SYNTHETIC_P02_` |
| Append-only schema | `trg_audit_logs_no_update`, `trg_audit_logs_no_delete` present |
| Transaction probes | ROLLBACK removed probe row; `nextval` advanced across ROLLBACK; `pg_advisory_xact_lock` succeeded; `TRUNCATE ... RESTART IDENTITY` succeeded |

## 3. PostgreSQL RED → GREEN

RED was executed from a fresh `git archive HEAD` tree at `/tmp/opencode/gula-int-head-red`
(import origin verified as the temp tree), with the **same** final test file copied in.
GREEN was executed from the working tree. Both used `--noconftest` and the dedicated
`GULA_P02_PG_DSN`; no SQLite fixture was used for these runs.

| Run | Command target | Result |
|---|---|---|
| RED | untouched HEAD `app.routes.ai` | **6 failed / 2 passed**, exit 1 — `/tmp/opencode/gula-int-p02-red.log` |
| GREEN | working tree `app.routes.ai` | **8 passed**, exit 0 — `/tmp/opencode/gula-int-p02-green.log` |

Test-to-requirement mapping:

| Test | Requirement | RED behavior | GREEN behavior |
|---|---|---|---|
| `test_gate_environment_is_disposable_postgres` | PG gate proof | pass | pass |
| `test_r1_canonical_chain_row` | R1 canonical chained row | fail: `chain_hash is None` | pass |
| `test_r2_failure_propagates` | R2 forced failure propagates | fail: exception swallowed | pass |
| `test_r3_rollback_preserves_original_error` | R3 rollback never masks original error | fail: exception swallowed | pass |
| `test_r4_lab_id_from_order` | R4 deterministic `lab_id` | fail: `lab_id is None` | pass |
| `test_r5_caller_signal_before_ai` | R5 fail before AI call | fail: endpoint continued | pass |
| `test_r6_concurrent_distinct_alerts` | R6 concurrent chained writes | pass (HEAD wrote two unchained rows; chain verifier skipped NULLs) | pass with two chained rows |
| `test_r7_commit_survives_session_close` | R7 retained `db.commit()` | fail: `chain_hash is None` | pass |

## 4. Related / regression / security suites

Command: `pytest -q` across 14 audit and AI suites, normal conftest, `ENV=test`.

Result: **224 passed / 9 skipped / 0 failed**, exit 0, 115.83 s —
`/tmp/opencode/gula-int-p02-related.log`.

Suites: `test_audit_bypass_regression`, `test_audit_anchor`,
`test_audit_chain_integrity`, `test_audit_chain_isolation_guard`,
`test_audit_positional_regression`, `test_f01_legacy_audit_writer`,
`test_f04_audit_verifier_chain`, `test_ai_integration`, `test_ai_platform`,
`test_ai_platform_authorization`, `test_ai_guardrails`, `test_ai_evaluation`,
`test_ai_benchmark`, `test_ai_fabric_access`.

No provider API call, real DB outside the disposable container, PHI, or production
credential was used. The 9 skips are the PG-only isolation guard tests with their
own DSN unset; the dedicated P-02 PG suite covers the PG path.

## 5. Static verification

| Check | Result |
|---|---|
| Ruff check, new test file | **all checks passed** |
| Ruff format check, new test file | **already formatted** |
| Ruff check delta, `ai.py` HEAD → worktree | 4 pre-existing findings → 3; **zero new findings** (`RUF001`/`RUF002` Arabic/en-dash warnings are pre-existing) |
| Ruff format status, `ai.py` | HEAD and worktree both fail the current formatter for pre-existing formatting; no new hunk-specific reformat required |
| Strict MyPy, new test file | **Success: no issues found in 1 source file** |
| Strict MyPy delta, `ai.py` HEAD → worktree | identical normalized error set; **zero new errors** (pre-existing untyped/generic findings preserved) |

Logs: `p02-ruff-head.txt`, `p02-ruff-worktree.txt`, `p02-mypy-head.txt`,
`p02-mypy-worktree.txt`, `p02-mypy-test.log` under this directory's evidence bundle
(source logs in `/tmp/opencode/gula-int-p02-*`).

## 6. Implemented change (exact P-02 scope)

`backend/app/routes/ai.py`, `_emit_critical_alert`:

- canonical `log_action(...)` replaces direct `AuditLog(...)` construction;
- `lab_id` is looked up from `LabOrder.lab_id` for the audited order and passed
  explicitly (`None` only when no order resolves — no fabricated value);
- `db.commit()` is retained immediately after `log_action(...)`;
- the blanket suppression was replaced with one guarded rollback attempt followed
  by a bare `raise`; rollback failure is logged and never masks the original error;
- now-unused `contextlib` import removed.

Unrelated pre-existing mixed-provenance changes in the same file
(`require_ai_operator` additions) were not part of this implementation and were not
modified by this cycle.

`backend/tests/test_p02_critical_alert_audit_postgres.py` is a new additive PG16
RED/GREEN suite; no existing SHA registry was changed.

## 7. Residual / disclosed conditions

| Item | Disposition |
|---|---|
| Advisory anchor-file vs DB divergence on rollback | Explicitly accepted in REV3 §5; anchor is non-authoritative and `verify_audit_chain` reads only `audit_logs`. No new behavior added. |
| `audit_service` unlocked head read / hash computation race | Out of P-02 scope; deferred to `P-03-CONCURRENCY` in the P-03 REV3 packet. |
| Governance DB-sync warning during HEAD import | Pre-existing HEAD behavior (`ai_model_registry` bind syntax); observed in RED only and unrelated to the audited write. |
| Mixed provenance | Still present: 20 staged `R100`, 162 unstaged tracked, 312 untracked. No staging/commit attempted. |
| DeepSeek key rotation | Owner action; `ROTATION UNVERIFIED`; no value printed and no history rewrite. |
| Acceptance gates | No 11-report acceptance matrix, release acceptance, deployment, backup/recovery or client validation performed for P-02. |

## 8. Status statement

- P-02: **IMPLEMENTED**, **TESTED**, **INDEPENDENTLY REVIEWED** (engineering scope).
- Independent review verdict: **DECISION-READY**, 0 CRITICAL / 0 HIGH / 0 MEDIUM /
  2 accepted LOW residuals — `P-02_INDEPENDENT_REVIEW_2026_11_24.md`.
- P-02: not `ACCEPTED`, not `PRODUCTION READY`. No acceptance or deployment gate was run.
- P-03 and all remaining R4 packages remain queued and unimplemented in this cycle.
- **HOLD TRUE · `production_ready_items = 0` · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED.**
