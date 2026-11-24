# 03 — Capability Matrix (ADR-018 conformance)

**Program:** GOC Discovery & Design
**Status:** DISCOVERY
**Baseline:** [ADR-018 National Platform Operations Center](../adr/ADR-018-national-operations.md)
**Date:** 2026-11-15

---

## 1. How to read this matrix

Every row is a commitment made by ADR-018, either in its **Decision**, **Key Design
Decisions**, or **Implementation Strategy** sections. State is one of:

| State | Definition |
|---|---|
| ✅ Met | Implemented and reachable; behavior matches the commitment |
| 🟡 Partial | Exists but incomplete, unverified, in-memory, or missing a required control |
| ❌ Absent | No implementation found |

"Partial" is never counted as met. A commitment is met only when its safety control is
also present.

## 2. Matrix

### 2.1 Core architecture commitments

| ID | ADR-018 commitment | State | Evidence / reason |
|---|---|---|---|
| A-01 | `control_plane/` module as orchestration layer | ✅ Met | package exists, registered in `factory.py:760` |
| A-02 | Orchestrate existing tools, do not replace them | ✅ Met | no CI/Grafana/PagerDuty reimplementation; delegation throughout |
| A-03 | Workflow engine `control_plane/workflows/` — operations as code | ❌ Absent | directory does not exist |
| A-04 | Read-only dashboard `control_plane/dashboard/` | 🟡 Partial | snapshot exists in `operations/center.py`; no dedicated module; 4/7 sections are placeholders |
| A-05 | Centralized operations view across environments | 🟡 Partial | one view exists; environments not modeled; no environment field in snapshots |

### 2.2 Registry & topology

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| R-01 | Central component registry | ✅ Met | `registry/component.py`; 12 component types |
| R-02 | Dependency topology | 🟡 Partial | `registry/topology.py` computes topology from registered deps; unverified against reality |
| R-03 | Component lifecycle states | ✅ Met | `ComponentStatus` 6 states |
| R-04 | Durable registry | ❌ Absent | in-memory singleton only |

### 2.3 Health & monitoring

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| H-01 | Aggregate health across components | ✅ Met | `HealthAggregator.aggregate()` |
| H-02 | Probe-based health (not bookkeeping) | 🟡 Partial | probes exist, but `auto_heal` also flips status without probing |
| H-03 | Health data feeds dashboard | ✅ Met | `DashboardSnapshot.infrastructure.health_grade` |
| H-04 | Probe targets constrained to known-safe hosts | ❌ Absent | arbitrary URL from request body (F-03) |

### 2.4 Release management

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| L-01 | Release records with channels | ✅ Met | `ReleaseChannel` 4 channels; `Release` dataclass |
| L-02 | Pipeline build→test→staging→canary→prod gates | ❌ Absent | no gate enforcement; `deploy()` advances without checks |
| L-03 | Manual approval points | 🟡 Partial | `approve()` exists, but approver identity is caller-supplied (F-02) |
| L-04 | Rollback capability | 🟡 Partial | `rollback_version` field + rollback statuses; no rollback endpoint, no verification |
| L-05 | Separation of duties (requester ≠ approver ≠ deployer) | ❌ Absent | single-call self-approval supported via `approve_first` |
| L-06 | Automatic halt on clinical-safety signal | ❌ Absent | no link between release state and clinical safety state |

### 2.5 Fleet & deployment

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| F-01 | Node / container / edge-device inventory | 🟡 Partial | descriptors exist; in-memory; no heartbeat ingestion endpoint |
| F-02 | Deployment execution | 🟡 Partial | `provisioning.deploy(plan)` returns a plan result; no real orchestration, no verification |
| F-03 | Blast-radius control | ❌ Absent | `POST /fleet/deploy` accepts arbitrary image/config from any authenticated user |

