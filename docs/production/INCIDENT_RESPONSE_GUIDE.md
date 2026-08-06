# GULA Platform — Incident Response Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL

---

## 1. Incident Severity Classification

| Severity | Definition | Response Time | Examples | Notify |
|----------|-----------|--------------|----------|--------|
| **SEV1** | Platform down or data loss risk | <15 min | Backend completely down, database failure, data breach, major security incident | On-call + Engineering Lead + CTO |
| **SEV2** | Degraded performance, some users affected | <30 min | High latency, partial outage, non-critical data inconsistency | On-call + Engineering Lead |
| **SEV3** | Non-critical bug, minor feature broken | <2 h | Single endpoint failing, minor UI bug, cosmetic issue | Team channel + Jira |
| **SEV4** | Cosmetic issue, documentation bug | <1 week | Typo, minor UI glitch, documentation error | Jira ticket only |

---

## 2. Incident Lifecycle

```
DETECT → TRIAGE → CONTAIN → MITIGATE → RESOLVE → POST-MORTEM
```

### Phase 1: Detect

**Sources of detection:**
- Automated monitoring alerts (Prometheus, Grafana, PagerDuty)
- User reports (Slack, email, support ticket)
- Manual observation (team member notices issue)
- Security tool alerts (WAF, IDS, SIEM)

**Action:**
- Acknowledge the alert
- Open an incident channel in Slack: `#gula-incident-<date>-<seq>`
- Post initial notification with available information

### Phase 2: Triage

**Objective:** Determine severity and assign ownership.

```bash
# 1. Check current health
curl -s https://api.gula.health/health
curl -s https://api.gula.health/health/deep | jq .

# 2. Check recent changes
git log --oneline -10
kubectl get events -n gula-platform --sort-by=lastTimestamp | tail -10

# 3. Check monitoring
# Grafana: Platform Overview dashboard
# Check: error rate, latency, request volume, resource usage

# 4. Determine severity
# SEV1: Platform down, data loss, security breach
# SEV2: Degraded but operational
# SEV3: Minor issue
# SEV4: Documentation/cosmetic
```

### Phase 3: Contain

**Objective:** Prevent the incident from getting worse.

| Incident Type | Containment Actions |
|--------------|-------------------|
| Backend crash | Restart container, scale up replicas |
| Database failure | Activate circuit breaker, promote replica |
| Security breach | Rotate secrets, block IPs, disable accounts |
| Traffic spike | Enable rate limiting, scale out |
| Data corruption | Stop writes, take snapshot, restore from backup |

### Phase 4: Mitigate

**Objective:** Reduce or eliminate impact to users.

- Apply workaround (feature flag, hotfix, configuration change)
- Redirect traffic (blue-green switch, canary rollback)
- Scale resources to handle load
- Enable degraded mode if available
- Communicate status to users

### Phase 5: Resolve

**Objective:** Restore normal operations.

```bash
# 1. Apply permanent fix
git commit -m "fix: resolve root cause of incident"

# 2. Deploy fix
# (standard deployment procedure)

# 3. Verify resolution
curl -s https://api.gula.health/health/deep | jq .

# 4. Monitor for stability (15-30 min)

# 5. Close incident
# Post resolution message in incident channel
```

### Phase 6: Post-Mortem

**Objective:** Learn and prevent recurrence.

**Schedule:** Within 24 hours for SEV1, within 1 week for SEV2+

**Attendees:** All involved team members

**Post-Mortem Document Template:**

```markdown
# Post-Mortem: [Incident Title]

**Date:** YYYY-MM-DD
**Duration:** [Start] — [End] UTC
**Severity:** SEV[X]
**Incident Commander:** [Name]

## Summary
[1-2 paragraph description of what happened]

## Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | Incident detected via [source] |
| HH:MM | Severity classified as SEV[X] |
| HH:MM | Containment action taken |
| HH:MM | Mitigation deployed |
| HH:MM | Service restored |
| HH:MM | Monitoring period ended |

## Root Cause
[5 Whys analysis]

## Impact
- Availability: [%] uptime during incident
- Users affected: [count]
- Data loss: [YES/NO + extent]
- Financial impact: [if measurable]

## What Went Well
- [Thing that worked well]

## What Went Wrong
- [Thing that didn't work well]

## Action Items
| # | Action | Owner | Deadline |
|---|--------|-------|----------|
| 1 | [Action] | [Owner] | [Date] |

## Appendices
- Related logs
- Monitoring dashboards
- Communication history
```

