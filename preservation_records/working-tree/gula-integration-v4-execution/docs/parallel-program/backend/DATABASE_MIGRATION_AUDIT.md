# A07 — Backend, API & Database Audit: DATABASE & MIGRATION AUDIT

**Agent:** A07 · **Program:** PROGRAM-GULA-PARALLEL-001 · **Wave:** A (READ-ONLY)
**Date:** 2026-11-19
**Status:** REVIEW-ONLY — **no** Alembic command, migration, database connection, or git state change was performed. All statements are from static file parsing and read-only git object-store queries.

---

## 1. Scope & Method

| Item | Detail |
|---|---|
| Read scope | `backend/migrations/versions/**` (109 `.py` files), `backend/app/database.py`, `backend/app/models/**` (core tables), `CLAUDE.md:180-184,284-294,315-327`, `docs/constitution/15_DATABASE_CONSTITUTION.md`, `docs/constitution/data_preservation/**`, `docs/constitution/23_BACKWARD_COMPATIBILITY.md`, `Makefile` backup targets, `.github/workflows` backup references. |
| Static parse | All 109 migration files parsed for `revision`, `down_revision`, idempotency guards, FK/index/`ALTER` statements. No execution. |
| Git queries (read-only) | `branch --show-current`, `rev-parse HEAD`, `rev-list --left-right --count HEAD...origin/main`, `merge-base HEAD origin/main`, `ls-tree -r --name-only <ref>`, `status --porcelain`, `diff --stat`, `diff`. |
| Explicitly NOT done | No `alembic upgrade/downgrade`, no `pg_dump`, no service start, no checkout/stage/merge/cherry-pick, no edit of any migration. |

### 1.1 Governing policy

- `CLAUDE.md:315-327` — **Migration Policy (MANDATORY)**: never modify an existing migration; all schema changes are new revisions; `20250322_0000_create_base_schema.py` immutable; every migration idempotent (`_has_column()`, `_table_exists()`, `_index_exists()`); new columns nullable or `server_default`; clean-DB test before PR.
- `docs/constitution/15_DATABASE_CONSTITUTION.md:19` — "Cascade delete is used carefully — **never cascade delete that would destroy patient data**."
- `docs/constitution/15_DATABASE_CONSTITUTION.md:26-29` — existing migrations immutable, idempotency guards, round-trip test.
- `docs/constitution/15_DATABASE_CONSTITUTION.md:35-42` — §19 N+1 prevention; §21 statement timeout.
- `docs/constitution/23_BACKWARD_COMPATIBILITY.md`, `data_preservation/**` — compatibility and DR policy baseline.
- `PROGRAM_CONTROL.md:58-75,107-125` — protected user work; verified migration numbers.

---

## 2. HIGH-RISK TRACK — Git history & migration divergence (independent verification)

### 2.1 Current git facts (re-verified 2026-11-19, read-only)

| Metric | PROGRAM_CONTROL §2.6 (Phase 0) | A07 re-verification | Agreement |
|---|---|---|---|
| Branch | `integration/gula-unification-v1` | `integration/gula-unification-v1` | ✅ |
| HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | same | ✅ |
| Divergence `HEAD...origin/main` | ahead 2 / behind 0 | `2  0` | ✅ |
| Merge-base | `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` | same | ✅ |
| Migrations tracked at HEAD | 101 | 101 | ✅ |
| Migrations at `origin/main` | 101 | 101 | ✅ |
| Migrations at merge-base | 101 | 101 | ✅ |
| Committed local-only / remote-only migrations | 0 / 0 | 0 / 0 (derived from 101=101=101 and clean 2-commit delta) | ✅ |
| `.py` files on disk in `backend/migrations/versions/` | 109 | 109 | ✅ |
| Untracked new migrations | 8 | 8 | ✅ |
| Working-tree porcelain entries | 378 (Phase 0) | **379** (audit time) | ⚠️ +1, outside A07 write set |

**Conclusion: PROGRAM_CONTROL §2.6 is CONFIRMED.** The brief's historical figures (57 / 101 / 50 / 7 / 51) remain stale and must not be repeated. There is **no committed migration divergence**, no divergent-history merge is required, and the local +2 commits are non-migration evidence tranches. No P0 on committed git history.

### 2.2 Additional fact not recorded in PROGRAM_CONTROL §2.6

Besides the 8 **untracked** migrations, **8 tracked migration files are unstaged-modified** (USER WORK). `git diff --stat -- backend/migrations/versions/` reports:

