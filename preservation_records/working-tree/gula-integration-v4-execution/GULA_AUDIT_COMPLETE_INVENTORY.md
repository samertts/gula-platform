# GULA AUDIT COMPLETE INVENTORY — COMPREHENSIVE REVIEW

**Directive:** `GULA-AUDIT-COMPREHENSIVE-REVIEW` (owner-authorized, 2026-11-20)
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Baseline HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling repository:** `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91` (read-only, untouched)
**Method:** read-only static inventory (source, migrations, SQL, scripts, tests). No production service, DB or Redis access. No test suite run in this workstream.
**Release posture:** **HOLD** — Stable v1.0.0 **NOT declared** — `PRODUCTION READY` **NOT authorized** — `production_ready_items = 0`.

Companion deliverables: `GULA_AUDIT_CALLSITE_MATRIX.md`, `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`, `GULA_AUDIT_SECURITY_FINDINGS.md`, `GULA_AUDIT_REMEDIATION_ROADMAP.md`, `GULA_AUDIT_ACCEPTANCE_CRITERIA.md`.
**Governance reference:** `OD-001` is recorded `ACCEPTED` in `GULA_OWNER_DECISION_REGISTER.md` for the defined SEC-015/F-01 engineering scope only, on the authority of `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md` (MD5 `329049ee6bed006901660e43b2d4b995`). This inventory does not reopen that acceptance or extend it to release readiness; all findings below are separately scoped observations.

---

## 1. Scope, authority and reachability vocabulary

**Authorized:** R0–R2 read-only/autonomous inventory; R3 disposable-isolated probes only; R4 report-only preparation (no implementation without explicit owner authorization); R5 prohibited.

**Reachability labels used throughout:**
- `ACTIVE` — wired into a live request/startup path; evidence names the importer, registration or route.
- `DORMANT` — code exists but no live caller/wiring found; evidence names the absence and any recorded dormancy decision.
- `UNKNOWN` — evidence insufficient to decide without execution or unavailable deployment context; never treated as harmless.
- `MANUAL` — standalone script/CLI with no automatic scheduler or CI invocation found.

**Dormant ≠ harmless.** Dormant writers are recorded as latent bypasses with an owner decision requirement.

---

## 2. Canonical audit path (baseline)

| Item | Evidence |
|---|---|
| Canonical writer | `backend/app/services/audit_service.py:256-332` — `AuditLog(...)` construction `:275`; `db.add`/`db.flush()` at `:309-310` (PostgreSQL) and `:326-329` (SQLite) |
| Model / table | `backend/app/models/audit_log.py:10-27` → `audit_logs` |
| Isolation guard | `_require_audit_safe_isolation()` `:74-117`; invoked **only in the PostgreSQL branch** at `:293`; checks live `READ COMMITTED`, configured isolation, and DBAPI `autocommit`; fails closed via `AuditChainIsolationError` (`:68-71`) |
| Chain serialization | PG advisory transaction lock `:297-300`; SQLite no-op write reservation `:318` (no isolation guard) |
| Chain hash | `_compute_chain_hash` `:162-175` (JSON-sorted payload, canonical UTC timestamp `:120-134`) |
| Predecessor read | `_get_last_chain_hash` `:178-184` (genesis `"0"*64`) |
| Anchor checkpoint | `_write_anchor` `:187-197`, every 100 entries `:331-332`; HMAC verification `:154-159`, `:199-253` |
| Verification | `verify_audit_chain` `:335-367`; **skips `chain_hash IS NULL` rows** at `:345-347` |
| Immutability (PG only) | `backend/migrations/versions/20250322_0002_perf_indexes_audit_protection.py:78-103` (`trg_audit_logs_no_update`, `trg_audit_logs_no_delete`); `backend/app/core/startup_guard.py:674-699`; `config/postgres/audit.sql:117-142` |

**Commit responsibility:** `log_action` flushes but does **not** commit. The caller owns the commit. This is why an internal `commit()` in any alternative writer is a transaction-boundary defect (see §4 A1).

---

## 3. Canonical call sites (summary)

AST-based enumeration from the prior focused review found **203 direct `log_action(...)` calls in 56 files**. A separate text scan in this review found 200 calls in 54 backend modules after excluding tests, `def` declarations and the unrelated NHOP `log_action`; the difference is scope/filter methodology, reconciled in `GULA_AUDIT_CALLSITE_MATRIX.md`.

Representative high-volume sites: `backend/app/routes/login.py:103` (×11), `backend/app/nhdw/services.py:85` (×24), `backend/app/routes/admin.py:197` (×12), `backend/app/services/hospital_service.py:70` (×10), `backend/app/routes/ai.py:659` (the `AUDIT-BYPASS-001` repair). Every canonical call inherits the guard; suppression is determined by the enclosing handler (see `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`).

