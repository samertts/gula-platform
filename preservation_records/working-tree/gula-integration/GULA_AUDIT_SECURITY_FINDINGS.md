# GULA AUDIT SECURITY FINDINGS — COMPREHENSIVE REVIEW

**Directive:** `GULA-AUDIT-COMPREHENSIVE-REVIEW` (owner-authorized, 2026-11-20)
**Repository / HEAD:** `gula-integration` @ `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549`
**Method:** read-only static analysis. No application test, DB, Redis, production service, or external AI system was used. All findings are reproducible by reading the cited files; none was execution-verified in this workstream.
**Release posture:** **HOLD** — Stable v1.0.0 **NOT declared** — `PRODUCTION READY` **NOT authorized** — `production_ready_items = 0`.

Companion deliverables: `GULA_AUDIT_COMPLETE_INVENTORY.md`, `GULA_AUDIT_CALLSITE_MATRIX.md`, `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`, `GULA_AUDIT_REMEDIATION_ROADMAP.md`, `GULA_AUDIT_ACCEPTANCE_CRITERIA.md`.

**Severity definitions:** `HIGH` = audit trail can be subverted or a safety-critical event lost on an active path; `MEDIUM` = meaningful integrity/availability/compliance gap, bounded by dormancy or scope; `LOW` = defense-in-depth, tooling accuracy, or documentation gap; `INFO` = inventory fact requiring a decision, not a defect.

---

## 0. Findings summary

| ID | Severity | Title | Path | Reachability | Owner gate |
|---|---|---|---|---|---|
| AUD-F01 | MEDIUM (HIGH if activated) | Dormant raw writer bypasses canonical guard, schema and hash | `shared/audit/service.py:26-62` | DORMANT | **R4** |
| AUD-F02 | MEDIUM | Critical-result alert suppresses audit guard refusal | `backend/app/routes/ai.py:658-675` | ACTIVE | **R4** |
| AUD-F03 | MEDIUM | Control-plane release/deployment approval has no durable audit | `control_plane/routes.py:317-400`, `release/manager.py:69-99` | ACTIVE | **R4** |
| AUD-F04 | MEDIUM | Standalone verifier computes a different hash → false tampering | `scripts/audit_verifier.py:24-28` | MANUAL / daemon | R0–R2 tooling + owner review |
| AUD-F05 | LOW | Anchor write/read failures logged and suppressed | `audit_service.py:187-197,251-253` | ACTIVE | R4 if behavior changed |
| AUD-F06 | LOW | NULL-hash rows skipped by canonical verifier; demo script creates 50 | `audit_service.py:345-347`, `scripts/generate_demo_data.py:767-778` | ACTIVE verifier / MANUAL writer | R4 if behavior changed |
| AUD-F07 | LOW | Stale chain verifier self-skips | `scripts/dive.py:457-480` | MANUAL | R0–R2 tooling |
| AUD-F08 | LOW | SQLite has no append-only trigger | `audit_service.py:311-329` + migrations | DEV/TEST | R4 if behavior changed |
| AUD-F09 | LOW | Active domain audit stores outside canonical guard/verification | A6–A13 in inventory | ACTIVE (multiple) | R4 decision on scope |
| AUD-F10 | LOW | Active control-plane audit-log route is inert; stale 503 claim | `control_plane/routes.py:403-421` | ACTIVE route | R4 if behavior changed |
| AUD-F11 | LOW | Registered platform audit service has no consumer | `backend/app/platform/audit.py:28-105` | DORMANT | R4 decision |
| AUD-F12 | LOW | DB-trigger audit writes to parallel `audit_log` store | `config/postgres/audit.sql:41-103` | ACTIVE on fresh bootstrap | R4 decision |
| AUD-F13 | INFO | Dormant `sndhs_audit_logs` store has protection but no writer | migration `20260505_0005:57-150` | DORMANT | Owner classification |
| AUD-F14 | INFO | Call-count documentation mismatch (203 AST vs 206 textual) | `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md:135` | Documentation | Documentation correction |
| AUD-F15 | **HIGH when `ENABLE_FINANCIAL_ENGINE=true`; MEDIUM default (404-gated)** | Invalid audit-call keywords cause TypeError after financial mutation commit | `backend/app/financial/routes.py:313,368` | ACTIVE when flag enabled | **R4** |
| AUD-F16 | MEDIUM | MPI resolution failure suppressed; patient proceeds with null MPI identity | `backend/app/services/patient_service.py:500-510` | ACTIVE | **R4 if behavior changed** |
| AUD-F17 | MEDIUM (silent) | Password-reset audit calls silently swallowed after commit | `backend/app/routes/password_reset.py:52-53,80-81` | ACTIVE | **R4** |
| AUD-F18 | MEDIUM | Conditional fail-open identity audit on denials/failed step-ups | `b4_guard.py:156-159`, `step_up_service.py:153-156`, `authorization_decision.py:601-604` | ACTIVE | **R4** |
| AUD-F19 | LOW | Communication audit failures suppressed at four sink layers; null sink discards | `shared/communication/audit.py:94-110`, `backend/app/communication/__init__.py:104-145` | ACTIVE | **R4 decision** |
| AUD-F20 | LOW | FHIR decorator audits successful mutations only | `backend/app/audit/__init__.py:23` | ACTIVE | **R4 scope decision** |
| AUD-F21 | LOW | Pool/isolation documentation diverges from source defaults | `docs/decisions/OPERATIONS_DECISIONS.md:35-40` vs `backend/app/database.py:188-192` | Documentation | R1/R2 |

