# A07 — Backend, API & Database Audit: BACKEND AUDIT

**Agent:** A07 (Backend, API & Database Auditor) · **Program:** PROGRAM-GULA-PARALLEL-001
**Wave:** A (READ-ONLY AUDIT) · **Date:** 2026-11-19
**Status:** REVIEW-ONLY — no source/config file was modified; no git state changed; no database/service/migration was executed.

---

## 1. Scope & Method

| Item | Detail |
|---|---|
| Primary read scope | `backend/app/` (structure, Pydantic validation, error handling, session/transaction management, query performance, `lab_id` tenant isolation, factory/middleware wiring) |
| Files read in depth | ~35 (`config.py` excerpts, `database.py`, `factory.py`, `main.py`, `middleware.py` excerpts, `core/error_contract.py`, `security/dependencies.py`, 4 route modules, 6 model modules, 8 untracked + 8 modified migrations, 4 contract modules, 5 policy docs) |
| Files mechanically scanned | 63 `backend/app/routes/*.py` modules (grep/heuristic), 109 `backend/migrations/versions/*.py` files (static AST-lite parse of `revision`/`down_revision`), all 5 control documents |
| Excluded from writes | All source, config, migration, route, model, contract and policy files. 378→379 pre-existing changed paths are USER WORK (see §5). |
| Tooling | Read-only `read`/`grep`/`glob`, read-only `git` (`status`, `ls-tree`, `diff --stat`, `rev-list`, `merge-base`), and in-memory Python text parsing. **No** `alembic`, no DB connection, no service start. |

### 1.1 Baseline policy understood

- `CLAUDE.md:315-327` — Migration Policy: existing migrations immutable; base schema `20250322_0000_create_base_schema.py` immutable; every migration idempotent; new columns nullable or `server_default`.
- `CLAUDE.md:341-353` — Security Invariants: all patient-data queries filter `lab_id = current_user.lab_id`; patient-card HMAC verified before data return.
- `CLAUDE.md:365-372` — Human approval required for auth logic, API response-shape changes, DB schema changes.
- `docs/constitution/15_DATABASE_CONSTITUTION.md` — DB constitution (§7 cascade rule at line 19; §19 N+1 prevention).
- `PROGRAM_CONTROL.md:58-75` — 378 paths of protected user work; `FILE_OWNERSHIP_MATRIX.md:69-79` — A07 is reviewer only.

---

## 2. Architecture & Wiring — Verified Controls (positive findings)

These are confirmed correct and should be preserved; they are **not** defects.

| Control | Evidence | Note |
|---|---|---|
| Lifespan pattern (no `@app.on_event`) | `backend/app/factory.py:839-917` | Complies with `CLAUDE.md:110-123`. |
| Centralised exception translation (domain / HTTP / validation / catch-all) | `backend/app/factory.py:1147-1150`, handlers at `:970-1094` | Canonical envelope `build_error_payload` (`core/error_contract.py:55-82`) keeps `detail`/`detail_ar` legacy fields. |
| Validation errors never echo submitted values | `core/error_contract.py:31-52`; `factory.py:1018-1037` | Only `loc`, `type`, `msg` retained. |
| CORS defensive checks | `factory.py:467-470` | Rejects `*` with credentials; production requires HTTPS origins. |
| Tenant-scoped reads in patient services | `services/patient_service.py:83,122,170,267,318-321,351-359,390-407` | `lab_id` consistently applied. |
| Patient-card HMAC + issuing-lab binding | `routes/patient_card.py:64-68,128,144-158` | `token_lab_id != current_user.lab_id` → 403 with audit. Good reference implementation. |
| DB statement/idle-in-transaction timeouts | `database.py:229-239` | `statement_timeout`, `work_mem=16MB`, `idle_in_transaction_session_timeout=60s`. |
| Pool budget documented and env-configurable | `database.py:180-204`; `CLAUDE.md:180-184` | Current default `2 × (5+10) = 30` connections (comment at `:186` still says `2×(5+15)=40` — stale comment, P3 housekeeping). |
| Read-replica engine with primary fallback | `database.py:244-271,380-394` | Good; fallback is silent (see A07-006). |
| `X-API-Version` response header emitted | `backend/app/middleware.py:200` | Exposed through CORS at `factory.py:492`. |

