# GULA AUDIT REMEDIATION ROADMAP — COMPREHENSIVE REVIEW

**Directive:** `GULA-AUDIT-COMPREHENSIVE-REVIEW` (owner-authorized, 2026-11-20)
**Repository / HEAD:** `gula-integration` @ `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549`
**Status of every package below:** `PREPARED — NOT IMPLEMENTED — NOT STAGED — NOT COMMITTED`.
**Release posture:** **HOLD** — Stable v1.0.0 **NOT declared** — `PRODUCTION READY` **NOT authorized** — `production_ready_items = 0`.

Companion deliverables: `GULA_AUDIT_COMPLETE_INVENTORY.md`, `GULA_AUDIT_CALLSITE_MATRIX.md`, `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`, `GULA_AUDIT_SECURITY_FINDINGS.md`, `GULA_AUDIT_ACCEPTANCE_CRITERIA.md`.

---

## 1. Authority tiers

| Tier | Meaning | Authorization in this workstream |
|---|---|---|
| R0 | Read-only observation / inventory | Autonomous — executed |
| R1 | Documentation-only correction | Autonomous — executed for OD-001 synchronization; further documentation changes prepared only |
| R2 | Non-audit-behavior tooling correction in isolated scope | Prepared; execution requires disposable isolated environment and owner review before deployment |
| R3 | Any test execution | Disposable isolated environments only; none executed in this workstream |
| **R4** | **Any audit behavior change** | **Explicit owner authorization required before implementation** — all R4 packages below are prepared only |
| R5 | Prohibited actions (production access, PHI, release, merge, direct push to main, publication of unreviewed changes) | Not attempted; excluded |

**No source, test, migration, configuration, staging-area, branch, protected-MD5 or release decision was changed by this roadmap.**

---

## 2. Package inventory

### P-01 — Retire the dormant raw audit writer (AUD-F01)

| Field | Plan |
|---|---|
| Finding | `AUD-F01` — `shared/audit/service.py:26-62`, `backend/app/control_plane/audit.py:26-124`, `shared/audit/service.py:130-155` |
| Scope | Remove or redirect `create_audit_entry`, `AuditService.log`, `query_audit_log` stale-column queries and `EnterpriseAudit.log/query`; eliminate the internal `commit()` at `shared/audit/service.py:61`. |
| Behavior impact | No active request path changes (`EnterpriseAudit` never instantiated, `set_audit()` never called, `/control-plane/audit-log` inert). Dormant capability removed or delegated. |
| Regression test | (a) AST test: no raw `INSERT INTO audit_logs` outside `backend/app/services/audit_service.py`; (b) if delegated, assert `EnterpriseAudit.log()` produces a chained row via `log_action`; (c) assert no internal commit in any audit writer. |
| Rollback | Single revert of the touched modules; no migration, no staging change, 20 `R100` renames untouched. |
| Owner gate | **R4 — explicit owner authorization required.** |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-02 — Stop suppressing critical-result audit failures (AUD-F02)

| Field | Plan |
|---|---|
| Finding | `AUD-F02` — `backend/app/routes/ai.py:658-675` |
| Scope | Replace blanket `except Exception` with propagation of `AuditChainIsolationError` and DB errors; make rollback explicit; optionally route the alert through a durable outbox (separate decision). |
| Behavior impact | **Active clinical path.** A failed audit write will fail the endpoint instead of being silently logged. Availability trade-off must be accepted by the owner. |
| Regression test | REPEATABLE READ session → assert exception propagates, no row written; READ COMMITTED → assert chained `critical_result_alert` row and commit. |
| Rollback | Revert the single `routes/ai.py` hunk. |
| Owner gate | **R4 — explicit owner authorization required** (changes audit failure behavior). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-03 — Durable audit for control-plane release/deployment actions (AUD-F03)

| Field | Plan |
|---|---|
| Finding | `AUD-F03` — `control_plane/routes.py:317-400`, `release/manager.py:69-99`, `config/secrets.py:59-67` |
| Scope | Add canonical `log_action` writes at approval, deployment and secret-access boundaries; preserve in-memory fields for response only; define action names and actor extraction. |
| Behavior impact | New audit rows on control-plane actions; no change to approval logic. Requires owner scope decision on whether control-plane events belong in the canonical chain. |
| Regression test | Disposable DB: drive approval/deploy endpoints; assert exactly one chained row per action with actor, version and correlation ID; assert guard refusal on non-READ-COMMITTED. |
| Rollback | Revert targeted control-plane hunks; no migration if reusing `audit_logs`. |
| Owner gate | **R4 — scope decision + implementation authorization required.** |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-04 — Align standalone verifier with the canonical algorithm (AUD-F04)

