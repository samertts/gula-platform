# GSF Disaster Recovery Plan

**Document ID**: GSF-DR-001  
**Version**: 1.0.0  
**Effective Date**: 2026-07-25  
**Classification**: Confidential — GULA Platform Engineering  

---

## 1. Purpose

This Disaster Recovery (DR) Plan defines the procedures for recovering the GULA
National Healthcare Platform in the event of a catastrophic failure, natural
disaster, or large-scale cyber incident. The plan ensures continuity of
healthcare services across all Iraqi governorates.

---

## 2. Recovery Objectives

### 2.1 RTO and RPO Targets

| Service Tier | RTO (Recovery Time Objective) | RPO (Recovery Point Objective) | Services |
|-------------|-------------------------------|-------------------------------|----------|
| Tier 0 — Critical | 1 hour | 0 minutes (zero data loss) | Authentication, Authorization, Audit |
| Tier 1 — High | 2 hours | 5 minutes | FHIR API, Patient Records, Orders |
| Tier 2 — Medium | 4 hours | 15 minutes | Laboratory Results, Pharmacy |
| Tier 3 — Standard | 8 hours | 1 hour | Reporting, Analytics, Admin |
| Tier 4 — Batch | 24 hours | 24 hours | Data Warehouse, ML Pipelines |

### 2.2 Recovery Priority

```
Priority 1: AuthN/AuthZ → FHIR API → Patient Records
Priority 2: Laboratory → Pharmacy → Clinical Workflows
Priority 3: Admin Panel → Reporting → Analytics
Priority 4: ML Pipelines → Data Exports → Archival
```

---

## 3. Disaster Scenarios

| Scenario | Likelihood | Impact | Recovery Strategy |
|----------|------------|--------|-------------------|
| Complete data center failure (fire, flood) | Low | Critical | Active-Passive DR site failover |
| Regional outage (power grid, internet) | Medium | High | Multi-region deployment, offline-first |
| Ransomware encryption of production systems | Medium | Critical | Immutable backups, DR site, clean restore |
| Database corruption | Medium | High | Point-in-time recovery (PITR) |
| Cloud provider region failure | Low | Critical | Multi-cloud or cloud-to-on-prem DR |
| Kubernetes cluster loss | Medium | High | GitOps-based cluster rebuild |
| Cryptographic key loss | Low | Critical | Key escrow, HSM backup, split knowledge |
| Large-scale DDoS (nation-state) | Low | High | CDN failover, scrubbing center |

---

## 4. Backup Strategy

### 4.1 Backup Schedules

| Data Type | Backup Type | Frequency | Retention | Storage |
|-----------|-------------|-----------|-----------|---------|
| Patient database (PostgreSQL) | Full | Daily | 30 days | Encrypted S3/MinIO |
| Patient database (PostgreSQL) | WAL | Continuous | 7 days | Encrypted S3/MinIO |
| FHIR resource store | Full | Daily | 30 days | Encrypted S3/MinIO |
| Audit logs | Incremental | Hourly | 7 years | WORM S3 |
| Secrets (Vault) | Snapshot | Daily | 30 days | Encrypted S3 |
| Configuration (K8s, Terraform) | GitOps | Every change | Forever | Git repository |
| Container images | Registry copy | Every build | 90 days | Secondary registry |
| Object storage (MinIO) | Replication | Continuous | 30 days | DR site MinIO |
| Encryption keys (HSM) | Backup | Weekly | Forever | Escrow + split knowledge |

### 4.2 3-2-1 Backup Strategy

```
3 copies of data
├── Primary (production cluster)
├── Secondary (DR site)
└── Tertiary (immutable offline backup)
2 different media
├── SSD/NVMe (primary + DR)
└── Tape/Glacier (offline)
1 off-site copy
└── Geographically separated region
```

### 4.3 Backup Testing

| Test Type | Frequency | Success Criteria |
|-----------|-----------|-----------------|
| Automated backup integrity check | Daily | SHA-256 verification |
| Database restore test (non-prod) | Weekly | Full restore + data verification |
| DR site synchronization test | Monthly | RPO validation |
| Full DR failover drill | Quarterly | RTO validation |
| Immutable backup restoration | Semi-annually | Offline restore from tape/Glacier |

---

## 5. Failover Procedures

### 5.1 Active-Passive DR

```
                          ┌────────────┐
                          │  DNS / LB  │
                          └──────┬─────┘
                                 │
              Normal Operation ──┼── Failover
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
             ┌──────────────┐        ┌──────────────┐
             │  Primary     │        │  DR Site     │
             │  Site        │◄──────►│  (Passive)   │
             │  (Active)    │  Sync  │  (Standby)   │
             └──────────────┘        └──────────────┘
                    │                        │
                    ▼                        ▼
             ┌──────────────┐        ┌──────────────┐
             │  PostgreSQL  │ ────►  │  Streaming   │
             │  Primary     │  WAL   │  Replica     │
             └──────────────┘        └──────────────┘
```

### 5.2 Failover Triggers

| Condition | Trigger | Action |
|-----------|---------|--------|
| Primary site unreachable > 5 min | Automated health check | Auto-failover to DR |
| Database replication lag > 30 seconds | Monitoring alert | Investigate, manual DR if > 5 min |
| Ransomware confirmed | IR Lead decision | Isolate primary, activate DR |
| Building evacuation ordered | Physical security | Manual DR activation |
| Planned maintenance | Scheduled | Controlled switchover |