**One HIGH finding exists on a feature-flagged active path (AUD-F15).** Dormant bypasses are not dismissed; they are assigned owner decisions. Silent suppression paths (AUD-F17, AUD-F18) are treated as higher-severity than logged suppression (AUD-F02).

---

## 1. Finding detail

### AUD-F01 — Dormant raw audit writer bypasses canonical guard, schema and hash

| Field | Record |
|---|---|
| Severity | **MEDIUM** (conditional **HIGH** if activated) |
| Exact path/line | `shared/audit/service.py:26-62` — predecessor read `:36-38`, `GENESIS` sentinel `:39`, hash `:41`, raw `INSERT` `:43-47`, **internal `commit()` `:61`**; callers `backend/app/control_plane/audit.py:40`, `shared/audit/service.py:143` |
| Reproduction evidence | Static: (a) no `_require_audit_safe_isolation` call in the module; (b) `compute_chain_hash` (`:14-23`, pipe-delimited 6 fields) differs from canonical `_compute_chain_hash` (`backend/app/services/audit_service.py:162-175`, JSON-sorted 9 fields); (c) INSERT names `entity_type`, `entity_id`, `previous_hash`, `timestamp` — no migration adds these to `audit_logs` (only `chain_hash` in `20260324_0009:44`, `lab_id` in `20260813_0001`); (d) repo-wide `EnterpriseAudit(` → zero matches, `set_audit(` → definition only; `/control-plane/audit-log` short-circuits at `routes.py:412-413`. |
| Exploitability / operational impact | **DORMANT**, no active exploit shown. If wired: (1) a transaction at REPEATABLE READ/SERIALIZABLE could fork the chain because no isolation guard runs; (2) rows would fail canonical verification due to the different hash payload; (3) `:61` commits the caller's whole transaction prematurely, breaking clinical-mutation/audit atomicity; (4) against the current schema the INSERT likely fails with an undefined-column error (fail-closed by accident, not by design). |
| Remediation (prepared, not implemented) | Remove `create_audit_entry`/`AuditService.log` or redirect them to canonical `log_action`; delete `EnterpriseAudit` or make it a thin delegator; remove the internal commit; retire `query_audit_log`'s stale column names. **R4 — explicit owner authorization required before implementation.** |
| Regression test | (a) Assert no raw `INSERT INTO audit_logs` exists outside `backend/app/services/audit_service.py`; (b) instantiate `EnterpriseAudit` and assert `log()` calls `log_action` (or that the class is removed); (c) assert `log_action` guard raises under REPEATABLE READ and that no alternative writer can be reached from control-plane routes. |
| Rollback strategy | Single revert of the targeted module(s); no migration, no staging-area or protected-file change; 20 `R100` renames untouched. |
| Owner authorization requirement | **R4 audit behavior change — explicit owner authorization required.** No implementation, staging, commit or deployment in this workstream. |

### AUD-F02 — Critical-result alert suppresses audit guard refusal

| Field | Record |
|---|---|
| Severity | **MEDIUM** |
| Exact path/line | `backend/app/routes/ai.py:658-675` — `try` `:658`, `log_action` `:659-670`, `db.commit()` `:671`, `except Exception` `:672`, `logger.error` `:673`, `contextlib.suppress(db.rollback())` `:674-675` |
| Reproduction evidence | Static: `log_action` raises `AuditChainIsolationError` at `audit_service.py:293` under non-READ-COMMITTED or AUTOCOMMIT; `_emit_critical_alert` catches it at `:672` and returns normally. Review-3 observation **R3-02** records the same path at `:658-676`. |
| Exploitability / operational impact | **ACTIVE.** A critical lab-result alert can be omitted from the tamper-evident trail while the API response succeeds. This is a clinical-safety/compliance audit gap. No active exploitation demonstrated; static reachability proven. |
| Remediation (prepared, not implemented) | Re-raise guard failures (or convert to an explicit durable outbox event) instead of logging and continuing; remove the blanket `except Exception`; make rollback explicit. **R4 — owner authorization required.** |
| Regression test | Set the session to REPEATABLE READ, call `_emit_critical_alert`, assert `AuditChainIsolationError` propagates and no row is written; assert a successful call writes a chained row with `action="critical_result_alert"`. |
| Rollback strategy | Revert the single `routes/ai.py` hunk; no migration or protected-file change. |
| Owner authorization requirement | **R4.** This changes audit failure behavior on an active clinical path. |

