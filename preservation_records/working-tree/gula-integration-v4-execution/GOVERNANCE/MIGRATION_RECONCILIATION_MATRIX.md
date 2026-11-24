# Migration Reconciliation Matrix

**Program:** GULA Stable v1.0.0 — Repository Unification
**Task:** Reconcile the local `remediate-security-001` lineage (HEAD `f478676b`) with `origin/main` (`2827c1ff`).
**Integration branch:** `integration/gula-unification-v1` (base = `origin/main` @ `2827c1ff`).
**Status:** Phase 1 — DISCOVER/RECONCILE (read-only). No migrations modified or executed.
**Date:** 2026-11-14

> Authority: `GOVERNANCE/AI_AGENT_RULES.md` and `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md`.
> Verification vocabulary: PASS / FAIL / BLOCKED / NOT RUN / UNKNOWN. Everything below is static analysis unless stated.

## 1. Method

- Enumerated every `backend/migrations/versions/*.py` at `HEAD` (local, 57 revisions) and `origin/main` (remote, 101 revisions).
- Parsed each module with Python AST: `revision`, `down_revision`, `depends_on`, imports, helper functions, module vars, and the ordered `op.*` call sequence (method name + literal args) for `upgrade()` and `downgrade()`.
- Compared each file by: byte SHA-256 → token stream (whitespace/comment-insensitive) → DDL op-signature (method+literal args+order).
- Cross-checked local-only table/column needs against the remote schema (all 408 remote `create_table` names) and remote code (`backend/app`).
- Everything is reproducible with `/tmp/opencode/unify/migration_matrix.py` and the derived artefacts.

## 2. Status legend

| Status | Meaning | Action on converged tree |
|---|---|---|
| `IDENTICAL` | Byte-identical file. | Keep base. |
| `SEMANTICALLY_EQUIVALENT` | Different text, identical DDL effect (formatting, typing, or SQLite-only guards). | Keep base; no functional change lost. |
| `LOCAL_CHANGE_REQUIRED` | Local copy must be dropped or re-authored (remote superset, or a local-only migration must be re-based onto the remote head). | Discard local variant / forward-port local semantics. |
| `REMOTE_CHANGE_REQUIRED` | Base file must be amended to carry a local-only improvement. | Patch base migration. |
| `CONFLICT` | Incompatible schema or semantics for the same object; a design decision is required. | **STOP — decision required.** |
| `REMOTE_ONLY` | Exists only on `origin/main`. | Adopt from base. |
| `UNVERIFIED` | Not yet classified. | Manual review. |

## 3. Summary

| Status | Files |
|---|---:|
| `IDENTICAL` | 1 |
| `SEMANTICALLY_EQUIVALENT` | 43 |
| `LOCAL_CHANGE_REQUIRED` | 11 |
| `REMOTE_CHANGE_REQUIRED` | 1 |
| `CONFLICT` | 1 |
| `REMOTE_ONLY` | 51 |
| `UNVERIFIED` | 0 |
| **Total** | **108** |

Chain integrity (static): local head `20260810_0001`; remote head `20260908_0001` (merge of `20260819_0004`, `20260820_0005`, `20260908_0002`). Zero duplicate revisions, zero missing parents, zero cycles on both sides.

## 4. The 8 files that required manual adjudication

These share a filename + revision but diverge beyond formatting. All were inspected at source level.

| File | Resolution | Rationale |
|---|---|---|
| `20260324_0008_lab_result_test_type_fk_set_null.py` | `LOCAL_CHANGE_REQUIRED` | Discard local; remote adds SQLite batch_alter branch (superset). Net PG schema identical (FK ON DELETE SET NULL). |
| `20260324_0010_production_indexes.py` | `SEMANTICALLY_EQUIVALENT` | Formatting only + downgrade uses op.drop_index vs DROP INDEX IF EXISTS; same 16 indexes. |
| `20260506_0001_financial_engine_phase_a.py` | `SEMANTICALLY_EQUIVALENT` | Formatting only; remote adds guard get_bind() calls. Same tables/indexes. |
| `20260715_0001_national_ecosystem_partners.py` | `LOCAL_CHANGE_REQUIRED` | Discard local; remote adds JSONB/JSON dialect fallback + typing. Same 6 tables. |
| `20260716_0004_radiology_platform.py` | `LOCAL_CHANGE_REQUIRED` | Discard local; remote reformats and adds SQLite batch FK path. Same tables/indexes/FK. |
| `20260719_0001_ai_platform_tables.py` | `LOCAL_CHANGE_REQUIRED` | Discard local; remote adds dialect fallbacks (sa.JSON vs JSONB/ARRAY) + pgvector guard. Same 8 tables. |
| `20260722_0001_authorization_expansion.py` | `REMOTE_CHANGE_REQUIRED` | Remote comments out all 13 explicit create_index calls it shares with local; local actively creates 15 indexes (13 shared + `ix_organizations_tenant`, `ix_users_organization`, `ix_users_tenant`; remote additionally comments `ix_roles_role_id` which local never created). **Not** rewritten in place (forward-only): the 15 local indexes are restored in forward migration `20261114_0006_unify_authorization_indexes`, guarded by `IF NOT EXISTS`. |
| `20260723_0002_niam_completion_tables.py` | `LOCAL_CHANGE_REQUIRED` | Discard local; remote reorders batch_alter for SQLite + same 50 tables/constraints. Verify niam_audit_entries/sessions columns equivalent. |

