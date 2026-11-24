# GULA AUDIT FAILURE PROPAGATION REPORT — COMPREHENSIVE REVIEW

**Directive:** `GULA-AUDIT-COMPREHENSIVE-REVIEW` (owner-authorized, 2026-11-20)
**Repository / HEAD:** `gula-integration` @ `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549`
**Method:** read-only static analysis of exception handlers, transaction boundaries, connection/pool semantics and verification paths. No database, Redis, production service, or application test executed in this workstream.
**Release posture:** **HOLD** — no `PRODUCTION READY` — `production_ready_items = 0`.

Companion deliverables: `GULA_AUDIT_COMPLETE_INVENTORY.md`, `GULA_AUDIT_CALLSITE_MATRIX.md`, `GULA_AUDIT_SECURITY_FINDINGS.md`, `GULA_AUDIT_REMEDIATION_ROADMAP.md`, `GULA_AUDIT_ACCEPTANCE_CRITERIA.md`.

**Semantics legend:** `RE-RAISE` (failure reaches caller) · `LOG+SUPPRESS` (logged, request continues) · `CONVERT` (different exception/result) · `DEFER` (retry/background) · `SWALLOW` (silent) · `FAIL-CLOSED` (write refused before any statement).

---

## 1. Failure-semantics summary

| Path | Path:line | Audit failure behavior | Reachability | Impact |
|---|---|---|---|---|
| Canonical writer guard | `backend/app/services/audit_service.py:74-117`, invoked `:293` | **FAIL-CLOSED** — `AuditChainIsolationError` before any data statement | `ACTIVE` (all PG canonical calls) | Intended protection; rejects non-READ-COMMITTED and AUTOCOMMIT |
| Canonical writer body | `audit_service.py:256-332` | propagates SQLAlchemy errors; **no internal commit** | `ACTIVE` | Caller owns commit; failure normally propagates |
| Anchor checkpoint | `audit_service.py:187-197` | **LOG+SUPPRESS** — `except Exception` → `logger.error` | `ACTIVE` | Anchor evidence lost; DB chain unaffected |
| `_emit_critical_alert` | `backend/app/routes/ai.py:658-675` | **LOG+SUPPRESS** — broad `except Exception`, `logger.error`, `contextlib.suppress(db.rollback())` | `ACTIVE` | Guard refusal / DB error swallowed; critical clinical alert absent from audit |
| `@audit_log` decorator | `backend/app/audit/__init__.py:18-67` | **RE-RAISE** (`logger.exception` then `raise` at `:63-64`) | `ACTIVE` on decorated FHIR routes | Correct fail-closed semantics; uncommitted clinical mutation rolled back by dependency |
| `shared.audit.create_audit_entry` | `shared/audit/service.py:26-62` | propagates, but **internally commits at `:61`** | `DORMANT` | Premature commit of caller transaction; no guard; incompatible schema |
| `verify_audit_chain` | `audit_service.py:335-367` | returns `verified=True` while skipping NULL-hash rows `:345-347` | `ACTIVE` read-only | Unchained rows invisible to tamper detection |
| `scripts/audit_verifier.py` | `scripts/audit_verifier.py:24-28,43-62` | reports false tampering on valid canonical rows; `sys.exit(1)` `:62` | `MANUAL` / daemon (`scripts/gula_guardian.py:49-56`) | Incorrect integrity alarms; possible alarm fatigue |
| `scripts/dive.py` chain check | `scripts/dive.py:457-480` | self-skipping stale columns (`hash`, `prev_hash`, `data`) | `MANUAL` | No effective verification |
| Financial routes — invalid keywords | `backend/app/financial/routes.py:313,368` | **TypeError after commit** — `entity_type`/`entity_id` rejected by canonical signature; mutation at `:311`/`:367` already committed | `ACTIVE` when `ENABLE_FINANCIAL_ENGINE=true` (404 by default) | Committed financial mutation with **no audit row**; retry can duplicate the transaction (AUD-F15, HIGH when enabled) |
| `_resolve_mpi` | `backend/app/services/patient_service.py:500-510` | **SUPPRESS** — broad `except Exception` writes `mpi_resolve_failed` audit then returns `(None, None)` | `ACTIVE` | Patient created with no MPI identity; original error invisible (AUD-F16) |
| Password reset | `backend/app/routes/password_reset.py:52-53,80-81` | **SWALLOW** — `contextlib.suppress(Exception)` around `log_action`, no logger, after commit (`:50`,`:79`) | `ACTIVE` | Credential-lifecycle events silently unaudited (AUD-F17) |
| B4 / step-up / authorization denials | `identity/adaptive_auth/b4_guard.py:156-159`, `identity/services/step_up_service.py:153-156`, `identity/services/authorization_decision.py:601-604` | **CONDITIONAL SUPPRESS** — denial/failed-step-up audit errors swallowed; success paths re-raise or convert to deny | `ACTIVE` | Denial evidence lost silently; success paths fail closed (AUD-F18) |
| FHIR decorator | `backend/app/audit/__init__.py:23-64` | **RE-RAISE** on successful-call audit failure; **BYPASS** for failed wrapped calls (`func()` at `:23` outside `try`) | `ACTIVE` | Failed clinical mutations produce no audit (AUD-F20) |
| Clinical command guard | `backend/app/clinical/command_guard.py:199-218,246-271` | **RE-RAISE** after `record_audit_failure(...)` metric | `ACTIVE` | Fail-closed; no unaudited completed/rejected command |
| Clinical gateway | `backend/app/clinical_gateway/service.py:272-298`, `routes.py:205-241` | **CONVERT** → `ClinicalGatewayAuditFailure` → rollback + HTTP 503 | `ACTIVE` | Fail-closed; original audit cause hidden by `from None` at route level |
| Communication sinks | `shared/communication/audit.py:94-110`, `backend/app/communication/__init__.py:104-145` | **LOG+SUPPRESS** at four layers; `NullAuditSink` explicitly discards | `ACTIVE` | Durable audit outage visible only in logs (AUD-F19) |
| Integrations reject | `backend/app/routes/integrations.py:209-240` | **CONVERT** — broad `except` → rollback + HTTP 503 | `ACTIVE` | Inbox rejection not committed; client gets 503 |
| Patient-card failed scan | `backend/app/routes/patient_card.py:129-142` | **PROPAGATES LOCALLY** — audit inside `except CardTokenError`; no local rollback | `ACTIVE` | Audit failure replaces intended 400 with a 500 |
| Workspace denial | `backend/app/identity/api/workspaces.py:143-152` | **PROPAGATES LOCALLY** — audit inside `except WorkspaceAccessDenied` | `ACTIVE` | Audit failure replaces intended 403 |
| MPI merge savepoint | `backend/app/services/mpi/resolver.py:983-1025` | **SAVEPOINT ROLLBACK + RE-RAISE** — `begin_nested()` at `:983`, rollback at `:1023-1025` | `ACTIVE` | No partial merge or audit row; fail-closed |
| MPI retry | `backend/app/services/mpi/reliability.py:208-235` | **RETRIED** — fresh session, reconcile, replay transient failures ≤3; `AuditChainIsolationError` is a `RuntimeError` → not retried | `ACTIVE` | Transient DB audit failures replayed with whole transaction |