### AUD-F03 — Control-plane release/deployment approval has no durable audit

| Field | Record |
|---|---|
| Severity | **MEDIUM** |
| Exact path/line | `backend/app/control_plane/routes.py:317-400`; `backend/app/control_plane/release/manager.py:69-99` (in-memory `approved_by`/`deployed_by` at `:36-37,74,86`; `logger.info` at `:75,87,94`); `config/secrets.py:59-67::access_audit_log()` has zero callers |
| Reproduction evidence | Static: no `log_action(` or `EnterpriseAudit.log()` anywhere under `backend/app/control_plane`; `/control-plane/audit-log` returns an empty list (`routes.py:412-413`); `EnterpriseAudit` is never instantiated. |
| Exploitability / operational impact | **ACTIVE.** Release approvals, deployment actions and secret-access events are recorded only in process memory and logs, which are not tamper-evident and do not survive restart. Governance decisions in the control plane have no durable audit trail. |
| Remediation (prepared, not implemented) | Add canonical `log_action` writes at approval/deploy/secret-access boundaries with actor, decision, version and correlation ID; keep in-memory fields for response only. **R4 — owner authorization required.** |
| Regression test | Drive the approval/deploy endpoints against a disposable DB; assert one chained `audit_logs` row per action with correct actor and action names; assert no write under non-READ-COMMITTED isolation. |
| Rollback strategy | Revert the targeted control-plane hunks; no migration required if reusing `audit_logs`. |
| Owner authorization requirement | **R4.** Also requires owner decision on whether control-plane actions belong in the canonical trail (scope decision). |

### AUD-F04 — Standalone verifier computes a different hash → false tampering

| Field | Record |
|---|---|
| Severity | **MEDIUM** |
| Exact path/line | `scripts/audit_verifier.py:24-28` (`compute_hash`), `:43-56` (comparison), `:62` (`sys.exit(1)`); invoked by `scripts/gula_guardian.py:49-56` on a 5-minute loop |
| Reproduction evidence | Static diff of payloads: script uses `f"{prev_hash}|{id}|{user_id}|{action}|{resource_type}|{resource_id}|{created_at.isoformat()}"`; canonical `audit_service.py:162-175` uses `prev_hash + json.dumps(record, sort_keys=True, ensure_ascii=False)` over `id, user_id, user_role, action, resource_type, resource_id, details, ip_address, created_at` with `_canonical_audit_timestamp` (`:120-134`). Missing fields and raw `isoformat()` guarantee mismatch whenever those fields are populated. |
| Exploitability / operational impact | **MANUAL / daemon.** Legitimate rows are reported as `TAMPER DETECTED` and the process exits 1. False integrity alarms can mask a real tampering event and erode trust in verification. This is a false-positive generator, **not** a chain bypass. |
| Remediation (prepared, not implemented) | Delete the standalone verifier or make it call `verify_audit_chain` from `backend.app.services.audit_service`; update `gula_guardian.py` accordingly. R0–R2 tooling correction; owner review before any daemon deployment. |
| Regression test | Build a canonical chained row (disposable SQLite), run the verifier entry point, assert `verified=True` and exit 0; mutate a field, assert detection. |
| Rollback strategy | Revert the script hunks; no DB or protected-file change. |
| Owner authorization requirement | R0–R2 for code correction; **no daemon restart/deployment without owner authorization** (release posture HOLD). |

### AUD-F05 — Anchor write/read failures logged and suppressed

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `backend/app/services/audit_service.py:187-197` (`_write_anchor`, `except Exception` `:195-196`); `:199-253` (`get_latest_anchor`, `except` `:251-253`) |
| Reproduction evidence | Static: `open(..., "a")` failure at `:193` is caught and logged; `get_latest_anchor` returns `None` on any read error. |
| Exploitability / operational impact | **ACTIVE.** Loss of the external HMAC checkpoint (disk full, permission, key error) is silent to callers. DB chain integrity is unaffected, but independent tamper-evidence degrades. |
| Remediation (prepared, not implemented) | Emit a metric/alert on anchor failure; make policy explicit about whether anchor failure must fail the request. **R4 if behavior changed.** |
| Regression test | Monkeypatch `open` to raise; assert an error log/metric is emitted and that DB chain write succeeds or fails per the chosen policy. |
| Rollback strategy | Revert the single module hunk. |
| Owner authorization requirement | **R4 if failure behavior changes**; metrics-only change is R2 with owner review. |