---

## 3. Findings

Severity: **P0** halt / **P1** critical / **P2** major / **P3** minor.
Every finding: ID, Severity, Title, Evidence, Affected components, Root cause, Safe-fix possible?, Approval required?.

### A07-001 — P1 — `get_current_user` return type is unsound against route annotations; `lab_id` may be `None` or cross-domain

- **Evidence**
  - `backend/app/security/dependencies.py:36` — `def get_current_user(...) -> LabUser | User:`
  - `backend/app/security/dependencies.py:138-141` — `_user_id_var.set(user.id); _lab_id_var.set(user.lab_id)`
  - `backend/app/models/user.py:20` — `lab_id = Column(Integer, ForeignKey("labs.id", ondelete="SET NULL"), nullable=True)`
  - `backend/app/models/lab_user.py:15` — `lab_id ... nullable=False`
  - Route annotations assume `LabUser`: `backend/app/routes/stats.py:15,22-25`; `patients.py:168,185`; `results.py:332`; `admin.py:296` (etc. — most 63 route modules follow this pattern).
  - `backend/app/security/dependencies.py:143-155` only enforces `require_institutional_user()` on device endpoints, not on lab-scoped routes.
- **Affected components:** auth dependency, all lab-scoped routes, stats, patients, results, admin, DB error-correlation context.
- **Root cause:** A single dependency serves two disjoint account families with independent primary-key spaces (`LabUser` vs `User`); the `User` family has a nullable, semantically different `lab_id`. Static type annotations claim `LabUser`, so no type checker or reviewer sees the mismatch. A citizen `User` token that satisfies `decode_token`/`perm_version` and reaches a lab-scoped route will pass `lab_id=None` (or a non-lab-scoped value) into a service filter.
- **Impact:** Tenant-filter correctness depends entirely on service-layer behaviour; `lab_id=None` can produce empty results or, if a service omits the filter for `None`, cross-tenant reads. Also corrupts the DB error-correlation `lab_id`.
- **Safe-fix possible?** **No** — fixing means either (a) introducing a separate `get_lab_user` dependency and re-annotating/re-wiring many routes, or (b) adding a hard runtime guard in `get_current_user`. Both change auth behaviour. Static-analysis-only plan required.
- **Approval required?** **YES** — auth/RBAC behaviour change and tenant-isolation semantics (`CLAUDE.md:365`, `AGENT_ASSIGNMENTS.md:47`). Cross-reference **A04** (Security & Identity) before any action.
- **Remediation plan (review only):** 1) Inventory every route annotated `current_user: LabUser` and classify which genuinely require institutional accounts. 2) Add explicit `Depends(require_institutional_user)` to those routes (or a dedicated dependency factory) rather than relying on annotation. 3) Add a test matrix asserting a citizen `User` token receives 403 on all lab-scoped routes. 4) Re-check `_lab_id_var` is set only for institutional accounts. Do **not** change token claim resolution here.

### A07-002 — P2 — Validation asymmetry: `PatientUpdate` accepts values that `PatientCreate` rejects; phone normalization validates one form and stores another

- **Evidence**
  - `backend/app/routes/patients.py:44-125` — `PatientCreate` validates `full_name`, `phone`, `gender`, `birth_date`, `email`, `national_id`, `family_id`.
  - `backend/app/routes/patients.py:132-159` — `PatientUpdate` validates **only** `full_name` and `family_id`; `phone`, `birth_date`, `gender`, `email` are unvalidated.
  - `backend/app/routes/patients.py:57-60` — validator regex-checks `cleaned = re.sub(r"[\s\-\+]", "", v)` but **returns `v`**, so the un-normalized string is persisted.
  - `backend/app/services/patient_service.py:407` — phone lookup is an exact match `Patient.phone == phone`.
  - `backend/app/models/patient.py:13-16,39` — `Gender` enum is `M`/`F`, column `gender = String(1)`; create validator (`:65`) also accepts `"male"`/`"female"` (4–6 chars).