**Indirect wrappers:** `backend/app/audit/__init__.py:18-67` (`@audit_log` → `log_action` `:45`, commit `:59`), `backend/app/platform/audit.py:32-51`, `backend/app/audit/audit_log.py:6` re-export, `shared/communication/audit.py` bound via `backend/app/communication/__init__.py:112,124`.

---

## 4. Alternative audit writers (all bypass the canonical guard)

| ID | Path:line | Target store | Guard | Reachability / evidence |
|---|---|---|---|---|
| A1 | `shared/audit/service.py:36-62` — raw `INSERT INTO audit_logs` at `:44`, own `FOR UPDATE` predecessor read `:36-38`, own commit `:61` | `audit_logs` with **incompatible columns** (`entity_type`, `entity_id`, `previous_hash`, `timestamp`) | No | **DORMANT.** Callers: `backend/app/control_plane/audit.py:40`, `shared/audit/service.py:143`; wired only as optional singleton (`backend/app/control_plane/sdk.py:50,60,132`). No `set_audit()` caller; `backend/app/control_plane/routes.py:412-414` returns `{"entries": [], "note": "Audit service not initialized"}`. Schema mismatch: no migration adds these columns to `audit_logs` (only `chain_hash` at `20260324_0009:44`, `lab_id` at `20260813_0001`). Latent chain fork + premature commit if activated. |
| A2 | `config/postgres/audit.sql:41-73` — `audit_trigger_function()`, `INSERT INTO audit_log` at `:64`; row triggers `:75-103` on `patients`, `test_orders`, `test_results`, `samples`, `users` | `audit_log` (singular), DDL `:9-31` | No | **ACTIVE on fresh full-compose DB bootstrap only** (`docker-compose.full.yml:39` mounts to `/docker-entrypoint-initdb.d/02-audit.sql`). No application writer; independent store, no hash chain, not covered by canonical verification. |
| A3 | `scripts/generate_demo_data.py:761-778` — ORM `AuditLog(...)` at `:767` | `audit_logs` | No — no `chain_hash`, no guard | **MANUAL** (CLI at `:10-14`; no Makefile/CI reference). Inserts NULL-hash rows silently skipped by `verify_audit_chain:345-347`. |
| A4 | `gula_registration_portal.py:33-44` own SQLite schema; raw `INSERT INTO audit_logs` at `:85` | separate SQLite DB `/home/ubuntu/gula_users.db`, own columns | No | **MANUAL / standalone** (`__main__` demo `:105`; no importer found). Separate unchained store. |
| A5 | `nhop-platform/app/services/audit.py:13,23` — own `log_action`, `AuditLog(...)` at `:23` | `audit_log` (singular) in `nhop-platform/app/models/audit_log.py:18` | No — different signature | **DORMANT / archived** (`backend/app/domain_platform/config/dormancy.json:12` = `archived`, ADR-026). 13 calls in 4 NHOP modules are **not** the canonical function. |
| A6 | `backend/app/identity/services/audit_service.py:92,144`; `canonical_audit.py:145`, `session.add` `:175-178` | `niam_audit_entries` (`identity/models/audit.py:267`) | No — own chain, own verifier | **ACTIVE.** Separate chain; `canonical_audit.py:127` uses `with_for_update()`, older service does not. Not covered by canonical verification. |
| A7 | `backend/app/identity/api/audit.py:111-146` — export endpoint writes `DATA_EXPORT_REQUESTED`/`audit.export` | `niam_audit_entries` | No | **ACTIVE**, permission-gated (`audit.export` at `:120`). |
| A8 | `backend/app/identity/admin/services.py:493` — `PortalAuditLog(...)` | `niam_admin_audit_logs` (`identity/admin/models.py:60`) | No | **ACTIVE** admin subsystem; separate store. |
| A9 | `backend/app/services/mpi/resolver.py:172` — `MergeAudit(...)` | `mpi_merge_audit` (`services/mpi/models.py:192`) | No — own verifier `:262`, canonical cross-check `:284` | **ACTIVE.** |
| A10 | `backend/app/national/task_engine/application/service.py:327` — `TaskAuditLog(...)` | `national_task_audit_logs` (`.../infrastructure/models.py:126`) | No | Domain store; classified, not chained. |
| A11 | `backend/app/national/ecosystem/partners/service.py:410` — `PartnerAuditLog(...)` | `ecosystem_partner_audit_logs` (`.../models.py:73`) | No | Domain store; not chained. |
| A12 | `backend/app/billing/service.py:23`; `payments/service.py:85`; `payments/control_service.py:48` | `billing_audit_events`, `pay_audit_events` | No — ORM listeners enforce append-only (`billing/models.py:142-149`, `payments/models.py:313-325`) | **ACTIVE** financial domain stores. Forward migrations drop two of these tables (`20260814_0009:137`, `20260812_0005:147`). |
| A13 | `backend/app/services/clinical_service.py:930`; `authorization_service.py:447`; `governance/repositories/base.py:60` | `clinical_audit_records`, `authorization_audit`, `gov_*_audit*` | No | Domain stores; no canonical guard/verification. |
| A14 | In-memory/file harness stores: `backend/app/health_core/authorization/audit.py:108,129`; `health_core/reliability/audit.py:89,146`; `health_core/audit_anchor/store.py:33`; `health_core/audit_anchor/verification.py:85`; `health_data/governance/audit.py:83`; `national/security/audit.py:58`; `pharmacy/dispensing.py:425`; `security/integrity.py:27` | in-memory lists / append-only JSONL | No | **DORMANT harness** — no `health_core` wiring in `factory.py`, `routes/__init__.py`, `main.py`; confined to `backend/tests/health_core/*`. Accounting objects, not canonical persisted audit. |
| A15 | `shared/communication/audit.py:52-90` (`AuditEvent`/`AuditSink`/`LoggingAuditSink`) | log sink only | Wrapper: `backend/app/communication/__init__.py:112,124` binds canonical `log_action` | Active when composite sink configured; otherwise logging-only. |