| File | Change |
|---|---|
| `20260324_0006_patient_family_guardian.py` | 19 +++--- |
| `20260324_0009_audit_chain_hash_result_engine_version.py` | 8 ++- |
| `20260324_0010_production_indexes.py` | 2 +- |
| `20260716_0003_pharmacy_platform.py` | 36 ++++---- |
| `20260716_0004_radiology_platform.py` | 24 ++++++- |
| `20260814_0002_organization_structure.py` | 2 - |
| `20260815_0023_drug_substitution.py` | 67 +++++++++- |
| `20260820_0004_surgical_safety_checklists.py` | 25 ++++-- |

Total: **141 insertions, 42 deletions**. Nothing is staged (`git diff --cached --stat` empty). These are modifications to **already-committed, already-merged migrations** — a direct conflict with `CLAUDE.md:321` if they were ever committed. Example: `20260815_0023_drug_substitution.py` gains `_align_catalog_identity()` (lines ~21-70 of the diff), an INTEGER→VARCHAR(26) one-way repair that drops and re-adds FKs by introspecting `pg_constraint`. Example: `20260324_0009` gains an `_index_exists()` guard in `downgrade()`. Both look like deliberate repair work, but **A07 did not modify, stage, or test them**.

- **Finding A07-014** (below) records this. It is **not** a P0 on history — it is a protected-user-work / policy-alignment item requiring user decision.

### 2.3 Static migration-chain integrity (all 109 files on disk)

| Check | Result |
|---|---|
| Files with a parseable `revision` literal | 109 / 109 |
| Duplicate `revision` IDs | **0** |
| `down_revision` values pointing to a missing revision | **0** |
| Base revisions (`down_revision` is `None`) | **1** — `20250322_0000` (`20250322_0000_create_base_schema.py`) |
| Heads on disk | **1** — `20261119_0001` (`20261119_0001_niam_step_up_events.py`) |
| Heads in tracked tree only (HEAD) | **1** — `20260908_0001` (`20260908_0001_merge_heads.py`) |
| Intentional merge revisions (tuple `down_revision`) | 4 — `20260815_0003`, `20260815_0015`, `20260819_0001`, `20260908_0001` |

**Conclusion:** No duplicate revision IDs and no `down_revision` chain break are visible statically. The 8 untracked migrations form a **clean linear extension** of the tracked head:

```
20260908_0001 (tracked HEAD/legacy head)
  └─ 20261114_0001_unify_foundation            [UNTRACKED]
     └─ 20261114_0002_unify_fk_indexes          [UNTRACKED]
        └─ 20261114_0003_unify_communication    [UNTRACKED]
           └─ 20261114_0004_unify_professional_identity [UNTRACKED]
              └─ 20261114_0005_unify_domain_platform    [UNTRACKED]
                 └─ 20261114_0006_unify_authorization_indexes [UNTRACKED]
                    └─ 20261118_0001_oauth2_account_kind [UNTRACKED]
                       └─ 20261119_0001_niam_step_up_events [UNTRACKED]  ← disk head
```

**P0 on migrations/history: NONE detected statically.** The risk is **governance**: a clean checkout of `origin/main` (or HEAD) stops at `20260908_0001`; any new migration authored against the on-disk head `20261119_0001` would have an unresolvable `down_revision` in that checkout. See A07-016.

---

## 3. Database integrity, indexes, constraints & backward compatibility — Findings

### A07-014 — P1 — `patients.lab_id` uses `ON DELETE CASCADE`: deleting a laboratory destroys patient and clinical data

- **Evidence**
  - `backend/migrations/versions/20250322_0000_create_base_schema.py:155` — `sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False)` in `patients`.
  - `20250322_0000...:185` — `lab_orders.patient_id` → `patients.id` `ondelete="CASCADE"`.
  - `20250322_0000...:219` — `lab_results.order_id` → `lab_orders.id` `ondelete="CASCADE"`.
  - ORM mirrors it: `backend/app/models/patient.py:27`, `lab_order.py:27`, `lab_result.py:31`; `Patient.orders` uses `cascade="all, delete-orphan"` (`patient.py:43`).
  - Policy: `docs/constitution/15_DATABASE_CONSTITUTION.md:19` — "never cascade delete that would destroy patient data"; `CLAUDE.md:342-345` data-integrity invariants.