- **Affected components:** `POST /patients`, `PUT /patients/{id}`, `GET /patients` search, phone-based duplicate detection, MPI linkage.
- **Root cause:** Two independent Pydantic models with duplicated-but-divergent validators; no shared base schema. Normalization is computed for validation but discarded.
- **Impact:** Clients can PUT a malformed phone/date/email; stored phones with separators will not match exact phone lookups (duplicate detection / family matching can silently miss); `gender` values diverge across create/update paths.
- **Safe-fix possible?** **Partially** — extracting shared validators into a reusable schema is source-safe in principle, but any behaviour change to accepted inputs is an API-contract change.
- **Approval required?** **YES** — request/response contract change affects mobile/frontend clients (`CLAUDE.md:369`).
- **Remediation plan:** 1) Factor validators into a shared mixin used by both create and update models. 2) Decide explicitly whether to normalize phone on write (requires a data backfill + dedup analysis) or reject non-canonical input. 3) Add contract tests asserting create/update accept the same value set. 4) Align `Gender` enum with accepted wire values and the widened DB column (see A07-017 in `DATABASE_MIGRATION_AUDIT.md`).

### A07-003 — P2 — N+1 query pattern in paginated pending-labs list

- **Evidence**
  - `backend/app/routes/admin.py:270` — `labs = query.order_by(...).offset(skip).limit(limit).all()`
  - `backend/app/routes/admin.py:273-276` — `for lab in labs:` followed by `db.query(LabUser).filter(LabUser.lab_id == lab.id, LabUser.role == "admin").first()`
  - Policy: `docs/constitution/15_DATABASE_CONSTITUTION.md:31` (§19: "N+1 query patterns are prevented through eager loading and joined queries").
- **Affected components:** `GET /admin/labs/pending` (verify exact path at `admin.py:250-255`), DB pool under admin load.
- **Root cause:** Per-row ORM query inside a loop instead of one aggregate/joined query.
- **Impact:** `limit + 1` queries per request; degrades linearly with page size and adds avoidable pool pressure. Not exploitable as-is (admin-only), so P2.
- **Safe-fix possible?** **Yes** — replace with a single `query(Lab, LabUser).outerjoin(...)` or one `in_()` batch query; response shape unchanged.
- **Approval required?** **No** for an internal query rewrite that preserves the response shape; **Yes** if the file is user-modified (verify `git status --porcelain -- backend/app/routes/admin.py` at Wave C — `PROGRAM_CONTROL.md:53` lists 126 modified backend files).
- **Remediation plan:** 1) Confirm `admin.py` is clean before Wave C. 2) Batch-load admin users with `Lab.id.in_([...])`. 3) Add a query-count regression test (`SQLAlchemy event` counter) asserting ≤2 queries for a 50-lab page.

### A07-004 — P3 — Correlation `ContextVar`s are set inside a synchronous dependency (threadpool) and may not reach the event-loop context

- **Evidence**
  - `backend/app/security/dependencies.py:138-141` — `_user_id_var.set(...)`, `_lab_id_var.set(...)` inside `def get_current_user(...)` (sync, so FastAPI runs it in a worker thread via `run_in_threadpool`).
  - `backend/app/database.py:21-24,459-462` — vars read in `check_db_connection_detail()`.
  - `backend/app/database.py:18-20` — comment states middleware sets `request_id`/`endpoint` and `get_current_user` sets `user_id`/`lab_id`.
- **Affected components:** DB error logs, incident correlation, `_health_alert_loop` diagnostics.
- **Root cause:** `contextvars.ContextVar` writes made in a threadpool worker thread do not propagate back to the event-loop task's context. (This is a well-known anyio/FastAPI behaviour — **labelled as high-confidence inference from code structure**, not proven by runtime test; no service was started.)
- **Impact:** DB error logs may carry `user_id=None`, `lab_id=None` even on authenticated requests, weakening audit correlation.
- **Safe-fix possible?** **Yes** at the code level (set the vars in async middleware after route resolution or pass explicit context), but it touches shared infrastructure.
- **Approval required?** **YES** — logging/observability behaviour change in a healthcare platform, and likely overlaps A04/A08 ownership.
- **Remediation plan:** 1) Verify with a focused unit test using `anyio.to_thread.run_sync` that the value is absent in the parent context. 2) If confirmed, move propagation to an async middleware that reads the authenticated principal from `request.state`. 3) Preserve current log field names.

