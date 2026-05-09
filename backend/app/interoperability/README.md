# `backend/app/interoperability/` — Sovereign Interop Scaffolding

**Status:** Non-wired architectural scaffolding. **Not** imported by
`app/main.py`. **Not** registered as FastAPI routes. **Not** part of the
production runtime today.

## Purpose

Anchor the architectural shape for sovereign-grade institutional
interoperability per `docs/sovereign/phase16-interoperability/`:

- `AdapterBase` — abstract adapter interface
- `TrustDomain` — bounded-trust manifest dataclass
- `InteropAuditEvent` — interop-only audit event shape
- `InteropPrincipal` — synthetic principal carried by adapter calls
- `failure_isolation` — circuit breaker + retry helpers (pure-Python)
- `manifest` — manifest validation helpers

## Compatibility Guarantee

This package is intentionally **not wired** into `app/main.py`. Importing
it has no side effects on the running platform. It does not:

- mount routes
- access the database
- register middlewares
- alter audit-chain behavior
- start background tasks
- introduce new heavyweight dependencies (stdlib only)

A future, explicitly-approved wiring phase may register interop routes
under `/interop/{adapter_name}/{operation}` gated behind:

```
ENABLE_INTEROP=true
INTEROP_ADAPTER_ALLOWLIST=...
```

Until then the surface is silent.

## Why It's Here

Even non-wired scaffolding is useful: it pins the contract, lets the
governance documents reference real symbols, and gives reviewers a
concrete object to argue with.

## Boundary Rules

- Adapters MUST NOT import from `backend/app/routes/`.
- Adapters MAY import read-only from `backend/app/models/` (when wiring is
  approved).
- Adapter trust bindings are bounded by a `TrustDomain` manifest; they are
  not user-inheritable.
- Every adapter operation emits an `InteropAuditEvent`.
- Every external integration fails closed.

See `docs/sovereign/phase16-interoperability/02-adapter-framework.md`.