- **Affected components:** `labs`, `patients`, `lab_orders`, `lab_results`, all clinical descendants, tenant offboarding flows, backup/restore.
- **Root cause:** Base schema chose referential convenience over data preservation. Because the base schema is immutable, the flaw is hereditary in every deployment.
- **Impact:** A single `DELETE FROM labs WHERE id = X` (operator action, tenant lifecycle code, or accidental admin tooling) irreversibly removes the lab's patients, orders and results. This is a patient-safety / data-preservation risk, not a hypothetical: the FK is present in the immutable bootstrap snapshot.
- **Safe-fix possible?** **Yes** — a **new** forward migration can `DROP`/`ADD` the FK constraint with `ON DELETE RESTRICT` (or soft-delete the lab instead), plus an application-level guard. Requires a dependency-order review because many child tables reference `patients.id` with CASCADE.
- **Approval required?** **YES** — DB schema change + data-preservation semantics (`CLAUDE.md:368,374-381`; base schema immutable at `:323`). Must also be reviewed by A05 (clinical data) and A04 (tenant lifecycle).
- **Remediation plan:** 1) Enumerate every FK that transitively reaches `patients` (static migration scan) and document the cascade graph. 2) Draft a new idempotent revision that replaces `patients.lab_id` FK with `ON DELETE RESTRICT`, guarded by `_constraint_exists()`. 3) Audit all `DELETE FROM labs` call sites and replace with soft-deactivate (`labs.is_active=false`). 4) Add a round-trip migration test and a chaos test asserting a lab delete cannot remove patient rows. 5) Verify backup/restore covers the constraint shape. **No execution in Wave A.**

### A07-015 — P2 — 8 untracked migrations gate the current head; clean checkouts would be one revision behind

- **Evidence**
  - `git status --porcelain -- backend/migrations/versions/` lists 8 `??` files (`20261114_0001..0006`, `20261118_0001`, `20261119_0001`).
  - Tracked-only head = `20260908_0001`; on-disk head = `20261119_0001` (§2.3).
  - `20261114_0001_unify_foundation.py:31` — `down_revision = "20260908_0001"`; chain continues linearly to `20261119_0001`.
  - `PROGRAM_CONTROL.md:121-125` — these files are USER WORK; `CONFLICT_REGISTER.md:13` (CR-006) status OPEN — BLOCKED.
- **Affected components:** every deployment path (`alembic upgrade head`), CI `migration-check`, clean checkouts, future migrations authored by any agent.
- **Root cause:** Local schema-unification work exists only in the working tree, not in any commit. Nothing is wrong with the chain itself; the risk is environmental.
- **Impact:** A fresh clone upgrades to `20260908_0001` and silently lacks foundation widening, FK indexes, communication/domain tables, OAuth2 `account_kind`, and NIAM step-up events. ORM models that reference those tables/columns (e.g., `health_core`, `communication`, `domain_platform`) would then fail at runtime.
- **Safe-fix possible?** **No** in Wave A — merging/committing user work is forbidden (`PROGRAM_CONTROL.md:213-216`).
- **Approval required?** **YES** — the user must explicitly release these files, and the orchestrator must approve a controlled review/commit. No cherry-pick, rebase, or merge is authorised.
- **Remediation plan:** 1) Preserve verbatim. 2) Independent line-by-line review of all 8 files (A07 has read 4 in full + sampled 2; remaining two need full review before any merge). 3) Verify each migration's `upgrade()` on an isolated disposable DB **only after** approval — not in Wave A. 4) Decide whether they become one squashed revision or eight; either way, keep `down_revision` chain intact. 5) Add a CI assertion that `alembic heads` returns exactly one head in a fresh clone.

### A07-016 — P2 — Several untracked migrations are not idempotent, contrary to the mandatory migration policy

