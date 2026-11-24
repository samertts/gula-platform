# P-04 / AUD-F04 — AFTER record (standalone verifier delegates to canonical chain)

**Generated:** 2026-11-20 UTC · **Repo:** `gula-integration`, branch `integration/gula-unification-v1`
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` (unchanged — no commit)
**Posture:** HOLD · Stable v1.0.0 NOT declared · PRODUCTION READY NOT authorized · `production_ready_items = 0`.
**Data:** synthetic only, disposable SQLite test DB; no PHI, secrets, production DB, real anchors, daemon restart or deploy.

## 1. Implementation

| File | Change |
|---|---|
| `scripts/audit_verifier.py` | Removed local `compute_hash()` and `hashlib` import. Imports canonical `app.services.audit_service as canonical`. `verify_chain(db=None, output=print) -> int` counts rows and calls `canonical.verify_audit_chain(db, limit=total + 1000)`, so the full chain is checked even beyond the canonical helper's default 1000-row cap. Maps result to the original human-readable output and returns explicit exit codes: 0 intact/empty, 1 tampered, 2 verification error. `main()` owns `sys.exit`; the `if __name__ == "__main__"` block uses `sys.exit(main())`. |
| `backend/tests/test_f04_audit_verifier_chain.py` | NEW — 6 synthetic regression tests. |
| `AUDIT_EXECUTION_RECORDS/P-04_BEFORE.md` | NEW — defect evidence and tooling-only strategy. |

**Scope:** read-only verification tooling. No audit write behavior, schema, migration, route,
canonical verifier code, guardian code, daemon state or deployment changed. `gula_guardian.py`
is untouched; its non-zero-means-alert subprocess contract is preserved.

## 2. Verification

Environment: Python 3.12.13 (`/tmp/opencode/gula-int-py312/bin/python`), pytest 9.1.1,
`ENV=test PYTHONPATH=..:/home/samertts/workspace/projects/gula-integration`.

| Phase | Command | Result | Exit |
|---|---|---|---:|
| RED (before fix) | `pytest tests/test_f04_audit_verifier_chain.py -q` | **6 failed** — intact canonical chain reported `TAMPER DETECTED`; verifier not injectable; static guards | 1 |
| GREEN (after fix) | same | **6 passed**, 1 warning, 82.67 s | 0 |
| Related suites | 9 audit / guardian / control-plane / P-01 modules | **136 passed, 9 skipped**, 1 warning, 104.52 s | 0 |
| Ruff | `ruff check scripts/audit_verifier.py backend/tests/test_f04_audit_verifier_chain.py` | All checks passed | 0 |
| `git diff --check` | repo root | clean | 0 |

Related suites: `test_audit_chain_integrity`, `test_audit_chain_isolation_guard`,
`test_audit_positional_regression`, `test_audit_bypass_regression`, `test_audit_anchor`,
`test_b3_verified_guardian`, `test_compliance_integrity`, `test_control_plane_authorization`,
`test_f01_legacy_audit_writer`.

## 3. Test coverage map

| Test | Pins |
|---|---|
| `test_f04_intact_canonical_chain_is_not_reported_as_tamper` | decisive defect: canonical-intact chain no longer false-tampers |
| `test_f04_tampered_row_returns_exit_one` | real mutation is still detected with exit 1 |
| `test_f04_empty_log_returns_zero` | empty-chain exit 0 and message |
| `test_f04_source_delegates_to_canonical_verifier` | no local hash, no hashlib; only `main()` exits |
| `test_f04_checks_beyond_canonical_default_limit` | `limit >= row count` overrides canonical 1000-row cap (1500-row simulation) |
| `test_f04_verification_error_returns_distinct_exit_code` | errors return 2 and are not mislabeled as tampering |

## 4. Independent review

**Verdict: PASS. CRITICAL: 0. HIGH: 0. MEDIUM: 0.** Fresh-context, read-only reviewer; repository
unchanged by the review. The reviewer reproduced RED (6 failed on a HEAD copy, including
`TAMPER DETECTED` + `SystemExit: 1` on an intact canonical chain), GREEN (6 passed, 86.45 s),
related suites (136 passed / 9 skipped, 99.49 s), ruff clean and `git diff --check` clean.

Confirmed: the HEAD defect (pipe-joined hash vs canonical JSON payload + UTC normalization);
exactly one authoritative algorithm (no `hashlib` / `compute_hash` remain); `limit = total + 1000`
correctly overrides the canonical 1000-row cap with no off-by-one and correct empty-log handling;
exit codes 0/1/2 preserve the untouched guardian's non-zero-means-alert contract; same table and no
filters for count and verification; injected sessions are caller-owned and owned sessions are closed;
error output contains exception type only (no PII/message); no write, schema, migration, route,
daemon restart, deploy or production access; staged renames and protected MD5s untouched.

**No blocking conditions.** Standing conditions (must remain true): HOLD posture; no daemon restart,
deploy, commit, staging change or production DB access for P-04; no `ACCEPTED` or `PRODUCTION READY`
award; `production_ready_items = 0`.

**Non-blocking residual risks — recorded, NOT fixed after review (the reviewed artifact is frozen):**

| ID | Sev | Residual | Future-acceptance action |
|---|---|---|---|
| L1 | LOW | `SessionLocal()` at `:49` runs before the `try`; a failure there or in `db.close()` escapes the 0/1/2 mapping (Python exits 1, guardian still alerts) | Move creation inside `try`, guard `close()`, add subprocess exit-code test |
| L2 | LOW | TOCTOU between count and verification select; `_VERIFY_BUFFER = 1000` covers realistic drift (not a regression — old tool had no cap) | Single snapshot transaction or larger buffer if >1000 inserts in the gap are conceivable |
| I1–I4 | INFO | Subprocess boundary tested by inspection only; AST guard does not cover `raise SystemExit`/`os._exit`; one test closes the injected session; tool verifies chain hashes only, not HMAC anchors (pre-existing) | Add end-to-end CLI exit-code test; broaden AST guard; anchor verification remains a separate package |

**Systemic residual (pre-existing, outside AUD-F04):** writer and verifier share one canonical hash
algorithm, so compromise of that algorithm would be a false negative. Chain-tail deletion is not
detected by hash verification alone (I4). Neither is self-accepted here.

## 5. Status

`IMPLEMENTED` + `TESTED` + `INDEPENDENTLY REVIEWED` (verdict PASS, 0 CRITICAL/HIGH/MEDIUM).
NOT `ACCEPTED`, NOT `PRODUCTION READY`. No commit, staging change, guardian restart, deploy or
production access. The post-review code is frozen: no hardening edits were applied after the verdict.
