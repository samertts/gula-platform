# Phase-02B Completion Report — API Client & DTO Synchronization

Date: 2026-07-24
Program: PROGRAM-FRONTEND-009

## Summary

Phase-02B synchronized the frontend API client, DTOs, and endpoints with the existing backend contracts.

## Changes Made

### Critical Fix
1. **`src/api/client.ts`** — Refresh token URL changed from `/login` → `/auth/refresh`.
   The old code POSTed to the login endpoint with the refresh token in an Authorization header,
   which would always fail (login endpoint doesn't handle refresh tokens).
   Now correctly POSTs `{ refresh_token }` to `/auth/refresh` per both the mobile.py
   and identity API refresh endpoints.

### Minor Fixes
2. **`src/types/api.ts`** — Added `access_token?: string` to `LoginResponse` for NIAM API compatibility.
3. **`src/permissions/index.ts`** — Fixed whitespace bug on `staff: 20` (extraneous leading space).

### Verifications
4. **TypeScript**: `tsc --noEmit` — passes cleanly (0 errors)
5. **ESLint**: `eslint . --max-warnings=0` — passes cleanly (0 errors, 0 warnings)
6. **Build**: `npm run build` — passes (4.02s)

## Backend Audit Results

URL mismatches initially suspected were verified against backend routes and confirmed correct:
- `/auth/forgot-password` ✅ exists
- `/auth/reset-password` ✅ exists  
- `/national-id/verify` ✅ exists
- `/id-scan/scan` ✅ exists

## Remaining Debt (deferred to Phase-02C)

1. **Type consolidation**: `backend.ts` (570 lines) overlaps with `models.ts` (358 lines) and `api.ts` (48 lines).
   16 type names are duplicated across files with different shapes. Needs careful merge.
2. **~75% of endpoints.ts return `Record<string, unknown>`**: No type safety for most API responses.
3. **`permissions/index.ts` `ROLE_LEVELS`** duplicates `types/backend.ts` `ROLE_LEVELS`
   (but different shapes — permissions has `receptionist`, backend doesn't).
