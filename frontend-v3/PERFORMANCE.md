# Performance Report

## Bundle Optimization

### Code Splitting
✅ All 29 pages lazy loaded via React.lazy()
✅ Route-based chunk splitting (each page = separate chunk)
✅ Main bundle: 451 kB (142 kB gzip)
✅ Framework chunk (react, react-dom, router): ~140 kB gzip

### Build Metrics
| Metric | Value |
|--------|-------|
| Build time | ~1.4s |
| Modules | 1,748 |
| Chunks | 37 |
| Total output | ~750 kB (gzip: ~185 kB) |

## Data Fetching

### React Query Configuration
- `staleTime`: 30s (default)
- `retry`: 1 (default)
- All queries use typed `useQuery` hooks with auto-caching
- All mutations auto-invalidate related queries

### Optimizations
- Query key convention: `["domain", "resource", ...params]`
- Dependent queries via `enabled` flag
- Invalidation on mutation success
- Debounced search inputs (300ms)

## Realtime
- WebSocket with exponential backoff reconnection (max 10 retries)
- Server-Sent Events for lab streams
- Heartbeat ping/pong every 30s

## Recommendations
1. Add virtualization for large tables (e.g., `@tanstack/react-virtual`)
2. Implement route prefetching for predicted next pages
3. Add service worker for PWA offline support
4. Consider `react-query` `keepPreviousData` for paginated tables
5. Add automated bundle analysis to CI pipeline
