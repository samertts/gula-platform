# 02 — Discovery: Current State

**Program:** GOC Discovery & Design
**Status:** DISCOVERY — evidence only, no changes
**Method:** direct source inspection of `backend/app/control_plane/` at the current
integration branch tip
**Date:** 2026-11-15

---

## 1. Inventory

| Metric | Value | Evidence |
|---|---|---|
| Package | `backend/app/control_plane/` | directory |
| Python modules | 32 (excluding `__pycache__`) | `find … -name '*.py' \| wc -l` |
| Lines of code | 2,715 | `wc -l` across package |
| Subpackages | `config/`, `digital_twin/`, `fleet/`, `operations/`, `policy/`, `registry/`, `release/` | directory listing |
| HTTP endpoints | 21 under `/control-plane` | `grep -c '^@router\\.' routes.py` |
| Registered at runtime | yes | `factory.py:760-761` |
| Migrations | none | no `control_plane` table in `migrations/versions/` |
| Concrete tables | none | `base.py` defines mixins only |
| Tests referencing package | 0 | `grep -rln control_plane backend/tests` → 0 |

### 1.1 Module map

| Module | Lines | Responsibility |
|---|---|---|
| `routes.py` | 351 | 21 HTTP endpoints; delegates to `ControlPlaneSDK` |
| `sdk.py` | 133 | Process-singleton facade over all managers |
| `enums.py` | 60 | `PlatformComponent` (12), `ComponentStatus` (6), `TenantLevel` (6), `ReleaseChannel` (4), `ConfigurationScope` (4) |
| `multi_tenant.py` | 140 | 6-level tenant hierarchy; bridges kernel `TenantRegistry` |
| `service_manager.py` | 135 | Service lifecycle registry |
| `analytics.py` | 114 | Operational KPIs |
| `audit.py` | 124 | 11 control audit actions → `shared.audit.service` |
| `integration.py` | — | Cross-layer wiring |
| `base.py` | 59 | `ControlPlaneBaseMixin`, `TenantAwareMixin`, `ComponentAwareMixin` (no tables) |
| `registry/component.py` | 99 | `ComponentDescriptor` + singleton `ComponentRegistry` |
| `registry/health.py` | 83 | `HealthAggregator`; HTTP probe of `health_endpoint` |
| `registry/topology.py` | 111 | Dependency topology view |
| `config/manager.py` | 115 | Scoped configuration store (in-memory) |
| `config/features.py` | — | Feature flags |
| `config/secrets.py` | 74 | `SecretsManager` bridging kernel `SecretsLoader` |
| `policy/manager.py` | 129 | 8 policy domains, 4 effects; bridges `core.policy_engine` |
| `policy/enforcer.py` | — | Policy evaluation adapter |
| `fleet/manager.py` | 126 | Nodes, containers, edge devices |
| `fleet/provisioning.py` | 95 | `DeploymentPlan` → `deploy()` |
| `release/manager.py` | 158 | Release records, channels, approve/deploy/rollback |
| `operations/center.py` | 69 | `DashboardSnapshot` (7 sections) |
| `operations/automation.py` | 87 | auto-heal, scale, maintenance window |
| `digital_twin/engine.py` | 111 | Twin construction |
| `digital_twin/models.py` | 80 | Infra/Service/Application/Hospital twins |

### 1.2 Endpoint inventory (21)

| Method | Path | Mutating | Guard |
|---|---|---|---|
| GET | `/control-plane/registry/components` | no | `get_current_user` |
| POST | `/control-plane/registry/components` | **yes** | `get_current_user` |
| PUT | `/control-plane/registry/components/{name}` | **yes** | `get_current_user` |
| DELETE | `/control-plane/registry/components/{name}` | **yes** | `get_current_user` |
| GET | `/control-plane/registry/topology` | no | `get_current_user` |
| GET | `/control-plane/health` | no | `get_current_user` |
| GET | `/control-plane/config/{scope}/{component}` | no | `get_current_user` |
| PUT | `/control-plane/config/{scope}/{component}` | **yes** | `get_current_user` |
| POST | `/control-plane/config/reload` | **yes** | `get_current_user` |
| GET | `/control-plane/policies` | no | `get_current_user` |
| POST | `/control-plane/policies` | **yes** | `get_current_user` |
| POST | `/control-plane/policies/evaluate` | no | `get_current_user` |
| GET | `/control-plane/fleet/nodes` | no | `get_current_user` |
| POST | `/control-plane/fleet/deploy` | **yes** | `get_current_user` |
| GET | `/control-plane/operations/dashboard` | no | `get_current_user` |
| GET | `/control-plane/releases` | no | `get_current_user` |
| POST | `/control-plane/releases` | **yes** | `get_current_user` |
| POST | `/control-plane/releases/deploy` | **yes** | `get_current_user` |
| GET | `/control-plane/audit-log` | no | `get_current_user` |
| GET | `/control-plane/digital-twin/{component_type}` | no | `get_current_user` |
| GET | `/control-plane/kpis` | no | `get_current_user` |

