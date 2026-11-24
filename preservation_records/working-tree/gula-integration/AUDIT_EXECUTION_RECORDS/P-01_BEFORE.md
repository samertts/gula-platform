# P-01 / AUD-F01 — BEFORE record (dormant raw audit writer)

**Finding:** `GULA_AUDIT_SECURITY_FINDINGS.md` AUD-F01 — MEDIUM (HIGH if activated), DORMANT,
owner gate R4. Roadmap package P-01.
**Authority:** MASTER-MANDATE-1.0 + OWNER AUTHORIZATION (accelerated completion, 2026-11-20).
**Posture:** HOLD · not ACCEPTED · not PRODUCTION READY · `production_ready_items = 0`.
**Data:** synthetic only; isolated SQLite disposable test DB; no PHI, production DB or secret.

## Defect proven by inspection (2026-11-20)

`shared/audit/service.py::create_audit_entry` writes with raw SQL to columns
`entity_type`, `entity_id`, `previous_hash`, `timestamp`. The canonical `AuditLog` model has
`resource_type`, `resource_id`, `chain_hash`, `created_at` and **none** of those four legacy
columns (verified against the ORM metadata under `ENV=test`). Consequences:

1. The INSERT cannot succeed on a migration-built canonical `audit_logs` table.
2. It computes the chain with its own `compute_chain_hash()` (simple `|` concatenation), which is
   a **different algorithm** from canonical `_compute_chain_hash()` (JSON payload + id/role/ip).
   Even if the row existed, `verify_audit_chain()` would either skip or flag it.
3. It calls `db_session.commit()` internally, breaking caller transaction atomicity.
4. `query_audit_log()` selects the same four non-existent columns, so reads fail too.
5. `backend/app/control_plane/audit.py::EnterpriseAudit` delegates to both raw functions.

Reachability: `EnterpriseAudit` is imported by `backend/app/control_plane/sdk.py` but is never
instantiated in any active request path and `set_audit()` is never called; `/control-plane/audit-log`
is inert. The defect is therefore DORMANT — **HIGH if activated**.

## Fix strategy (constitution-compliant)

The GULA project constitution forbids removing dormant enterprise modules ("Dormant modules are
strategic assets"). Therefore the module is **redirected, not deleted**:

- `create_audit_entry` → lazy-delegate to canonical `backend.app.services.audit_service.log_action`
  (the roadmap's sanctioned "delegated" option), mapping `entity_type`/`entity_id` into
  `resource_type`/`resource_id` and preserving the original identifiers inside `details`.
- `query_audit_log` → read canonical columns only, mapping back to the legacy return shape.
- Remove the internal `commit()`; the caller owns the transaction.
- Keep `compute_chain_hash()` available for the still-pending P-04 verifier alignment, but no
  audit writer may use it.

No active request path, no canonical audit behavior, no schema, no migration and no staged rename
is changed.