### AUD-F06 — NULL-hash rows skipped by canonical verifier; demo script creates 50

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `backend/app/services/audit_service.py:344-347` (`if entry.chain_hash is None: continue`); `scripts/generate_demo_data.py:763-780` (50 `AuditLog(...)` at `:767-778`, no `chain_hash`); A3 in inventory |
| Reproduction evidence | Static: verifier can return `{"status": "intact", "verified": True}` while NULL-hash rows exist; demo script never sets `chain_hash`. Known limitation from AUDIT-BYPASS-001, preserved in Review-3 findings. |
| Exploitability / operational impact | **ACTIVE verifier / MANUAL writer.** Unchained rows are outside tamper detection. Demo data is synthetic; no production writer of NULL-hash rows was found in the canonical path. |
| Remediation (prepared, not implemented) | Report NULL-hash rows explicitly in `verify_audit_chain` (count/status) rather than silently skipping; route demo writer through `log_action`. **R4 if verification semantics change.** |
| Regression test | Insert one NULL-hash row in disposable DB; assert verifier reports it in a dedicated field and does not return `verified=True` without disclosure. |
| Rollback strategy | Revert the verifier hunk and/or demo script hunk. |
| Owner authorization requirement | **R4** for verifier semantics; R2 for demo-script correction. |

### AUD-F07 — Stale chain verifier self-skips

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `scripts/dive.py:457-480` (`check_hash_chain`) |
| Reproduction evidence | Static: references non-existent `hash`, `prev_hash`, `data` columns; no call path found that would report meaningful results. |
| Exploitability / operational impact | **MANUAL.** Provides no effective verification; misleading tooling. No audit data exposure. |
| Remediation (prepared, not implemented) | Remove the function or delegate to canonical `verify_audit_chain`. R0–R2 tooling. |
| Regression test | Assert the removed/delegated function returns canonical verification output on a disposable DB. |
| Rollback strategy | Revert the single script hunk. |
| Owner authorization requirement | R0–R2; owner review before deployment. |

### AUD-F08 — SQLite has no append-only trigger

| Field | Record |
|---|---|
| Severity | **LOW** (dev/test scope) |
| Exact path/line | PG triggers only: `backend/migrations/versions/20250322_0002_perf_indexes_audit_protection.py:78-103`, `backend/app/core/startup_guard.py:688-695`, `config/postgres/audit.sql:134-142`. SQLite branch `audit_service.py:311-329` has no trigger. Tests mutate rows directly: `backend/tests/unit/test_audit_chain_integrity.py:128,144,161`, `test_audit_chain_isolation_guard.py:357,365`. |
| Reproduction evidence | Static: no SQLite trigger creation found; tests exercise UPDATE/DELETE/TRUNCATE deliberately. Production is documented as PostgreSQL (`audit_service.py:54-55`). |
| Exploitability / operational impact | **DEV/TEST.** Direct mutation of `audit_logs` is possible in SQLite; hash verification would detect most changes but NULL-hash rows are skipped (AUD-F06). |
| Remediation (prepared, not implemented) | Add SQLite triggers for dev/test parity, or document the scope explicitly in the verifier output. **R4 if behavior changed.** |
| Regression test | On disposable SQLite, attempt UPDATE/DELETE and assert rejection (or documented allowance) plus verifier detection. |
| Rollback strategy | Revert the migration/script hunk; no production migration in this package. |
| Owner authorization requirement | **R4** if production behavior changes; dev/test-only change is R2. |

### AUD-F09 — Active domain audit stores outside canonical guard/verification

| Field | Record |
|---|---|
| Severity | **LOW** (scope decision required) |
| Exact path/line | A6–A13 in `GULA_AUDIT_COMPLETE_INVENTORY.md` §4: `niam_audit_entries` (`identity/services/audit_service.py:92,144`, `canonical_audit.py:145,175-178`), `niam_admin_audit_logs` (`identity/admin/services.py:493`), `mpi_merge_audit` (`services/mpi/resolver.py:172`), `national_task_audit_logs` (`national/task_engine/application/service.py:327`), `ecosystem_partner_audit_logs` (`national/ecosystem/partners/service.py:410`), `billing_audit_events`/`pay_audit_events`, `clinical_audit_records`, `authorization_audit`, `gov_*_audit*` |
| Reproduction evidence | Static: each store has its own model/table and writer; none calls `log_action` or `_require_audit_safe_isolation`; some have independent hash chains (NIAM, MPI), others append-only ORM listeners (billing/payments). |
| Exploitability / operational impact | **ACTIVE** but domain-scoped. No single tamper-evidence guarantee spans all stores; an operator checking only canonical `audit_logs` would miss these events. Not a canonical-chain bypass because they are separate stores. |
| Remediation (prepared, not implemented) | Produce an authoritative audit-surface registry mapping each store to its owner, guarantee and verifier; decide which events must mirror into the canonical chain. **R4 decision.** |
| Regression test | Registry completeness test: enumerate `__tablename__` containing `audit` and assert each is registered with an owner and verification status. |
| Rollback strategy | Documentation/registry only; no behavior change. |
| Owner authorization requirement | **R4 scope decision** before any mirroring implementation. |

