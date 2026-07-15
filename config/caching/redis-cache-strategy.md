# GULA Platform — Redis Cache Strategy

## Cache Layers

| Layer | Store | Purpose | TTL |
|-------|-------|---------|-----|
| L1 | In-memory dict | Hot data, idempotency | 30-60s |
| L2 | Redis | Distributed cache | 1min-1h |
| L3 | PostgreSQL | Source of truth | N/A |

## Cache Key Naming

```
gula:{domain}:{entity}:{id}:{field}
gula:patient:{patient_id}:profile
gula:lab:{lab_id}:orders:{status}
gula:user:{user_id}:session
gula:rates:auth:{ip}
```

## TTL Policies

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Patient profile | 5 min | Changes infrequently, high read volume |
| Lab results | 2 min | Clinical correctness — short TTL |
| Reference ranges | 1 h | Seldom changes |
| User session | 30 min | JWT expiration boundary |
| Feature flags | 5 min | Fast flag propagation |
| Rate limit counters | 1 min | Window-based reset |
| Lookup tables | 1 h | Static data |
| Idempotency keys | 24 h | Business requirement |

## Invalidation

- **Write-through**: Update DB → update cache → respond
- **Write-behind**: Update DB → queue invalidation → async cache update
- **Pattern**: Delete cache key on write, lazy-load on read
- **Bulk**: Pattern-based invalidation (`gula:patient:{id}:*`)

## Warming

- On startup: warm reference ranges, lookup tables
- On deploy: warm feature flags
- Scheduled: warm popular patient profiles every 5 min

## Monitoring

- Cache hit rate target: >90%
- Eviction rate: <0.1% of total keys/minute
- Memory usage: <80% of `maxmemory`
- Latency: p99 < 5ms

## Serialization

- Python objects: msgpack (faster, smaller)
- Complex objects: JSON with compression
- Avoid: pickle (security risk)