---

## 2. Canonical writer — fail-closed guard and transaction semantics

**`backend/app/services/audit_service.py:74-117`** (`_require_audit_safe_isolation`) is called at **`:293`**, inside the PostgreSQL branch only, **before** the advisory lock, serial-sequence reservation, predecessor read, and `db.add`/`db.flush()`.

Checks performed on the actual connection:
1. `connection.get_isolation_level()` — live `SHOW transaction isolation level` (`:87`).
2. Engine/connection execution option `isolation_level` (`:88-93`).
3. DBAPI `getattr(..., "autocommit", None)` (`:94`).

Failure behavior:
- Any exception reading connection state → `AuditChainIsolationError` (`:95-98`).
- Undetermined autocommit → raise (`:100-103`).
- `autocommit=True` → raise (`:104-107`) — prevents the advisory lock from being released immediately after the predecessor read.
- Configured isolation not in `{"READ COMMITTED"}` → raise (`:108-111`).
- Live isolation not in `{"READ COMMITTED"}` → raise (`:112-116`).

**Operational result:** a transaction at REPEATABLE READ / SERIALIZABLE, or an AUTOCOMMIT connection, cannot take an audit write. This is the F-01 acceptance scope. **A caller that catches this exception and continues can defeat the operational intent without altering the database** — see §3.