### A07-005 — P3 — `create_app(override_mode=...)` mutates global `os.environ["RUNTIME_MODE"]` without restoring it

- **Evidence**
  - `backend/app/factory.py:1097-1106` — `if override_mode: os.environ["RUNTIME_MODE"] = override_mode`
  - `backend/app/config.py` imports `RUNTIME_MODE` at module load (`factory.py:24`), so the env write does not reliably re-drive imported constants; it only affects downstream `os.getenv`/`_is_openapi_mode` paths that read the env lazily.
- **Affected components:** in-process test runners, OpenAPI export tooling, any caller using multiple `create_app` modes in one process.
- **Root cause:** Global mutable process state used as a mode switch; imported constants and lazy env reads can disagree.
- **Impact:** Mode leakage between app instances; an `openapi`-mode app can leave later instances behaving inconsistently.
- **Safe-fix possible?** **Yes** — pass mode explicitly through a local context object instead of env, or save/restore the env var with a `try/finally`.
- **Approval required?** **No** (internal tooling behaviour), but overlaps A09 test tooling — log a SCOPE_REQUEST if the fix touches test fixtures.
- **Remediation plan:** 1) Replace env mutation with an explicit `runtime_mode` parameter threaded into the `_is_*_mode()` helpers. 2) If env must stay, restore the prior value in `finally` at app creation. 3) Add a test creating `openapi` then `production` apps in one process.

### A07-006 — P3 — Read-replica fallback to primary is silent

- **Evidence**
  - `backend/app/database.py:247-271` — on replica creation failure, `read_engine = None`; `ReadSessionLocal = sessionmaker(bind=read_engine or engine)`.
  - `backend/app/database.py:586-616` — `get_pool_status()` reports `read_replica_enabled: READ_REPLICA_ENABLED and read_engine is not None`, but no per-request signal is emitted.
- **Affected components:** analytics/reporting routes using `get_read_db()`, capacity planning.
- **Root cause:** Fail-open fallback with only a startup warning log.
- **Impact:** Under replica failure, all "read-only" load silently returns to the primary; combined with a slow-primary scenario this can amplify latency. This is a capacity/observability concern, not a data-integrity issue.
- **Safe-fix possible?** **Yes** — add a response header or metric counter for `read_source=replica|primary`.
- **Approval required?** **No** for a metric; **Yes** if adding a client-visible header (API contract).
- **Remediation plan:** expose a Prometheus counter `gula_read_db_fallback_total` (coordinate with A08) rather than a new HTTP header.

### A07-007 — P3 — Phantom `__all__` entry in `app.models`

- **Evidence**
  - `backend/app/models/__init__.py:62` — `"Appointment",` listed in `__all__`.
  - No `Appointment` import or definition exists anywhere in `backend/app/models/__init__.py` (full file read: lines 1–110).
  - No `from app.models import *` found in `backend/` (grep), so currently latent.
- **Affected components:** `app.models` package, tooling/REPL users, any future star import.
- **Root cause:** `__all__` drifted after a model was removed/renamed.
- **Impact:** `from app.models import *` raises `AttributeError: module 'app.models' has no attribute 'Appointment'`.
- **Safe-fix possible?** **Yes** — remove the stale entry (one-line edit).
- **Approval required?** **No**, provided `git status --porcelain -- backend/app/models/__init__.py` is clean.
- **Remediation plan:** 1) Confirm no external consumer expects `Appointment`. 2) Delete the `__all__` entry. 3) Add an import-smoke test (`import app.models; from app.models import *`).

---

## 4. Cross-cutting observations (no finding ID)