### 5.3 Failover Steps

1. **Verify DR site readiness** — Confirm DR cluster healthy, data synced
2. **Promote DR database** — Promote streaming replica to primary
3. **Update DNS** — Switch traffic to DR site load balancer
4. **Verify services** — Run smoke tests on all Tier 0/1 services
5. **Scale DR compute** — Scale up DR cluster to production capacity
6. **Monitor** — Activate enhanced monitoring in DR region
7. **Communicate** — Notify stakeholders of active DR status

### 5.4 Failback Steps

1. **Rebuild primary site** — Restore infrastructure from IaC
2. **Sync data back** — Reverse replication to restored primary
3. **Test primary site** — Full smoke test on restored site
4. **Switch traffic** — DNS change back to primary
5. **Verify** — Confirm primary operating normally
6. **Return DR to standby** — Resync DR as replica

---

## 6. Data Restoration

### 6.1 Database Restore

```bash
# Point-in-time recovery
pg_restore --dbname=gula_production \
  --format=custom \
  --jobs=8 \
  --verbose \
  /backups/gula_production_20260725.dump

# WAL replay for point-in-time
pg_dump --dbname=gula_production \
  --format=custom \
  --jobs=8 \
  --file=/backups/gula_production_20260725.dump
```

### 6.2 Kubernetes Restore (GitOps)

```bash
# Recreate cluster from GitOps
flux bootstrap github \
  --owner=gula-platform \
  --repository=gula-infra \
  --path=clusters/production

# Verify all workloads
kubectl get all --all-namespaces
```

### 6.3 Secrets Restore

```bash
# Restore Vault from snapshot
vault operator raft snapshot restore \
  /backups/vault_snapshot_20260725.snap

# Verify secrets
vault list secret/gula/production/
```

---

## 7. Testing Schedule

| Test | Frequency | Scope | Success Criteria |
|------|-----------|-------|-----------------|
| Database restore | Weekly | Single DB restore | < 4 hours RTO, zero data loss |
| DR failover (planned) | Monthly | Full stack DR test | < 1 hour RTO (Tier 0) |
| DR failover (unannounced) | Annually | Full stack no-notice test | < 2 hours RTO (Tier 0-1) |
| Network failover | Quarterly | DNS/LB failover | < 5 min propagation |
| Backup restore (full) | Semi-annually | Full production restore | < 8 hours (full platform) |
| Offline restore | Annually | Restore from tape/Glacier | < 24 hours |

---

## 8. DR Site Requirements

### 8.1 On-Premises DR

| Requirement | Specification |
|-------------|---------------|
| Location | Geographically separate governorate (> 100 km) |
| Power | Dual redundant UPS + 72-hour generator |
| Network | Dedicated fiber (minimum 10 Gbps) |
| Compute | 100% production capacity (warm standby) |
| Storage | 100% production capacity with replication |
| Security | Equivalent to primary (access control, surveillance) |
| Staff | 24/7 on-call team |

### 8.2 Cloud DR (AWS)

| Requirement | Specification |
|-------------|---------------|
| Region | AWS Middle East (Bahrain) or Europe |
| Compute | RDS Multi-AZ + ECS/EKS Auto Scaling |
| Storage | S3 Cross-Region Replication + Glacier |
| Database | RDS Read Replica in DR region |
| Network | Direct Connect + VPN backup |

---

## 9. Offline-First Considerations

For Iraqi governorates with unreliable connectivity:

| Scenario | Strategy |
|----------|----------|
| Internet outage at health facility | Local-first mode with queued synchronization |
| Regional network outage | Synchronization via mobile mesh (LoRa/incl. SATCOM backup) |
| Prolonged outage (> 72 hours) | Physical data transfer (encrypted USB/NAS) |
| DR site unreachable | Multiple distributed data stores with eventual consistency |
| Power outage | UPS + generator + solar backup at facilities |

### Offline DR Procedures

1. Local instances operate independently with local audit logs
2. Data changes queued in local store with write-ahead log
3. When connectivity restored, sync with conflict resolution
4. Audit logs synchronized with hash chain verification
5. Protected health information encrypted end-to-end during sync

---

## 10. Documentation and Training

| Document | Location | Owner |
|----------|----------|-------|
| DR Runbook | security/runbooks/dr_runbook.md | Platform Eng Lead |
| Database Recovery Guide | security/runbooks/db_recovery.md | DBA Lead |
| K8s Cluster Recovery | security/runbooks/k8s_recovery.md | K8s Lead |
| Vault Recovery Guide | security/runbooks/vault_recovery.md | Security Lead |
| DR Test Report Template | security/templates/dr_test_report.md | Platform Eng Lead |

---

## 11. DR Plan Review

| Activity | Frequency | Owner |
|----------|-----------|-------|
| DR plan review | Quarterly | Platform Eng Lead |
| RTO/RPO assessment | Quarterly | Platform Eng Lead |
| Backup test results review | Monthly | DBA Lead |
| DR site capacity review | Monthly | Platform Eng Lead |
| Third-party DR audit | Annually | External Auditor |

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-07-25 | GULA Security Team | Initial DR plan |