### AUD-F10 — Active control-plane audit-log route is inert; stale 503 claim

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `backend/app/control_plane/routes.py:403-421`, especially `:412-413` (`{"entries": [], "count": 0, "note": "Audit service not initialized"}`) |
| Reproduction evidence | Static + `git show HEAD:` comparison: behavior unchanged; no `set_audit()` caller. `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md:135` describes a 503 for this route — inaccurate relative to code. |
| Exploitability / operational impact | **ACTIVE route, no data.** Operators may believe audit is available via this endpoint. The stale 503 claim is a documentation accuracy issue; the accepted Review-3 scope is not reopened. |
| Remediation (prepared, not implemented) | Either wire the route to canonical `log_action`/query with authorization, or return an explicit 501/404 and remove misleading claims; correct the documentation note in a new dated record. **R4 if behavior changed.** |
| Regression test | Assert the route's response contract matches the documented one; assert no unauthenticated access. |
| Rollback strategy | Revert the route hunk or documentation line. |
| Owner authorization requirement | **R4** for route behavior; documentation correction is R1. |

### AUD-F11 — Registered platform audit service has no consumer

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `backend/app/platform/audit.py:28-105`, `PlatformRegistry.register("audit", ...)` `:101-105`; `create_entry` correctly delegates to canonical `log_action` `:42-51` |
| Reproduction evidence | Static: no import of `app.platform.audit` outside itself; `factory.py:724-725` imports only `.platform.routes`; no `PlatformRegistry.get("audit")`. |
| Exploitability / operational impact | **DORMANT.** No active bypass; a correctly delegating wrapper is simply unused. Confusion risk if a future caller assumes registration means activation. |
| Remediation (prepared, not implemented) | Remove registration or document it as an inactive capability; add a test that asserts no dormant platform service is advertised as active. |
| Regression test | Assert `PlatformRegistry.get("audit")` is either absent or explicitly marked dormant. |
| Rollback strategy | Revert the module hunk. |
| Owner authorization requirement | R2 documentation / **R4 if registration behavior changes**. |

### AUD-F12 — DB-trigger audit writes to parallel `audit_log` store

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `config/postgres/audit.sql:41-73` (`audit_trigger_function()`, INSERT at `:64`), triggers `:75-103` on `patients`, `test_orders`, `test_results`, `samples`, `users`; DDL `:9-31`; mounted by `docker-compose.full.yml:39` |
| Reproduction evidence | Static: triggers write to `audit_log` (singular), a different table with `event_type/old_values/new_values/severity`; no hash chain; canonical `verify_audit_chain` queries `audit_logs`. |
| Exploitability / operational impact | **ACTIVE on fresh full-compose bootstrap.** A second audit store exists outside the canonical trail with no tamper-evidence guarantee. No application code writes to it directly. |
| Remediation (prepared, not implemented) | Document the store as a separate control, add a verifier or consolidate into `audit_logs` via canonical writer. **R4 decision.** |
| Regression test | On disposable PG bootstrap, assert the parallel store is registered in the audit-surface registry and that its immutability trigger rejects UPDATE/DELETE. |
| Rollback strategy | Revert the SQL/compose hunk; no canonical DB migration. |
| Owner authorization requirement | **R4 decision** for consolidation; R2 for documentation. |

### AUD-F13 — Dormant `sndhs_audit_logs` store

| Field | Record |
|---|---|
| Severity | **INFO** |
| Exact path/line | migration `backend/migrations/versions/20260505_0005_sndhs_phase1_audit_logs_v2.py:57-150` (append-only triggers + REVOKE) |
| Reproduction evidence | Static: no application writer found (`sndhs_audit` appears only in `core/sndhs_flags.py:44` and `scripts/sndhs_phase1_backfill.py:103`). |
| Exploitability / operational impact | **DORMANT.** Protected but unused store; no current risk, requires classification. |
| Remediation (prepared, not implemented) | Record in the audit-surface registry with owner and retention decision. |
| Regression test | Registry completeness test (as in AUD-F09). |
| Rollback strategy | None needed (documentation only). |
| Owner authorization requirement | Owner classification; no implementation. |

### AUD-F14 — Call-count documentation mismatch

