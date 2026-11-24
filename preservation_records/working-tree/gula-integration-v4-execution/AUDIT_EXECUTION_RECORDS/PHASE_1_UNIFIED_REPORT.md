# PHASE 1 UNIFIED REPORT — P-13 / P-15 / P-16

**Generated:** 2026-11-20 UTC · **Repo:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Data class:** SYNTHETIC ONLY. No PHI, real patient data, production DB, secrets or financial transaction used.

**Posture:** HOLD remains · Stable v1.0.0 NOT declared · PRODUCTION READY NOT authorized · `production_ready_items = 0`.
**Status vocabulary is exclusive:** IMPLEMENTED / TESTED / INDEPENDENTLY REVIEWED / ACCEPTED / PRODUCTION READY are never merged. No package below is ACCEPTED or PRODUCTION READY.

---

## 1. Packages, changed files and decisions

| Package | Finding | Files changed (incremental delta) | Focused | Related | Independent verdict | Decision |
|---|---|---|---|---|---|---|
| P-13 Financial audit | AUD-F15 (HIGH only when `ENABLE_FINANCIAL_ENGINE=true`; MEDIUM default) | `backend/app/financial/routes.py`, `backend/tests/test_p13_financial_audit_integrity.py` | 8/8 | 134/134 | PASS WITH CONDITIONS, 0 CRIT/HIGH | **PASS WITH CONDITIONS** |
| P-15 Password-reset audit | AUD-F17 (MEDIUM, silent) | `backend/app/routes/password_reset.py`, `backend/tests/test_p15_password_reset_audit_integrity.py`, `backend/tests/unit/test_session_revocation.py` | 6/6 | 58/58 | PASS WITH CONDITIONS, 0 CRIT/HIGH | **PASS WITH CONDITIONS** |
| P-16 MPI identity | AUD-F16 (MEDIUM) | `backend/app/services/patient_service.py`, `backend/app/services/mpi/api.py`, `backend/app/services/mpi/schemas.py`, `backend/tests/test_p16_mpi_identity_integrity.py` | 11/11 | 105/105 | PASS WITH CONDITIONS, 0 CRIT/HIGH; 5/5 conditions cleared | **PASS WITH CONDITIONS** |

**Pre-existing user work preserved, not judged as regression:** P0-D session-revocation changes in `password_reset.py`; AUD-PRV-001/003 duplicate and force-create controls in `patient_service.py`; all 20 staged R100 renames.

---

## 2. Exact test commands and results

Environment for every run: `cd /home/samertts/workspace/projects/gula-integration/backend`, interpreter `/tmp/opencode/gula-int-py312/bin/python` (Python 3.12.13, pytest 9.1.1), `ENV=test PYTHONPATH=..`.

| # | Command (pytest args) | Passed | Failed | Skipped | Exit |
|---|---|---:|---:|---:|---:|
| 1 | `tests/test_p13_financial_audit_integrity.py -q` | 8 | 0 | 0 | 0 |
| 2 | P-13 related financial/audit set | 134 | 0 | 0 | 0 |
| 3 | `tests/test_p15_password_reset_audit_integrity.py -q` | 6 | 0 | 0 | 0 |
| 4 | P-15 related: `test_p15…` + `unit/test_session_revocation.py` + `test_auth_infrastructure.py` -q | 58 | 0 | 0 | 0 |
| 5 | `tests/test_p16_mpi_identity_integrity.py -q` (initial) | 6 | 0 | 0 | 0 |
| 6 | P-16 related: 11 MPI/patient/audit modules -q (initial) | 105 | 0 | 0 | 0 |
| 7 | `tests/test_p16_mpi_identity_integrity.py -q` (post-review, 5 added tests) | 11 | 0 | 0 | 0 |
| 8 | P-16 related 11-module set -q (post-review re-run) | 105 | 0 | 0 | 0 |
| 9 | Independent reviewer focused P-16 | 6 | 0 | 0 | 0 |
| 10 | Independent reviewer related subset | 25 | 0 | 0 | 0 |

Static checks (final): `ruff check` on all touched source and test files → **All checks passed**, exit 0. `git diff --check` → exit 0.

RED evidence: P-13 and P-15 established against `git show HEAD`. P-16 initial RED was **5 failed / 1 passed** (corrected from an overstated 6-failed claim per review condition F3); the sixth test is a valid invariant guard but does not detect the P-16 delta.

---

## 3. Independent reviews

All three reviews were performed by fresh-context, read-only subagents with no repository modification. None awarded ACCEPTED or PRODUCTION READY.

- **P-13** — PASS WITH CONDITIONS. Verified canonical `resource_type`/`resource_id`, audit flush before a single commit, `get_db` rollback, flag unchanged, no money/policy change. Conditions: real-canonical-writer failure test **added and passing**; PostgreSQL branch not empirically covered; retry/double-charge idempotency gap (pre-existing, out of scope); `PricingService.create_rule` unaudited (pre-existing).
- **P-15** — PASS WITH CONDITIONS. Verified both audit calls moved before `db.commit()`, `contextlib.suppress` removed, `resource_id=user.id`, no token/password/secret in audit details, rate limiting and enumeration message preserved. Open conditions: no DB/commit-failure, interruption or retry test (fail-closed design structurally atomic); both test files untracked until the preservation commit; R4 owner acceptance of the fail-closed availability trade-off not recorded; brittle `len(calls)==2` AST guard.
- **P-16** — PASS WITH CONDITIONS, all 5 conditions cleared with regression tests: F1 admin monitor `GET /mpi/reconciliation/outstanding`; F2 idempotent pending-review marker; F3 RED claim corrected; F4 duplicate `@dataclass` removed; F5 `_safe_match_score` guard. Residual pre-existing risks F6/F7/F9 disclosed, not self-accepted.