**9 of 21 endpoints mutate operational state.** None requires a privileged role.

## 2. State model — what is durable

| Manager | Storage | Durable | Multi-worker safe |
|---|---|---|---|
| `ComponentRegistry` | `dict` in singleton | ❌ | ❌ |
| `FleetManager` | `dict` in singleton | ❌ | ❌ |
| `ReleaseManager` | `dict` in singleton | ❌ | ❌ |
| `PolicyManager` | `dict` in instance | ❌ | ❌ |
| `ConfigurationManager` | `dict` in instance | ❌ | ❌ |
| `MultiTenantController` | bridges kernel registry | partial | depends on kernel |
| `SecretsManager` | bridges kernel loader | n/a (read-only) | n/a |
| Audit | `shared.audit.service` | ✅ (DB) | ✅ |

**Consequence:** after any process restart, the platform "forgets" every registered
component, release, policy, node, and configuration override. With more than one worker
(the normal production topology), two requests can observe different platform truth.

## 3. Integration surface

| Integration | Direction | Evidence |
|---|---|---|
| `app.kernel.integration.get_kernel` | component registry, tenant registry, secret loader | `registry/component.py`, `multi_tenant.py`, `config/secrets.py` |
| `app.core.self_healing.health` | circuit-breaker state, degradation level | `operations/center.py`, `registry/health.py` |
| `app.core.policy_engine` | `evaluate_policy`, `ActionType` | `policy/manager.py` |
| `shared.audit.service` | `create_audit_entry`, `query_audit_log` | `audit.py` |
| `httpx` | outbound HTTP to component `health_endpoint` | `registry/health.py` |
| `factory.py` | router registration | `factory.py:760` |

## 4. Behavioral observations

**4.1 Health aggregation is caller-directed.** `HealthAggregator.check_component` treats
`ComponentDescriptor.health_endpoint` as a fetch target:

```python
if comp.health_endpoint:
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(comp.health_endpoint)
```

`health_endpoint` arrives from the request body at component registration. Any authenticated
caller can therefore make the server issue outbound HTTP requests to arbitrary destinations
(including internal network addresses) — see F-03.

**4.2 Release approval identity is caller-supplied.** `POST /releases/deploy`:

```python
user_str = data.get("user", "unknown")
if data.get("approve_first", False):
    sdk.releases.approve(release_id, user_str)
release = await sdk.releases.deploy(release_id, user_str)
```

The approver and the deployer are the same string, taken from the body. The authenticated
principal is never consulted. See F-02.

**4.3 Dashboard is four-sevenths placeholder.** `DashboardSnapshot` returns real data for
`infrastructure` and `performance`; `clinical`, `security`, `ai`, and `compliance` return
notes such as `"delegated to governance layer"`. See G-07.

**4.4 Auto-heal mutates status without verification.** `AutonomousOperations.auto_heal`
promotes `DEGRADED`/`REGISTERED` components to `ACTIVE` with no probe of the underlying
system. That is optimistic bookkeeping, not healing. See G-08.

**4.5 No ADR-018 Phase 3 or 4 surface.** No incident, change-request, maintenance-window, or
compliance-report models, tables, or endpoints exist anywhere in the package.

## 5. Conclusion of discovery

The prototype is a **well-shaped domain model with no operational safety**. Its vocabulary
(components, fleet, releases, policies, tenants, twins) is directly reusable and should be
retained. Its execution model (in-memory singletons, permissive auth, unverified state
transitions) must be replaced before the GOC can be called an operations center.

Discovery produces no changes. See [03](03_CAPABILITY_MATRIX.md) for the ADR-018 conformance
matrix, [04](04_GAP_ANALYSIS.md) for ranked gaps, and [05](05_SECURITY_AND_GOVERNANCE.md) for
the security findings F-01…F-07.