| Field | Record |
|---|---|
| Severity | **INFO** |
| Exact path/line | `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md:135` (206 textual) vs AST enumeration 203 direct calls / 56 files; this review's filtered text scan 200 calls / 54 modules |
| Reproduction evidence | Different scopes/filters: AST counts direct `log_action(...)` calls including tests; text scan excluded tests, `def` declarations and the unrelated NHOP `log_action`. |
| Exploitability / operational impact | Documentation accuracy only; no code behavior. Does not change Review-3 verdict. |
| Remediation (prepared, not implemented) | Add a dated clarification in the audit deliverables defining the count methodology; do not rewrite the accepted Review-3 report. |
| Regression test | AST test asserting the documented count matches the current tree (with an explicit scope parameter). |
| Rollback strategy | Documentation-only. |
| Owner authorization requirement | R1 documentation correction. |

### AUD-F15 — Invalid audit-call keywords cause TypeError after financial mutation commit

| Field | Record |
|---|---|
| Severity | **HIGH when `ENABLE_FINANCIAL_ENGINE=true`**; **MEDIUM in default configuration** (routes return 404) |
| Exact path/line | `backend/app/financial/routes.py:313-321` (`create_transaction`) and `:368-376` (`run_billing_cycle`); imports canonical `log_action` at `:17`; `db.commit()` at `:311` and `:367` occurs **before** the failing audit call |
| Reproduction evidence | Static (verified first-hand): canonical signature at `backend/app/services/audit_service.py:256-266` has `resource_type`/`resource_id`, no `entity_type`/`entity_id`. Both calls pass `entity_type="fin_transaction"` / `"fin_billing_cycle"` and `entity_id=...` → `TypeError: log_action() got an unexpected keyword argument 'entity_type'`. Router registered at `factory.py:584-585`; `_should_init_financial()` (`factory.py:62-67`) gates on `ENABLE_FINANCIAL_ENGINE`, default `"false"` (`config.py:428`); `_check_enabled()` at `routes.py:39-41` returns 404 when disabled. |
| Exploitability / operational impact | When enabled: the financial mutation is **committed**, then `log_action` raises `TypeError` → the request returns 500 with **no audit record**. A client retry can create a duplicate transaction (double-charge risk) and the audit trail is silently incomplete. This is an active audit-bypass and atomicity defect on a financial path, gated by a feature flag. |
| Remediation (prepared, not implemented) | Rename `entity_type`→`resource_type` and `entity_id`→`resource_id` at both sites; move the audit call before the commit or use one transaction so audit and mutation commit atomically; add a static signature test over all `log_action` call sites. **R4 — owner authorization required** (audit call behavior change). |
| Regression test | (a) AST test: every `log_action` keyword is in the canonical signature — this finding would have been caught; (b) disposable DB with flag enabled: POST a transaction, assert one chained `audit_logs` row with `resource_type="fin_transaction"`, no 500, and no duplicate on a single request; (c) run-cycle equivalent. |
| Rollback strategy | Revert the single `backend/app/financial/routes.py` hunk; no migration, no protected-file or staging change. |
| Owner authorization requirement | **R4** — audit behavior change on a financial path; also requires owner decision on enabling the feature. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F16 — MPI resolution failure suppressed; patient proceeds with null MPI identity

| Field | Record |
|---|---|
| Severity | **MEDIUM** |
| Exact path/line | `backend/app/services/patient_service.py:465-510` — `except Exception as mpi_err` at `:500`, `log_action(action="mpi_resolve_failed")` at `:501-509`, return at `:510`; return values initialized to `(None, None)` at `:481-482` |
| Reproduction evidence | Static: the broad handler at `:500` contains no `raise`; it writes the audit event and returns. `create_patient` at `:228` receives `(None, None)` and populates `resp["citizen_ulid"]`/`resp["mpi_match_method"]` at `:247-248`. The MPI exception is suppressed; the audit event itself is written through the canonical guard. Only 2 of 236 `log_action` calls are lexically inside an `ExceptHandler` (this one and a narrow re-raising `CardTokenError` handler at `routes/patient_card.py:129`). |
| Exploitability / operational impact | **ACTIVE.** A patient record can be created with no MPI identity while the caller sees a success response. The original MPI failure is invisible outside the log line embedded in `details`. Clinical identity linkage and national-ID traceability degrade. The audit event is present, so this is a **mutation-semantics** issue rather than an audit-write bypass. |
| Remediation (prepared, not implemented) | Re-raise after auditing, or return an explicit failure result to the caller; keep the `mpi_resolve_failed` audit event. **R4 if failure behavior changes.** |
| Regression test | Force MPI resolution to raise in a disposable env; assert the audit row exists and that the caller receives an explicit failure (or documented degraded result), not an unnoticed `(None, None)`. |
| Rollback strategy | Revert the single `patient_service.py` hunk. |
| Owner authorization requirement | **R4 if behavior changes**; R2 for documentation only. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F17 — Password-reset audit calls silently swallowed after commit

