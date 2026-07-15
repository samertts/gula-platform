# Runbook: Security Incident

**Severity:** SEV1 (breach) / SEV2 (attempt) / SEV3 (policy)
**Response Time:** <15 min (SEV1) / <30 min (SEV2) / <2h (SEV3)
**Last Updated:** 2026-07-15
**Classification:** CONFIDENTIAL — Operations Team Only

---

## Symptoms

### Detection Methods

- **Automated alert**: WAF block spike, auth failure spike, IDS/IPS alert
- **User report**: Account compromised, unusual activity observed
- **Audit log anomaly**: Mass data access, unusual time patterns, high-value target access
- **Threat intel**: Credentials found in breach database, dark web mention
- **Monitoring**: Unusual traffic patterns, new admin accounts, configuration changes

### Potential Indicators

- Unauthorised access to sensitive data (patients, national IDs, financial records)
- Mass data export / scraping (1000s of records in short time)
- Brute force or credential stuffing attacks
- SQL injection or XSS attempts (WAF blocks increasing)
- Account compromise (logins from unusual locations)
- Ransomware / data encryption (unusual file changes, ransom note)
- Insider threat (unusual access patterns, after-hours access)
- Supply chain attack (suspicious dependency or container image)

## Quick Triage

```bash
# 1. Check recent audit logs for anomalies
docker compose exec postgres psql -U gula -c "
SELECT created_at, actor_id, action, resource_type, resource_id, details
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC LIMIT 50;"

# 2. Check active sessions
docker compose exec postgres psql -U gula -c "
SELECT id, email, last_login, last_ip, is_active
FROM lab_users
WHERE is_active = true
ORDER BY last_login DESC LIMIT 20;"

# 3. Check WAF logs (Cloudflare)
curl -s -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/security/events?time_start=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)"

# 4. Check rate limit hits
curl -s http://localhost:8000/admin/rate-limit/stats \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# 5. Check SSH access logs
journalctl -u ssh -n 50 --no-pager
```

## Incident Classification

| Severity | Definition | Examples | Response |
|----------|-----------|----------|----------|
| **SEV1** | Active data breach or platform compromised | Unauthorised data access, ransomware, account takeover of admin | <15min, full team |
| **SEV2** | Attempted breach with impact | Brute force in progress, WAF bypass found, compromised non-admin account | <30min, ops team |
| **SEV3** | Policy violation or vulnerability found | Weak password discovered, exposed internal endpoint, missing security header | <2h, assigned owner |
| **SEV4** | Best practice improvement | Outdated TLS, missing security header, documentation gap | <1 week, ticket |

## SEV1 Incident Response

### Phase 1: Containment

**Objective:** Stop the bleeding.

```bash
# 1. ROTATE ALL SECRETS
# Run emergency secret rotation script
./scripts/rotate-secrets.sh --emergency

# 2. BLOCK COMPROMISED IP AT CLOUDFLARE
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/access_rules/rules" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"block","configuration":{"target":"ip","value":"<malicious-ip>"},"notes":"SEV1 incident containment"}'

# 3. REVOKE ALL USER SESSIONS
docker compose exec postgres psql -U gula -c "UPDATE lab_users SET token_version = token_version + 1;"

# 4. DISABLE COMPROMISED ACCOUNTS
docker compose exec postgres psql -U gula -c "UPDATE lab_users SET is_active = false WHERE id IN ('<user-id>');"

# 5. ENABLE ENHANCED LOGGING
curl -X POST http://localhost:8000/admin/security/enable-enhanced-logging \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# 6. TRIGGER PAGERDUTY INCIDENT
./scripts/pagerduty-trigger.sh \
  --severity=SEV1 \
  --title="Security incident: active containment in progress"
```

### Phase 2: Investigation

**Objective:** Understand the scope and method.

```bash
# 1. Audit log analysis — identify all actions by compromised user
docker compose exec postgres psql -U gula -c "
SELECT created_at, action, resource_type, resource_id, details, ip_address
FROM audit_logs
WHERE actor_id IN ('<compromised-user-id>')
ORDER BY created_at;"

# 2. Check database for data exfiltration
docker compose exec postgres psql -U gula -c "
SELECT created_at, actor_id, action, count(*) as access_count
FROM audit_logs
WHERE action LIKE 'read%'
AND resource_type = 'patients'
AND created_at > NOW() - INTERVAL '24 hours'
GROUP BY created_at, actor_id, action
ORDER BY access_count DESC LIMIT 20;"

# 3. Check application logs for suspicious patterns
docker compose logs --since=24h gula-backend | grep -i "error\|unauthorized\|forbidden\|suspicious"

# 4. Export relevant logs for forensics
docker compose logs --since=24h gula-backend > /tmp/forensics/backend-24h.log
docker compose logs --since=24h postgres > /tmp/forensics/postgres-24h.log

# 5. Take database snapshot for forensics
pg_dump -U gula -h localhost gula > /tmp/forensics/db-snapshot-$(date +%Y%m%d-%H%M).sql
```