1. **Factory wiring is broad but fragile.** `_register_routes()` (`factory.py:519-836`) imports ~80 route modules unconditionally; one import-time error prevents app creation. `openapi` mode skips only a handful of DB-heavy modules (`:669-671`, `:718-722`), so the OpenAPI surface depends on importable DB/AI code. No static finding — noted for A01 architecture context.
2. **Error handling is well centralised** (`factory.py:970-1094`) with a deliberate distinction between production (no stack traces) and development (logged exceptions). No stack-trace leakage found.
3. **Transaction boundaries** are service-layer `db.commit()` calls (e.g., `patient_service.py:243,302`), with `get_db()` rollback-on-exception (`database.py:284-298`). No leaked-session path found in the sampled routes. Read-replica sessions use the same cleanup pattern.
4. **`lab_id` is explicitly threaded** through service calls in every sampled patient/result/stat route. The residual risk is A07-001 (principal type), not a missing filter in the sampled code.
5. **Query performance**: `citizen_portal.py:314-326,373-389` correctly uses `joinedload`; `patient_service.py:329-332` batches order statistics with `in_()`; the confirmed N+1 is A07-003.
6. **PostgreSQL version drift** between `CLAUDE.md:16` (PG17) and `docs/constitution/15_DATABASE_CONSTITUTION.md:6` (PG16) is recorded in `DATABASE_MIGRATION_AUDIT.md` (A07-019) to avoid duplication.

---

## 5. Protected user work encountered (report only — NOT touched)

- 8 untracked migrations: `20261114_0001..0006_unify_*`, `20261118_0001_oauth2_account_kind.py`, `20261119_0001_niam_step_up_events.py` (`PROGRAM_CONTROL.md:121-125`).
- 8 **modified tracked** migrations (not listed in PROGRAM_CONTROL §2.6): `git diff --stat -- backend/migrations/versions/` shows changes to
  `20260324_0006_patient_family_guardian.py`, `20260324_0009_audit_chain_hash_result_engine_version.py`, `20260324_0010_production_indexes.py`, `20260716_0003_pharmacy_platform.py`, `20260716_0004_radiology_platform.py`, `20260814_0002_organization_structure.py`, `20260815_0023_drug_substitution.py`, `20260820_0004_surgical_safety_checklists.py` (141 insertions, 42 deletions). These are unstaged user edits to already-merged migrations — a policy concern raised in `DATABASE_MIGRATION_AUDIT.md`.
- Working-tree count at audit time: **379** porcelain entries vs **378** at Phase 0 (`PROGRAM_CONTROL.md:52`); the delta is outside this agent's write set (A07 wrote only its three owned report files). No git state was changed by A07.

---

## 6. Remediation plan summary (PLANS ONLY — no edits performed)

| Finding | Plan owner (proposed) | Wave C eligibility | Gate |
|---|---|---|---|
| A07-001 | A04 + A07 review | **BLOCKED** | Auth-behaviour approval; route files may be user-modified |
| A07-002 | A07 plan / A09 tests | **BLOCKED** | API contract approval; `patients.py` clean check |
| A07-003 | A07 | **BLOCKED** | `admin.py` clean check; no response-shape change |
| A07-004 | A07 + A08 | **BLOCKED** | Observability approval; cross-agent scope |
| A07-005 | A07 | **BLOCKED** | Verify clean; A09 test coordination |
| A07-006 | A08 (metrics) | **BLOCKED** | A08 ownership; metric-only variant needs no API approval |
| A07-007 | A07 | **BLOCKED** | Verify `__init__.py` clean |

All Wave C remediation remains **BLOCKED** by `PROGRAM_CONTROL.md:150` (no approved register, no confirmed ownership, no clean-file verification). A07 is a reviewer only (`AGENT_ASSIGNMENTS.md:19,66`).

## 7. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A07-01 → Orchestrator/A04:** Request A04's findings on `get_current_user` account-domain resolution before any tenant-filter change (A07-001).
2. **SCOPE_REQUEST-A07-02 → Orchestrator/A09:** Request a contract test for create/update validation parity and an N+1 query-count test (A07-002, A07-003).
3. **SCOPE_REQUEST-A07-03 → Orchestrator/A08:** Request read-replica fallback metric ownership (A07-006).
4. **SCOPE_REQUEST-A07-04 → Orchestrator:** Confirm whether the 8 modified tracked migrations constitute user work to be preserved verbatim; A07 recommends preservation and a new forward migration instead of rewriting them.

---

*End of BACKEND_AUDIT.md. Companion reports: `API_CONTRACT_AUDIT.md`, `DATABASE_MIGRATION_AUDIT.md`.*