**SQLite branch (`:311-329`)** has no isolation guard: it relies on a no-op `UPDATE audit_logs SET id = id WHERE 1 = 0` (`:318`) to hold the write lock until commit. SQLite is dev/test only per the module docstring; this difference is explicit and is not a production bypass.

**Commit boundary:** `log_action` ends after `db.flush()` (`:310` / `:329`) and optional anchor write (`:331-332`). It never commits. Atomicity of the clinical mutation and its audit record therefore depends on the caller committing the same `Session`. A caller that commits early, rolls back, or uses a different session can break that atomicity. This is the mechanism exploited by the internal commit in A1.

---

## 3. `_emit_critical_alert` — suppression of the guard refusal (R3-02)

**`backend/app/routes/ai.py:647-675`**

```python
647: def _emit_critical_alert(...):
650:     """Write a critical-result alert to the canonical chained audit log. Non-fatal.
658:     try:
659:         log_action(db, action="critical_result_alert", ...)
671:         db.commit()
672:     except Exception as exc:
673:         logger.error("[AI] critical_result_alert audit write failed: %s", exc)
674:         with contextlib.suppress(Exception):
675:             db.rollback()
```

**Failure semantics:** `LOG+SUPPRESS`. The `except Exception` at `:672` catches `AuditChainIsolationError` from the guard, all SQLAlchemy errors from the canonical writer, and commit errors. None are re-raised. The caller of `_emit_critical_alert` receives `None` and the clinical response proceeds.

**Reproduction (static):** any condition that makes `_require_audit_safe_isolation` raise at `audit_service.py:293` — e.g. a per-transaction `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` on the session used by this handler — produces the log line at `:673` and no audit row. The rollback at `:674-675` is itself wrapped in `contextlib.suppress`, so rollback failure is also swallowed.

**Operational impact:** critical-result alerts — a clinical-safety and compliance-relevant event — can be silently omitted from the tamper-evident trail. A READ-COMMITTED-only scope accepted under OD-001 is enforced at the writer but not at this caller. **No active exploit of this path was demonstrated**; this is a static reachability finding.

**Owner gate:** remediation changes audit behavior → **R4, explicit owner authorization required before implementation**.

---

## 4. Anchor checkpoint — suppressed write failure

**`backend/app/services/audit_service.py:187-197`**

```python
187: def _write_anchor(entry_id, chain_hash):
188:     try:
189:         anchor_file = _current_anchor_file()
190:         anchor_file.parent.mkdir(parents=True, exist_ok=True)
191:         data = ...
192:         sig = _anchor_hmac(data)
193:         with open(anchor_file, "a", encoding="utf-8") as f:
194:             f.write(...)
195:     except Exception as e:
196:         logger.error("AUDIT ANCHOR WRITE FAILED (id=%s): %s", entry_id, e)
```

**Failure semantics:** `LOG+SUPPRESS`. Disk-full, permission or key errors are logged only. The DB hash chain is still written; the external anchor checkpoint is lost. `get_latest_anchor()` (`:199-253`) likewise returns `None` on read failure (`:251-253`) with `logger.warning`.

