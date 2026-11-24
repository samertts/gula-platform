# Final Acceptance Report — GULA Stable v1.0.0

**Document:** `FINAL_ACCEPTANCE_REPORT.md`
**Repository:** `gula-integration`, branch `integration/gula-unification-v1`
**HEAD reviewed:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19; pinned Python 3.12.13; `ENV=test RUNTIME_MODE=test
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`; synthetic/disposable data only.

## Decision

**GULA Stable v1.0.0 is NOT declared.** This report is an evidence ledger, not a release
certificate. `PRODUCTION READY` is **not** awarded to any item. Status vocabulary is limited to
`IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED /
NOT IMPLEMENTED`.

## 18 acceptance criteria — honest status

| # | Criterion | Status | Evidence / gap |
|---|---|---|---|
| 1 | Zero open Critical security findings | `BLOCKED` | Tier A HIGH fixes `INDEPENDENTLY VERIFIED` at engineering scope (`PHASE2_CLOSEOUT.md`); owner-gated decisions remain; no authoritative clean finding register reviewed this session |
| 2 | Zero unmitigated / risk-accepted High findings | `BLOCKED` | B4 implemented and `INDEPENDENTLY VERIFIED` (24 adversarial tests) under owner directive §4; B1/B2/B3/B5 all implemented and `INDEPENDENTLY VERIFIED` at engineering scope under §5 (238 combined targeted tests); residual R-01…R-11 and Tier B/B5 residuals remain open in `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` and the governance docs, so the criterion is not awarded |
| 3 | All critical tests pass | `TESTED` (engineering) | focused 37/37 step-up, 238 combined Tier B + canonical regressions (incl. 12 B5 fix regressions), gates 6/6 + national VERDICT PASS; first full run had one CPU-timing flake; post-fix final tree `5124 passed / 0 failed` |
| 4 | Full suite passes on final tree | `TESTED` | `/tmp/opencode/final_tree_full_suite_p1_fixed.log` — **`5124 passed, 28 skipped, 203 warnings, EXIT=0 (15m32s)`**, zero failures, authoritative post-fix tree (all step-up + Tier B + B5 + care-continuum closure fixes); `5124 = 5117 + 7` (7 static care-continuum tests added, 1 opt-in DB lifecycle test skipped without its env var); supersedes the `5117` Tier B tree run |
| 5 | Team C independent verification of critical fixes | `INDEPENDENTLY VERIFIED` (engineering scope) | Phase 1, Phase 2, step-up, B4 and Tier B **B1/B2/B3/B5** are each `INDEPENDENTLY VERIFIED` by fresh-context Team C. The later Tier B pass blocked B5 on a reproducible HIGH escalation bypass + integration gap (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` §4); fixes were implemented and a third fresh-context pass (`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`, `2026-11-19T10:35:28Z`) confirmed all three findings remediated with 0 real API-reachable bypasses and awarded B5 `INDEPENDENTLY VERIFIED`. One defense-in-depth residual (forged DB row) is recorded, not accepted as production evidence. The care-continuum FK-closure migration `20261119_0003` P1 fix was also `INDEPENDENTLY VERIFIED` at engineering scope by a fresh-context Team C re-verification (`/tmp/opencode/teamc_cc_reverify_report.md`, A–G PASS, falsification proof) |
| 6 | Institution / patient isolation intact | `TESTED` (scoped) | AUD-PRV-001/003 `INDEPENDENTLY VERIFIED`; tenant-isolation matrix suite passing; no new cross-account wiring |
| 7 | Identity / auth / authorization lifecycle correct | `TESTED` (scoped) | Phase 1/2 closeouts; step-up 37 adversarial tests; B4 implemented + `TESTED` — 24 adversarial cross-account tests, 51 related regressions, Ruff clean, OpenAPI unchanged (1815 paths), narrow RBAC + step-up + audit, no new engine (`B4_CROSS_ACCOUNT_SECURITY_REPORT.md`); B4 independently verified. Tier B B1/B2/B3/B5 all independently verified at engineering scope; B5's prior authority-laundering bypass and ungoverned legacy delegation route were fixed and re-verified (`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`) |
| 8 | Immutable audit log intact | `TESTED` (scoped) | audit-anchor + step-up audit tests passing; no audit weakening |
| 9 | No unapproved migration gaps | `BLOCKED` | NR-011 is resolved in code (fresh Wave 0, 19/19 tests) but the broader ADR-A backlog and owner ratification remain (ledger §4 items 18–22). The 45 care-continuum `cc_*` tables now have migration coverage via uncommitted revision `20261119_0003` (62-table FK closure, full-chain PG lifecycle + FK/UNIQUE/enum constraint probes PASS, 8 regression tests; ledger §16, `DATABASE_MIGRATION_READINESS.md` §4). Fresh-context Team C found and I fixed one P1 FK-integrity defect (`use_alter=True` FK silently omitted by Alembic — explicit `create_foreign_key`/`drop_constraint` added, FK parity regression tests added); fresh-context Team C re-verification awarded the migration `INDEPENDENTLY VERIFIED` at engineering scope (checks A–G PASS, falsification proof; `/tmp/opencode/teamc_cc_reverify_report.md`) — issued by Team C, not self-awarded, `PRODUCTION READY` not awarded. Criterion 9 remains `BLOCKED` on the broader ADR-A backlog and owner ratification; no release claim |
| 10 | Disposable-DB restore tests pass | `NOT IMPLEMENTED` | no restore/PITR drill this session; earlier rehearsal did not fully meet the criterion (ledger §4) |
| 11 | Clinical alert failure behavior proven | `BLOCKED` | Tier A AUD-CLIN-003 `INDEPENDENTLY VERIFIED`; full outage/Retry/DLQ drill needs runtime infra; no delivery claim |
| 12 | Required service integrations pass | `BLOCKED` | Static 18-service inventory review complete (ledger §12, `TESTED`). The 45 `care_continuum` `cc_*` tables now have migration coverage via uncommitted `20261119_0003` (ledger §16), but `create_all` still masks schema gaps in tests and the 74-operation surface still writes no audit log. Runtime end-to-end integration not attempted (operational resources prohibited). No runtime integration claim |
| 13 | Frontend build passes | `TESTED` (fresh) | Wave 4 static gates re-run this session (Node v24.18.0): `npm run typecheck` EXIT=0, `npm run lint` EXIT=0, `npm run test` 16 files / 56 tests EXIT=0, plus 5 governance verifiers all EXIT=0 (`GOVERNANCE/EXECUTION_LEDGER.md` §10). `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md` retained |
| 14 | CI passes | `BLOCKED` | no CI run this session; full suite + gates only |
| 15 | RPO/RTO + restore results documented | `NOT IMPLEMENTED` | not measured; operational resources prohibited |
| 16 | All required architecture decisions closed | `BLOCKED` | ADR-A/B, AUD-API-002, AUD-ARCH-003 owner ratification pending |
| 17 | No unproven production claim | `IMPLEMENTED` | control maintained: no `PRODUCTION READY` awarded anywhere; all statuses bound to specific evidence |
| 18 | Protected files / decisions preserved | `IMPLEMENTED` | control maintained: both HEADs pinned; 20 R100 renames intact; 3 protected MD5s identical; `production_ready_items == 0`; no protected decision modified |

## Summary

- **`INDEPENDENTLY VERIFIED`:** 1/18 (criterion 5 — all critical fixes, including B5, now carry fresh-context Team C engineering-scope awards; per-control awards recorded in the master status).
- **`IMPLEMENTED`:** 2/18 (criteria 17, 18 — honesty and preservation controls).
- **`TESTED` at engineering scope:** 6/18 (3, 4, 6, 7, 8, 13 — scoped, not production). *(Corrected from the prior tally of 5: criterion 7 is `TESTED` in the table, not `BLOCKED`.)*
- **`BLOCKED`:** 7/18 (1, 2, 9, 11, 12, 14, 16).
- **`NOT IMPLEMENTED`:** 2/18 (10, 15).
- Total: 1 + 2 + 6 + 7 + 2 = 18. Criterion 4 is met by the post-fix final-tree run (`5124 passed / 28
  skipped / 0 failed, EXIT=0`); criterion 5 is met by the third fresh-context Team C pass that re-verified all
  three B5 findings (`INDEPENDENTLY VERIFIED`, engineering scope). These are engineering-scope awards
  only — no `PRODUCTION READY` and no v1.0.0 declaration.

Closing the remaining criteria requires owner decisions (B4 authorization, Tier B policies,
architecture ratifications) and operational/runtime evidence (restore drill, service integration,
CI, measured RPO/RTO) that are outside this directive's safe engineering lane. No commit, push,
PR, merge, deploy, operational DB/Redis access, real patient data, or external integration was
used. No test was deleted, skipped, or weakened.

**Completed this session:** post-fix final-tree full-suite result recorded
(`5117 passed / 27 skipped / 0 failed, EXIT=0`), fresh-context Team C step-up verdict awarded
(`INDEPENDENTLY VERIFIED`, engineering scope), and — under explicit owner directive
`GULA-MASTER-AUTH-2026-11-19` §4 — B4 implemented, `TESTED` (24 adversarial tests;
`B4_CROSS_ACCOUNT_SECURITY_REPORT.md`) and **`INDEPENDENTLY VERIFIED` at engineering scope** by
fresh-context Team C (`INDEPENDENT_VERIFICATION_TEAM_C_B4.md`: 10 independent probes, all 8 audit
fields persisted, 0 real bypasses, 4 residual risks R-1…R-4). Under §5, Tier B B1 (centralized PHI
permission map), B2 (separate consent/break-glass, fail-closed), B3 (verified guardian/minor,
canonical NID input only, no NHID minted) and B5 (account-based, scope/expiry/revocation/depth-capped
delegation into the single canonical authority, additive reversible migration `20261119_0002`) are
all implemented and `TESTED` — combined Tier B + canonical regressions **226 passed / 0 failed**,
Ruff clean, OpenAPI 1815 paths unchanged, single migration head. Of two fresh-context Team C Tier B
passes, the later and more adversarial one awarded `INDEPENDENTLY VERIFIED` (engineering scope) to
**B1, B2 and B3** but set **B5 `BLOCKED`** after reproducing a HIGH authority-laundering bypass and a
HIGH integration gap (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` §4). The conservative B5 verdict
governs; the earlier no-bypass pass is superseded, not hidden. A real Alembic drift defect in the B5 model
registration/migration index names was found and fixed, with 6 new regression tests
(`tests/unit/test_b5_migration_drift_regression.py`) and a live disposable-PG upgrade/downgrade/
re-upgrade round-trip; Wave 2 database integrity is `TESTED` (ledger §8). All three Team C B5
findings have since been fixed with 6 further regression tests
(`tests/unit/test_b5_security_regressions.py`, focused suite **238 passed / EXIT=0**, Ruff clean,
canonical `/niam/delegations` API added and legacy surface failed closed, transitive-chain validation
added); see ledger §11 / TIER_B_SECURITY_REPORT §9. Post-fix full-suite confirmation is **complete**
(`5124 passed / 0 failed, EXIT=0`). A third fresh-context Team C pass
(`INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`, `2026-11-19T10:35:28Z`) independently re-tested
all three B5 findings, confirmed each remediated with zero real API-reachable bypasses, and awarded
**B5 `INDEPENDENTLY VERIFIED`** (engineering scope) — no self-award. One defense-in-depth residual
(forged DB row at enforcement) is recorded in master status §6 and is not accepted as production
evidence. **Next gates:** Waves 3–7 evidence, Team C triage of recorded residuals, and owner-gated
architecture/legal/clinical/production decisions. No release or
production claim. Git SHA at baseline: `2206654dc713ea2de8c564a3207dfe05fde23549`.