---

## 4. Residual risks and owner gates

See the existing registers `STATUS/OPEN_BLOCKERS.md`, `GOVERNANCE/UNIFICATION_BLOCKERS.md`,
`GOVERNANCE/GECS/BLOCKER_REGISTRY.md`, `docs/release/KNOWN_LIMITATIONS.md`, plus the scan record
`AUDIT_EXECUTION_RECORDS/SECRET_SCAN_RECORD.md`. Summary:
- P-15 fail-closed availability trade-off needs **R4 owner acceptance** (not self-awarded).
- P-13 retry idempotency key is out of the authorized scope (would change charging policy).
- AUD-F01…F04, F18 remain MEDIUM; F05…F12, F19…F21 LOW/INFO.
- A pre-existing 2026-03-08 commit on `origin/main` contains a committed `.env` with one
  API-key-shaped value. Not introduced by this work; no history rewrite performed. Full
  methodology, counts and owner-action note: `AUDIT_EXECUTION_RECORDS/SECRET_SCAN_RECORD.md`.

---

## 5. Git invariants — before and after Phase 1

| Invariant | Before | After |
|---|---|---|
| Branch | `integration/gula-unification-v1` | unchanged |
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | unchanged (no commit at report time) |
| Staged name-status MD5 | `56c524d6ffe9872c3a3ac6eff8c8f203` | unchanged |
| Staged count / R100 | 20 / 20 | unchanged |
| Unstaged / untracked | 160 / 647 | 160 / 652 at original Phase 1 certification; 162 / 660 after the P-01/P-04 addendum (§6) |
| `git diff --check` | exit 0 | exit 0 |
| Protected `FINAL_DECISION.md` MD5 | `effdfeaf10234678d83b2668c4489552` | unchanged |
| Protected `MPI_FINAL_INDEPENDENT_AUDIT.md` MD5 | `1a02c01563c93b07a7cdb92c0462bf36` | unchanged |
| Protected `MPI_INDEPENDENT_AUDIT_FINDINGS.md` MD5 | `ea3969d09aaf7b0b28a065838b44a594` | unchanged |
| Protected sibling HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | unchanged |
| `production_ready_items` | 0 | 0 |

No `reset`, `clean`, `restore`, `stash`, `git add .`, `git add -A`, force-push, merge, deploy or production access occurred.

---

## 6. Addendum — P-01 / AUD-F01 and P-04 / AUD-F04 (2026-11-20, later in the same session)

| Package | Finding | Files | Focused | Related | Independent verdict |
|---|---|---|---|---|---|
| P-01 dormant raw audit writer | AUD-F01 | `shared/audit/service.py`, `backend/tests/test_f01_legacy_audit_writer.py` | RED 7 failed → GREEN 9 passed (2 added reviewer conditions) | 120 passed / 9 skipped | PASS WITH CONDITIONS, 0 CRIT/HIGH, 4/4 conditions cleared |
| P-04 standalone verifier | AUD-F04 | `scripts/audit_verifier.py`, `backend/tests/test_f04_audit_verifier_chain.py` | RED 6 failed → GREEN 6 passed | 136 passed / 9 skipped | **PASS**, 0 CRIT/HIGH/MED, no blocking conditions |

Full evidence: `AUDIT_EXECUTION_RECORDS/P-01_BEFORE.md`, `P-01_AFTER.md`, `P-04_BEFORE.md`,
`P-04_AFTER.md`. P-01 redirects the dormant legacy writer to canonical `log_action` (constitution:
preserved, not removed) and clears concurrency/LIKE/import conditions. P-04 removes the divergent
local hash and delegates full-chain verification to the canonical verifier with exit codes 0/1/2;
the guardian is untouched and no daemon was restarted.

F02/F03 remain `BLOCKED`: R4 active-path behavior changes with no package-specific owner sign-off.
Independently reissued decision packets (required change, risks, tests, acceptance conditions, owner
decision text): `P-02_DECISION_PACKET.md`, `P-03_DECISION_PACKET.md`. The P-04 code is frozen after
its independent review; any further edit requires a new review cycle. The pre-existing public `.env`
item affects **DeepSeek** (`DEEPSEEK_API_KEY`) and requires owner rotation — see
`ENV_INCIDENT_REVIEW.md`; no value was reproduced and no history was rewritten. OD-001 remains the only
`ACCEPTED` owner decision and is limited to SEC-015/F-01 engineering scope.

Post-addendum invariants: HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`, staged 20 × R100 with
name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`, unstaged 162 / untracked 660, all protected MD5s
and sibling HEAD unchanged, backup branch verified on origin at committed HEAD,
`git diff --check` exit 0, `production_ready_items = 0`. The engineering-verification scorecard is
now 6/29 ≈ 20.7% `INDEPENDENTLY REVIEWED` — not platform completion. HOLD unchanged; no commit,
integration-branch push, Draft PR, merge, deploy or production access.
