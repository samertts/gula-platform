# Independent review — P-02 and P-03 decision packets

**Date:** 2026-11-20 UTC · **HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Scope:** `AUDIT_EXECUTION_RECORDS/P-02_DECISION_PACKET.md`, `AUDIT_EXECUTION_RECORDS/P-03_DECISION_PACKET.md`
**Method:** fresh-context, read-only independent reviewer (session `ses_e0559f72bffesRsBJZ3S5M8a9w`),
supplemented by local corroboration against `git show HEAD:<path>`. No files, tests, staging area,
protected MD5 or release decision were changed by the review. No implementation was started.
**Gate:** R4 review only. This review awards **no implementation authorization**, **no `ACCEPTED`**,
**no `PRODUCTION READY`**, and no change to HOLD.

## Verdicts

| Packet | Verdict | CRITICAL | HIGH | MEDIUM | LOW/INFO | Implementation |
|---|---|---:|---:|---:|---:|---|
| P-02 / AUD-F02 | **FAIL — NOT DECISION-READY** | 1 | 2 | 2 | 2 | `BLOCKED` |
| P-03 / AUD-F03 | **FAIL — NOT DECISION-READY** | 1 | 6 | 4 | 2 | `BLOCKED` |

**Structural defect common to both packets:** their evidence baseline is the **uncommitted working
tree**, not HEAD. The repository's Git HEAD still has the original defects and none of the
hardening the packets tell the owner to "preserve". Signing either packet as written would
authorize a materially different change from the one described. The packets must be rewritten
against an explicit baseline before any owner decision.

---

## P-02 / AUD-F02 — FAIL

### CRITICAL

1. **The defect as described does not exist at HEAD.** The packet (§1) cites canonical
   `log_action(...)` at `backend/app/routes/ai.py:659-670`, `db.commit()` at `:671`,
   `except Exception` at `:672`, and `AuditChainIsolationError` at
   `backend/app/services/audit_service.py:293`. At HEAD, locally re-verified:
   - `git show HEAD:backend/app/routes/ai.py` → `_emit_critical_alert` at `:641-667`, with **direct
     `AuditLog(...)` construction**, `db.commit()` and `except Exception`; **no `log_action` call**.
   - `git show HEAD:backend/app/services/audit_service.py | wc -l` → **270 lines**; no `:293`, no
     `AuditChainIsolationError` and no isolation guard.
   The cited code exists only in the uncommitted working tree. §2's instruction to "preserve the
   already-correct parts … do not reintroduce direct `AuditLog` construction" is therefore
   vacuous at HEAD: the real HEAD fix is a different, larger R4 change.

### HIGH

2. **Caller-level behavior impact is hidden.** In the working tree the helper is invoked inside
   `loop.run_in_executor` with only `finally: db2.close()` and no error channel; re-raising propagates
   into `/ai/interpret` before the interpretation call. The endpoint would fail before returning a
   clinical interpretation — not merely "alert unavailable". The packet's "no blanket denial of
   care outside this alert write path" is misleading because this *is* the interpretation path.
3. **Decisive RED test is not executable with the declared tooling.** The packet specifies
   synthetic SQLite fixtures, but the guard's isolation check is PostgreSQL-only
   (`audit_service.py:286-293` in the working tree; dialect check at HEAD `:215`) and accepts only
   READ COMMITTED. SQLite cannot raise the guard error, so RED test #1 can never behave as written.
   A disposable PostgreSQL instance and a caller-level assertion on the endpoint failure signal are
   required.

### MEDIUM

4. **Owner decision text is not a single unambiguous decision** — §6 leaves
   "(a) fail closed / (b) durable outbox" as a slash placeholder while §2 says (b) is out of scope;
   the unconditional "I accept the associated availability trade-off" is inapplicable to (b).
5. **Rejection conditions are not explicitly defined** — §5 defines acceptance and §7 defines
   rollback, but no engineering rejection rule (e.g. any CRITICAL/HIGH finding, regression, or
   failed RED → reject). The owner's "defer" alternative is not an engineering rejection rule.
6. **Related-suite list is imprecise** — "bypass" generically; the concrete regression is
   `backend/tests/unit/test_audit_bypass_regression.py:66-126`, which exercises this helper.

### LOW / INFO
- Line-reference drift: packet §1 says `:646-675`; `GULA_AUDIT_SECURITY_FINDINGS.md:64` says
  `:658-675`; the working-tree function begins at `:647`.
- R3-02 is graded **LOW** in `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md:149`; the packet calls
  it only an "observation" without preserving the rating.