**Impact:** weakens independent tamper-evidence (the anchor file is the cross-check outside the DB). No DB-chain integrity loss. Owner gate: R4 if behavior is changed.

---

## 5. `@audit_log` decorator — correct re-raise

**`backend/app/audit/__init__.py:18-67`**

```python
23: result = func(...)
24: try:
...
45:     log_action(...)
59:     db.commit()
60: except Exception:
63:     logger.exception("audit_log decorator failed")
64:     raise
65: return result
```

**Failure semantics:** `RE-RAISE`. Audit integrity takes precedence; the dependency rolls back the uncommitted clinical mutation. This is the desired behavior and is **not** a suppression path. Note the decorator writes only on successful execution (`:23` before the `try`), so a failed mutation produces no audit entry — an intentional scope limit, not a failure-suppression bug.

---

## 6. Alternative writer `create_audit_entry` — internal commit and no guard

**`shared/audit/service.py:26-62`**

- Predecessor read with `FOR UPDATE` at `:36-38` uses a **`GENESIS` string sentinel** (`:39`), not the canonical `"0"*64`.
- Hash at `:41` uses `compute_chain_hash` (`:14-23`), a pipe-delimited 6-field payload — **different** from canonical `_compute_chain_hash` (JSON-sorted 9-field payload, `audit_service.py:162-175`).
- Raw `INSERT INTO audit_logs (... entity_type, entity_id, previous_hash, timestamp ...)` at `:43-47` targets columns absent from the canonical schema (see `GULA_AUDIT_COMPLETE_INVENTORY.md` §4 A1).
- **`db_session.commit()` at `:61`** commits the caller's entire transaction.

**Failure semantics:** propagates DB errors (no broad handler), but introduces a transaction-boundary failure mode: a caller that called `create_audit_entry` mid-workflow would commit clinical mutations prematurely. Because no guard runs, an activation would also fork the hash chain and produce rows the canonical verifier flags as tampered. Reachability: **DORMANT** (`EnterpriseAudit` optional singleton, no `set_audit()` caller).

---

## 7. Verification-path failure modes

### 7.1 Canonical verifier skips NULL-hash rows
`backend/app/services/audit_service.py:344-347`:
```python
344: for entry in entries:
345:     if entry.chain_hash is None:
346:         prev_hash = entry.chain_hash or prev_hash
347:         continue
```
Rows written without `chain_hash` (e.g. A3 demo data) are invisible to tamper detection. The status can be `"intact" / verified=True` while unchained rows exist. This is a known limitation inherited from AUDIT-BYPASS-001 and is documented, not newly introduced.

### 7.2 Standalone verifier computes the wrong hash
`scripts/audit_verifier.py:24-28`:
```python
payload = f"{prev_hash}|{entry.id}|{entry.user_id}|{entry.action}|{entry.resource_type}|{entry.resource_id}|{entry.created_at.isoformat()}"
```
Canonical `_compute_chain_hash` (`audit_service.py:162-175`) hashes a JSON-sorted record including `user_role`, `lab_id`, `details`, `ip_address` and canonicalised UTC microseconds. The script omits all of these and uses raw `isoformat()`. Every legitimately chained row with any of those fields populated will be reported as `TAMPER DETECTED` (`:50-54`) and the script exits 1 (`:62`). It is invoked by `scripts/gula_guardian.py:49-56` on a 5-minute loop if that daemon runs. **This is a false-positive generator, not a bypass** — its operational impact is incorrect integrity alarms and loss of trust in the verifier.

### 7.3 Stale verifier
`scripts/dive.py:457-480` `check_hash_chain` references non-existent `hash` / `prev_hash` / `data` columns and self-skips; it provides no effective verification.

---

## 8. Broad `except Exception` inventory (audit-adjacent)

