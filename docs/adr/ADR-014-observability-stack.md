# ADR-014: Observability Stack Selection

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, DevOps Lead

---

## Context

The GULA platform requires a comprehensive observability stack to monitor production health, diagnose issues, track performance trends, and alert on anomalies. The selected stack must provide:

- **Metrics** — CPU, memory, request rate, latency, error rate, queue depth, cache hit ratio
- **Logs** — Centralized log aggregation with search, filtering, and correlation
- **Traces** — Distributed tracing across services for performance analysis
- **Alerting** — Configurable alerts with routing to Slack, PagerDuty, Email
- **Dashboards** — Visual representation of all observability data

**Requirements:**
- Open source (no vendor lock-in)
- Data residency control (health data must remain in-region)
- Horizontal scalability as data volume grows
- Integration with Kubernetes and Docker environments
- Low operational overhead
- Active community and ecosystem

## Decision

Adopt the OpenTelemetry + Prometheus/Loki/Tempo + Grafana stack (the "LGTM" stack with OpenTelemetry).

### Components

| Component | Purpose | Retention | Storage |
|-----------|---------|-----------|---------|
| **OpenTelemetry Collector** | Instrumentation agent, data pipeline | — | — |
| **Prometheus** | Metrics collection and storage | 30 days | Local SSD |
| **Loki** | Log aggregation and search | 30 days | Local SSD + Object storage |
| **Tempo** | Distributed tracing storage | 7 days | Local SSD + Object storage |
| **Grafana** | Visualization, dashboards, alerting | — | PostgreSQL (for metadata) |
| **Alertmanager** | Alert routing and deduplication | — | — |

### Data Flow

```
Application / Infrastructure
    │
    ▼
OpenTelemetry Collector
    │
    ├── Metrics ──► Prometheus ──► Grafana
    ├── Logs    ──► Loki      ──► Grafana
    └── Traces  ──► Tempo     ──► Grafana
                                        │
                                        ▼
                                  Alertmanager
                                        │
                                    ┌───┼───┐
                                    ▼   ▼   ▼
                                 Slack PD Email
```

### Why OpenTelemetry (vs. direct agent)

- Single agent for metrics, logs, and traces
- Vendor-neutral data format
- Auto-instrumentation for common frameworks
- Extensible via processors and exporters
- Future-proof — industry standard for observability

### Why Prometheus (vs. Thanos, VictoriaMetrics)

- De facto standard for Kubernetes metrics
- Simple, reliable, well-understood
- Rich ecosystem of exporters and integrations
- Can be scaled with Thanos if needed
- Active community

### Why Loki (vs. Elasticsearch)

- Purpose-built for log aggregation
- Lower resource consumption (no indexing of log content)
- Native Grafana integration
- Cheaper to operate at scale
- Labels-based indexing is sufficient for our use case

### Why Tempo (vs. Jaeger)

- Native Grafana integration
- Lower storage requirements (no indexing of trace content)
- Scales horizontally with object storage backend
- Active development by Grafana Labs

## Alternatives Considered

### 1. Datadog

**Pros:** All-in-one platform, easy setup, rich features, excellent UI.
**Cons:**
- **Very expensive** — Estimated $5,000-15,000/month at our scale
- **Data sovereignty risk** — Health data leaves our infrastructure
- **Vendor lock-in** — Hard to migrate away
- **Rejected because:** Cost and data sovereignty concerns are deal-breakers for Iraqi health data.

### 2. Elastic Stack (Elasticsearch, Logstash, Kibana, APM)

**Pros:** Mature, full-featured, good documentation.
**Cons:**
- **Resource intensive** — Elasticsearch requires significant RAM and storage
- **Operational complexity** — Cluster management is non-trivial
- **Cost at scale** — Licensing for Elastic APM is expensive
- **Rejected because:** Loki is lighter-weight and sufficient for our needs; Tempo handles tracing better than Elastic APM.

### 3. New Relic

**Pros:** Excellent APM, easy instrumentation, good dashboards.
**Cons:**
- **Very expensive** — Per-host pricing at scale
- **Data sovereignty risk** — All data leaves our infrastructure
- **Vendor lock-in**
- **Rejected because:** Cost and data sovereignty concerns.

### 4. Self-hosted ELK with Jaeger

**Pros:** Full control, no vendor lock-in.
**Cons:**
- **Elasticsearch resource consumption** — Heavy for log storage
- **Jaeger + Grafana integration** — Less seamless than Tempo
- **More components to manage**
- **Rejected because:** LGTM stack is lighter-weight and better integrated.

## Consequences

### Positive
- **Zero licensing cost** — All components are open source
- **Data residency** — All observability data stays within our infrastructure
- **No vendor lock-in** — OpenTelemetry format is portable
- **Seamless Grafana integration** — Metrics, logs, and traces in one UI
- **Horizontal scalability** — All components can scale independently
- **Active community** — Grafana, Prometheus, and OpenTelemetry have large communities

### Negative
- **Operational overhead** — Running 5+ observability components requires effort
- **Storage costs** — 30-day log and metric retention requires significant disk
- **Setup complexity** — Configuration of OpenTelemetry, Prometheus rules, Loki pipelines, Tempo sampling, and Grafana dashboards is non-trivial
- **Alert fatigue risk** — Without careful tuning, too many alerts can desensitize the team

### Neutral
- **Skill requirement** — Team needs to learn OpenTelemetry, PromQL, LogQL, TraceQL
- **Grafana version upgrades** — Need to stay current to get new features and security patches

## References

- OpenTelemetry: https://opentelemetry.io
- Prometheus: https://prometheus.io
- Loki: https://grafana.com/oss/loki
- Tempo: https://grafana.com/oss/tempo
- Grafana: https://grafana.com/oss/grafana
- ADR-013: Production Platform Architecture
- `config/prometheus/` — Prometheus configuration
- `config/grafana/` — Grafana dashboards