### Adequate (P-02)
R4/HOLD posture; `production_ready_items = 0`; explicit exclusion of commit/push/PR/merge/release/
`PRODUCTION READY`/HOLD change; no schema/migration/dependency/hash-semantics change; synthetic-data
and disposable-environment requirement; mixed-provenance warning; hunk-scoped rollback; accurate
20 × R100 staged MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`; cross-check to R3-02.

### Owner sub-decision required (exact wording)
> "I select failure policy **(a) fail closed** for P-02 / AUD-F02. I accept that an audit write
> refusal (non-READ-COMMITTED/AUTOCOMMIT) or a DB failure during the critical-result alert write
> will fail the `/ai/interpret` request before the interpretation is returned; this availability
> trade-off is accepted on this path only. If policy (b) is selected, this packet is not authorized
> and a separate durable-outbox design package is required. I separately authorize or defer any
> staging/commit of `backend/app/routes/ai.py`; this decision alone authorizes none. No commit,
> staging change, merge, release, deployment, `PRODUCTION READY`, or change to HOLD is authorized."

---

## P-03 / AUD-F03 — FAIL

### CRITICAL

1. **Premises not corroborated at HEAD.** The packet cites approval/deploy routes at
   `control_plane/routes.py:317-400` and `/audit-log` at `:403-413`. At HEAD, locally re-verified:
   the file has **351 lines**; `/audit-log` is at `:309-327`; there is **no `/releases/{id}/approve`
   route**; HEAD deploy takes the actor from the request body (`data.get("user", "unknown")`).
   Authenticated-principal attribution and the two-person rule exist only in the uncommitted
   working tree. Implementing §2 at HEAD would add unstated actor-attribution behavior plus audit
   writes — hidden R4 scope. `/audit-log` at HEAD returns
   `{"entries": [], "count": 0, "note": "Audit service not initialized"}`, not a bare empty list.

### HIGH

2. **No DB session source specified.** `control_plane/routes.py` has no `get_db`/`SessionLocal`/
   `Session` dependency (HEAD or working tree), while `ReleaseManager.approve/deploy` are purely
   in-memory. `log_action` requires `db: Session`. The packet never states where the session comes
   from nor commit/rollback ordering relative to in-memory state mutation.
3. **`/audit-log` rewiring unspecified and overlapping F01.** `sdk.audit` is `EnterpriseAudit`
   whose `query()` calls the stale-column shared writer (the F01 area); `set_audit` has no callers,
   so `sdk.audit is None`. The packet asserts canonical reads "part of the package" with no
   mechanism — a distinct R4 change intersecting F01.
4. **Secret-access boundary undefined; test #3 not executable.**
   `control_plane/config/secrets.py::access_audit_log()` is a pure dict builder with **zero callers**;
   the real accessors are `get()` / `get_required()` / `rotate()`, none with a DB session. Wiring
   `access_audit_log()` alone produces no audit rows on real secret access.
5. **Idempotency contradiction.** §3 and §4.6 require exactly one row per successful action, but
   §2 forbids schema changes and `log_action` has no correlation/dedupe parameter, unique constraint
   or lookup. Exactly-once cannot be guaranteed under retry/concurrency.
6. **Decisive RED tests unexecutable on SQLite** for the same PostgreSQL-only guard reason as P-02
   (§4.1, §4.2, §4.5 need disposable PostgreSQL).
7. **Owner decision text is blank/contradictory** — "scope option __"; scope (c) is declared
   out-of-scope in §2 yet selectable; §5 requires a separate failure-policy decision while §6 fixes
   fail-closed; (d) defer is listed in §2 but omitted from the authorization text.

### MEDIUM

8. **Rejection conditions not explicitly defined.**
9. **Risk row assumes authenticated-principal attribution** — false at HEAD (`routes.py:294`).
10. **§2 overstates enforcement** — "no write under non-READ-COMMITTED isolation"; the guard is
    skipped when `bind is None` or the dialect is not PostgreSQL. Acceptance must scope this to PG.
11. **Action-name taxonomy conflict** — the packet proposes `control.release_approved` /
    `control.release_deployed` / `control.secret_accessed`, while
    `control_plane/audit.py:12-23` already defines `control.deployment`, `control.release`,
    `control.decision`, `control.secret_access`. Reconciliation is unspecified.

### LOW / INFO
- The historical stale-503 documentation drift (`GULA_AUDIT_SECURITY_FINDINGS.md:27`) is not
  reconciled with the current `/audit-log` response shape.

### Adequate (P-03)
R4/HOLD posture; explicit exclusion of commit/merge/release/deploy/`PRODUCTION READY`/HOLD change;
scope options (a)-(d) enumerated; actor-from-principal and "never log secret values" principles;
reuse of `audit_logs` without migration/schema change/new dependency; risk coverage including
availability, privacy, duplicates, provenance and inert-route false assurance; hunk-scoped rollback;
accurate staged MD5; correct cross-check that OD-001 is the only accepted decision and OD-002…025
remain BLOCKED; no package-specific owner authorization text exists for F02/F03.

### Owner sub-decision required (exact wording)
> "I select P-03 scope option **(a) all three boundaries — approval, deployment, secret access**
> [or **(b) approval and deployment only**]. I select the **fail-closed** audit failure policy for
> each selected boundary and accept that those control-plane requests fail when the audit write
> cannot be chained. I confirm the **authenticated principal is the sole actor source** and no
> actor/identity field from a request body is accepted. I confirm **secret values are never written
> to audit details**; only the key reference/name is recorded. I authorize P-03 exactly as scoped,
> including re-pointing `/control-plane/audit-log` to canonical `audit_logs` rows. Option (c)
> requires a separate design package; option (d) defers this packet. This decision grants no
> commit, staging change, merge, release, deployment, `PRODUCTION READY`, or HOLD-change authority."

---

## Disposition

- **P-02** and **P-03**: **return to preparation**. Both must be rewritten with an explicit
  baseline (HEAD vs uncommitted working tree), explicit test environment (PostgreSQL for guard
  paths), explicit caller-level failure signals, DB session/source, secret-access boundary,
  rejection criteria and a single unambiguous owner decision text. Then re-review. **Do not
  implement either packet.**
- No `ACCEPTED` / `PRODUCTION READY` award; HOLD unchanged; `production_ready_items = 0`.
