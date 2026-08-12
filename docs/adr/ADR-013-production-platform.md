# ADR-013: Production Platform Architecture

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, DevOps Lead, CTO

---

## Context

The GULA platform has evolved from a monolith prototype into a national-scale healthcare platform serving Iraqi medical laboratories. The current Docker Compose deployment is insufficient for the required 99.99% availability, multi-region disaster recovery, enterprise security, and scalability demands.

We need a production-grade architecture that provides:
- 99.99% availability (53 minutes downtime per year max)
- Multi-region disaster recovery (RPO 5s, RTO 5min)
- Zero-downtime deployments (blue-green and canary)
- Full observability (metrics, logs, traces)
- Enterprise security (mTLS, WAF, encryption)
- Horizontal scalability
- Self-healing infrastructure

## Decision

Adopt a Kubernetes-based platform architecture with the following components:

### 1. Container Orchestration: Kubernetes + Helm
- Kubernetes 1.28+ for container orchestration across multi-node clusters
- Helm charts for repeatable, version-controlled deployments
- Kustomize for environment-specific overlays
- **Reasoning:** Industry standard, cloud-agnostic, rich ecosystem, self-healing

### 2. Database HA: Patroni for PostgreSQL 16
- Patroni manages PostgreSQL streaming replication with automatic failover
- 1 primary + 2 replicas minimum
- Automatic leader election and replica promotion
- **Reasoning:** Battle-tested PostgreSQL HA solution, automatic failover, no data loss (synchronous replication)

### 3. Cache HA: Redis Sentinel
- 3-node Sentinel cluster with 1 master + 2 replicas
- Automatic failover on master failure
- Client-side routing via Sentinel discovery
- **Reasoning:** Simple HA for Redis, automatic failover, proven in production

### 4. Messaging Resilience: RabbitMQ Cluster
- 3-node RabbitMQ cluster with mirrored queues
- Durable queues with HA policy
- Automatic failover with mirrored queue promotion
- **Reasoning:** Reliable message delivery, cluster support, well-understood

### 5. Object Storage: MinIO Distributed
- 4-node MinIO with erasure coding (16:8)
- Data redundancy across nodes
- S3-compatible API
- **Reasoning:** Self-hosted, S3-compatible, erasure coding durability, no vendor lock-in

### 6. Service Mesh: Linkerd
- mTLS for all inter-service communication
- Traffic splitting for canary deployments
- Automatic metrics and tracing
- **Reasoning:** Lightweight, Kubernetes-native, automatic mTLS, minimal overhead

### 7. Observability: OpenTelemetry + Prometheus/Loki/Tempo + Grafana
- OpenTelemetry for instrumentation (metrics, logs, traces)
- Prometheus for metrics storage (30-day retention)
- Loki for log aggregation (30-day retention)
- Tempo for distributed tracing (7-day retention)
- Grafana for visualization and alerting
- **Reasoning:** Open source, no vendor lock-in, data residency control, active community

### 8. Edge Security: Cloudflare
- CDN for static assets and API caching
- WAF for application security
- DDoS protection (L3/L4/L7)
- DNS management with failover
- SSL/TLS termination
- **Reasoning:** Best-in-class edge security, global CDN, DDoS protection, DNS failover

### 9. Certificate Management: cert-manager
- Let's Encrypt certificates with automatic renewal
- 90-day certificate lifetime, renewal at 30 days
- HTTP-01 and DNS-01 challenge support
- **Reasoning:** Automated certificate lifecycle, no manual intervention

### 10. Deployment Strategy: Blue-Green + Canary
- Blue-green for major version deployments
- Canary for risky changes (traffic splitting via Linkerd)
- Automated rollback on health check failure
- HPA for auto-scaling based on CPU/memory/request rate

## Alternatives Considered

### 1. Managed Cloud Services (AWS RDS, ElastiCache, etc.)

**Pros:** Lower operational overhead, managed backups, automatic scaling.
**Cons:** Vendor lock-in, data sovereignty concerns (Iraqi health data), higher cost at scale, compliance complexity.
**Rejected because:** Data sovereignty requirements for Iraqi health data make cloud-agnostic self-hosting necessary.

### 2. Docker Swarm

**Pros:** Simpler than K8s, part of Docker ecosystem.
**Cons:** Limited ecosystem, no service mesh, fewer HA features, smaller community.
**Rejected because:** Kubernetes is the industry standard with richer ecosystem for production-grade deployments.

### 3. Istio Service Mesh

**Pros:** More features than Linkerd (more policy options, richer telemetry).
**Cons:** Higher resource consumption, more complex, steeper learning curve.
**Rejected because:** Linkerd's simplicity and lower overhead are better suited for our team size while still providing essential mTLS and traffic splitting.

### 4. Datadog for Observability

**Pros:** All-in-one platform, easy setup, rich features.
**Cons:** Very expensive at scale, data sovereignty risk (health data leaves control), vendor lock-in.
**Rejected because:** OpenTelemetry stack provides equivalent capabilities with data residency control and lower cost.

### 5. NGINX Ingress Controller Only

**Pros:** Simple, well-understood.
**Cons:** No mTLS, no traffic splitting for canary, manual configuration.
**Rejected because:** Service mesh (Linkerd) is needed for automated mTLS and advanced traffic management.

## Consequences

### Positive
- **99.99% availability** through multi-node HA for all components
- **Self-healing infrastructure** — K8s restarts failed pods, Patroni promotes DB replicas, Sentinel handles cache failover
- **Zero-downtime deployments** via blue-green and canary strategies
- **Full observability** with metrics, logs, traces in a single Grafana interface
- **Enterprise security** with mTLS, WAF, DDoS protection
- **Data residency** control with self-hosted infrastructure
- **Cloud-agnostic** — can run on any Kubernetes provider or on-premise
- **Horizontal scalability** for all components

### Negative
- **+50% operational complexity** — K8s cluster management, Helm, Linkerd, Patroni, all require specialised knowledge
- **Additional infrastructure cost** — Multi-node clusters, monitoring stack, edge CDN increase monthly costs 2-3x
- **Longer learning curve** for the operations team
- **More moving parts** increases the surface area for potential issues

### Risks
- **Multi-region latency** — Synchronous replication between ME and EU regions may impact write latency
- **Data sovereignty compliance** — Must ensure EU DR region complies with Iraqi health data regulations
- **Kubernetes version upgrades** — Require careful planning and testing
- **Patroni split-brain** — Rare but possible in network partition scenarios, mitigated by synchronous replication and failover safeguards

## References

- `k8s/` — Kubernetes manifests and Helm charts
- `docker-compose.yml` — Docker Compose deployment (for development/staging)
- `helm/gula-platform/` — Helm chart for platform deployment
- ADR-002: Monolith First Architecture
- ADR-005: PostgreSQL Redis Stack
- ADR-009: Self-Healing Infrastructure
- `docs/production/PRODUCTION_GUIDE.md` — Production architecture details
- `docs/production/DISASTER_RECOVERY_GUIDE.md` — Disaster recovery strategy
