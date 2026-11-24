# Team A — Database Integrity and Migration Reassessment (A4)

**Audit ID:** A4
**Date:** 2026-11-18
**Repository:** `gula-integration`
**Audited ref:** working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling boundary:** `/home/samertts/workspace/projects/gula-platform` observed read-only at `f478676b`; never modified.
**Mode:** adversarial, READ-ONLY, static/synthetic evidence only.
**Machine-readable companion:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A4_DATA_API.json`

---

## 1. Decision boundary (unchanged)

This reassessment does **not** overturn, close, reinterpret, or downgrade any protected decision. No owner gate was opened or satisfied by this pass.

| Decision / finding | Owner state after this audit |
|---|---|
| Release decision (`GOVERNANCE/FINAL_DECISION.md`) | **HOLD** — unchanged; protected MD5 `effdfeaf10234678d83b2668c4489552` verified matching on disk |
| MPI implementation verdict | **REJECT** — unchanged (A3 boundary respected) |
| ADR-A / 284-table migration gap | **BLOCKED** — unchanged; no migration authored, staged, or applied |
| MP-001; ODR-001…ODR-004; D-020; D-021; ADR-A…ADR-J | **UNCHANGED** — no approval inferred |
| AUD-02 / AUD-07 / AUD-16 | **OPEN** — unchanged; not re-reported here |
| NR-011 FK failure (previously disclosed) | Not re-reported as a new finding; static root-cause corroboration recorded as `AUD-DB-004` only |

Assurance vocabulary used here is limited to `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `BLOCKED`, `NOT IMPLEMENTED`. Every new finding has `status = DISCOVERED` in the JSON artifact. **No audited work is awarded `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` by this auditor** — that authority belongs to Team C only.

---

## 2. Method and evidence limits

**Performed:** AST parsing of migration modules, deterministic grep/scan of all migration versions, file reads of `env.py`, `database.py`, the cited ORM models, and cross-checks against protected governance evidence. Synthetic reproduction/falsification designs were constructed for every finding.

**Not performed (mandate prohibitions):** no operational PostgreSQL connection, no `alembic` command against any database, no migration creation or execution, no git add/commit/push, no network access, no secrets, no real patient data, no modification of any pre-existing file.

**Evidence boundary consequence:** live-schema facts (notably the `1364` destructive-looking operations from the PG diff) cannot be independently reproduced in this pass and are recorded as owner-gated `BLOCKED`, not confirmed or refuted.

---

## 3. Static migration census — no topology finding raised

All `107` migration files present in the worktree were enumerated and parsed with a refined AST scan that handles annotated assignments (`revision: str = ...`). Earlier signals of "6 heads" were **falsified** as an AST artifact of annotated assignments. Verified facts:

| Property | Result |
|---|---|
| Files on disk / unique revisions | 107 / 107 |
| Duplicate revisions | 0 |
| Cycles | 0 |
| Root | single — `20250322_0000` |
| Head | single — `20261114_0006` |
| Merge migrations | `20260815_0003`, `20260815_0015`, `20260819_0001`, `20260908_0001` |
| Historical branch points | `20260814_0006`, `20260814_0011`, `20260815_0002`, `20260815_0022`, `20260819_0003` |
| Tracked vs on-disk versions | 102 tracked; 6 untracked head files `20261114_0001..0006`; 8 modified existing revisions |

Aggregate upgrade operations (static counts across all revisions): `op.create_table` 435, `op.create_index` 943, `op.execute` 233, `op.add_column` 75, `op.get_bind` 55, `op.create_foreign_key` 10, `op.batch_alter_table` 7, `op.bulk_insert` 3, `op.create_unique_constraint` 3, `op.drop_constraint` 3. Table drops occur in downgrade paths only. The chain has one root and one head: **no topology finding was raised**, and the initial multi-head signal is explicitly retracted.

---

## 4. Cross-check of protected 284 / 1364 figures