| Field | Plan |
|---|---|
| Finding | `AUD-F04` — `scripts/audit_verifier.py:24-28,43-62`, `scripts/gula_guardian.py:49-56` |
| Scope | Remove `compute_hash` and call `verify_audit_chain` from `backend.app.services.audit_service`; update exit-code semantics; document the guardian dependency. |
| Behavior impact | Tooling only. Eliminates false tampering alarms. No audit write behavior change. |
| Regression test | Disposable SQLite: build a canonical chain, assert verifier exit 0; mutate one field, assert detection and exit 1. |
| Rollback | Revert script hunks. |
| Owner gate | R0–R2 for the code change; **owner review before any daemon restart/deployment** (HOLD). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-05 — Surface anchor failures instead of silent logging (AUD-F05)

| Field | Plan |
|---|---|
| Finding | `AUD-F05` — `audit_service.py:187-197,251-253` |
| Scope | Emit a metric/structured log on anchor write/read failure; decide policy (fail request vs degrade) with the owner. |
| Behavior impact | Potential change to request outcome if fail-closed policy is chosen. |
| Regression test | Monkeypatch file write/read failure; assert metric emitted and chosen policy applied. |
| Rollback | Revert the single module hunk. |
| Owner gate | R2 for metrics; **R4 if request outcome changes**. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-06 — Disclose NULL-hash rows in chain verification (AUD-F06)

| Field | Plan |
|---|---|
| Finding | `AUD-F06` — `audit_service.py:344-347`, `scripts/generate_demo_data.py:763-780` |
| Scope | Add `unchained_rows` count/status to `verify_audit_chain`; route demo writer through `log_action` or label its rows explicitly. |
| Behavior impact | Verification output changes; no audit write behavior change in production. |
| Regression test | Disposable DB with one NULL-hash row: assert it is disclosed and `verified` reflects the chosen policy. |
| Rollback | Revert the verifier/demo hunks. |
| Owner gate | **R4 if verification semantics change**; R2 for demo script only. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-07 — Remove or delegate stale chain verifier (AUD-F07)

| Field | Plan |
|---|---|
| Finding | `AUD-F07` — `scripts/dive.py:457-480` |
| Scope | Delete `check_hash_chain` or delegate to canonical `verify_audit_chain`. |
| Behavior impact | Tooling only. |
| Regression test | Assert the entry point returns canonical verification results. |
| Rollback | Revert the script hunk. |
| Owner gate | R0–R2; owner review before deployment. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-08 — SQLite dev/test append-only parity (AUD-F08)

| Field | Plan |
|---|---|
| Finding | `AUD-F08` — no SQLite trigger; tests mutate audit rows directly |
| Scope | Add SQLite triggers for dev/test parity **or** explicitly document the scope in verifier output. No production migration. |
| Behavior impact | Dev/test only; production is PostgreSQL. |
| Regression test | Disposable SQLite: assert UPDATE/DELETE rejected (or documented allowance) and verifier detects changes. |
| Rollback | Revert the dev/test hunk. |
| Owner gate | R2 for dev/test; **R4 if production behavior changes**. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-09 — Authoritative audit-surface registry (AUD-F09, AUD-F12, AUD-F13)

| Field | Plan |
|---|---|
| Findings | `AUD-F09` (domain stores), `AUD-F12` (DB-trigger `audit_log`), `AUD-F13` (`sndhs_audit_logs`) |
| Scope | Registry mapping every audit table/store to owner, writer, guard, verifier, immutability guarantee and retention decision. No behavior change. |
| Behavior impact | Documentation/registry only. Defines scope before any mirroring decision. |
| Regression test | Enumerate `__tablename__` containing `audit` and assert each is registered; assert no unregistered audit table. |
| Rollback | Remove the registry file/hunk. |
| Owner gate | R0–R2 for registry; **R4 for any subsequent mirroring into the canonical chain**. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-10 — Control-plane audit-log route contract (AUD-F10)

| Field | Plan |
|---|---|
| Finding | `AUD-F10` — `control_plane/routes.py:403-421` |
| Scope | Either wire to canonical query with authorization, or return explicit unavailable status; issue a dated documentation correction for the stale 503 claim. |
| Behavior impact | API contract change if wired. |
| Regression test | Assert documented response contract and permission enforcement. |
| Rollback | Revert route/documentation hunk. |
| Owner gate | **R4 if route behavior changes**; R1 for documentation. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-11 — Dormant platform audit registration (AUD-F11)

