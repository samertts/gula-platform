# National Platform Runtime — Performance Report

## Resource Footprint

| Resource | Per Module | Total (9 modules) |
|----------|-----------|-------------------|
| Source files | ~15 avg | 137 |
| Python memory (loaded) | ~2-5 MB | ~30 MB |
| DB tables | 3-5 avg | ~35 |
| API endpoints | ~20 avg | 181 |

## DB Connection Pool Impact

```
Existing pool:  WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) = 3 × (6 + 12) = 54
New pool budget: +0 (reuses existing connections via SessionLocal)
```

The Runtime modules do not create their own connection pools. They use the existing `SessionLocal` from `database.py`, which already manages a pool of 54 connections within PostgreSQL's default 100 connection limit. **Zero additional connection overhead.**

## EventBus Throughput

- Each module publishes events asynchronously via `kernel.event_bus.EventBus`
- EventBus uses `asyncio.create_task` for non-blocking dispatch
- Busy-polling loop runs every 0.5 seconds for scheduled events
- All event handlers registered at module startup via subscription

## Bottleneck Analysis

| Component | Risk | Mitigation |
|-----------|------|------------|
| DB writes | Low | Repositories batch via bulk_insert when possible |
| EventBus | Low | Async dispatch, 0.5s polling interval |
| Template rendering | Low | Jinja2/Mustache cached compilation |
| Search adapters | Medium | Adapter pattern — Elasticsearch adapter scales horizontally |
| QR generation | Low | Lightweight (PIL qrcode ~50ms per image) |
| Notification delivery | Medium | Async dispatch with per-channel rate limiting |

## Scaling Recommendations

1. **Search**: Use Elasticsearch adapter for national-scale deployments (>1M documents)
2. **Notifications**: Deploy dedicated notification workers for high-throughput SMS/Email
3. **Background Jobs**: Scale worker count with `feats_capacity` per job type
4. **Metrics**: Export to Prometheus via `/national/observability/metrics` for cluster-level monitoring