- **Evidence**
  - `20261118_0001_oauth2_account_kind.py:33-38` — bare `op.add_column("oauth2_tokens", ...)` / `op.drop_column(...)`; no `IF NOT EXISTS`, no `_has_column()` guard.
  - `20261114_0003_unify_communication.py:18-50+` — bare `op.create_table("comm_notifications", ...)` and `op.create_index(...)`; no `_has_table()`/`_index_exists()` guard.
  - `20261114_0005_unify_domain_platform.py:15-45+` — bare `op.create_table("niam_domain_registrations", ...)`; no guard.
  - Contrast (correct patterns): `20261114_0001_unify_foundation.py:40-71,123-124` (`_has_table`, `_columns`, `ADD COLUMN IF NOT EXISTS`); `20261114_0002_unify_fk_indexes.py:29+` (all `CREATE INDEX IF NOT EXISTS`, 200+ statements); `20261114_0006_unify_authorization_indexes.py:41-48`; `20261119_0001_niam_step_up_events.py:20-27,65-70`.
  - Policy: `CLAUDE.md:324` — "Every migration must be idempotent"; `15_DATABASE_CONSTITUTION.md:27`.
  - Minor metadata drift: `20261114_0003` docstring says `Revises: 20260802_0002` but `down_revision = "20261114_0002"` (line 14); `20261114_0005` docstring says `Revises: 20260805_0002` but `down_revision = "20261114_0004"` (line 12).
- **Affected components:** the 3 named untracked migrations, CI round-trip gate (`CLAUDE.md:392-394`), any replay after a partial failure.
- **Root cause:** Different authors/templates; no static gate enforcing guard helpers.
- **Impact:** A retried/partially-applied migration fails with `DuplicateColumnError`/`DuplicateTableError`; the documented `downgrade -1 && upgrade head` round-trip may fail for `20261118_0001`. Severity P2 because these files are not yet merged.
- **Safe-fix possible?** **Yes** (add guards) — but the files are USER WORK and read-only for A07.
- **Approval required?** **YES** — user must release the files; any edit is a DB schema-artifact change.
- **Remediation plan:** 1) Add `_has_column()` guard to `20261118_0001`; `_has_table()`/`_index_exists()` guards to `0003` and `0005`. 2) Correct stale `Revises:` docstrings. 3) Add a static CI check: every migration must contain at least one guard helper or `IF NOT EXISTS` before `op.create_table`/`op.add_column`/`op.create_index`. 4) Round-trip on disposable DB after approval.

### A07-017 — P2 — ORM metadata drift: widened DB columns are still declared narrow in SQLAlchemy models

- **Evidence**
  - Untracked `20261114_0001_unify_foundation.py:76-80` widens `patients.health_id` 20→32, `canonical_patients.health_id` 20→32, `patients.gender` 1→10, `canonical_patients.gender` 1→10, `citizens.gender` 1→10.
  - ORM still declares: `backend/app/models/patient.py:28` `health_id = Column(String(20), ...)`, `:39` `gender = Column(String(1), ...)`; `backend/app/models/canonical_patient.py:32` `health_id = Column(String(20), ...)`, `:36` `gender = Column(String(1), ...)`.
  - `backend/app/routes/patients.py:65` accepts `"male"`/`"female"` (5–6 chars) while `models/patient.py:13-16` `Gender` enum is `M`/`F` and column was `String(1)`.
- **Affected components:** ORM metadata, `alembic revision --autogenerate` output, patient/canonical-patient writes, `Gender` enum consumers.
- **Root cause:** The forward migration widened physical columns without a corresponding model change (or vice versa).
- **Impact:** `--autogenerate` will propose **narrowing** the columns back to 20/1 (data-truncation risk if applied); ORM-side validation/length assumptions disagree with the database. Cross-reference A07-002.
- **Safe-fix possible?** **Yes** — align model types to the intended widened widths and unify the gender value domain.
- **Approval required?** **YES** — model/schema alignment and gender domain affect stored clinical data and API contract.
- **Remediation plan:** 1) Decide canonical gender encoding (e.g., `M`/`F` wire and storage) and update validator + enum + column together. 2) Update model `String` widths to match migration (32/10). 3) Add a metadata-vs-DB schema diff check (non-executing: compare `Base.metadata` against migration-declared types) to CI. 4) Do **not** run `--autogenerate` against a real DB.

### A07-018 — P3 — `20261119_0001` uses a deprecated SQLAlchemy table-existence API (speculative runtime risk)

- **Evidence**
  - `backend/migrations/versions/20261119_0001_niam_step_up_events.py:20-22` — `conn = op.get_bind(); return conn.dialect.has_table(conn, name)`.
  - Modern SQLAlchemy (1.4+/2.x) exposes `has_table` on `Inspector` (`inspect(bind).has_table(name)`); the dialect-level method is legacy. Other migrations in the tree use `inspect(op.get_bind()).has_table(...)` (e.g., `20260324_0009` line 33) and `sa.inspect(...).get_table_names()` (`20261114_0001:36-41`).
