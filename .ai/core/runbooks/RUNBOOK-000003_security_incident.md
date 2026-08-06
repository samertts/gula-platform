---
id: RUNBOOK-000003
type: runbook
title: "Security Incident Response"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 90%
tags: [incident, security, response, sev1]
related_skills: []
related_playbooks: []
source: docs/runbooks/security-incident.md
---

# RUNBOOK-000003: Security Incident Response

**Severity:** SEV1
**Response Time:** <30 minutes
**Source:** `docs/runbooks/security-incident.md`

## Prerequisites
- [ ] Security team notified
- [ ] Incident commander assigned
- [ ] Communication channel established

## Immediate Actions (First 15 minutes)

### Step 1: Contain
```bash
# Isolate affected systems
# Block suspicious IPs
# Revoke compromised credentials
# Disable affected accounts
```

### Step 2: Assess
```bash
# Check access logs
docker compose logs --tail=1000 gula-backend | grep -i "unauthorized\|forbidden\|attack"

# Check for data exposure
# Review audit logs
# Check database access patterns
```

### Step 3: Preserve evidence
```bash
# Snapshot affected containers
docker commit gula-backend evidence/backend-$(date +%Y%m%d%H%M)

# Export logs
docker compose logs gula-backend > evidence/backend-$(date +%Y%m%d%H%M).log

# Database audit
docker compose exec postgres psql -U gula -c "SELECT * FROM audit_log WHERE created_at > NOW() - INTERVAL '1 hour';"
```

## Investigation Phase

### Step 4: Root cause analysis
- Identify attack vector
- Determine scope of compromise
- Timeline reconstruction
- Affected data assessment

### Step 5: Remediation
- Patch vulnerability
- Rotate all secrets
- Force password resets if needed
- Update security rules

## Validation
- [ ] Incident contained
- [ ] Vulnerability patched
- [ ] Secrets rotated
- [ ] Monitoring enhanced
- [ ] Stakeholders notified
- [ ] Post-mortem scheduled

## Full Reference
See `docs/runbooks/security-incident.md` for complete runbook.