Key observation: seven of the eight are remote **supersets** (SQLite test-compatibility guards, `sa.JSON` fallbacks for JSONB/ARRAY, typing modernisation) with an identical PostgreSQL DDL effect. Only `20260722_0001_authorization_expansion.py` contains a local advantage the base lost: origin/main comments out its explicit `op.create_index(...)` calls (13 of them), while the local lineage created 15 indexes.

## 5. The 7 local-only migrations — forward-port plan

These exist only on the local lineage. Since the converged base is `origin/main` (which already passes `20260723_0002`), each must be re-authored as a forward migration on top of remote head `20260908_0001` (not replayed in place).

| File | Status | Forward-port | Plan |
|---|---|---|---|
| `20260802_0001_widen_patient_health_id.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port: re-base down_revision to remote head; keep health_id/gender widening (remote still String(20)); guard org/facility ADD COLUMN (remote added contact_*; local adds org_id/name_en/ar/parent_org_id/facility_id). |
| `20260802_0002_stable_fk_indexes.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port 200 IF NOT EXISTS FK indexes; all 108 target tables confirmed present in remote schema. Re-base to new head. |
| `20260804_0001_communication_experience.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port comm_notifications/comm_notification_events/comm_user_preferences (+12 indexes); no remote equivalent. Re-base down_revision. |
| `20260805_0001_claims_lab_idempotency.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port claims unique-constraint swap to composite (lab_id, idempotency_key); remote still has global unique. Re-base. |
| `20260805_0002_stable_identity_platform.py` | `CONFLICT` → **DECIDED (supersede)** | partial | niam_workspaces schema COLLIDES with remote 20260814_0003 (different PK/FKs). Remote niam_workspace_contexts/niam_memberships/niam_membership_invitations/niam_roles/niam_role_permissions/niam_role_assignments/verification_records supersede local workspace_* + citizen verification tables. **Do NOT replay this revision.** Split: `niam_professional_registry` + `niam_identity_providers` → `20261114_0004`; `niam_professional_authorizations` (from 20260810_0001) → `20261114_0004`; workspace/citizen tables retired. |
| `20260806_0001_domain_platform.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port 6 niam_domain_* tables; no remote equivalent. Re-base down_revision (currently 20260805_0002 which conflicts). |
| `20260810_0001_professional_authorizations.py` | `LOCAL_CHANGE_REQUIRED` | yes | Forward-port niam_professional_authorizations; no remote equivalent. Re-base down_revision (currently local-only 20260806_0001). |

### 5.1 Verification performed for the forward-ports

- `20260802_0002_stable_fk_indexes.py`: all **108 distinct target tables** for its **200 indexes** were confirmed to exist in the remote schema (`/tmp/opencode/unify/index_target_missing.txt` is empty). Safe to re-apply with `IF NOT EXISTS`.
- `20260802_0001_widen_patient_health_id.py`: remote `patients.health_id` / `canonical_patients.health_id` are still `String(20)`; remote never widened them. The widening is still required. The organization/facility `ADD COLUMN`s overlap partially with remote `20260722_0001` (which adds `contact_email|phone|address`); local must keep only the non-overlapping columns and remain idempotent.
- `20260805_0001_claims_lab_idempotency.py`: remote still declares `claims.idempotency_key ... unique=True`; the composite `(lab_id, idempotency_key)` change is still required.
- `20260804_0001` (`comm_*`), `20260806_0001` (`niam_domain_*`), `20260810_0001` (`niam_professional_authorizations`): no remote table with the same name exists; forward-port is additive.

### 5.2 Implemented forward migrations (2026-11-14)

All six are chained from remote head `20260908_0001` and live in `backend/migrations/versions/` on `integration/gula-unification-v1`:

| Forward revision | Source local revision(s) | Contents |
|---|---|---|
| `20261114_0001_unify_foundation` | `20260802_0001`, `20260805_0001`, part of `20260723_0002` | health_id/gender widening; guarded organization/facility columns; claims composite `(lab_id, idempotency_key)`; `niam_identity_authorities` |
| `20261114_0002_unify_fk_indexes` | `20260802_0002` | 200 guarded FK indexes (all 108 target tables verified present) |
| `20261114_0003_unify_communication` | `20260804_0001` | `comm_notifications`, `comm_notification_events`, `comm_user_preferences` + indexes |
| `20261114_0004_unify_professional_identity` | `20260805_0002` (registry/providers), `20260810_0001` | `niam_professional_registry`, `niam_identity_providers`, `niam_professional_authorizations` |
| `20261114_0005_unify_domain_platform` | `20260806_0001` | 6 `niam_domain_*` tables |
| `20261114_0006_unify_authorization_indexes` | `20260722_0001` (15 local indexes) | guarded restoration of the indexes origin/main commented out |

**Validation status:**

- Migration graph: **PASS** — 107 revisions, single head `20261114_0006`, 0 missing parents, 0 cycles.
- `py_compile` on all six: **PASS**.
- Fresh `alembic upgrade head` on a disposable PostgreSQL 16 database: **BLOCKED (pre-existing NR-003)** — the *upstream* origin/main chain fails at `20260815_0023_drug_substitution` because `pharmacy_drug_catalog.id` is `Integer` while its FK columns are `String(26)`. This is the known Pharmacy PK divergence, not caused by the unification. Evidence in `DATABASE_COMPATIBILITY_REPORT.md`.
- Isolated tail test (`20261114_0001/0003/0004/0005/0006`) on a minimal prerequisite schema: **PASS** — upgrade, reverse-order downgrade, and re-upgrade all succeed; all 13 expected tables and 5 spot-check indexes present; widening verified (`patients.health_id varchar(32)`, `gender varchar(10)`).
- `20261114_0002` (200 FK indexes): **STATIC PASS** — every target table exists in the remote migration set and each statement is `CREATE INDEX IF NOT EXISTS`; not executed because the fresh chain is upstream-blocked.

## 6. CONFLICT — `niam_workspaces` schema collision (DECIDED)

> **DECISION (2026-11-14): Option 1 — Supersede local platform. APPROVED by Program Director.**
> origin/main's workspace architecture is canonical. Local `niam_workspace_*` and `niam_citizen_identity_verifications` are retired (not forward-ported). Only `niam_professional_registry`, `niam_identity_providers`, and `niam_professional_authorizations` are forward-ported, re-keyed to the remote identity model. Local `WorkspaceService`/`ProfessionalRegistry`/`CitizenRegistry` call-sites will be reconciled to remote `niam_workspace_contexts`/`niam_memberships`/`niam_roles`/`verification_records` during the code reconciliation phase.
> Consequence: `20260805_0002_stable_identity_platform` is **not** replayed; its unique tables are split into forward migration `20261114_0004_unify_professional_identity` (professional registry + identity providers + professional authorizations), and its workspace tables are dropped from scope.

This is the single blocking design decision in the migration reconciliation.

| Aspect | Local `20260805_0002_stable_identity_platform` (PROGRAM-STABLE-003) | Remote `20260814_0003_workspace_architecture` |
|---|---|---|
| `niam_workspaces.id` | local identity/workspace model (integer/uuid workspace id) | `String(26)` primary key |
| Key columns | `workspace_id`, `owner_identity_id`, `owner_person_id`, `organization_id` (local int FK) | `workspace_key`, `owner_account_id → niam_accounts`, `organization_id → niam_organizations`, `facility_id`, `department_id`, `professional_type`, `is_personal`, `version` |
| Companion tables | `niam_workspace_roles`, `_members`, `_permission_templates`, `_departments`, `_teams`, `_invitations`, `_delegations` | `niam_workspace_contexts`, `niam_memberships`, `niam_membership_invitations`, `niam_membership_applications`, `niam_roles`, `niam_permissions`, `niam_role_permissions`, `niam_role_assignments` |
| Session binding | adds `workspace_id`/`workspace_bound_at` to `niam_sessions` | server-authoritative `niam_workspace_contexts` (session→workspace) |
| Citizen verification | `niam_citizen_identity_verifications` | `verification_records` (20260814_0001) |

**Finding:** origin/main implements a newer, account/organization-centric workspace architecture that structurally supersedes the local PROGRAM-STABLE-003 workspace platform. Two tables with the same name but incompatible definitions cannot both be applied.

**Not superseded (genuine local features with no remote equivalent):**
- `niam_professional_registry` (national professional licence registry — issuing country, registration number, profession).
- `niam_identity_providers` (country-agnostic configurable identity providers).
- `niam_professional_authorizations` (professional authorisation scopes).

**Options** (decision needed before any implementation):
1. **Supersede (recommended):** adopt remote workspace architecture as canonical; forward-port only `niam_professional_registry`, `niam_identity_providers`, `niam_professional_authorizations`, adapting FKs to remote `niam_accounts`/`niam_identities`/`niam_persons`; retire local `niam_workspace_*` + `niam_citizen_identity_verifications` in favour of remote membership/role/verification tables; refactor local `WorkspaceService`/`ProfessionalRegistry`/`CitizenRegistry` call-sites accordingly.
2. **Preserve local platform under a separate namespace** (e.g. prefix tables) and run it alongside remote's — highest cost, duplicated concepts, not recommended.
3. **Renegotiate remote architecture** to adopt the local model — contradicts the decision to converge on `origin/main`; out of scope.

## 7. Full matrix

Machine-readable full matrix: `reconciliation_matrix.tsv` (this directory) and `reconciliation_matrix.json`.

### 7.1 Common files (`IDENTICAL` / `SEMANTICALLY_EQUIVALENT` / `LOCAL_CHANGE_REQUIRED` / `REMOTE_CHANGE_REQUIRED` / `CONFLICT`)

| Status | Revision | Local ops | Remote ops | File |
|---|---|---:|---:|---|
| `SEMANTICALLY_EQUIVALENT` | `20250322_0000` | 87 | 87 | `20250322_0000_create_base_schema.py` |
| `IDENTICAL` | `20250322_0001` | 5 | 5 | `20250322_0001_add_roles_hierarchy.py` |
| `SEMANTICALLY_EQUIVALENT` | `20250322_0002` | 11 | 11 | `20250322_0002_perf_indexes_audit_protection.py` |
| `SEMANTICALLY_EQUIVALENT` | `20250322_0003` | 5 | 5 | `20250322_0003_order_validation_state.py` |
| `SEMANTICALLY_EQUIVALENT` | `20250323_0004` | 9 | 9 | `20250323_0004_core_enforcement.py` |
| `SEMANTICALLY_EQUIVALENT` | `20250323_0005` | 1 | 1 | `20250323_0005_citizen_email_nullable.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260324_0006` | 5 | 5 | `20260324_0006_patient_family_guardian.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260324_0007` | 4 | 4 | `20260324_0007_lab_type_director_website.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260324_0008` | 2 | 4 | `20260324_0008_lab_result_test_type_fk_set_null.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260324_0009` | 3 | 3 | `20260324_0009_audit_chain_hash_result_engine_version.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260324_0010` | 0 | 0 | `20260324_0010_production_indexes.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260329_0011` | 15 | 15 | `20260329_0011_subscription_tiers_feature_flags.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260329_0012` | 7 | 7 | `20260329_0012_lab_result_version_citizen_indexes.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260407_0001` | 7 | 7 | `20260407_0001_claims_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260413_0001` | 17 | 17 | `20260413_0001_mpi_citizen_registry.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260417_0001` | 4 | 4 | `20260417_0001_consent_table.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260428_0001` | 20 | 20 | `20260428_0001_edge_platform.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260503_0001` | 7 | 7 | `20260503_0001_stats_trends_perf_indexes.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0001` | 7 | 7 | `20260505_0001_sndhs_phase1_extend_patients.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0002` | 3 | 3 | `20260505_0002_sndhs_phase1_index_national_id.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0003` | 5 | 5 | `20260505_0003_sndhs_phase1_visits_table.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0004` | 4 | 4 | `20260505_0004_sndhs_phase1_lab_orders_visit_id.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0005` | 13 | 13 | `20260505_0005_sndhs_phase1_audit_logs_v2.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260505_0006` | 6 | 6 | `20260505_0006_sndhs_phase1_constraints.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260506_0001` | 30 | 32 | `20260506_0001_financial_engine_phase_a.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260511_0001` | 18 | 18 | `20260511_0001_ai_interactions_dataset.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260511_0002` | 3 | 3 | `20260511_0002_ai_safety_hallucination_columns.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260714_0001` | 100 | 100 | `20260714_0001_national_lims_tables.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260715_0001` | 6 | 9 | `20260715_0001_national_ecosystem_partners.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0001` | 66 | 66 | `20260716_0001_nhdw_platform.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0002` | 73 | 73 | `20260716_0002_nursing_platform.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0003` | 92 | 92 | `20260716_0003_pharmacy_platform.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260716_0004` | 86 | 98 | `20260716_0004_radiology_platform.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0005` | 42 | 42 | `20260716_0005_national_ems_and_disaster_response_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0006` | 42 | 42 | `20260716_0006_national_blood_bank_and_transfusion_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0007` | 48 | 48 | `20260716_0007_national_critical_care_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0008` | 44 | 44 | `20260716_0008_national_biomedical_engineering_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0009` | 24 | 24 | `20260716_0009_national_public_health_and_disease_surveillance_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0010` | 15 | 15 | `20260716_0010_national_health_command_center_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0011` | 18 | 18 | `20260716_0011_national_pilot_deployment_and_readiness_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0012` | 12 | 12 | `20260716_0012_national_platform_lifecycle_and_governance_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0013` | 9 | 9 | `20260716_0013_national_trust_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0014` | 11 | 11 | `20260716_0014_governance_identity_persistence.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0015` | 7 | 7 | `20260716_0015_auth_security_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260716_0016` | 14 | 14 | `20260716_0016_canonical_patient_unification.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260719_0001` | 8 | 22 | `20260719_0001_ai_platform_tables.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260720_0001` | 1 | 1 | `20260720_0001_gap_closure_composite_indexes.py` |
| `REMOTE_CHANGE_REQUIRED` | `20260722_0001` | 49 | 37 | `20260722_0001_authorization_expansion.py` |
| `SEMANTICALLY_EQUIVALENT` | `20260723_0001` | 22 | 22 | `20260723_0001_niam_identity_platform_tables.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260723_0002` | 73 | 74 | `20260723_0002_niam_completion_tables.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260802_0001` | 13 | None | `20260802_0001_widen_patient_health_id.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260802_0002` | 200 | None | `20260802_0002_stable_fk_indexes.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260804_0001` | 15 | None | `20260804_0001_communication_experience.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260805_0001` | 3 | None | `20260805_0001_claims_lab_idempotency.py` |
| `CONFLICT` | `20260805_0002` | 69 | None | `20260805_0002_stable_identity_platform.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260806_0001` | 23 | None | `20260806_0001_domain_platform.py` |
| `LOCAL_CHANGE_REQUIRED` | `20260810_0001` | 9 | None | `20260810_0001_professional_authorizations.py` |

### 7.2 Remote-only migrations (adopt from base)

51 revisions exist only on `origin/main`, spanning `20260811_0001_wave3_identity_mapping` … `20260908_0002_clinical_command_receipts`. They are adopted wholesale; no local counterpart exists. Full list in the TSV.

## 8. Decisions and next actions

1. **DECIDED** — workspace architecture = Section 6 Option 1 (supersede local platform). Unblocks `20260805_0002`, `20260806_0001`, `20260810_0001`.
2. Author forward migrations F1…Fn on `integration/gula-unification-v1` with `down_revision` chained from `20260908_0001`; keep every operation idempotent (`IF NOT EXISTS` / inspector guards); never rewrite existing remote revisions.
3. Restore the 24 indexes lost in `20260722_0001` via a new forward migration (F7) — do **not** modify the applied base revision.
4. Execute the migrated chain on a **disposable** PostgreSQL database only (`172.18.0.2:5432`, user `postgres`, DB `gula_unify_scratch`) and prove clean-DB creation + downgrade + re-upgrade. Never touch the existing `gula` database.
5. Then proceed to code reconciliation inventory (backend/app, security/, frontend-v3, scripts, docs) and the remaining five GOVERNANCE deliverables.

---
_Generated from static AST analysis; PostgreSQL DDL effect assessed per file. No database was written during this task._