| Field | Record |
|---|---|
| Severity | **MEDIUM** — silent suppression (no log, no signal) of credential-lifecycle audit events |
| Exact path/line | `backend/app/routes/password_reset.py:52-53` (`with contextlib.suppress(Exception): log_action(... "password_reset_requested" ...)`) and `:80-81` (`... "password_reset_completed" ...`) |
| Reproduction evidence | Static (verified first-hand): both `log_action` calls are wrapped in `contextlib.suppress(Exception)` with **no logger call**. The business change is already committed (`:50`, `:79`) before the audit attempt. `/forgot-password` is pre-authentication; `/reset-password` accepts a reset token. The guard refusal at `audit_service.py:293` (or any DB error) is swallowed with zero observable signal. |
| Exploitability / operational impact | **ACTIVE.** Password-reset request and completion — security- and compliance-critical credential events — can be entirely absent from the tamper-evident trail with no log entry. Unlike AUD-F02 (which logs), this is a truly silent loss. The committed state change cannot be rolled back by the dependency. |
| Remediation (prepared, not implemented) | Remove `contextlib.suppress`; allow audit failures to propagate (fail-closed) or write to a durable retry/outbox with an alert. Consider auditing before commit so audit and credential change share a transaction. **R4 — owner authorization required.** |
| Regression test | Force `log_action` to raise in a disposable env; assert the failure is observable (exception or alert metric) and that no silent path exists; assert a successful reset writes a chained row with the correct action. |
| Rollback strategy | Revert the single `password_reset.py` hunk; no migration, no protected-file or staging change. |
| Owner authorization requirement | **R4 — explicit owner authorization required** (audit failure behavior on an authentication path). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F18 — Conditional fail-open identity audit on denials and failed step-ups

| Field | Record |
|---|---|
| Severity | **MEDIUM** |
| Exact path/line | `backend/app/identity/adaptive_auth/b4_guard.py:144-159` (`except Exception:` `:156`, `if required: raise` `:157-158`, comment `:159`); `backend/app/identity/services/step_up_service.py:141-156` (`logger.exception` `:153-154`, `if outcome == "success": raise` `:155-156`); `backend/app/identity/services/authorization_decision.py:591-604` (`except Exception:` `:601`, allowed→`deny(audit_failure)` `:602-603`, denied→`return decision` `:604`) |
| Reproduction evidence | Static (verified first-hand): all three handlers suppress audit-write failures when the decision is a **denial** or a **failed step-up**. B4 denial callers (`:194,211,227,266`) omit `required=True`; only successful cross-account access (`:240-251`) sets it. `authorization_decision` returns a denied decision with **no log** of the audit outage. |
| Exploitability / operational impact | **ACTIVE.** Denials — the security-significant outcomes most needed for forensic review — can lose their audit evidence silently. Successful privileged actions fail closed (correct), but the asymmetric policy means an audit outage is invisible precisely when an attacker is being denied. |
| Remediation (prepared, not implemented) | Make audit failures observable on denial paths (structured log + metric at minimum); decide with the owner whether denials must fail closed or use a durable buffer. **R4 — owner authorization required.** |
| Regression test | Force the identity audit sink to raise on a denial; assert an alert/metric is emitted and the documented policy holds; assert successful privileged access still fails closed. |
| Rollback strategy | Revert the three targeted hunks independently. |
| Owner authorization requirement | **R4 — explicit owner authorization required** (identity audit failure policy). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F19 — Communication audit failures suppressed at four sink layers; null sink discards

| Field | Record |
|---|---|
| Severity | **LOW** |
| Exact path/line | `shared/communication/audit.py:94-103` (per-sink `except Exception: logger.exception`), `:106-110` (`NullAuditSink.record: pass`); `shared/communication/center.py:551-555`; `backend/app/communication/__init__.py:104-145` (own `SessionLocal` → `log_action` → `db.commit()` `:134`, `except: db.rollback(); logger.exception` `:135-141`, outer `except` `:144-145`); `backend/app/communication/experience/sinks.py:102-109,187-194` |
| Reproduction evidence | Static (verified first-hand for primary paths): the composite sink logs and continues when any sink fails; the durable sink uses a short independent session and logs+rolls back on failure; `NullAuditSink` explicitly discards. Default `audit_enabled=True` in config, but the policy when the durable sink is absent/down is log-only. |
| Exploitability / operational impact | **ACTIVE.** Communication audit artifacts can be lost without affecting delivery; failures appear only in logs. Not a canonical-chain bypass (the durable sink uses `log_action`), but the layered suppression makes outage detection unreliable. |
| Remediation (prepared, not implemented) | Define a single audit-sink failure policy (metric/alert on any sink failure; explicit registration of `NullAuditSink`); document which events require the durable sink. **R4 decision** for policy; R2 for metrics-only. |
| Regression test | Force each sink to raise; assert a metric is emitted and the operation outcome matches the documented policy; assert no event is silently discarded unless `NullAuditSink` is explicitly configured. |
| Rollback strategy | Revert the targeted sink hunks. |
| Owner authorization requirement | **R4 decision** on sink failure policy; R2 for observability-only changes. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F20 — FHIR decorator audits successful mutations only