| Claim | Static cross-check | Verdict |
|---|---|---|
| 284-table gap (`GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_DB_ALEMBIC_DIFF_CLASSIFICATION.md:15,169-171`) | Category arithmetic `191 + 5 + 6 + 82 = 284` PASS; 16 grouped inventory rows `6+5+4+6+21+2+5+1+43+45+32+45+37+17+10+5 = 284` PASS | Arithmetically corroborated; ownership remains **BLOCKED** under ADR-A |
| FK target `national_encounters` | `backend/app/ehr/models/allergy.py:14` declares `ForeignKey('national_encounters.id')`; grep across all 107 migration versions finds zero definitions | Static root cause corroborated — `AUD-DB-004` |
| Three "mentioned" tables | `hospital_operation_theaters`, `national_citizens`, `national_patients` appear only as guarded conditional FK targets, never as `create_table` | Confirmed |
| 1364 destructive-looking operations (`GOVERNANCE/NATIONAL_INTEGRATION/ADVERSARIAL_REVIEW_RECORD.md:97`) | Requires live-PG `alembic check` diff to reproduce; internally consistent arithmetically per that record | **NOT independently reproducible statically** — owner-gated `BLOCKED`; no PG connection used here |

No destructive migration was produced or applied. This report does not change the ADR-A posture.

---

## 5. New database findings (all `status = DISCOVERED`)

Full machine-readable detail, including alternatives and owner-gating flags, is in `FINDINGS_A4_DATA_API.json`. Summaries below preserve evidence, reproduction, falsification, root cause, impact, severity, likelihood, remediation, and owner gate.

### AUD-DB-001 — Tenant isolation is application-only; no database-enforced row-level security

- **Severity:** HIGH; **likelihood:** MEDIUM; **classification:** owner-decision; **owner_gated:** true.
- **Evidence:** `backend/app/database.py:20-24` — `lab_id` in `contextvars.ContextVar`, not a DB session setting; `backend/app/database.py:284-298` — `get_db()` yields a plain `Session` with no `SET LOCAL` / `current_setting()` / tenant role; all 107 migration files — zero `CREATE POLICY` / `ROW LEVEL SECURITY` / `current_setting()` DDL (grep verified).
- **Reproduction:** `grep -rniE 'ROW LEVEL SECURITY|CREATE POLICY|current_setting\(|SET LOCAL' backend/migrations/versions/*.py` returns no DDL policy hits; `get_db()` sets no tenant context. **Falsification:** cite any migration creating an RLS policy or a `get_db()` tenant setting — none exists.
- **Root cause:** multi-tenancy implemented exclusively as `lab_id == actor.lab_id` repository/service filters; no DB-level defense in depth.
- **Impact:** one omitted/incorrect predicate in any query exposes cross-tenant PHI; national deployment raises breach/confidentiality impact with no DB backstop.
- **Remediation:** owner ruling first (ADR-A/tenant architecture); evaluate PostgreSQL RLS plus session tenant context, and meanwhile add a static query-lint gate asserting `lab_id` predicates on all PHI-table queries.
- **Alternatives:** (1) app-only scoping + query lint (lowest cost, weaker); (2) RLS policies per tenant-bearing table (strong, migration-heavy, owner-gated); (3) schema/database per tenant (strongest, highest TCO, conflicts with national single-deployment model).

### AUD-DB-002 — Unguarded `drop_constraint` in `20260815_0016` breaks fresh-install and drifted-DB upgrade paths

- **Severity:** MEDIUM; **likelihood:** MEDIUM; **classification:** potentially destructive; **owner_gated:** false.
- **Evidence:** `backend/migrations/versions/20260815_0016_device_tenant_isolation.py:16-21` — `op.drop_constraint('uq_integrated_devices_uid', ...)` with no existence guard; `:22-26` creates composite `(lab_id, device_uid)` unique constraint; `:29-39` downgrade re-adds global unique on `device_uid`. Contrast guarded sibling `backend/migrations/versions/20260815_0002_scope_inbox_idempotency.py:27-40`.
- **Reproduction:** construct a DB where `uq_integrated_devices_uid` does not exist (fresh install whose ORM declares only the composite constraint), run `alembic upgrade 20260815_0016` — the unguarded drop raises a lookup error. Downgrade falsification: insert two rows with the same `device_uid` under different `lab_id`, then downgrade — global unique creation fails.
- **Falsification:** show a runtime inspector guard in `upgrade()` — absent.
- **Root cause:** migration authored for one lineage state; no inspector-based idempotency guard unlike neighbouring revisions.
- **Impact:** forward upgrade can abort mid-chain on fresh/drifted databases; downgrade is data-dependent and may fail after legitimate per-lab duplicate UIDs exist.
- **Remediation:** wrap drop and create in inspector guards (mirror `20260815_0002`) and document a data-reconciliation precondition for downgrade.
- **Alternatives:** (1) inspector guards (recommended, mechanical); (2) new forward-only reconciliation migration behind ADR-A; (3) forward-only with documented no-op downgrade warning.

