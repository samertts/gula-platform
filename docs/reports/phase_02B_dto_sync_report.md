# DTO Sync Report — Phase-02B

Date: 2026-07-24

## Current State

Three type files coexist with overlapping definitions:

### `types/api.ts` (Authoritative for: Auth)
- `LoginRequest` — `{ email, password }` matches `routes/login.py:LoginRequest`
- `LoginResponse` — `{ token, refresh_token, token_type, user }` matches `routes/login.py` return
- `LoginResponse.access_token?` — added for NIAM `/auth/refresh` compatibility
- `JwtPayload` — `{ user_id, lab_id, role, perm_ver, type, jti, exp }`

### `types/models.ts` (Authoritative for: Domain)
- 35 interfaces for domain models, dashboard data, AI responses, health status
- Some fields differ from backend (e.g., `CriticalAlert` has `critical_tests: string[]` vs backend's `test_name, value, flag`)

### `types/backend.ts` (Legacy — derived from backend models)
- 50+ interfaces — most accurate to actual backend schemas
- Includes request DTOs (CreatePatientRequest, CreateOrderRequest, etc.) not in models.ts
- Includes type unions (UserRole, Permission, OrderStatus, etc.) not in models.ts
- PURELY a reference file — imported directly by 4 files for specific types

## Changes Made

| File | Change |
|---|---|
| `types/api.ts` | Added `access_token?: string` to LoginResponse |
| `types/models.ts` | (no changes — type dedup deferred) |
| `types/backend.ts` | (no changes — kept for direct imports) |
| `types/index.ts` | (reverted — backend.ts not in barrel export to avoid duplication) |

## Remaining Debt

1. `backend.ts` vs `models.ts` has 12 overlapping types with different shapes
2. Recommend consolidating in Phase-02C: move backend.ts unique types into models.ts, then remove backend.ts
3. `endpoints.ts` still uses `Record<string, unknown>` for ~75% of return types
