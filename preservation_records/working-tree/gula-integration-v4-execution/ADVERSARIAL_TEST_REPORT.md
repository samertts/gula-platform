# Adversarial Test Report

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19; pinned Python 3.12.13; synthetic/disposable data only; no operational DB/Redis/HTTP/real patient data.
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. No `PRODUCTION READY` awarded.

## 1. Step-up adversarial suite (this execution) — `TESTED`

`backend/tests/unit/test_niam_step_up.py`: **37 passed, 1 warning, `EXIT=0`**.

| Attack hypothesis | Test / mechanism | Outcome |
|---|---|---|
| Client supplies another account's MFA completion | OpenAPI structural assertion — body has only `code` + `method` | rejected structurally |
| Replay of a used TOTP code within the window | `code_fingerprint` single-use + DB unique constraint + concurrent dual-verify | exactly 1 event, 1 `StepUpDenied`, duplicate insert raises `IntegrityError` |
| Expired / stale evidence (301s) | frozen-clock boundary test | denied |
| Boundary inclusive (299s / 300s) | frozen-clock tests | accepted |
| Clock skew / future timestamp | future `verified_at` test | denied |
| Session substitution / token substitution / JTI mismatch | server-re-read session + JTI binding tests | denied |
| Revoked / expired session | revocation + expiry tests | denied |
| Disabled / rotated / removed MFA factor | factor fingerprint checks | denied |
| Suspended / locked / disabled / deactivated account, `is_locked` | 6 parameterized cases, staging + assertion | denied `account_inactive` |
| Invalid config (blank, `abc`, `0`, `-1`, `29`, `3601`) | lazy validated loader | `StepUpConfigurationError` / HTTP 503 |
| Missing / ambiguous evidence | dedicated denial tests | denied |
| Concurrent verification race | `asyncio.gather` dual verify | single event; audited denial |
| Migration interruption / downgrade | disposable-DB upgrade→downgrade test | table created then removed; constraints present |

## 2. Prior adversarial coverage (re-confirmed, unchanged)

- **Phase 1:** five fixes, Team C adversarial review and re-runs; final tree `4913 passed / 0 failed` (`PHASE1_CLOSEOUT.md`). `INDEPENDENTLY VERIFIED` (engineering scope).
- **Phase 2 Tier A:** six fixes; 32 new tests + ~25 Team C probes; Team C successfully falsified **three recording errors** (not the fixes), corrected and re-verified (`PHASE2_CLOSEOUT.md`). Final tree `4947 passed / 0 failed`. `INDEPENDENTLY VERIFIED` (engineering scope).
- **Full-suite chain:** first step-up full run `4973 passed / 1 failed` (CPU-timing benchmark flake `1680/s < 2000/s`, passed 3 isolation runs); clean re-run `4974 passed / 27 skipped / EXIT=0`; **authoritative final tree `4984 passed / 27 skipped / 203 warnings / EXIT=0 (15m04s)`** — `/tmp/opencode/step_up_final_full_suite.log`, zero failures.

## 3. Directive §6 coverage gaps (honest)

The directive's full adversarial matrix (token forgery, BOLA/BFLA, cross-tenant, PHI enumeration,
break-glass, clinical duplicate/outbox loss, API mass-assignment, migration interruption, offline
CRDT/vector-clock, etc.) is **partially covered** by the existing suite. This report does not claim
complete matrix coverage. Not run this session: broker outages, runtime HTTP probes, operational
migration interruption, offline-sync convergence under network loss. Those remain `BLOCKED` or
`NOT IMPLEMENTED` in `FINAL_ACCEPTANCE_REPORT.md`.

## 4. Rules observed

No test deleted, skipped or weakened; no threshold lowered (the `rate > 2000` benchmark assertion
remains intact). Every failure above was either reproduced and fixed in source, or documented as
environmental with isolation evidence. No finding was raised from a generic green suite.

**Final decision:** step-up adversarial scope `INDEPENDENTLY VERIFIED` (engineering scope) by
fresh-context Team C — 57+ independent probes, zero real bypasses, focused 37/37, final tree 4984/0.
No production claim. Evidence anchors: `NIAM_STEP_UP_SECURITY_REPORT.md` §5,
`GOVERNANCE/ADVERSARIAL_ASSURANCE/NIAM_STEP_UP_PREREQUISITE.md` §7, closeout reports.