---

## 3. Incident Command Structure

### Roles

| Role | Responsibility | Assigned To |
|------|---------------|-------------|
| **Incident Commander (IC)** | Overall coordination, decision making, communication | Most senior on-call |
| **Scribe** | Timeline recording, action tracking | Any team member |
| **Technical Lead** | Diagnosis and fix implementation | Backend/infra specialist |
| **Communications Lead** | Stakeholder updates, status page | Engineering Lead |
| **Security Lead** | Security-related incidents | Security team member |

### Role Handoff

```
Initial on-call → Incident Commander
              ↓
       If SEV1 → Engineering Lead becomes IC
              ↓
       If extended → CTO assumes IC
```

### Decision Authority

| Decision | Approver |
|----------|----------|
| Rollback deployment | IC |
| Restore from backup | IC + DBA |
| Rotate secrets | Security Lead |
| Declare SEV1 | Any team member |
| Communication to stakeholders | Communications Lead |
| Post-mortem approval | Engineering Lead |

---

## 4. Communication Templates

### Incident Acknowledgment

```
🚨 INCIDENT ACKNOWLEDGED 🚨

Incident: [Brief description]
Severity: SEV[X] (initial assessment)
Detected: [TIMESTAMP UTC]
Detected by: [Alert / User / Manual]

Initial assessment:
[1-2 sentences]

Current status:
[Investigating / Containing / Mitigating]

Incident Commander: [Name]
Channel: #gula-incident-<date>-<seq>
Next update: [TIME UTC]
```

### Status Update (15 min intervals for SEV1)

```
🔄 INCIDENT UPDATE #[N] 🔄

Incident: [Title]
Severity: SEV[X]
Duration: [Start] — [Ongoing/End] UTC

Progress:
- [What has been done since last update]

Current status:
- [What's happening now]

Next step:
- [What will happen next]

Next update: [TIME UTC] (or "No further updates expected")
```

### Resolution

```
✅ INCIDENT RESOLVED ✅

Incident: [Title]
Severity: SEV[X]
Duration: [Start] — [End] UTC (X minutes)
RTO met: YES / NO (SLA: X minutes, actual: X minutes)

Root cause:
[1-2 sentences]

Resolution:
[1-2 sentences]

Impact:
[Brief impact summary]

Post-mortem: [DATE/TIME]
Channel: #gula-incident-<date>-<seq> (archived in 24h)

Thank you for your patience,
Incident Commander: [Name]
```

---

## 5. Incident Response by Type

### 5.1 Backend Down (SEV1)

**Symptoms:** Health check fails, users see 503

**Response:** [Runbook: backend-down](../runbooks/backend-down.md)

**Key Actions:**
1. Check container status and logs
2. Check resource usage (OOM?)
3. Check database connectivity
4. Restart or rollback
5. Verify recovery

### 5.2 Database Failure (SEV1)

**Symptoms:** Circuit breaker open, writes failing

**Response:** [Runbook: database-down](../runbooks/database-down.md)

**Key Actions:**
1. Check Patroni status
2. Check disk space
3. Promote replica if needed
4. Verify recovery

### 5.3 High Latency (SEV2)

**Symptoms:** API slow, users complaining

**Response:** [Runbook: high-latency](../runbooks/high-latency.md)

**Key Actions:**
1. Identify slow queries
2. Check connection pool
3. Check resource usage
4. Optimize or scale

### 5.4 Security Incident (SEV1-SEV3)

**Symptoms:** Breach, attack, anomaly

**Response:** [Runbook: security-incident](../runbooks/security-incident.md)

**Key Actions:**
1. Contain (rotate secrets, block IPs)
2. Investigate scope
3. Eradicate threat
4. Recover and verify

### 5.5 Deployment Failure (SEV1-SEV2)

