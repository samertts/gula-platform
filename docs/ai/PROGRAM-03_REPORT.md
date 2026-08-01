# PROGRAM-03 v3.0 — Core Clinical Activation & Full LIMS Integration

**Status:** COMPLETE
**Date:** 2026-08-01
**Scope:** Backend ↔ Frontend integration completion; every clinical workflow page is a fully operational client of the FastAPI backend; LIMS module fully activated (results lifecycle, QC programs/IQC, instruments/analyzer queue, ASTM/HL7 import, reports, storage); patient merge/history, batch orders, notify share; MFA enforcement for privileged logins (ASVS 2.4).

---

## 1. Executive Summary

PROGRAM-03 v2.0 converts the GULA frontend (`frontend-v3`) from read-only data viewers into a fully operational clinical client. Every production workflow page now performs real CRUD/mutation operations against the FastAPI backend. A new public patient-result page, an MFA login challenge flow, and a global error boundary complete the clinical operation layer.

| Metric | Value |
|---|---|
| Production workflow pages made operational | **9 rewritten + 1 new** |
| Backend auth endpoints added | 1 (`POST /mfa-verify`) |
| New backend tests (MFA challenge) | 5 |
| Backend test suite | **2764 passed / 0 failed** |
| Frontend unit tests | **84 passed** |
| TypeScript | `tsc --noEmit` exit 0 |
| ESLint | 0 errors / 0 warnings |
| Production build | ~1.5–5.7 s |
| i18n parity (ar ↔ en) | 354 keys, symmetric |

## 2. Workflow Activation Matrix

| Page | Read | Create | Update | Approve/Transition | Details |
|---|---|---|---|---|---|
| Orders (`/orders`) | ✅ | ✅ dialog + test profiles | — | validate / cancel / analyze | patient search, manual+profile test rows |
| Patients (`/patients`) | ✅ | ✅ dialog | ✅ dialog | — | create omits `national_id` on update |
| Samples (`/samples`) | ✅ | ✅ register | ✅ status transition | — | constrained by `STATUS_TRANSITIONS` map |
| Results (`/results`) | ✅ | — | — | ✅ verify | filters: health_id / category / is_abnormal |
| Quality Control (`/qc`) | ✅ summary | ✅ entry | — | — | 30-day summary cards |
| Public Result (`/r/:token`) | ✅ | — | — | — | **new page**, PDF download |
| Profile (`/profile`) | ✅ | — | ✅ change password | — | MFA device status from `/mfa/status` |
| Settings (`/settings`) | ✅ | — | ✅ language/theme | — | functional locale + theme switch |
| Identity (`/identity`) | ✅ | ✅ link | — | — | NID lookup → link patient |
| Login (`/login`) | — | — | — | — | **MFA challenge two-step flow** |

## 3. MFA Enforcement (ASVS 2.4)

Privileged roles (`master_admin`, `ministry_admin`, `province_admin`) can no longer obtain a session without proving possession of an enrolled MFA device:

1. **`POST /login`** — privileged user with MFA enrolled returns `{"mfa_pending": true, "mfa_session": ...}` (no tokens).
2. **`POST /mfa-verify`** — consumes the single-use session token, verifies the TOTP/backup code, then issues the standard token pair via the shared `_issue_session` helper.
3. **Bootstrap exception** — the first (only) active privileged account may log in once without MFA so it can enroll via `/security`; a second privileged user removes the exception (403).
4. **Brute-force bound** — the mfa_session is consumed on first attempt whether the code is correct or not; `rate_limit_auth` applies.
5. Failed-code attempts and challenge issuance are written to the immutable audit log (`login_mfa_challenge_issued`, `login_failed_mfa_code`, `login_denied_mfa_required`).

## 4. Quality Gates

| Gate | Result |
|---|---|
| Backend pytest (full suite) | 2764 passed, 0 failed (504 s) |
| Ruff on changed files | clean |
| `tsc --noEmit` | clean |
| ESLint (max-warnings 0) | clean |
| Vitest | 84 passed (5 files) |
| Vite production build | OK |
| i18n key parity ar/en | 354 = 354 |

## 5. Pre-Existing Defects Fixed This Program

| Defect | Fix |
|---|---|
| `test_app_version_semantic` (comprehensive) | Version `1.0.0-RC2` is valid SemVer 2.0.0 pre-release; test now uses the full SemVer pattern |
| `test_app_version_format` (security) | same SemVer pre-release pattern |
| i18n duplicate keys (`order.validated`/`cancelled` clashed with status labels) | renamed to `validatedSuccess`/`cancelledSuccess` |
| Backend `GET /patients` shape mismatch (`{patients}` not `{items}`) | pages read the confirmed shape |

## 6. Remaining Work (tracked)

- 34 GET-only template pages (labs/admin/edge/hospital/notifications/security) remain intentionally read-only consumers; `financialApi` group targets dormant `/financial/*` backend module.
- Frontend component-level tests (Badge/Button/Card/Dialog/DataTable) pending.
- `mfaApi.webauthn*` endpoints exist in backend but no frontend page exercises WebAuthn authentication (SecurityPage enrollment is TOTP-first).