| Field | Record |
|---|---|
| Severity | **LOW** (scope decision) |
| Exact path/line | `backend/app/audit/__init__.py:18-67` — `result = func(*args, **kwargs)` at `:23` is **outside** the `try` at `:24`; docstring at `:19` says "on successful endpoint execution"; applied at `routes/ehr_fhir.py:1367,1391,1414` |
| Reproduction evidence | Static (verified first-hand): if the wrapped FHIR function raises, execution never enters the `try`, so no `log_action` (`:45`) and no `db.commit()` (`:59`) occur. Audit failures on successful calls re-raise correctly (`:60-64`). |
| Exploitability / operational impact | **ACTIVE.** Failed FHIR create/update/delete attempts — which can be clinically and security significant — produce no audit entry. This is a documented design choice, not a suppression bug, but it leaves a coverage gap on an active clinical path. |
| Remediation (prepared, not implemented) | Owner decision: either keep success-only semantics and document it explicitly, or add explicit failure-event auditing around the wrapped call. **R4 scope decision.** |
| Regression test | Force the wrapped function to raise; assert the audit behavior matches the chosen documented policy. |
| Rollback strategy | Revert the decorator hunk. |
| Owner authorization requirement | **R4 scope decision** before any behavior change. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### AUD-F21 — Pool/isolation documentation diverges from source defaults

| Field | Record |
|---|---|
| Severity | **LOW** (documentation accuracy; static-only) |
| Exact path/line | `backend/app/database.py:188-192` (`DB_POOL_SIZE` default `5`, `DB_MAX_OVERFLOW` `10`, `DB_POOL_TIMEOUT` `10`, `DB_POOL_RECYCLE` `1800`); `docs/decisions/OPERATIONS_DECISIONS.md:35-40` states `WEB_CONCURRENCY=3`, `pool_size=6`, `max_overflow=12`, `pool_timeout=30`, `pool_recycle=3600` and asserts "Implemented in `backend/app/database.py`" |
| Reproduction evidence | Static diff: source defaults are `5/10/10/1800` (effective budget `2 × (5+10) = 30` with source `WEB_CONCURRENCY=2`), while the ADR documents `6/12/30/3600` (`3 × (6+12) = 54`) as implemented. No runtime verification was performed; env overrides may change effective values. No explicit `isolation_level` is passed to `create_engine`; the canonical writer enforces READ COMMITTED at `audit_service.py:74-117`. |
| Exploitability / operational impact | **Documentation only.** Operators relying on the ADR may mis-size connection budgets or misjudge stale-connection behavior. Not an audit-chain defect. Conclusions are static-only per the review constraints. |
| Remediation (prepared, not implemented) | Correct the ADR (or the source defaults) to a single authoritative value; add a test asserting documented defaults match `database.py`. **R1/R2 documentation correction.** |
| Regression test | Unit test comparing documented constants with `database.py` environment defaults. |
| Rollback strategy | Revert the documentation hunk. |
| Owner authorization requirement | R1/R2 documentation; no audit behavior change. |
| Status | `PREPARED — NOT IMPLEMENTED` |

---

## 2. Cross-cutting notes

- **Guard strength:** the F-01 guard itself is **not weakened** by any finding. It fails closed before any data statement on PostgreSQL. The gaps are at callers (AUD-F02/F15/F16/F17/F18), alternative writers (AUD-F01), verification tooling (AUD-F04/F07), sink layers (AUD-F19), scope coverage (AUD-F03/F09/F12/F20), and documentation drift (AUD-F21).
- **One active HIGH finding (AUD-F15)** exists on a feature-flagged path (`ENABLE_FINANCIAL_ENGINE=true`): an invalid-keyword audit call raises `TypeError` after the financial mutation is committed, leaving that mutation unaudited. In the default configuration these routes return 404, so the finding is MEDIUM by default. Dormant high-impact paths are separately labelled with conditional severity and owner gate.
- **Silent suppression is ranked above logged suppression:** AUD-F17 (password reset) and denial-side AUD-F18 lose audit evidence with no log at all; AUD-F02 logs its failure. All are R4.
- **OD-001 remains accepted for its defined engineering scope only.** None of these findings reopens that acceptance; they are new, separately scoped observations with their own owner gates.
- **No PHI, secret values, or production data appear in this report.**

**Status:** `HOLD`. All remediations are prepared only; none implemented, staged, committed or deployed.