| Field | Plan |
|---|---|
| Finding | `AUD-F11` — `backend/app/platform/audit.py:28-105` |
| Scope | Remove the registration or mark it explicitly dormant in `PlatformRegistry` docs/tests. |
| Behavior impact | Dormant capability only; no active caller. |
| Regression test | Assert no dormant service is advertised as active. |
| Rollback | Revert the module hunk. |
| Owner gate | R2 documentation / **R4 if registration behavior changes**. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-12 — Clarify call-count methodology (AUD-F14)

| Field | Plan |
|---|---|
| Finding | `AUD-F14` — 203 AST / 206 textual / 200 filtered-textual |
| Scope | Publish the count methodology in `GULA_AUDIT_CALLSITE_MATRIX.md`; do not rewrite the accepted Review-3 report. |
| Behavior impact | None. |
| Regression test | AST test with explicit scope parameters. |
| Rollback | Documentation-only. |
| Owner gate | R1. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-13 — Fix invalid audit-call keywords on financial routes (AUD-F15)

| Field | Plan |
|---|---|
| Finding | `AUD-F15` — `backend/app/financial/routes.py:313,368` (HIGH when `ENABLE_FINANCIAL_ENGINE=true`) |
| Scope | Rename `entity_type`→`resource_type` and `entity_id`→`resource_id` at both sites; move the `log_action` call so audit and financial mutation commit in one transaction; add an AST test validating every `log_action` keyword against the canonical signature. |
| Behavior impact | Feature-flagged active financial path. Fixes a committed mutation with no audit record and the associated retry/double-charge risk. Owner must decide whether to enable the engine. |
| Regression test | AST signature test (would have caught this finding); disposable DB with flag enabled → POST transaction and run-cycle, assert one chained `audit_logs` row each, HTTP 200, no duplicate on a single request. |
| Rollback | Revert the single `backend/app/financial/routes.py` hunk; no migration, no protected-file or staging change. |
| Owner gate | **R4 — explicit owner authorization required** (audit behavior change on a financial path). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-14 — Stop suppressing MPI resolution failure (AUD-F16)

| Field | Plan |
|---|---|
| Finding | `AUD-F16` — `backend/app/services/patient_service.py:500-510` |
| Scope | After writing the `mpi_resolve_failed` audit event, re-raise or return an explicit degraded-result indicator instead of silently returning `(None, None)`. |
| Behavior impact | Active patient-creation path; changes API outcome on MPI failure. Keep the audit event in all cases. |
| Regression test | Force MPI failure in a disposable env; assert the audit row exists and the caller receives an explicit failure/degraded result; assert the success path still populates `citizen_ulid`. |
| Rollback | Revert the single `patient_service.py` hunk. |
| Owner gate | **R4 if failure behavior changes**; R2 for documentation only. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-15 — Stop silently swallowing password-reset audit failures (AUD-F17)

| Field | Plan |
|---|---|
| Finding | `AUD-F17` — `backend/app/routes/password_reset.py:52-53,80-81` |
| Scope | Remove `contextlib.suppress(Exception)` around both `log_action` calls; fail closed or write to a durable retry path with an alert; consider auditing before commit so audit and credential change share a transaction. |
| Behavior impact | Active pre-auth/password-reset endpoints. Audit failures become observable (and may fail the request). Owner must accept the availability trade-off on an authentication path. |
| Regression test | Force `log_action` to raise in a disposable env; assert failure is observable (exception or alert metric); assert a successful reset writes a chained row with the correct action. |
| Rollback | Revert the single `password_reset.py` hunk; no migration, no protected-file or staging change. |
| Owner gate | **R4 — explicit owner authorization required** (audit failure behavior on an authentication path). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-16 — Make identity denial-path audit failures observable (AUD-F18)

| Field | Plan |
|---|---|
| Finding | `AUD-F18` — `b4_guard.py:156-159`, `step_up_service.py:153-156`, `authorization_decision.py:601-604` |
| Scope | Add structured log/metric on denial and failed-step-up audit failures; owner decision on fail-closed vs durable buffer for denials. Keep successful privileged paths fail-closed. |
| Behavior impact | Active identity authorization paths; denial outcomes may change if fail-closed is chosen. |
| Regression test | Force identity audit sink to raise on a denial; assert alert/metric emitted and policy holds; assert successful privileged access still fails closed. |
| Rollback | Revert the three targeted hunks independently. |
| Owner gate | **R4 — explicit owner authorization required** (identity audit failure policy). |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-17 — Define communication sink failure policy (AUD-F19)

