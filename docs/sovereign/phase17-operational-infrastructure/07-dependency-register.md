# Phase 17-07 — Infrastructure Dependency Register

The register lists every external infrastructure dependency the platform
has, the failure mode, and the contingency. It is reviewed quarterly.

## Core

| Dependency | Used by | Failure mode | Contingency |
|------------|---------|--------------|-------------|
| PostgreSQL 16 | Everything | Crash, replication lag, disk pressure | DR replica + WAL streaming + RB-02 |
| Redis 7 | Cache, rate limit, session store | Crash, memory pressure | Restart; cache miss penalty only |
| Docker engine | All containers | Daemon crash | Auto-restart; orchestrator failover |
| api-gateway (Docker nginx) | Ingress | Crash | Host nginx fallback; replicated |
| Host nginx | TLS termination | Crash | Maintenance page; secondary host |

## Secrets & Keys

| Secret | Source | Failure mode | Contingency |
|--------|--------|--------------|-------------|
| `SECRET_KEY` | Sovereign KMS / `.env` | Lost | Re-issue; sessions invalidated |
| `ENCRYPTION_KEY` | Sovereign KMS | Lost | Catastrophic; `national_id` decryption breaks |
| `NID_HMAC_KEY` | Sovereign KMS | Lost | National-id index breaks; rebuild required |
| `REFRESH_TOKEN_SECRET` | Sovereign KMS | Lost | Forced re-login |
| `DEVICE_HMAC_KEY` | Sovereign KMS | Lost | Device-card revocation needed |
| Adapter peer credentials | Per-adapter | Compromise | Per-adapter revocation; circuit open |
| `METRICS_BEARER_TOKEN` | Generated locally | Lost | `make metrics-token` regenerates |

## Networking

| Dependency | Failure mode | Contingency |
|------------|--------------|-------------|
| Sovereign internet egress | Outage | Provincial / edge offline mode |
| DNS | Misconfiguration | Hard-coded IPs in adapter clients (manifest) |
| Sovereign VPN to peers | Outage | Adapter circuit open; clinical unaffected |
| Telco SMS gateway | Outage | Alternate channel from Phase 23 |
| Payment gateway | Outage | Manual settlement; fraud detection paused |

## Observability

| Dependency | Failure mode | Contingency |
|------------|--------------|-------------|
| Prometheus | Crash | Metrics gap; alerting moves to manual |
| Grafana | Crash | Read prometheus directly; CLI dashboards |
| Alert webhook (Telegram/Slack/Discord) | Outage | Email fallback; SMS to on-call |
| Sentry (optional) | Outage | Local error logs sufficient |

## Edge

| Dependency | Failure mode | Contingency |
|------------|--------------|-------------|
| Edge agent | Offline | 72h local operation per Phase 23 |
| Lab device bridge | Crash | Manual result entry path |
| Provincial postgres | Crash | Local degraded read; central reads continue |

## External / Partner Systems

| Partner | Adapter | Failure | Contingency |
|---------|---------|---------|-------------|
| Ministry of Health | `moh-fhir` | Outage | Outbound queue; non-clinical reports delayed |
| National Health Insurance | `nhis-fhir` | Outage | Reimbursement queues; no automated execution affected |
| National Statistics | `dhis2-aggregator` | Outage | Aggregated push delayed; backfill on recovery |
| National ID system | `nid-resolver` | Outage | New patient registration with national-id deferred |
| Telcos | `sms-gateway` | Outage | Alternate carrier; paper notification fallback |
| Payment gateway | `payment-rails` | Outage | Manual settlement + reconciliation queue |
| Government interoperability hub | `gov-hub` | Outage | Direct point-to-point if pre-arranged |

## Update Discipline

This register is updated whenever:

- A new adapter is added.
- A dependency is replaced.
- A failure mode is discovered in production or drill.
- A vendor changes contractual SLA.

The register file is committed; the latest commit timestamp is the
"as-of" date.
