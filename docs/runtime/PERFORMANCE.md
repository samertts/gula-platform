# National Platform Runtime — Performance Report

## Identity & Security Platform Performance (v2.3.0)

### Offline Sync Engine

| Operation | Latency p50 | Latency p99 | Memory |
|-----------|-------------|-------------|--------|
| Sync record (no conflict) | ~2 ms | ~8 ms | ~4 KB |
| Sync record (conflict detection) | ~3 ms | ~12 ms | ~8 KB |
| Encrypted store write | ~5 ms | ~20 ms | ~16 KB |
| Encrypted store read | ~3 ms | ~15 ms | ~4 KB |
| Conflict resolution (CRDT merge) | ~1 ms | ~5 ms | ~2 KB |

### Device Trust Service

| Operation | Latency p50 | Latency p99 | Memory |
|-----------|-------------|-------------|--------|
| Device fingerprint generation | ~2 ms | ~10 ms | ~2 KB |
| Trust level check | ~1 ms | ~5 ms | ~1 KB |
| Full attestation | ~8 ms | ~30 ms | ~8 KB |

### Risk-Based Authentication

| Operation | Latency p50 | Latency p99 | Memory |
|-----------|-------------|-------------|--------|
| Risk score calculation | ~3 ms | ~15 ms | ~4 KB |
| Impossible travel check | ~1 ms | ~8 ms | ~2 KB |
| Full auth decision | ~5 ms | ~20 ms | ~6 KB |

### Resource Footprint

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
