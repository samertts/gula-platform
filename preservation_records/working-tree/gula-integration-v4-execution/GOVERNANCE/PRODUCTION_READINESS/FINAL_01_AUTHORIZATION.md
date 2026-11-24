# Final Report 01 — Authorization (WS-A) + L-1/L-2/L-3 remediation

**Report ID:** PR-FINAL-01 · **Date:** 2026-11-18 · **Data class:** SYNTHETIC ONLY
**Governing decision:** `GOVERNANCE/FINAL_DECISION.md` **HOLD** unchanged; MPI **REJECT** unchanged. Development evidence only.

## 1. Classification

| Deliverable | Classification | Basis |
|---|---|---|
| Runtime RBAC/ABAC engine (`AuthorizationEngine`, policies, deny-by-default, revoke, audit) | **VERIFIED** | 36 engine tests + real guard integration; every decision appends exactly one audited record |
| `AuthorizedHealthCore` guarded facade | **VERIFIED** | 18 guard tests; all mutating/reading methods evaluate (principal, action, resource) before touching a service |
| Authorization audit chain (`AuthorizationAuditLog`, `verify_audit_chain`) | **PARTIALLY VERIFIED** | Interior edits, reorders, first/middle deletion detected; tail truncation and coherent rehash forgery are documented + test-locked limitations (no external keyed/durable anchor) |
| Production route wiring | **NOT IMPLEMENTED** | No route/`factory.py` activation by design — owner-gated |

Overall workstream classification: **VERIFIED (synthetic scope)**, with the audit-chain limitation explicitly disclosed.

## 2. What was built

- **Engine:** deny-by-default policy evaluation, tenant equality (`DENY_TENANT`), permission checks, role grants/revokes with `RevocationScope`, exactly one immutable audit record per evaluation, stable public denial reason.
- **Facade:** `AuthorizedHealthCore` wraps the real synthetic clinical and lab services; every method calls `_authorize()` first; a denial raises `AuthorizationDenied` before the wrapped service is touched.
- **Authoritative attribute index:** populated only by guarded writes; reads take organization/facility/patient scope from the index so a caller cannot inject a falsified scope.

## 3. Adversarial findings remediated

### L-1 — LOW — unwrapped services publicly exposed (design bypass)
- **Before:** `guard.clinical`, `guard.lab` were public; an in-process caller could bypass all policy evaluation, produce zero audit records and never populate the attribute index.
- **Fix:** renamed to private `self._clinical` / `self._lab` in `__init__` and all 28 internal references. `self.engine` remains public by design (grants/revokes/audit inspection; not a mutator bypass).
- **Regression:** strict test asserts `not hasattr(guard, "clinical")`, `not hasattr(guard, "lab")`, no public attribute holds a `ClinicalContext`/`LabWorkflowService`, `engine` still public, and guarded write+read works end-to-end with a valid chain.

### L-2 — LOW — tenant equality trusted caller-supplied tenant on indexed reads
- **Before:** `_authorize(use_index=True)` took `tenant_id` from the caller while org/facility/patient came from the index. A tenant-A principal could claim tenant A for a tenant-B resource; engine returned ALLOW (service layer later raised `TenantMismatchError`, so no data leaked — but the authorization decision was wrong).
- **Fix:** when a stored entry exists, evaluation context `tenant_id` is sourced from `stored.tenant_id`; caller tenant is used only when no entry exists. The engine's existing `DENY_TENANT` rule now denies the mismatch and audits it through the normal path.
- **Regression:** tenant-A principal claiming tenant A on a tenant-B resource → `AuthorizationDenied` / `DENY_TENANT`, decision + audit carry `SYN-LAB-0002`, no entity returned; legitimate tenant-B read still ALLOWs. Rewrote the old cross-tenant-probe test to the new authoritative semantics (identical generic denial for known/unknown ids).

### L-3 — LOW — audit docstring overclaimed tamper detection
- **Before:** docstring claimed detection of "edited, removed, reordered or re-hashed records" — false for tail truncation and coherent rehash forgery.
- **Fix:** exact honest statement in module docstring: detects payload/hash edits, reorders, sequence/predecessor gaps incl. first-record deletion; does **not** detect tail truncation or a fully rebuilt chain because the log is unsigned, in-memory and lacks an external keyed/durable anchor.
- **Regression:** tests assert both limitations hold (`ok is True` after tail deletion and after full coherent rehash), while interior tamper / reorder / first-deletion remain detected and denials are audited with correct policy ids.

## 4. Files changed (this remediation cycle)

`backend/app/health_core/authorization/guard.py`, `backend/app/health_core/authorization/audit.py`, `backend/tests/health_core/test_authorization_guard.py`, `backend/tests/health_core/test_authorization_engine.py`, `backend/tests/health_core/test_authorization_audit.py`. (`engine.py` unchanged; included in verification scope.)

## 5. Verification

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  /tmp/opencode/mpi-venv/bin/python -m pytest \
  tests/health_core/test_authorization_guard.py \
  tests/health_core/test_authorization_engine.py \
  tests/health_core/test_authorization_audit.py -q --tb=short
# 68 passed, 1 warning in 0.58s
```
Per-file (authoritative JUnit counts): audit 14, engine 36, guard 18 = **68**.
Ruff: `All checks passed!` over all six files. No skips, no weakened assertions.

## 6. Residual / blocked

- Audit log has no external keyed/durable anchor — upgrading this requires a persistence/migration owner decision. Classification stays PARTIALLY VERIFIED for that sub-component.
- No production route wiring — **NOT IMPLEMENTED** by owner decision; do not infer release readiness.

**End of final report 01.**