### 2.6 Configuration & policy

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| C-01 | Scoped configuration | 🟡 Partial | 4 scopes modeled; in-memory; no versioning, no rollback |
| C-02 | Configuration change audit | 🟡 Partial | audit action defined; not emitted on the config path (unverified) |
| C-03 | Policy definitions by domain | ✅ Met | 8 domains, 4 effects, 5 severities |
| C-04 | Policy evaluation via single engine | ✅ Met | bridges `core.policy_engine.evaluate_policy` |
| C-05 | Secret handling | ✅ Met | `SecretsManager` bridges kernel `SecretsLoader`; never persists values |
| C-06 | Secret rotation | 🟡 Partial | `rotate()` records history in memory; no durable rotation record |

### 2.7 Incidents & change management

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| I-01 | Incident classification SEV-1..SEV-4 | ❌ Absent | no model, no enum, no endpoint |
| I-02 | Escalation paths | ❌ Absent | — |
| I-03 | Post-mortem tracking | ❌ Absent | — |
| I-04 | On-call scheduling | ❌ Absent | ADR-018 Phase 3; nothing implemented |
| M-01 | Change management workflow | ❌ Absent | no change-request entity |
| M-02 | Scheduled maintenance windows | 🟡 Partial | boolean `_maintenance_window` in `operations/automation.py`; not enforced anywhere |
| M-03 | Blast-radius-limited rollouts | ❌ Absent | see F-03 |

### 2.8 Audit & compliance

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| U-01 | Every operational action logged | 🟡 Partial | 11 actions defined in `audit.py`; consistent emission across all 21 endpoints unverified |
| U-02 | Tamper-evident audit trail | ✅ Met | delegates to `shared.audit.service` (hash-chained) |
| U-03 | Compliance reporting for Iraqi health regulations | ❌ Absent | no export, no retention policy, no attestation |
| U-04 | Post-mortem support | ❌ Absent | depends on I-series |

### 2.9 Multi-tenancy

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| T-01 | 6-level national hierarchy | ✅ Met | `TenantLevel`; bridges kernel `TenantRegistry` |
| T-02 | Tenant-scoped configuration | 🟡 Partial | scope exists; isolation not enforced on read/write |
| T-03 | Cross-tenant administration prohibited | ❌ Absent | no tenant check on any endpoint (F-01) |

### 2.10 Quality

| ID | Commitment | State | Evidence / reason |
|---|---|---|---|
| Q-01 | Test coverage | ❌ Absent | 0 test files reference `control_plane` |
| Q-02 | Contract stability | ❌ Absent | request bodies typed as `dict[str, Any]`; no schemas in OpenAPI beyond generic object |
| Q-03 | Multi-worker correctness | ❌ Absent | in-memory singleton state |

## 3. Scorecard

| Category | Met | Partial | Absent | Total |
|---|---|---|---|---|
| Core architecture | 2 | 2 | 1 | 5 |
| Registry & topology | 2 | 1 | 1 | 4 |
| Health & monitoring | 2 | 1 | 1 | 4 |
| Release management | 1 | 2 | 3 | 6 |
| Fleet & deployment | 0 | 2 | 1 | 3 |
| Configuration & policy | 3 | 3 | 0 | 6 |
| Incidents & change | 0 | 1 | 6 | 7 |
| Audit & compliance | 1 | 1 | 2 | 4 |
| Multi-tenancy | 1 | 1 | 1 | 3 |
| Quality | 0 | 0 | 3 | 3 |
| **Total** | **12 (27%)** | **14 (31%)** | **19 (42%)** | **45** |

**Conformance: 27% met, 31% partial, 42% absent.**

The distribution matters more than the total: the *absent* mass is concentrated in
**safety-critical** categories — release gates, incidents, authorization, quality. The
*met* mass is concentrated in **read-model** categories — registry, health view, policy
vocabulary, audit bridge. That is the profile of a prototype that can describe operations
but cannot safely perform them.

## 4. What this implies for ADR-026

The proposed ADR must not claim to "implement ADR-018". It must state that ADR-018 is
**partially realized**, enumerate which commitments remain, and make completion of the
absent safety categories a precondition for the GOC being granted operational authority.
See [08](08_ROADMAP_AND_ACCEPTANCE.md) for the acceptance gate.
