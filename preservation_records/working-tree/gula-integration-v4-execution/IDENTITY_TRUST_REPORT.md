# Identity Trust Report

**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Date / environment:** 2026-11-19; pinned Python 3.12.13; synthetic/disposable data only.
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. No `PRODUCTION READY` awarded.

## 1. Trust chain — current status

| Link | Status | Evidence |
|---|---|---|
| Control-plane authorization (single authority) | `INDEPENDENTLY VERIFIED` (engineering) | Phase 1 AUD-SEC-001 / AUD-ARCH-003, `PHASE1_CLOSEOUT.md` |
| JWT account domain binding | `INDEPENDENTLY VERIFIED` (engineering) | Phase 1 AUD-SEC-002 |
| Staged privileged login / MFA usage | `INDEPENDENTLY VERIFIED` (engineering) | Phase 1 AUD-SEC-003; legacy `mfa_used` path unchanged by step-up work |
| Bearer/cookie logout revocation | `INDEPENDENTLY VERIFIED` (engineering) | Phase 2 AUD-SEC-004 (corrected + re-verified) |
| Async actor lock consistency | `INDEPENDENTLY VERIFIED` (engineering) | Phase 2 AUD-SEC-007 |
| NID duplicate / cross-facility PHI | `INDEPENDENTLY VERIFIED` (engineering) | Phase 2 AUD-PRV-001/003 |
| Fresh own-account MFA step-up signal | `INDEPENDENTLY VERIFIED` (engineering scope) | `INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md`, 37 tests + 57+ probes, final tree 4984/0 |
| Cross-account administration (B4) | `BLOCKED` | no source modified; owner approval pending |
| MPI / NHID national identity decisions | `BLOCKED` (owner-gated) | `HOLD`, `MPI REJECT`, `MP-001`, `ODR-001…004`, `D-020/D-021` untouched; protected MD5s identical |

## 2. Step-up contribution to identity trust

The step-up primitive closes a previously identified gap: `UserSession.mfa_used` was only ever
written `False` and no functional NIAM admin MFA event existed, so a fresh-MFA signal for a NIAM
administrator could not be produced. The new work item creates a *separate* proof-of-possession
signal (`NiamStepUpEvent`) without changing NIAM login/refresh/logout, `mfa_used`, the legacy
LabUser MFA route, or the single authorization authority. It reuses `shared.auth.mfa.verify_totp`
against the actor's own `Account.mfa_secret`.

Guarantees evidence-bound this session: server-side actor resolution; request body limited to
`code`+`method`; account/session/JTI/method/fingerprint/server-time binding; fail-closed rejection
of missing/expired/replayed/future-dated/mismatched/ambiguous evidence; suspended/locked account
denial; DB-level replay constraint; immutable audit of both outcomes; 300s owner-approved freshness
with 299/300/301 boundary tests. No new role or permission was created.

## 3. Residual trust gaps

- Step-up is not yet wired into B4; cross-account administration is unavailable.
- Team C awarded step-up `INDEPENDENTLY VERIFIED` at engineering scope (zero real bypasses); it did
  not exercise the authenticated HTTP path against a real DB (operational DB prohibited).
- Owner decisions on MPI merge/death-path/guardian policy remain open; no government API is claimed.
- No runtime/real-account MFA enrolment, no operational DB/Redis, no external identity provider
  integration, no production claim.

**Final decision:** identity trust is `TESTED` / `INDEPENDENTLY VERIFIED` at engineering scope for
the listed links; no `PRODUCTION READY`. Evidence anchors: `GOVERNANCE/IDENTITY_REMEDIATION/`, `PHASE1_CLOSEOUT.md`,
`PHASE2_CLOSEOUT.md`, `NIAM_STEP_UP_SECURITY_REPORT.md`. Git SHA: `2206654dc713ea2de8c564a3207dfe05fde23549`.