### AUD-DB-003 — Claims global idempotency uniqueness and NOT NULL constraints dropped; downgrade not reliably reversible

- **Severity:** HIGH; **likelihood:** MEDIUM; **classification:** breaking; **owner_gated:** true.
- **Evidence:** `backend/migrations/versions/20261114_0001_unify_foundation.py:9-11` claims "Every statement is additive or widening ... safe on an existing database"; `:106-120` executes `ALTER TABLE claims DROP CONSTRAINT IF EXISTS claims_idempotency_key_key` then creates composite unique `(lab_id, idempotency_key)`; `:83` and `:97` call `_drop_not_null('organizations','name')` and `_drop_not_null('facilities','name')`; `:172-176` downgrade re-adds global UNIQUE; `:178-180` deliberately does not restore NOT NULL.
- **Reproduction:** read `:106-120` against the header claim; two claims rows with the same `idempotency_key` in different labs after upgrade make downgrade fail when re-adding global uniqueness.
- **Falsification:** show that the operation is additive-only and downgrade restores all constraints — contradicted by cited lines.
- **Root cause:** idempotency scope changed from global to per-lab while the migration is documented as purely additive and its downgrade assumes pre-change data uniqueness.
- **Impact:** data-integrity semantics silently weakened; documentation misstates operation class (breaking, not additive); partial rollback can fail on production data, contradicting recorded rollback posture.
- **Remediation:** correct header to "breaking (constraint scope change)"; record the idempotency-scope decision with the owner; add a documented data check before downgrade or make downgrade conditional and explicit about residual state.
- **Alternatives:** (1) forward-only with documented residual state (recommended); (2) data-reconciliation downgrade that deduplicates keys (destructive — owner approval required); (3) revert the scope change (would undo MP/ODR-scoped per-lab design — owner-gated).

### AUD-DB-004 — ORM foreign key targets an unmigrated table — static root cause of the 284-table gap / NR-011

- **Severity:** HIGH; **likelihood:** HIGH; **classification:** owner-decision; **owner_gated:** true.
- **Evidence:** `backend/app/ehr/models/allergy.py:14` — `encounter_id = Column(String(26), ForeignKey('national_encounters.id', ondelete='SET NULL'), ...)`; zero `national_encounters` occurrences in all 107 migration versions (grep verified); `backend/migrations/env.py:36-40` imports `app.national.domain` so autogenerate discovers the FK target; `PHASEB_DB_ALEMBIC_DIFF_CLASSIFICATION.md:15,169-171` records 284 add-table differences under ADR-A BLOCKED.
- **Reproduction:** `grep -rn 'national_encounters' backend/migrations/versions/*.py` → empty; `grep -n 'national_encounters' backend/app/ehr/models/allergy.py` → line 14. Any autogenerate resolving this FK cannot find a migrated target. **Falsification:** add a migration defining `national_encounters` (would change the 284 figure) — not done.
- **Root cause:** national-domain ORM models entered metadata without Alembic history; ownership of `national_*` tables is undecided (ADR-B/W1), so they cannot simply be generated.
- **Impact:** autogenerate abort / incomplete schema; EHR allergy encounters cannot be represented in the migrated schema; 284-table gap stays BLOCKED; national deployment data model incomplete. The previously disclosed NR-011 failure is **not** re-reported — this is static corroboration only.
- **Remediation:** owner must rule on ADR-A/ADR-B ownership before any `CREATE_FORWARD` wave. This auditor proposes no migration and applies none.
- **Alternatives:** (1) owner-approved staged forward waves; (2) declare `national_*` intentionally unmigrated and remove from autogenerate scope (changes national platform design — owner-gated); (3) leave BLOCKED (current posture; keeps HOLD).