| Field | Plan |
|---|---|
| Finding | `AUD-F19` — `shared/communication/audit.py:94-110`, `backend/app/communication/__init__.py:104-145`, `shared/communication/center.py:551-555` |
| Scope | Single audit-sink failure policy: metric/alert on any sink failure, explicit registration of `NullAuditSink`, document which events require the durable sink. |
| Behavior impact | Active communication paths; failure observability improves, delivery behavior unchanged. |
| Regression test | Force each sink to raise; assert metric emitted and documented policy holds; assert no silent discard unless `NullAuditSink` explicitly configured. |
| Rollback | Revert targeted sink hunks. |
| Owner gate | **R4 decision** on policy; R2 for observability-only changes. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-18 — Resolve FHIR decorator audit scope (AUD-F20)

| Field | Plan |
|---|---|
| Finding | `AUD-F20` — `backend/app/audit/__init__.py:23` (wrapped function runs outside `try`) |
| Scope | Owner decision: keep success-only semantics and document explicitly, or add explicit failure-event auditing around the wrapped call. |
| Behavior impact | Active FHIR create/update/delete paths if failure auditing is added. |
| Regression test | Force wrapped function to raise; assert behavior matches the chosen documented policy. |
| Rollback | Revert the decorator hunk. |
| Owner gate | **R4 scope decision** before any behavior change. |
| Status | `PREPARED — NOT IMPLEMENTED` |

### P-19 — Correct pool/isolation documentation drift (AUD-F21)

| Field | Plan |
|---|---|
| Finding | `AUD-F21` — `docs/decisions/OPERATIONS_DECISIONS.md:35-40` vs `backend/app/database.py:188-192` |
| Scope | Make source defaults and ADR agree; add a test comparing documented constants with `database.py` defaults. |
| Behavior impact | Documentation only; no audit or connection behavior change. |
| Regression test | Unit test comparing documented values with source defaults. |
| Rollback | Revert the documentation hunk. |
| Owner gate | R1/R2 documentation; no audit behavior change. |
| Status | `PREPARED — NOT IMPLEMENTED` |

---

## 3. Sequencing (all subject to owner authorization)

| Phase | Packages | Rationale |
|---|---|---|
| 1 — Highest integrity value, lowest active risk | P-01, P-04, P-12, **P-19** | Remove dormant bypass and false alarms; clarify evidence and documentation. No active audit behavior change. |
| 2 — Active-path safety | **P-13, P-15, P-16**, P-02, P-03, P-14 | P-13 is the only active HIGH finding (feature-flagged); P-15/P-16 are silent suppression on authentication/identity paths; then owner decisions on audit-failure availability, control-plane scope and MPI failure semantics. |
| 3 — Verification completeness | P-05, P-06, P-07, P-08 | Improve evidence quality; R4 decisions where semantics change. |
| 4 — Scope and sink policy | P-09, P-10, P-11, **P-17, P-18** | Define the audit surface, sink failure policy and decorator scope before any consolidation mirroring. |

**No phase is authorized to begin without an explicit, package-specific owner decision.** OD-001 acceptance covers only the SEC-015/F-01 engineering scope and does not authorize any package above.

---

## 4. Global rollback and safety rules

1. Every package is independently reversible with a single targeted revert.
2. No package touches the 20 staged `R100` renames, the three protected MD5s, or `GOVERNANCE/FINAL_DECISION.md`.
3. No package introduces a migration without a separate owner decision and a forward-only, backwards-compatible design.
4. No package weakens `_require_audit_safe_isolation`, the advisory lock, the hash-chain computation, or any existing assertion.
5. No implementation in disposable environments may contact production services or use PHI/secrets.
6. After any authorized implementation: targeted tests only in a disposable isolated environment; record commands, versions, exit codes and counts; `git diff --check`; protected-MD5 recheck; `make brain` on structural changes.
7. No commit, push, merge, PR, rebase or deployment under this roadmap.

---

## 5. Acceptance gate for this roadmap

This roadmap is **accepted as prepared** only if: every package names its finding, impact, regression test, rollback and owner gate; no package is marked implemented; release posture is unchanged; and all repository invariants pass. The roadmap does **not** itself authorize remediation.

**Status:** `PENDING OWNER ACCEPTANCE` — no R4 implementation authorized.
