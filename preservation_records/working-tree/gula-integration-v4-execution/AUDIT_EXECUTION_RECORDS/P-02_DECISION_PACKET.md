# P-02 / AUD-F02 — independent owner decision packet

**Generated:** 2026-11-20 UTC (checkpoint reissue)
**Owner gate:** R4 — **explicit package-specific owner authorization required before any implementation**
**Current status:** `PREPARED ONLY` · NOT `IMPLEMENTED` · NOT `TESTED` · NOT `INDEPENDENTLY REVIEWED` · NOT `ACCEPTED` · NOT `PRODUCTION READY`
**Posture:** HOLD · `production_ready_items = 0` · no commit / push / PR / merge / deploy

This packet is self-contained. It does not rely on the accelerated-completion mandate recorded in
`GULA_MASTER_EXECUTION_STATUS.md` §5: that mandate was used for P-01 and P-04 and is **not** treated
here as authorization for an active clinical-path behavior change.

---

## 1. Finding and evidence

| Field | Record |
|---|---|
| ID / severity | `AUD-F02` — MEDIUM, **ACTIVE** clinical path |
| Source | `backend/app/routes/ai.py:646-675`, function `_emit_critical_alert` |
| Defect | The canonical `log_action(...)` call at `:659-670` and `db.commit()` at `:671` are wrapped in `except Exception` (`:672`). The handler logs the exception (`:673`) and performs `contextlib.suppress(db.rollback())` (`:674-675`), then returns normally. `AuditChainIsolationError` (raised in `backend/app/services/audit_service.py:293` for non-READ-COMMITTED / AUTOCOMMIT sessions) and any DB error are therefore swallowed. |
| Impact | A critical lab-result alert can be omitted from the tamper-evident trail while the API response still succeeds. This is a clinical-safety and ISO 27001 A.8.15 compliance gap, not a demonstrated exploit. Static reachability is proven; no PHI was used. |
| Reference | `GULA_AUDIT_SECURITY_FINDINGS.md` AUD-F02; review-3 observation R3-02. |

## 2. Required change (prepared, NOT applied)

1. Narrow the exception boundary in `_emit_critical_alert` to the exact audit/DB failures:
   - catch `AuditChainIsolationError` and SQLAlchemy DB errors explicitly;
   - perform explicit `db.rollback()` inside a narrow `try/finally` (or equivalent deterministic path);
   - **re-raise** the original exception after rollback so the caller cannot report success.
2. Preserve the already-correct parts: canonical `log_action` call with `action="critical_result_alert"`,
   `resource_type="lab_order"`, `user_role="system:ai"`, dict `details`, and the existing response
   contract for the success path. Do not reintroduce direct `AuditLog` construction.
3. Add an explicit failure signal to the caller only if the existing endpoint contract already has an
   error channel; otherwise propagate and let the route's standard error handling respond. No silent
   success is acceptable.
4. No schema change, no migration, no new dependency, no change to audit hash semantics, no other
   route touched.

**Owner sub-decision (mandatory):** choose the failure policy —
- **(a) fail closed (recommended):** the request fails when the audit write cannot be chained;
  consistent with OD-001's READ-COMMITTED-only scope. Availability trade-off must be accepted.
- **(b) durable outbox:** buffer the audit event and alert, requiring a new bounded context and its
  own design/decision — out of scope for a single-hunk fix.

## 3. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Critical-result alerts become unavailable under audit-chain failure (fail-closed) | HIGH (availability) | Owner explicitly accepts the trade-off; keep the failure narrow and observable via structured log/metric; no blanket denial of care outside this alert write path. |
| Rollback itself raises and masks the original error | MEDIUM | `finally`-based rollback with the original exception re-raised; test the rollback-failure variant. |
| Over-broad `except` still swallows `AuditChainIsolationError` | HIGH (security) | Static AST guard plus behavioral RED test on REPEATABLE READ. |
| Test uses production DB or PHI | HIGH (governance) | Synthetic orders only, disposable SQLite test DB via existing fixtures; no external service. |
| Mixed-provenance file (`backend/app/routes/ai.py` contains 6 unrelated workstream hunks) | HIGH (provenance) | Edit only the `_emit_critical_alert` hunk; do not stage or commit; preserve all other lines byte-for-byte. |

## 4. Test plan (R3, disposable isolated environment only)

**RED (must fail on current code):**
1. REPEATABLE READ / AUTOCOMMIT session → call `_emit_critical_alert` → assert `AuditChainIsolationError`
   propagates and no `audit_logs` row is written. Current code suppresses it → RED.
2. Static AST guard: `_emit_critical_alert` contains no blanket `except Exception` and calls
   `db.rollback()` on failure.

**GREEN:**
3. READ COMMITTED session → exactly one chained row with `action="critical_result_alert"`,
   correct `resource_id` (synthetic order id), dict-serialized details, and
   `verify_audit_chain(db)["verified"] is True`.
4. Forced DB error during `log_action` → rollback occurs, original error propagates, zero rows written.

**Related suites:** audit chain integrity, anchor, bypass, positional regression, isolation guard,
P-13 financial audit, P-15 password-reset audit, P-01 legacy writer, P-04 verifier, and the AI route
tests that exercise `_emit_critical_alert`.

**Tooling:** Python 3.12 at `/tmp/opencode/gula-int-py312/bin/python`, synthetic SQLite fixtures,
ruff on touched Python files, `git diff --check`. No production DB, Redis, anchor or daemon.

## 5. Acceptance conditions

**Engineering (to be earned, not assumed):**
- RED → GREEN demonstrated; related suites pass; ruff clean; `git diff --check` clean.
- Fresh-context independent review verdict with 0 CRITICAL/HIGH, recorded in `P-02_AFTER.md`.
- All review conditions cleared by new regression tests before any `INDEPENDENTLY REVIEWED` claim.

**Owner (explicit, still outstanding):**
- Package-specific authorization text (below).
- Written acceptance of the fail-closed availability trade-off (or approval of the outbox alternative).
- Separate decision for commit/staging scope: `backend/app/routes/ai.py` has mixed provenance; no
  commit authority is implied by this package decision.

## 6. Owner decision requested

> "I authorize package P-02 / AUD-F02 exactly as scoped in `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET.md`,
> selecting failure policy (a) fail closed / (b) durable outbox. I accept the associated availability
> trade-off. This authorization covers this package only; it does not authorize a commit, staging
> change, merge, release, deployment, `PRODUCTION READY`, or a change to HOLD."

Alternative: *"P-02 is deferred; keep the finding open and the packet prepared."*

## 7. Rollback

Revert only the `_emit_critical_alert` hunk. No migration, schema change or protected-file change.
The 20 staged `R100` renames and staged name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203` remain untouched.
