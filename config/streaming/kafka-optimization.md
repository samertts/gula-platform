# GULA Platform — Kafka Streaming Optimization

## Topic Configuration

```
partitions: 6 (3x brokers)
replication: 3
min.insync.replicas: 2
retention.ms: 604800000 (7 days)
retention.bytes: 53687091200 (50 GB)
compression.type: snappy
cleanup.policy: delete
```

## Producer Optimization

- batch.size: 65536 (64KB)
- linger.ms: 5
- compression.type: snappy
- acks: all (strongest durability)
- max.in.flight.requests.per.connection: 5
- enable.idempotence: true

## Consumer Optimization

- fetch.min.bytes: 1
- fetch.max.wait.ms: 500
- max.partition.fetch.bytes: 1048576 (1MB)
- session.timeout.ms: 30000
- heartbeat.interval.ms: 3000
- auto.offset.reset: earliest
- enable.auto.commit: false

## Monitoring

- Consumer lag: < 1000 messages per partition
- Request rate: < 1000 req/s per broker
- Throughput: < 50 MB/s per broker

## Key Topics

| Topic | Partitions | Retention | Purpose |
|-------|-----------|-----------|---------|
| order.events | 6 | 7d | Order lifecycle events |
| result.events | 6 | 7d | Result submission events |
| notification.events | 3 | 3d | Push notification triggers |
| audit.events | 6 | 30d | Immutable audit trail |