- **Affected components:** the newest head migration, all fresh deployments.
- **Root cause:** Mixed idempotency-guard idioms across migration authors.
- **Impact:** **LABELLED SPECULATION** — if the deployed SQLAlchemy version removes `dialect.has_table`, `upgrade()` raises `AttributeError` on a fresh DB. Static analysis cannot confirm the installed version (no dependency introspection/execution was performed). Severity P3 pending verification.
- **Safe-fix possible?** **Yes** — replace with `inspect(op.get_bind()).has_table(name)`.
- **Approval required?** **YES** — user-owned migration file, schema artifact.
- **Remediation plan:** 1) Read `backend/requirements*.txt` for the pinned SQLAlchemy version (A01 may have the dependency map). 2) If ≥2.0, patch the guard. 3) Round-trip on disposable DB after approval.

### A07-019 — P3 — PostgreSQL major version inconsistency across authoritative documents

- **Evidence**
  - `CLAUDE.md:16` — "PostgreSQL 17 + Redis 7".
  - `CLAUDE.md:392` — CI `migration-check` uses `postgres:17-alpine`.
  - `docs/constitution/15_DATABASE_CONSTITUTION.md:6` — "**PostgreSQL 16** is the primary database".
- **Affected components:** migration compatibility testing, backup/restore tooling, policy compliance evidence.
- **Root cause:** Constitution not updated after a runtime upgrade.
- **Impact:** Documentation/policy drift; a migration validated only on 17 may differ on 16 (and vice versa). No runtime defect found.
- **Safe-fix possible?** **Yes** — documentation-only update (or pin CI to the constitution version).
- **Approval required?** **No** for a doc correction; **Yes** if changing the CI image (A08 ownership).
- **Remediation plan:** orchestrator to decide canonical version; A08 to align CI image; update constitution and `CLAUDE.md` consistently.

### A07-020 — P3 — Backup/restore story is documented and scripted but has no automated CI/schedule verification in this repo

- **Evidence (positive)**
  - `Makefile:182-188` — `backup` target: `pg_dump -U postgres labdb | gzip > ./backups/gula_<ts>.sql.gz`.
  - `Makefile:396-399` — `validate-restore`, `continuous-backup` targets; scripts present: `scripts/backup.sh`, `backup-verification.sh`, `continuous-backup.sh`, `pitr-recover.sh`, `restore-test.sh`, `validate-restore.sh`.
  - `docs/constitution/data_preservation/{backup_strategy,restore_strategy,disaster_recovery_guide,emergency_ops_card,migration_safety_policy,protected_tables_registry}.md` (182–340 lines each).
- **Evidence (gap)**
  - Grep of `.github/workflows/*.yml` found **no** scheduled `pg_dump`/backup job (only generic cache `restore-keys` and deployment rollback steps). Scheduled backups are expected to be infrastructure/cron-driven, which A07 could not verify statically.
- **Affected components:** DR readiness, data-preservation gate evidence.
- **Root cause:** Backup orchestration is external to CI (ops-managed); repo contains scripts + docs only.
- **Impact:** **LABELLED SPECULATION** — if no external scheduler exists, recovery-point objectives are unverified. Not a confirmed defect.
- **Safe-fix possible?** **Yes** at documentation level (record where scheduling lives).
- **Approval required?** **No** for documentation; **Yes** for adding a CI workflow (A08 ownership).
- **Remediation plan:** hand to A08 to confirm scheduler/WAL archiving configuration; A07 will not add workflows.

---

## 4. Backward compatibility & idempotency — summary table (static)

| Migration group | Idempotency guards observed | Compatibility posture |
|---|---|---|
| `20250322_0000_create_base_schema.py` (immutable) | `_table_exists()` guards; widened columns folded in so later adds become no-ops | Additive; immutable by policy |
| SNDHS `20260505_0001..0006` | Guards present; dual-read rule documented (`CLAUDE.md:280-282`) | Nullable columns, backfill script |
| National platform `20260714_0001` … `20260908_0001` | Mixed; four intentional merge revisions with tuple `down_revision` | Additive table creation |
| 8 modified tracked migrations (user work) | Modifications **add** guards (e.g., `20260324_0009`, `20260815_0023`) | Forward-only repairs; **do not rewrite history** |
| 8 untracked migrations | Mostly guarded (`20261114_0001/0002/0006`, `20261119_0001`); unguarded in `20261114_0003`, `20261114_0005`, `20261118_0001` (`add_column`) | Additive/widening; one non-idempotent add-column |