---

## 5. Audit tables, models, triggers and mutability

- **Canonical `audit_logs`**: model `models/audit_log.py:10-27`; created `20250322_0000:244-267`; `chain_hash` added `20260324_0009:43-45`; `lab_id` added `20260813_0001:18-20`; indexes `20260720_0001:28`, `20260324_0010:67-70`.
- **PostgreSQL immutability**: three overlapping trigger declarations reject UPDATE/DELETE (`20250322_0002:90-103`, `startup_guard.py:688-695`, `config/postgres/audit.sql:134-142`).
- **SQLite**: **no append-only trigger**; direct UPDATE/DELETE possible. Tests exercise this (`backend/tests/unit/test_audit_chain_integrity.py:128,144,161`; `test_audit_chain_isolation_guard.py:357,365`, including `TRUNCATE` on PG at `:143`).
- **PG INSERT is not DB-guarded**: immutability triggers cover UPDATE/DELETE only; the isolation guard exists solely inside `log_action`'s PG branch.
- **`audit_log` (singular)**: DDL `config/postgres/audit.sql:9-31`, DB triggers on 5 business tables, immutability trigger `:126`. Separate NHOP table of the same name (A5).
- **`sndhs_audit_logs`**: append-only triggers + REVOKE in `20260505_0005:57-150`; **no application writer found** → dormant store.
- **Domain stores (A6–A13)**: no uniform DB-level immutability; some rely on ORM listeners or independent chains.
- **Runtime policy**: `backend/app/core/policy_engine.py:56,86` classifies `AUDIT_DELETE` as CRITICAL/never-allowed; `kernel/policy_runtime.py:205`. Operational guard, not a DB constraint.

---

## 6. Verification functions

| Function | Path:line | Target | Finding |
|---|---|---|---|
| `verify_audit_chain` | `services/audit_service.py:335-367` | canonical `audit_logs` | Authoritative; skips NULL-hash rows `:345-347` |
| `get_latest_anchor`, `_verify_anchor_hmac` | `services/audit_service.py:199-253`, `:154-159` | HMAC anchor files | Append-only by convention; written pre-commit |
| `audit_integrity` endpoint | `routes/compliance.py:678-699` (also `:731`, `:967`) | canonical | Read-only consumer |
| `scripts/audit_verifier.py:19-23,30` | verify_chain | canonical | **ALGORITHM MISMATCH** — pipe-delimited payload with `created_at.isoformat()`, omits `user_role`, `ip_address`, details, `lab_id`, and canonical timestamp canonicalization → would report **false tampering** on real canonical rows. Invoked by `scripts/gula_guardian.py:49-56` every 5 min if that daemon runs. |
| `scripts/dive.py:457-480` | `check_hash_chain` | canonical | **Stale** — checks non-existent `hash`/`prev_hash`/`data` columns; self-skips |
| NIAM verifiers | `identity/services/audit_service.py:162`; `identity/api/audit.py:150` | `niam_audit_entries` | Separate chain/schema |
| MPI verifiers | `services/mpi/resolver.py:262,284` | `mpi_merge_audit` + canonical cross-check | Separate |
| Harness verifiers | `health_core/*`, `health_data/governance/audit.py:83`, `national/security/audit.py:58`, `pharmacy/dispensing.py:425`, `security/integrity.py:27` | in-memory/domain | Independent algorithms; no canonical claim |

