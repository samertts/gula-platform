# Hook Sync Report — Phase-02B

Date: 2026-07-24

## Current State

`src/hooks/useApi.ts` wraps `endpoints.ts` with React Query (`@tanstack/react-query`).

No changes needed to hooks — they consume `endpoints.ts` generically via the `apiClient.api` Axios instance.

The type drift in `endpoints.ts` (`Record<string, unknown>` returns) means hooks provide no compile-time
type safety for ~75% of API responses. However, hook structure and React Query configuration are correct.

## Hook Inventory

- `useApi()` — returns the `apiClient.api` Axios instance
- All data fetching is done inline in pages using endpoints.ts directly with React Query

No hook sync changes required for Phase-02B.