Confirmed in this report:
- `backend/app/routes/ai.py:672` — `LOG+SUPPRESS` (critical alert).
- `backend/app/services/audit_service.py:95` (`_require_audit_safe_isolation`) — `CONVERT` to fail-closed exception (correct).
- `backend/app/services/audit_service.py:195` (`_write_anchor`) — `LOG+SUPPRESS`.
- `backend/app/services/audit_service.py:251` (`get_latest_anchor`) — `LOG+SUPPRESS` returning `None`.
- `backend/app/audit/__init__.py:60` — `RE-RAISE`.
- `backend/app/services/patient_service.py:500` (`_resolve_mpi`) — **SUPPRESS** of the MPI error after writing the audit event (AUD-F16).
- `backend/app/routes/password_reset.py:52,80` — **SWALLOW** via `contextlib.suppress(Exception)` (AUD-F17).
- `backend/app/identity/adaptive_auth/b4_guard.py:156`, `step_up_service.py:153`, `authorization_decision.py:601` — **CONDITIONAL SUPPRESS** on denial/failure paths (AUD-F18).
- `shared/communication/audit.py:96`, `backend/app/communication/__init__.py:135,144` — **LOG+SUPPRESS** in sink layers (AUD-F19).
- `backend/app/routes/integrations.py:234` — **CONVERT** to rollback + HTTP 503.
- `backend/app/audit/__init__.py:60` — `RE-RAISE`; `backend/tests/unit/test_audit_chain_isolation_guard.py` uses deliberate `contextlib.suppress` in probe code; test-only.

The call-site-relative `ExceptHandler` enumeration is recorded in `GULA_AUDIT_CALLSITE_MATRIX.md` §4: of 236 `log_action` calls, only **2** are lexically inside an `ExceptHandler` — the MPI handler above (broad, suppresses) and `routes/patient_card.py:129` (`CardTokenError`, narrow, re-raises). **Important limitation:** `contextlib.suppress(Exception)` is a `with` statement, not an `ExceptHandler`, so the AST handler analysis does **not** capture `password_reset.py:52,80`. Suppression must also be scanned by `contextlib.suppress` usage — recorded here and in AUD-F17. `_emit_critical_alert` (`routes/ai.py:672`) is not inside an enclosing handler but contains its own broad handler around the call.

---

## 9. Connection-pool and isolation behavior (source-derived)

- The guard reads the **live** connection (`:86`) via `db.connection()`; `get_isolation_level()` issues `SHOW transaction isolation level` so it observes both engine defaults and per-transaction `SET TRANSACTION`.
- `get_execution_options().get("isolation_level")` (`:88-93`) catches engine-level configuration; a transaction-level override is caught by the live check.
- AUTOCOMMIT is invisible to SQLAlchemy's `get_isolation_level()`, hence the explicit DBAPI flag check (`:94`, `:100-107`).
- The advisory lock `pg_advisory_xact_lock` (`:297-300`) is transaction-scoped: the DB releases it on commit or rollback; no application-side release exists. A connection returned to the pool without commit would still hold the lock until the transaction ends.
- The serial ID is reserved with `nextval(pg_get_serial_sequence('audit_logs','id'))` (`:303-305`) because the append-only trigger rejects UPDATE (`:301-302`).
- **No retry/backoff exists in the canonical writer.** A refused audit write is not automatically retried there; recovery depends on the caller (`_emit_critical_alert` does not retry). The **MPI retry helper** (`services/mpi/reliability.py:208-235`) is the only bounded-retry path found: fresh session per attempt, reconcile, replay transient failures ≤3; `AuditChainIsolationError` is a `RuntimeError` and therefore not retried.
- Connection settings (`backend/app/database.py:188-192`): defaults `WEB_CONCURRENCY=2`, `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`, `DB_POOL_TIMEOUT=10`, `DB_POOL_RECYCLE=1800`; `QueuePool` with `pool_pre_ping=True` on PostgreSQL (`:217-226`), `StaticPool` for SQLite dev/test (`:210-215`), `sessionmaker(autocommit=False)` at `:242`. No explicit `isolation_level` is passed to `create_engine` — the canonical writer enforces READ COMMITTED at `:74-117`.
- Per-connection setup (`:229-239`) sets `statement_timeout`, `work_mem`, and `idle_in_transaction_session_timeout=60s`; any setup exception is suppressed at `:238-239`. If setup fails, a long-held audit advisory lock loses its 60-second safety net.
- **Documentation drift (AUD-F21):** `docs/decisions/OPERATIONS_DECISIONS.md:35-40` documents `WEB_CONCURRENCY=3`, `6/12/30/3600` (budget `3×(6+12)=54`) and asserts "Implemented in `backend/app/database.py`"; source defaults are `5/10/10/1800` (budget `2×(5+10)=30`). Static-only; env overrides may change effective values.

