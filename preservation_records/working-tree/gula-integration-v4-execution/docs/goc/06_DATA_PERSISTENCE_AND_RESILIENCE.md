# 06 — Data, Persistence & Resilience

**Program:** GOC Discovery & Design
**Status:** DISCOVERY / DESIGN
**Date:** 2026-11-15

---

## 1. Current state

| Concern | Current behavior | Evidence |
|---|---|---|
| Persistence | None — dict state in singletons | `registry/component.py`, `fleet/manager.py`, `release/manager.py`, `policy/manager.py`, `config/manager.py` |
| Tables | None — `base.py` defines mixins only | `control_plane/base.py` |
| Migrations | None | no `control_plane` migration |
| History | None — current state only | no version tables |
| Multi-worker | Incorrect — each worker has its own copy | singleton pattern |
| Restart | Total state loss | dict storage |
| Backup/Restore | Not applicable (nothing persisted) | — |
| Audit durability | Durable | `shared.audit.service` (DB) |

**The central defect:** the GOC's audit trail can durably record that a release was
deployed, while the release registry itself has no record of existing. That is an
unreconcilable operational ledger.

## 2. Required data model (proposed)

Eight entities. Names are design-level; this document does not create tables.

| Entity | Purpose | Key fields | History |
|---|---|---|---|
| `goc_component` | Registered platform component | id, name (unique), type, version, status, owner, tenant, health_endpoint (validated) | status changes |
| `goc_component_dependency` | Directed dependency edges | from_component, to_component, kind | append-only |
| `goc_fleet_node` | Node / edge-device inventory | id, hostname, role, status, labels, last_heartbeat | heartbeat table |
| `goc_release` | Release record | id, name, version, channel, component, status, artifacts, created_by | transitions |
| `goc_release_approval` | Approval record | release_id, principal_id, principal_role, tenant, decision, reason, jti/correlation | append-only |
| `goc_configuration_version` | Versioned config | scope, component, key, value_hash, version, changed_by | append-only |
| `goc_policy` | Policy definition | name, domain, effect, severity, conditions, enabled | append-only |
| `goc_incident` | Incident lifecycle (P4) | id, severity, status, opened_by, opened_at, closed_at, post_mortem_ref | transitions |

Design rules:

1. **Append-only for anything that justifies a decision.** Approvals, config versions, policy
   changes, and incident transitions are never updated in place — a new row records the
   change.
2. **State tables carry `version` for optimistic concurrency.** Two operators editing the
   same component cannot silently overwrite each other.
3. **Tenant stamped on every row.** Tenant dominance is enforced by query predicate, not by
   application-layer hopefulness.
4. **No secret values.** Configuration stores hashes of secret references, never secret
   material. Secrets stay in the kernel loader.
5. **Correlation ID on every operational write.** Binds the DB row to the audit entry and to
   the HTTP request.

## 3. Resilience requirements

| Requirement | Design |
|---|---|
| Restart survival | All operational state persisted; startup loads from DB |
| Multi-worker correctness | DB is the single source of truth; no process-global mutable state |
| Startup reconciliation | On boot, compare DB components against live probes; mark `unknown` when unverifiable — never assume green |
| Degraded read | If DB is unavailable, GOC returns `503` with an explicit `state: unknown`, never an empty-but-healthy dashboard |
| Heartbeat expiry | Nodes without heartbeat beyond threshold become `unreachable`, not `active` |
| Audit atomicity | Operational write and audit entry committed in the same transaction (outbox if async) |
| Backup coverage | New tables included in existing backup/DR procedures; restore drill must include them |

## 4. Failure-mode behavior (required)

| Failure | GOC must | GOC must not |
|---|---|---|
| DB unreachable | Report `unknown` + `503` on read | Report components as healthy |
| Probe target unreachable | Mark component `unreachable` with error class | Flip to `active` |
| Audit write fails | Reject the operation | Commit the operation silently |
| Two concurrent config writes | Reject the stale one (version mismatch) | Last-write-wins |
| Worker restart mid-release | Resume from persisted release state | Forget the release |
| Tenant context missing | Deny | Default to national scope |

## 5. Data retention

| Data | Proposed retention | Rationale |
|---|---|---|
| Release + approval records | Permanent (national platform lifetime) | Regulatory traceability |
| Configuration versions | 7 years | Regulatory reconstruction |
| Policy changes | Permanent | Governance audit |
| Incident records | 7 years after closure | Post-mortem and compliance |
| Fleet heartbeats | 90 days rolling | Operability, bounded growth |
| Health probe results | 30 days rolling | Trend analysis, bounded growth |

Retention must be implemented as policy, not as an infinite table. Growth bounds are a
first-class requirement because operational telemetry volume scales with the national
footprint.

## 6. Migration strategy constraints

- New tables are **additive only**. No alteration of existing clinical, identity, or
  laboratory tables.
- One migration per phase, reversible (`downgrade` implemented and tested).
- No data migration from the prototype (there is nothing durable to migrate).
- Existing backup and DR scripts must be extended to cover the new tables **before** the
  phase that introduces them is declared complete.

## 7. Open questions for design review

1. Should release approvals require quorum (two principals) for the production channel, or
   is one approver distinct from the requester sufficient?
2. Is GOC state co-located with the primary platform database, or on a separate operational
   database to isolate blast radius?
3. Do fleet heartbeats justify a dedicated store given their volume, or can they share the
   platform database with a retention job?
4. What is the authoritative clock for approval timestamps — database, application, or the
   authentication token issuance time?

These are recorded as open, not assumed. They are inputs to ADR-026 acceptance.
