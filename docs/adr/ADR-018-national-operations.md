# ADR-018: National Platform Operations Center

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, DevOps Lead, Platform Architect

---

## Context

As the GULA platform expands from a single-laboratory SaaS to a national healthcare platform serving laboratories, hospitals, clinics, and government agencies across Iraq, operational complexity grows exponentially. There is no centralized system for managing platform operations across development, staging, and production environments.

**Requirements:**
- Centralized operations dashboard showing health, performance, and alerts across all environments
- Release management pipeline with approval gates, rollback capability, and audit trail
- Incident management system with severity classification, escalation paths, and post-mortem tracking
- Environment management for provisioning, scaling, and configuration of sandbox/staging/production
- Change management with approval workflows, scheduled maintenance windows, and blast radius control
- 24/7 monitoring and alerting with on-call scheduling and escalation
- Compliance reporting for Iraqi health data regulations

**Constraints:**
- Must integrate with existing infrastructure (Docker Compose, K8s, DigitalOcean, Cloudflare)
- Must not duplicate capabilities of existing tools (GitHub, Grafana, Prometheus)
- Must be deployable within existing team size (no dedicated SRE team initially)
- Must support both automated and manual operational workflows

## Decision

Implement a `control_plane/` module that serves as the National Platform Operations Center. Rather than building a monolithic operations portal, the operations center is a lightweight orchestration layer that integrates existing tools and adds unified workflow automation.

### Architecture

```
+----------------------------------------------------------------+
|               National Platform Operations Center              |
+----------------------------------------------------------------+
|                                                                 |
|  +------------+  +------------+  +------------+  +-----------+ |
|  | Operations |  | Release    |  | Incident   |  | Change    | |
|  | Dashboard  |  | Manager    |  | Manager    |  | Manager   | |
|  +------+-----+  +------+-----+  +------+-----+  +-----+-----+ |
|         |               |               |               |       |
|  +------+---------------+---------------+---------------+----+ |
|  |                    Workflow Engine                          | |
|  |  (Approval gates, automated rollbacks, escalations)        | |
|  +------+---------------+---------------+---------------+----+ |
|         |               |               |               |      |
|  +------+-------+  +----+-------+  +----+-------+  +----+---+ |
|  |  GitHub      |  | Kubernetes |  |  Grafana / |  | Cloud  | |
|  |  Actions     |  | / Docker   |  |  Prometheus|  | APIs   | |
|  +--------------+  +-----------+  +------------+  +--------+ |
|                                                                 |
+-----------------------------------------------------------------+
```

### Key Design Decisions

1. **Orchestration, not replacement** — The operations center orchestrates existing tools (GitHub Actions for CI/CD, Grafana for dashboards, PagerDuty for on-call, Kubernetes for deployment). It does not replace them but adds cross-tool workflows.

2. **Workflow engine as core** — A lightweight workflow engine (`control_plane/workflows/`) defines operations processes as code: release pipelines, incident response playbooks, change management flows. Workflows are version-controlled, auditable, and testable.

3. **Operations dashboard** — A read-only dashboard (`control_plane/dashboard/`) aggregates health, performance, and alert data from all environments. It does not provide write access (no accidental production changes).

4. **Release management** — Releases follow a defined pipeline: build -> test -> staging approval -> canary -> production approval -> rollout -> verify. Each step has automated gates and manual approval points.

5. **Incident management** — Incidents are classified as SEV-1 (critical/patient safety), SEV-2 (major), SEV-3 (minor), or SEV-4 (cosmetic). Each severity has defined response times, escalation paths, and post-mortem requirements.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | Operations dashboard with environment health views | 6 weeks |
| **Phase 2** | Release management pipeline with approval gates | 6 weeks |
| **Phase 3** | Incident management with escalation and on-call | 6 weeks |
| **Phase 4** | Change management, compliance reporting, full automation | 6 weeks |

## Consequences

### Positive
- **Unified operations view** — Single dashboard for all environments reduces cognitive load
- **Repeatable releases** — Standardized release pipeline reduces deployment errors
- **Faster incident response** — Defined playbooks and escalation paths reduce MTTR
- **Audit trail** — Every operational action is logged for compliance and post-mortem analysis
- **Team scalability** — Automated workflows allow a small team to manage national-scale operations
- **Integration, not replacement** — Leverages existing tool investments rather than replacing them

### Negative
- **Workflow maintenance** — Operations workflows must be kept in sync with actual processes
- **Initial setup overhead** — Integrating with multiple existing tools requires significant initial effort
- **Tool dependency** — Operations center is only as reliable as the tools it orchestrates
- **On-call burden** — 24/7 coverage requires team rotation and may cause burnout without adequate staffing

### Risks
- **Workflow drift** — Actual operations processes may diverge from defined workflows. Mitigated by: regular audits, workflow tests, making workflows the required path for all operations.
- **Dashboard overload** — Too much information leads to alert fatigue and missed signals. Mitigated by: tiered dashboards (executive summary / team detail / debug), tunable alert thresholds.
- **Single point of failure** — Operations center itself could go down during an incident. Mitigated by: lightweight design, static fallback dashboards, incident response runbooks that work offline.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 6** — Operational excellence and reliability are engineering requirements
- **ADR-013** — Production platform architecture provides the infrastructure the operations center manages
- **ADR-014** — Observability stack provides the monitoring data consumed by the operations dashboard
- **ADR-015** — Disaster recovery procedures are managed as incident response playbooks
- **Iraqi Health Data Regulations** — Change management and audit trails for compliance reporting
- **ITIL-aligned practices** — Incident, change, and release management follow established ITIL framework