**Round-trip note:** `20261114_0001` `downgrade()` deliberately does not reverse widening (`lines 178-180`) — correct for data safety, but it means the migration is *forward-only in practice*. This should be documented in the migration docstring rather than discovered during a downgrade test.

---

## 5. Positive DB controls (verified)

1. `patients` composite indexes for tenant-scoped lookup: `ix_patients_lab_id`, `ix_patients_lab_phone`, `ix_patients_lab_nid` (`20250322_0000:173-175`; `models/patient.py:21-23`).
2. `lab_orders` partial index `ix_lab_orders_status_pending ON (lab_id, created_at DESC) WHERE status='pending'` (`20250322_0000:208-209`).
3. Statement timeout + `work_mem` + idle-in-transaction timeout per connection (`backend/app/database.py:229-239`).
4. Connection pool budget with pre-ping and recycle (`database.py:206-226`, `CLAUDE.md:180-184`).
5. `20261119_0001` adds a **database-level replay guard** — unique `(account_id, code_fingerprint)` — plus FKs to `niam_accounts`/`niam_sessions` with `ON DELETE CASCADE` (`:46-54`). Well-designed for the step-up evidence use case. (Cascade here targets an ephemeral evidence table, not patient data — consistent with policy.)
6. `20261114_0001` claims idempotency re-scoping (`claims` unique key becomes `(lab_id, idempotency_key)`, `:106-120`) — a correct multi-tenant fix.
7. `20261114_0006` restores 15 authorization indexes that origin/main had commented out (`:22-43`) — good gap closure.

---

## 6. P0 status and gating

| Question | Answer |
|---|---|
| P0 on committed git history? | **NO** — merge-base valid; ahead 2 / behind 0; 101=101=101 migrations (§2.1). |
| Duplicate revision IDs? | **NO** (0/109). |
| `down_revision` chain breaks on disk? | **NO** (0 broken links; 1 base; 1 head). |
| P0 on migration *content*? | **NO confirmed P0.** A07-014 is P1 (patient-data cascade risk in immutable base schema) and requires approval; it is not a blocker for audit completion but must be escalated before any Wave C DB work. |
| Any migration executed against a real DB? | **NO.** |
| Any user work modified/staged? | **NO.** |

---

## 7. Remediation plan summary (PLANS ONLY)

| Finding | Proposed owner | Wave C status | Approval gate |
|---|---|---|---|
| A07-014 (P1 cascade) | A07 plan + A05 clinical review | **BLOCKED** | DB schema + data-preservation approval; base immutable |
| A07-015 (P2 untracked head) | Orchestrator + user | **BLOCKED** | User release; no merge/cherry-pick authorised |
| A07-016 (P2 idempotency) | User (files protected) | **BLOCKED** | User release + schema-artifact approval |
| A07-017 (P2 ORM drift) | A07 plan | **BLOCKED** | Model/schema + gender contract approval |
| A07-018 (P3 deprecated API) | User (file protected) | **BLOCKED** | User release |
| A07-019 (P3 PG version) | Orchestrator docs + A08 CI | **BLOCKED** | Doc decision; CI change = A08 |
| A07-020 (P3 backup evidence) | A08 | **BLOCKED** | A08 scope |

## 8. SCOPE_REQUESTs

1. **SCOPE_REQUEST-A07-09 (HIGH) → Orchestrator:** Obtain an explicit user decision on the 8 untracked + 8 modified migration files. A07 recommends **preserve verbatim** and treat any corrective work as new forward revisions. This is the prerequisite for any DB work in Wave C.
2. **SCOPE_REQUEST-A07-10 → Orchestrator/A05:** Joint review of the patient-data cascade graph (A07-014) before any schema change.
3. **SCOPE_REQUEST-A07-11 → Orchestrator/A01:** Obtain pinned SQLAlchemy version to resolve the speculative `dialect.has_table` risk (A07-018) — A07 did not inspect dependency manifests in this audit.
4. **SCOPE_REQUEST-A07-12 → Orchestrator/A08:** Confirm backup scheduling / WAL archiving and align CI Postgres image with the constitution (A07-019, A07-020).

---

*End of DATABASE_MIGRATION_AUDIT.md. Companion reports: `BACKEND_AUDIT.md`, `API_CONTRACT_AUDIT.md`.*
