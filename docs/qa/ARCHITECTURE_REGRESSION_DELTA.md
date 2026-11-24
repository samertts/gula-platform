# Architecture Regression Delta

Workstream 7. **No prior "BATCH-2/BATCH-3" architecture-sweep report was
found in this repository** (`find . -iname "*BATCH*"` turns up unrelated
matches — a `BatchProcessor.tsx` component, a document-processing
`batch_processor.py`, dependabot/mypy branch names, and an unrelated
`BATCH1_CLOSURE_AUDIT.md`/`13_batch1_completion.md` pair covering a
different subject). This is therefore a **fresh baseline sweep**, not a
delta against prior architecture-sweep history — stated honestly rather
than fabricating a comparison that doesn't exist. Its own findings should
serve as the baseline for any future delta.

Findings only — nothing in this section was changed as a result of
running it, per this workstream's own instruction ("do not modify the
architecture merely because a detector reports a difference").

| # | Check | Finding | Classification | Evidence |
|---|---|---|---|---|
| 1 | Migration head count | Exactly one head (`20260908_0003`) | **KEEP** | `alembic heads` |
| 2 | Duplicate migration revisions | None | **KEEP** | `grep -rh '^revision = ' \| sort \| uniq -c` — every count 1 |
| 3 | Duplicate migration filenames | None | **KEEP** | `ls migrations/versions/ \| sort \| uniq -c` |
| 4 | ORM↔physical schema drift | `TrustFramework.authority_id`/`AssuranceProfile.authority_id` referenced a nonexistent `niam_identity_authorities` — the *migration* was already correct (`niam_gov_authorities`); only the ORM string had drifted | **RECONCILE — already done this session** (`NIAM_LIVE_PATH_PROOF_3.md`) | `20260723_0002_niam_completion_tables.py:312` vs. the pre-fix `trust/models.py` |
| 5 | Cross-`MetaData` relationships | `niam_assignments.clinical_organization_resource_id` → `organizations` (legacy `Base`), `.clinical_facility_resource_id` → `facilities` (legacy `Base`) — `IdentityBase`'s own tables cannot be created in isolation from the legacy monolith's `Base` | **CROSS_DOMAIN_OWNER** — real, structural, not a bug to "fix" by removing the FK (the cross-reference is presumably intentional: a NIAM assignment scoped to a real organization/facility) | Confirmed twice this session (`NoReferencedTableError` when attempting `IdentityBase.metadata.create_all()` in isolation, both for `organizations` and `facilities`) |
| 6 | Duplicate `Base` declarations | **21** separate `declarative_base()` calls (19 real domain namespaces: `Base`, `IdentityBase`, `NationalBase`, `EHRBase`, `CareContinuumBase`, `CitizenPlatformBase`, `ClinicalBase`, `GovernanceBase`, `HealthDataBase`, `HospitalBase`, `DataPlatformBase`, `NHDWBase`, `NursingBase`, `PharmacyBase`, `RadiologyBase`, `TrustBase`, `FinBase`, `InsBase`, `DocIntelBase`; 2 are string-literal codegen templates, not live code) | **KEEP** — an intentional, pre-existing multi-domain-metadata architecture, not a duplication defect. Its real, evidenced *consequence* is finding #5 (cross-Base FKs create friction exactly where two domains' data genuinely relate) | `grep -rn "declarative_base()"` |
| 7 | Shadow application trees | `IdentityBase` is not part of `tests/conftest.py`'s merged-metadata SQLite fixture (`_all_metas` lists 16 Bases, `IdentityBase` absent) | **DEFER** — this is *why* every NIAM test in this repo uses hand-built fake sessions instead of a real (even SQLite) DB; merging it in would need finding #5 resolved first (cross-Base FK target availability) | `tests/conftest.py`'s `_session_engine` fixture; empirically confirmed attempting to add `IdentityBase.metadata.create_all()` standalone fails on both `organizations` and `facilities` |
| 8 | Duplicate kernels | None — exactly one `Kernel` class (`app/kernel/__init__.py`) | **KEEP** | `grep -rln "class.*Kernel\b"` |
| 9 | Duplicate database engines | `app/database.py`'s sync engine + `app/identity/niam_async_db.py`'s async engine (this session's own addition, intentional — see `NIAM_LIVE_PATH_PROOF_2.md`'s justification for why a second pool is unavoidable). Two more `create_engine(...)` call sites found, both investigated and ruled out as false positives: `app/engineering/generators/microservice.py:130` is a **string-literal codegen template** (scaffolds a *new* microservice's `app/database.py`, never executed as live code here); `app/document_intelligence/application/wiring.py:951` is a real, hardcoded `sqlite:///docint.db` fallback inside `build_orchestrator()`, but that function is **never called anywhere in the real application** (confirmed via `grep` — its only other reference is an error message telling a caller they forgot to call it) | **KEEP** (the two real engines, justified) / **DEFER** (the dormant `docint.db` fallback — dead code today, but a real trap if `build_orchestrator()` is ever wired up without a real `session_factory`) | `grep -rn "create_engine\|create_async_engine"`, call-site trace |
| 10 | Duplicate task/workflow runtimes | **NOT CHECKED** this pass — out of time budget; no evidence gathered either way | **UNKNOWN** |
| 11 | State-key / identity-key collisions | **NOT CHECKED** this pass beyond what NIAM-specific work already covered (Platform Authority's own partial unique index, Phase 10) | **UNKNOWN** for the rest of the codebase |
| 12 | Tenant-column inconsistencies | **NOT CHECKED** this pass — the existing `tenant-scope-sweep`/`scanner-false-positives` rows in `MUSTAFA_ACTIVE_REPAIR_QUEUE.md` already cover this extensively for other domains; not re-run here (unchanged surface) | **KEEP** (per existing queue, not re-verified this pass) |
| 13 | String PK vs Integer mismatches | The historically-known `pharmacy_drug_substitution_rules` FK type mismatch (Phase 10, still unfixed, still blocks a bare `alembic upgrade head` from blank) — re-confirmed present again this session (same workaround used: stamp past it) | **KEEP as documented, unfixed** — pre-existing, out of every phase's scope so far, needs a real migration fix (change the referencing column's type) |
| 14 | UUID truncation | **NOT CHECKED** this pass | **UNKNOWN** |
| 15 | API fields silently discarded | The entire Platform Authority field-boundary design (Phase 10) *is* this, by intent — deliberately allow-listed, not silent/accidental. No NEW instance found this pass. | **KEEP** (intentional design, not a defect) |
| 16 | Unbacked NOT NULL fields | `IdentityAuditEntry.uuid` — NOT NULL, no ORM/DB default, one call site (`CanonicalAuditService.record()`) never set it | **RECONCILE — already done this session** | `NIAM_LIVE_PATH_PROOF_3.md` |

## RESULT

**PARTIALLY VERIFIED.** 11 of 16 checklist items evidenced (6 clean/KEEP,
2 already reconciled this session, 3 deferred/cross-domain with concrete
reasoning); 5 not checked this pass (state-key collisions beyond NIAM,
duplicate task/workflow runtimes, UUID truncation, and tenant-column
inconsistencies deferred to the existing, more specialized queue rather
than re-run). No architecture was modified as a result of running this
sweep — every KEEP/DEFER/CROSS_DOMAIN_OWNER item is a finding, not an
action.