**Limitation:** pool configuration values were **not execution-verified**; no DB test was run. Any claim about runtime pool state is `UNKNOWN` in this report. Transaction-boundary facts above are source-derived (request session `database.py:284-298` rolls back on propagated exception; canonical writer flushes but caller commits; `shared/audit/service.py:61` commits internally; MPI merge uses a SAVEPOINT at `resolver.py:983-1025`; communication sink uses a short independent session).

---

## 10. Suppression / bypass register

| ID | Path | Type | Owner gate |
|---|---|---|---|
| SUP-01 | `routes/ai.py:672-675` | LOG+SUPPRESS of guard refusal and rollback failure | **R4 — owner authorization required** |
| SUP-02 | `audit_service.py:195-196` | LOG+SUPPRESS anchor write failure | R4 if behavior changed |
| SUP-03 | `audit_service.py:251-253` | LOG+SUPPRESS anchor read failure | R4 if behavior changed |
| SUP-04 | `audit_service.py:345-347` | NULL-hash rows skipped by verifier | R4 if behavior changed |
| SUP-05 | `shared/audit/service.py:61` | Internal commit bypasses caller transaction boundary | **R4 — owner authorization required** |
| SUP-06 | `scripts/audit_verifier.py:27` | Wrong hash algorithm → false tampering | R0–R2 tooling correction, owner review before deployment |
| SUP-07 | `scripts/dive.py:457-480` | Stale verification, self-skipping | R0–R2 tooling correction |
| SUP-08 | `routes/password_reset.py:52-53,80-81` | **SILENT SWALLOW** of credential-audit failures | **R4 — owner authorization required** |
| SUP-09 | `b4_guard.py:156-159`, `step_up_service.py:153-156`, `authorization_decision.py:601-604` | Conditional suppression on denial/failure paths | **R4 — owner authorization required** |
| SUP-10 | `shared/communication/audit.py:94-110`, `communication/__init__.py:104-145` | Layered sink suppression + explicit null sink | R4 policy decision / R2 metrics |
| SUP-11 | `audit/__init__.py:23` | Failed FHIR mutations produce no audit (scope limit) | **R4 scope decision** |
| SUP-12 | `routes/integrations.py:234-240`, `routes/patient_card.py:129-142`, `identity/api/workspaces.py:143-152` | Audit failure converts/replaces intended HTTP outcome | R4 decision |

---

## 11. Evidence discipline

No application tests were executed for this review. The focused results cited in earlier workstreams (13/13 focused, 73/73 related, 12/12 disposable PG16 guard, 25 state/connection probes, 4 cross-process probes) are **historical Review-3 evidence** for the accepted F-01 scope and are **not** presented as fresh results here. All findings above are static, reproducible by reading the cited files, and were not verified by execution in this workstream.

**Status:** `HOLD`. No source, test, migration or config changed; no R4 remediation implemented; no commit, push, merge or deployment.
