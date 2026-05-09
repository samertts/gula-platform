# Phase 16-03 — Institutional Trust Boundaries

## Principle

GULA does **not** federate trust. It **proxies** trust through bounded
adapters with explicit capability whitelists. No external party is granted a
role that exists in the internal RBAC matrix.

## Boundary Model

```
+---------------+   external peer credentials
| Peer system   +-------------------------------+
+-------+-------+                               |
        |                                       |
        | mTLS / OAuth2 / JWS-signed JWT        |
        v                                       |
+-------+-------+        adapter manifest       |
| Adapter (per  |  <-----------------------------+
| trust domain) |   defines what is allowed
+-------+-------+   regardless of peer claims
        |
        | InteropPrincipal (synthetic, scoped)
        v
+-------+-------+
| Service layer |   sees a principal whose role is the
+---------------+   minimum required for the declared op
```

**The peer never speaks in our role vocabulary.** A peer's "admin" claim
maps only to the operations the manifest pre-authorizes.

## InteropPrincipal

A synthetic principal class (scaffolding) used by adapters when invoking
internal services:

| Field | Value |
|-------|-------|
| `subject` | `interop:{domain_id}:{peer_subject}` |
| `lab_id` | derived from declared mapping; `None` for national aggregators on de-id flows |
| `role` | always one of: `INTEROP_READER`, `INTEROP_WRITER_LIMITED`, `INTEROP_REGULATOR_READ`, `INTEROP_AGGREGATOR_DEID` |
| `permissions` | derived from the manifest, never inherited from any other principal |
| `scope` | the explicit `operation` being executed |

These four `INTEROP_*` roles are **the only** roles an adapter can speak as.
They are not granted to humans; humans never log in as `INTEROP_*`.

## Tenancy Mapping

| Mode | Mapping behavior |
|------|------------------|
| `single_tenant_proxy` | Adapter binds 1:1 to a `lab_id`; the manifest names it. All data flowing through the adapter is for that lab. |
| `multi_tenant_aggregator` | Regulator-only. Reads aggregate metrics across labs; cannot write. |
| `national_aggregator` | Statistics platform. Reads only de-identified, k-anonymized data. Never raw patient identifiers. |

Mode is set at manifest load time and **immutable** for the adapter's
lifetime. Mode-changing requires a new adapter (new domain_id).

## Cross-Institution Restrictions

- An adapter for institution A MUST NOT see data sourced from institution B
  unless a reconciliation event (Phase 19) has explicitly recorded a
  cross-institution patient linkage and the adapter's manifest authorizes the
  operation.
- Reconciliation events themselves are visible only to:
  - The two participating tenants
  - The regulator audit reader (read-only)
- No adapter is granted "global patient lookup" capability. Period.

## Boundary Enforcement Hooks

| Hook | Where | Status |
|------|-------|--------|
| Manifest validator | `interoperability/manifest.py` (scaffold) | Documented |
| Capability whitelist check | `AdapterBase.call_outbound` / `handle_inbound` | Documented |
| InteropPrincipal builder | `interoperability/principal.py` (scaffold) | Documented |
| Audit emission | `core/audit_chain.py` (existing) extended via `InteropAuditEvent` | Pending wiring |
| Static check: no `routes/` import | Pre-commit / CI lint | Pending |
| Cross-tenant query guard | `database.py` request context vars | Existing (TI-1) |

## Out-of-Bound Boundaries

These boundaries are **not** enforced by interop and require external
controls:

- Network segmentation (VPC, firewall rules) — operational responsibility
- Peer-side credential lifecycle — contractual responsibility
- TLS termination on internal hop — gateway responsibility
- Sovereign KMS key custody — infra responsibility (Phase 17)

The interop layer is one defensive layer. It does not stand alone.
