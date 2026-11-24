# Team C Independent Verification — Consolidated Index

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date:** 2026-11-19
**Scope:** index of fresh-context Team C reports. It re-awards nothing; each verdict belongs to the
named primary report. Status vocabulary: `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED /
PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. **`PRODUCTION READY` is awarded by nobody.**

## 1. Primary independent reports

| Program | Report | Award / outcome | Scope limit |
|---|---|---|---|
| Earlier programs | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_REPORT.md` | consolidated engineering-evidence index; no re-award | not a production/clinical claim |
| Earlier programs | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C.md` | `INDEPENDENTLY VERIFIED` (engineering scope) — static + targeted + co-collection tests, forced FK-resolution probe | not runtime/DB/external validation |
| **Phase 1** | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` | five fixes `INDEPENDENTLY VERIFIED` (engineering scope) | no runtime/operational DB, no government/clinical validation; `AUD-API-002`, `AUD-ARCH-003` owner-gated |
| Phase 1 residuals | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` | corrected residuals re-verified; unchanged findings explicitly out of scope | no `PRODUCTION READY` |
| **Phase 2 Tier A** | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE2.md` | six fixes `INDEPENDENTLY VERIFIED` (engineering scope) | four residuals reported; all subsequently re-checked |
| Phase 2 residuals | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md` | all four residuals independently re-checked and found corrected (primary report's residual-outcome label), zero falsifications | no `PRODUCTION READY` |
| **NIAM step-up** | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md` | **`INDEPENDENTLY VERIFIED`** (engineering scope) — 37/37 focused tests, Ruff clean, boot/OpenAPI, single migration head, 57+ adversarial probes, **0 real bypasses** | no operational DB/Redis, no authenticated real-DB HTTP path, no production/clinical claim |

## 2. Step-up verdict — key re-derived evidence (from the primary report)

- Review window 2026-11-19T06:14Z → 06:35Z; target HEAD unchanged before/after.
- Request body only `code` + optional `method` (`required=[code]`, `HTTPBearer`); actor re-read from DB.
- MFA primitive reused (`shared.auth.mfa.verify_totp`); no duplicate engine; no new role/authority.
- Replay protection: DB unique `(account_id, code_fingerprint)` + `IntegrityError → StepUpDenied`.
- Denials confirmed for: cross-account code, replay in/out of window, session/JTI/account substitution,
  clock skew, revoked/inactive evidence, all four bad account statuses + `is_locked`, factor rotation,
  session expiry/termination, invalid config (HTTP 503), malformed codes/methods, ambiguous evidence.
- One `ObjectDeletedError` was traced to a **synthetic fixture** (uncommitted Account row rolled back);
  with a committed production-like account the audit row is written and there is no bypass.
- Boot: `app.main.app` → 1815 paths / 132 routes; my direct side-by-side check confirmed
  bare `create_app()` → 1808/125 (7 routes added in `app.main`). Both figures are correct for their entrypoint.
- Invariants intact: both HEADs, 20 R100 renames, three protected MD5s, `production_ready_items == 0`.

## 3. Boundaries of these awards

All awards are **engineering scope only**. None constitutes `PRODUCTION READY`, clinical/regulatory
validation, government integration, or a runtime deployment claim. Owner-gated decisions
(`HOLD`, `MPI REJECT`, `MP-001`, `ODR-001…004`, `D-020/D-021`, `ADR-A…J`, `AUD-02/07/16`,
`AUD-API-002`, `AUD-ARCH-003`) were not altered. B4 remains `BLOCKED` pending owner approval.

**Final decision:** Team C verification for the step-up prerequisite is complete and `INDEPENDENTLY
VERIFIED` at engineering scope. No production claim. No commit, push, PR, merge, or deploy.