---

## 7. Exports, attachments, archival and retention

- `backend/app/identity/api/audit.py:111-146` — `GET /audit/export`, permission-gated, itself writes an audit entry.
- `backend/app/routes/admin.py:906` — `GET /audit-logs`, read-only with lab scoping.
- `backend/app/core/bootstrap/permissions.py:184` — `audit:export` permission.
- **No application-level retention, purge or delete routine for `audit_logs` was found.** The only deletion statements are in tests and in downgrade/projection migrations (A12). Anchors are monthly append-only files (`audit_service.py:137-146`). `scripts/sndhs_phase1_rollback.sql:50` contains rollback DDL for the SNDHS table.

---

## 7A. Administrative and control-plane audit reachability

| Path | Status | Evidence |
|---|---|---|
| `backend/app/control_plane/audit.py:26-124` — `EnterpriseAudit.log/query/log_deployment/log_config_change/log_policy_change/log_decision/log_incident` | **DORMANT** | Only import is `control_plane/sdk.py:6`; repo-wide `EnterpriseAudit(` → **zero** matches; `self._service` (`audit.py:28`) never used; helpers only call `self.log()` (`audit.py:74,85,96,107,118`) with no external callers. `log()` → raw `create_audit_entry` at `audit.py:40-48`. |
| `backend/app/control_plane/sdk.py:50,60-61,131-133` — `set_audit()` / `.audit` | **DORMANT** | `_audit = None` at `:50`; repo-wide `set_audit(` finds only the definition; no DI/factory/CLI/kernel/startup caller. |
| `GET /control-plane/audit-log` — `control_plane/routes.py:403-421` | **ACTIVE route, inert audit** | Mounted `factory.py:760-761`, read-role guard `routes.py:33-37,403`; handler returns `{"entries": [], "count": 0, "note": "Audit service not initialized"}` at `:412-413`; `sdk.audit.query(...)` at `:414-420` unreachable. `git show HEAD:` confirms unchanged. No test references this route. Note: `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md:135` describes a 503; that characterization is stale relative to current code and is recorded as a documentation discrepancy, not relied upon here. |
| Control-plane release approval / deployment — `control_plane/routes.py:317-400`, `release/manager.py:69-99` | **ACTIVE, no durable audit** | Only in-memory `approved_by`/`deployed_by` (`manager.py:36-37,74,86`) and `logger.info` (`manager.py:75,87,94`). No `EnterpriseAudit.log()` or `log_action()` anywhere in the control plane. `config/secrets.py:59-67::access_audit_log()` builds a dict with **zero callers**. |
| `backend/app/platform/audit.py:28-105` + `PlatformRegistry.register("audit", ...)` | **DORMANT** | `create_entry` correctly delegates to canonical `log_action` (`:42-51`), but no import of `app.platform.audit` exists outside the module itself; `factory.py:724-725` imports only `.platform.routes`; no `PlatformRegistry.get("audit")` call. |
| Admin audit read / mutation writes — `backend/app/routes/admin.py:905-947`, `log_action` at `:197,236,402,435,512,548,625,787,852,887,986,1012` | **ACTIVE** | Router mounted `factory.py:574,578-579`; `GET /admin/audit-logs` gated by `require_permission("audit:read")` at `:907`. Duplicate `backend/app/services/admin_service.py:444-479::get_audit_logs()` has no runtime caller (tests only). |
| NIAM administrative audit — `backend/app/identity/api/audit.py:77-162`, `identity/admin/routes.py:322-331` | **ACTIVE** | Router `audit.py:18`, mounted `factory.py:819-820`; permission checks `audit.py:93,120,157`; export writes its own event `audit.py:127-145`; separate `niam_audit_entries` store (A6/A7). |
| Compliance audit reads — `backend/app/routes/compliance.py:140-177,678-711,716+,937+` | **ACTIVE** | `verify_audit_chain` imported `compliance.py:38`; admin role check `:696-697`; mounted `factory.py:576,578-579`. |
| `@audit_log` decorator / communication sink | **ACTIVE** | Decorator `backend/app/audit/__init__.py:18-67` applied at `routes/ehr_fhir.py:1367,1391,1414`; sink `backend/app/communication/__init__.py:93-132` → `log_action` `:124-132`, bound `:238-260`, default `audit_enabled=True` (`shared/communication/config.py:49,65`), router mounted `factory.py:826-828`. |
| `backend/app/national/security/audit.py:32-66` — `SecurityAuditService` | **DORMANT** | In-memory hash chain; no instantiations; `national/api/routes/security.py:98-118` assembled only in `national/api/routes/__init__.py:20-36`, never included in `factory.py`. |
| Separate root `platform/` tree — `platform/domain/services/audit.py:6-72`, `platform/apps/modules/patient/handlers.py:4-22` | **UNKNOWN / DORMANT handler** | `log()` has no callers; handler never subscribed (`module.py:23-24` `on_start: pass`); tree boots only via `platform/entry.py:29-37`, while deployed backend uses `backend/start_railway.sh:19` (`app.main:app`). |

