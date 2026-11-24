# P-04 / AUD-F04 — BEFORE record (standalone verifier divergence)

**Finding:** `GULA_AUDIT_SECURITY_FINDINGS.md` AUD-F04 — LOW, MANUAL/daemon, owner gate
`R0–R2 tooling + owner review` (no audit write behavior change). Roadmap package P-04.
**Authority:** MASTER-MANDATE-1.0 + OWNER AUTHORIZATION (accelerated completion, 2026-11-20).
**Posture:** HOLD · not ACCEPTED · not PRODUCTION READY · `production_ready_items = 0`.

## Defect proven by inspection (2026-11-20)

`scripts/audit_verifier.py::compute_hash` claims to "Match the logic in
app.services.audit_service._compute_chain_hash" but does not:

| Canonical `_compute_chain_hash` | Standalone `compute_hash` |
|---|---|
| `record = {id, user_id, user_role, action, resource_type, resource_id, details, ip_address, created_at}` | pipe-joins only `{prev, id, user_id, action, resource_type, resource_id, created_at}` |
| `payload = prev_hash + json.dumps(record, sort_keys=True, ensure_ascii=False)` | `payload = f"{prev_hash}\|{id}\|…"` |
| canonical timestamp normalisation via `_canonical_audit_timestamp` | raw `entry.created_at.isoformat()` |

Therefore an **intact** canonical chain is reported as `TAMPER DETECTED` with exit code 1.
`scripts/gula_guardian.py::verify_audit_chain` consumes that exit code and logs a critical tamper
alarm, so a healthy chain can raise a false integrity incident (and the inverse — a verifier that
happens to match a forged row — is not excluded).

Additional defect: on an empty log the verifier returns before closing nothing (the `finally:
db.close()` still runs — correct), but it prints a success line without an explicit exit code;
exit-0 semantics are implicit rather than asserted.

## Fix strategy (tooling only, R0–R2)

- Delete the local `compute_hash` and delegate to canonical `verify_audit_chain(db)` — one
  authoritative verification algorithm.
- Preserve human-readable output but add an explicit exit code (0 intact/empty, 1 tampered,
  2 verification error) and keep `gula_guardian.py`'s non-zero-means-alert contract unchanged.
- Document the guardian dependency in the verifier module docstring.
- No audit write behavior, schema, migration, route or production deployment is changed. No daemon
  restart is performed (HOLD).

## Regression test plan

Disposable SQLite: build a canonical chain with `log_action`, assert the standalone verifier
entry point returns 0; mutate one field, assert it detects the tamper and returns 1; assert the
verifier source no longer defines its own hash function.