**Symptoms:** Health check fails after deploy

**Response:** [Runbook: failed-deployment](../runbooks/failed-deployment.md)

**Key Actions:**
1. Roll back immediately
2. Assess if migration is affected
3. Fix forward or re-deploy
4. Verify recovery

### 5.6 Disk Full (SEV1)

**Symptoms:** Write operations fail, DB stops

**Response:** [Runbook: disk-full](../runbooks/disk-full.md)

**Key Actions:**
1. Free space (logs, WAL, Docker)
2. Verify DB restarts
3. Set up monitoring

---

## 6. Escalation Procedures

### Time-Based Escalation (SEV1)

| Elapsed | Action |
|---------|--------|
| 0 min | On-call acknowledges and begins triage |
| 10 min | If not mitigated, page secondary on-call |
| 20 min | If not mitigated, page Engineering Lead |
| 30 min | If not mitigated, page CTO |
| 60 min | Executive escalation (CEO, stakeholders) |

### Severity Escalation

```
Issue reported
    │
    ▼
SEV4 ──→ SEV3 (if persists >24h or wider impact)
SEV3 ──→ SEV2 (if affects >10% of users)
SEV2 ──→ SEV1 (if affects >50% of users or data risk)
```

---

## 7. Tools & Resources

### Monitoring Access

| Tool | URL | Access |
|------|-----|--------|
| Grafana | https://grafana.gula.internal | SSO / VPN |
| Prometheus | https://prometheus.gula.internal | Internal |
| Loki | https://loki.gula.internal | Grafana Explore |
| PagerDuty | https://gula.pagerduty.com | SSO |
| Cloudflare | https://dash.cloudflare.com | SSO |
| Sentry | https://sentry.gula.internal | SSO |

### Diagnostic Commands

```bash
# Health check
curl -s https://api.gula.health/health | jq .
curl -s https://api.gula.health/health/deep | jq .

# Container status
docker compose ps
docker compose logs --tail=100 [service]

# Database
docker compose exec postgres psql -U gula -c "SELECT count(*) FROM pg_stat_activity;"
docker compose exec postgres pg_isready -U gula

# Redis
docker compose exec redis redis-cli -a $REDIS_PASSWORD PING

# Resource usage
docker stats --no-stream
df -h
free -h

# Recent deployments
git log --oneline -10 --decorate
kubectl get events -n gula-platform --sort-by=lastTimestamp | tail -10
```

### Runbooks Reference

| Runbook | Location |
|---------|----------|
| Backend Down | `docs/runbooks/backend-down.md` |
| Database Down | `docs/runbooks/database-down.md` |
| High Latency | `docs/runbooks/high-latency.md` |
| Disk Full | `docs/runbooks/disk-full.md` |
| Certificate Expiry | `docs/runbooks/certificate-expiry.md` |
| Security Incident | `docs/runbooks/security-incident.md` |
| Failed Deployment | `docs/runbooks/failed-deployment.md` |
| Disaster Recovery | `docs/production/DISASTER_RECOVERY_GUIDE.md` |

---

## 8. Post-Incident Review Template

```markdown
## Post-Incident Review

**Incident ID:** INC-2026-XXXX
**Date:** YYYY-MM-DD
**Title:** [One-line description]
**Severity:** SEV[X]
**Duration:** [RTO actual vs target]

### Metrics
- Time to detection: [X min]
- Time to response: [X min]
- Time to mitigation: [X min]
- Time to resolution: [X min]
- User impact: [% of users affected]
- Data integrity: [Verified / Recovered / Lost]

### Root Cause (5 Whys)
1. Why did the incident occur?
2. Why wasn't it prevented?
3. Why wasn't it detected earlier?
4. Why did containment take too long?
5. Why did it impact users?

### Action Items
| Priority | Action | Owner | Due Date |
|----------|--------|-------|----------|
| P0 | [Critical fix] | [Name] | [Date] |
| P1 | [Important improvement] | [Name] | [Date] |
| P2 | [Nice to have] | [Name] | [Date] |

### Sign-off
- [ ] Engineering Lead
- [ ] Incident Commander
- [ ] Technical Lead
```
