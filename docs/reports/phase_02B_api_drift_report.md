# API Drift Report — Phase-02B

Date: 2026-07-24

## Drift Categories

### Critical (operational bug)
1. **Refresh token URL wrong** — `client.ts:66` POSTs to `/login` instead of `/auth/refresh`
   - Impact: Refresh always fails (login endpoint doesn't handle refresh tokens)
   - Fix applied: URL → `/auth/refresh`, body → `{ refresh_token }` instead of Authorization header

### URL Mismatches — FALSE ALARMS (resolved by backend audit)
| Frontend Path | Initial Suspicion | Backend Reality | Verdict |
|---|---|---|---|
| `/auth/forgot-password` | Maybe `/password-reset/request` | ✅ Exists at `routes/password_reset.py:35` | Correct |
| `/auth/reset-password` | Maybe `/password-reset/reset` | ✅ Exists at `routes/password_reset.py:57` | Correct |
| `/national-id/verify` | Maybe `/national-identity/verify` | ✅ Exists at `routes/national_identity.py:15` | Correct |
| `/id-scan/scan` | Maybe `/id-scan/upload` | ✅ Exists at `routes/id_scan.py:136` | Correct |

### Shape Mismatches

**LoginResponse** — `types/api.ts` has `{ token, refresh_token, token_type, user }` which matches `routes/login.py` return. Identity API returns `{ access_token, ... }`. No fix needed for login endpoint — but `access_token` added as optional for NIAM compatibility.

### Return Type Drift
~75% of `endpoints.ts` returns `Record<string, unknown>` — no static typing for backend responses.
Priority: Low (no runtime impact, but poor DX).

### Type Duplication
- 4 types duplicated between `api.ts` and `backend.ts` with different shapes
- 12 types duplicated between `models.ts` and `backend.ts` with different shapes
- This creates import ambiguity and maintainability debt