### AUD-DB-005 — Migration/source drift: chain head revisions and 8 existing revisions are uncommitted in this worktree

- **Severity:** MEDIUM; **likelihood:** HIGH; **classification:** unresolved; **owner_gated:** false.
- **Evidence:** `git status --porcelain backend/migrations/versions/` — 6 untracked files `20261114_0001..20261114_0006`, 8 modified files; 107 files on disk vs 102 from `git ls-files backend/migrations/versions/`; `backend/migrations/versions/20261114_0006_unify_authorization_indexes.py:17-18` is untracked and is the single chain head.
- **Reproduction:** run the two git commands above. **Falsification:** commit the 6 head files and confirm 108 tracked / 0 untracked — not done (read-only mandate).
- **Root cause:** integration worktree accumulated uncommitted migration lineage over HEAD `2206654d`.
- **Impact:** a clean checkout silently collapses the chain to an earlier head, losing the `20261114` reconciliation set; governance documents describing the current schema would become false; all 284-gap evidence depends on uncommitted files.
- **Remediation:** owner-directed atomic commit of the migration head set after full verification; until then treat all schema evidence as worktree-scoped and non-durable.
- **Alternatives:** (1) commit head migrations after verification (recommended); (2) archive a read-only evidence snapshot (does not replace commit); (3) keep HOLD and do not rely on this worktree for release decisions (current posture).

### AUD-DB-006 — Forward migration performs unlogged data deletion (role-permission over-grant repair)

- **Severity:** LOW; **likelihood:** LOW; **classification:** requires data transformation; **owner_gated:** false.
- **Evidence:** `backend/migrations/versions/20260814_0006_security_audit_governance.py:179-184` — `DELETE FROM niam_role_permissions WHERE role='organization_manager' AND permission='audit.read'`; no audit row emission or downgrade restoration in the same file.
- **Reproduction:** static read of `upgrade()` lines 179-184. **Falsification:** show an audit event for this deletion or a downgrade step restoring the grant — neither exists.
- **Root cause:** security over-grant repair implemented as inline DML in an Alembic upgrade with no audit event or reversal path.
- **Impact:** authorization state changes without an immutable audit trail; no deterministic restoration if the repair is later deemed wrong. Harm likelihood low because the deletion is narrowly scoped.
- **Remediation:** emit structured audit events for authorization-state DML in migrations and document the intended final grant set; do not rely on migration DML as the sole control record.
- **Alternatives:** (1) audit event + documented final state (recommended); (2) governed bootstrap service with its own audit log; (3) accept with explicit owner note.

---

## 6. Verdict and residual risk

1. **HOLD stands.** AUD-DB-004 confirms the ADR-A 284-table gap at the source level; AUD-DB-003 shows a breaking constraint change documented as additive; AUD-DB-001 removes any DB-level tenant backstop.
2. **No release assurance awarded.** This pass is static only; nothing here is `INDEPENDENTLY VERIFIED` or `PRODUCTION READY`.
3. **No destructive action taken.** No migration authored, staged, committed, or executed; no PG connection; no protected file modified.
4. **Top database material findings:** AUD-DB-004 (unmigrated FK / ADR-A gap), AUD-DB-003 (breaking idempotency uniqueness change mislabeled additive), AUD-DB-001 (no DB-enforced tenant isolation).
5. **Next owner actions (not performed here):** rule on ADR-A/ADR-B ownership; commit the uncommitted migration head set after verification; guard `20260815_0016`; correct `20261114_0001` classification; decide RLS strategy.

---

## 7. Artifact control statement

The only files created by this audit are:

- `GOVERNANCE/ADVERSARIAL_ASSURANCE/FINDINGS_A4_DATA_API.json`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/DATABASE_INTEGRITY_REPORT.md`
- `GOVERNANCE/ADVERSARIAL_ASSURANCE/API_AND_INTEROPERABILITY_AUDIT.md`

No pre-existing file, git index, configuration, database, or sibling repository was modified. No secret, credential, or patient datum is included; all reproduction designs are synthetic or static.