**No audit-writing middleware and no audit-writing background task were found.** This absence is explicit; it is not an assumption.

---

## 8. Verdict — can audit data be mutated outside the guarded path?

**Yes.** Concrete routes:
1. A1 `shared/audit/service.py:44` raw INSERT — bypasses guard and canonical schema (dormant but reachable via `EnterpriseAudit`).
2. A3 `scripts/generate_demo_data.py:767` NULL-`chain_hash` rows — invisible to canonical verification.
3. A2 `config/postgres/audit.sql:64` DB-trigger writes to a parallel store.
4. A4/A5 standalone and archived writers to separate stores.
5. **SQLite has no append-only trigger**; PG blocks UPDATE/DELETE but not INSERT outside `log_action`.
6. A6–A13 domain stores are written outside the canonical guard with independent or no verification.
7. **Audit events can be silently omitted on active paths** even when the canonical writer is correct: `password_reset.py:52-53,80-81` uses `contextlib.suppress(Exception)` with no logger (AUD-F17); identity denial/step-up paths suppress audit errors (AUD-F18); the FHIR decorator audits successful calls only (AUD-F20).
8. **Sink-layer loss:** the communication audit composite sink logs and continues on sink failure, and `NullAuditSink` explicitly discards events (AUD-F19).

This is an inventory verdict, not a claim of active exploitation. Severity, exploitability and owner gates are in `GULA_AUDIT_SECURITY_FINDINGS.md`; full per-path failure semantics are in `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`.

---

## 9. Command provenance

All inventory commands were read-only (`pwd`, `git rev-parse`, `git status --short`, `find`, `rg`, `sed`, `cat`, `md5sum`, `grep`, `wc`, `ls`). Full command list is retained in the agent evidence transcript; representative commands:

```bash
find . -path ./.git -prune -o \( -iname '*audit*' -o -iname '*ledger*' -o -iname '*immutable*' \) -type f -print | sort
rg -n -i 'INSERT[[:space:]]+INTO[[:space:]]+audit|UPDATE[[:space:]]+audit|DELETE[[:space:]]+FROM[[:space:]]+audit|TRUNCATE[[:space:]]+audit' .
rg -n '__tablename__\s*=\s*["'"'"'][^"'"'"']*audit' backend/app shared nhop-platform services platform
rg -n 'EnterpriseAudit|SharedAuditService|create_audit_entry|query_audit_log' backend/app shared scripts --glob '*.py'
git diff --cached --name-status | md5sum     # -> 56c524d6ffe9872c3a3ac6eff8c8f203
```

**Tool versions:** shell `rg`/`grep`/`find`/`sed`/`cat`/`md5sum` (system defaults); Python enumeration performed in a prior focused review with the pinned repo interpreter. No application test run in this workstream. Any earlier test counts (13/13 focused, 73/73 related, 12/12 PG16 guard) are **historical Review-3 evidence**, not fresh results for this review.

---

## 10. Invariant recheck at document creation

| Invariant | Expected | Observed | Result |
|---|---|---|---|
| Branch / HEAD | `integration/gula-unification-v1` / `2206654d…` | `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549` | PASS |
| Staged renames | 20 × `R100` | 20 × `R100` | PASS |
| Staged name-status MD5 | `56c524d6ffe9872c3a3ac6eff8c8f203` | `56c524d6ffe9872c3a3ac6eff8c8f203` | PASS |
| Protected MD5s | `effdfeaf…`, `1a02c015…`, `ea3969d0…` | exact match | PASS |
| `production_ready_items` | `0` (lines 480, 600) | `0` at both | PASS |
| Sibling HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | exact match | PASS |
| `git diff --check` | exit 0 | exit 0 | PASS |

**Status:** `HOLD`. No source, test, migration, config or staging change; no commit, push, merge, PR or deployment.