### Phase 3: Eradication

**Objective:** Remove the threat.

```bash
# 1. Patch vulnerability that was exploited
# (Deploy hotfix via emergency pipeline)
git checkout -b hotfix/security-issue-$(date +%Y%m%d)
# Apply fix
git commit -m "security: fix vulnerability"
git push origin hotfix/security-issue-$(date +%Y%m%d)

# 2. Rebuild all containers from clean images
docker compose build --no-cache
docker compose up -d --force-recreate

# 3. Force password reset for all users
docker compose exec postgres psql -U gula -c "
UPDATE lab_users SET password_hash = NULL, token_version = token_version + 1;"

# 4. Verify no backdoors remain
# Check for unusual cron jobs, startup scripts, network connections
crontab -l
systemctl list-units --state=running
ss -tlnp
```

### Phase 4: Recovery

**Objective:** Restore normal operations safely.

```bash
# 1. Restore from last clean backup (if data was compromised)
./scripts/restore-test.sh --backup=/backups/clean/backup-before-incident.sql.gz

# 2. Gradually re-enable services
docker compose up -d --scale gula-backend=1
# Monitor for 5 minutes
curl -s http://localhost:8000/health/deep | jq .
# Scale up if stable
docker compose up -d --scale gula-backend=3

# 3. Monitor for signs of re-infection
# Increase log level to DEBUG temporarily
curl -X POST http://localhost:8000/admin/log-level/DEBUG \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# 4. Rotate secrets again (second rotation = clean slate)
./scripts/rotate-secrets.sh
```

### Phase 5: Post-Mortem

**Objective:** Learn and prevent.

Schedule within 24 hours of incident resolution.

**Post-Mortem Meeting Agenda:**
1. Timeline reconstruction (all events from detection to resolution)
2. Root cause analysis (5 Whys)
3. Impact assessment (data, users, systems)
4. What went well
5. What went wrong
6. Action items (with owners and deadlines)
7. Update runbooks and monitoring

## Incident Communication

### Internal Communication

```markdown
## Security Incident Update - [DATE]

**Status:** ACTIVE / CONTAINED / RESOLVED
**Severity:** SEV1 / SEV2
**Incident ID:** INC-2026-XXXX

**What happened:**
[Brief, factual description]

**Current status:**
[What has been done, what's in progress]

**Impact:**
[Affected systems, users, data — if known]

**Actions taken:**
- [ ] Containment step 1
- [ ] Containment step 2

**Next steps:**
- [ ] Next action
- [ ] Next update at [TIME]

**Incident Commander:** [Name]
```

### External Communication (Stakeholders)

```markdown
Subject: [GULA] Security Incident Notification - [DATE]

Dear [Stakeholder],

We are writing to inform you of a security incident affecting
the GULA Platform.

Status: [RESOLVED / INVESTIGATING]
Date: [DATE]
Time detected: [TIME UTC]
Time resolved: [TIME UTC] (if applicable)

Summary:
[Brief description if appropriate — consult legal before sharing details]

Actions taken:
- [Action taken]

Impact:
[Impact assessment]

If you have questions, please contact:
- [Security team email]
- [Incident Commander]

Sincerely,
GULA Security Team
```

## Communication Templates

### SEV1 Declaration Message

```
🚨 SEV1 INCIDENT DECLARED 🚨

Incident: Security incident — [brief description]
Severity: SEV1
Time: [TIMESTAMP UTC]
Detected by: [Alert / User report / Manual]

Initial assessment:
[1-2 sentence description]

Containment in progress:
[Step being taken]

Incident Commander: [Name]
Channel: #gula-incident-[date]
```

### SEV1 Resolution Message

```
✅ SEV1 INCIDENT RESOLVED ✅

Incident: Security incident — [brief description]
Severity: SEV1
Duration: [START] — [END] UTC
RTO met: YES / NO (actual: [X] minutes)

Root cause:
[1-2 sentences]

Resolution:
[1-2 sentences]

Post-mortem scheduled: [DATE/TIME]
Full report: [Link to document]

Thank you,
Incident Commander: [Name]
```

## Post-Incident Checklist

- [ ] Incident documented in incident log
- [ ] Root cause identified and fixed
- [ ] Compromised credentials rotated
- [ ] Affected users notified
- [ ] Monitoring/alerts improved
- [ ] Runbook updated
- [ ] Compliance/regulatory notification sent (if required)
- [ ] Legal review completed
- [ ] Security team debrief completed
- [ ] Action items tracked in project management system
