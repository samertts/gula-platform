# GULA Global Vision Intelligence Index

**Not a runtime component.** This is the long-term architectural knowledge layer:
the tools and artifacts that answer *what exists, what is canonical, what is
duplicated, what is missing, what is obsolete, and what should eventually be
built* across the complete GULA platform.

**Rule: nothing listed here may be deleted as "unused".** None of it is imported
by runtime, and that is by design — it sits outside production paths, carries no
runtime dependencies, and is meant to be picked up months later.

---

## 1. Detectors and scanners — `tools/gula_intel/`

| Tool | Answers |
|---|---|
| `GULA-MIG-001` / `MIG-002` | Is the migration graph sound? Duplicate revisions, unmerged heads |
| `GULA-ARCH-001` | Which physical tables are claimed by two ORM classes? |
| `GULA-ARCH-002` | Which declarative bases are invisible to autogenerate? |
| `GULA-SCHEMA-001` | Does the ORM match the migration-built schema? |
| `GULA-SCHEMA-002` | Cross-domain ORM ↔ physical drift, all bases |
| `GULA-SCHEMA-003` | Which ORM tables have no physical table? |
| `GULA-SCHEMA-004` | Which cross-domain dependencies are unresolvable? |
| `GULA-STATE-001` | Clinical state-machine collisions |
| `DetectorState` | ABSENT / NOT_RUN / RAN_CLEAN / RAN_NO_EVIDENCE / RAN_FOUND / NOT_APPLICABLE — a detector that could not run never reports clean |

**Why it matters later:** these are how the complete platform gets audited without
re-deriving the repository by hand. 43 tests keep them honest.

## 2. Evidence collectors — `scripts/enterprise_readiness/`

`scan.py` (repository inventory) · `delta.py` (change between scans) ·
`reach2.py` (exact-name reachability — *not* import closure, which over-attributes) ·
`join.py` · `routes_reachable.py` (route decorators overstate by 304) ·
`ci_truth.py` (which workflows actually gate a PR) · `disposition.py`

## 3. Machine-readable registries — `docs/enterprise-readiness/`

| Artifact | Answers |
|---|---|
| `GULA_MASTER_COMPLETION_MAP.{md,json}` | What exists, at what state, in every domain |
| `GULA_CANONICAL_DISPOSITION_MATRIX.{md,json}` | Per-table disposition across 807 mapped tables |
| `GULA_CANONICAL_ARCHITECTURE_DECISIONS.{md,json}` | D-01…D-19 — every canonical decision and its evidence |
| `GULA_NATIONAL_CORE_IDENTITY_CONTRACT.{md,json}` | Per-entity identity and the ownership matrix |
| `GULA_BATCH_3_NATIONAL_CORE_SPEC.{md,json}` | Frozen scope: B3_REQUIRED / DEPENDENCY / B4+ / DEFER / RETIRE / BLOCKED |
| `GULA_VISIT_ENCOUNTER_ARCHITECTURE.{md,json}` | The clinical episode anchor and its consumers |
| `GULA_CLINICAL_STATE_REGISTRY.{md,json}` | Every state key, its owner, and what is unattributed |
| `GULA_NR029_FK_TARGET_RECONCILIATION.{md,json}` | How a dangling FK class was diagnosed |
| `GULA_NR030_PHYSICAL_ORM_OWNERSHIP.{md,json}` | Every physical table with no ORM owner |
| `GULA_BLOOD_BANK_AUDIT_GAP.{md,json}` | Audit coverage per mutating route |
| `GULA_BLOOD_BANK_LEGACY_BYPASS.md` | Legacy vs canonical command paths |
| `GULA_CI_TRUTH.{md,json}` | Which checks actually gate |
| `GULA_GLOBAL_CAPABILITY_RADAR.{md,json}` | External healthcare capabilities, with licences |
| `GULA_OSS_CANDIDATE_REGISTRY.{md,json}` | Reusable open-source components |
| `GULA_HEALTHCARE_IDEA_BACKLOG.{md,json}` | What should eventually be built |
| `GULA_DELETION_CANDIDATES.md` | The reduction map, and why the naive scan fails |

## 4. Decision and defect history — `docs/architecture/`

`GULA_MASTER_NEGATIVE_REGISTER.{md,json}` — 30 findings with root cause, evidence
strength, impact axes, minimal safe fix and acceptance criteria. **Includes the
corrections**: where an earlier finding was wrong and why. That record is the
reason the architecture is trustworthy; it must not be pruned to look tidier.

`ARCHITECTURE_DECISION_LOG.md`, `CANONICAL_ARCHITECTURE.md`, `ENTITY_CATALOG.md`,
`ADR-008`…`ADR-012`, `GULA_MASTER_REMEDIATION_PLAN.md`, and the
`GULA_P0_P1_REMEDIATION_*` series.

## 5. Guards that encode findings — `backend/tests/`

Not merely tests: each pins a measured fact so it cannot silently drift.

| Guard | Pins |
|---|---|
| `test_alembic_metadata_registry.py` | 5 fail-closed metadata conditions, incl. the DROP-TABLE set |
| `test_nursing_domain_contract.py` | The exact scope of the nursing reconciliation |
| `test_identity_contract_guards.py` | Identifier scheme, legacy episode widths |
| `blood_bank/test_state_registry_guard.py` | State collisions and machine participants |
| `blood_bank/test_audit_chain_coverage.py` | One mutation → one effect → one audit event |
| `blood_bank/test_sample_transition_idempotency.py` | Durable replay semantics |
| `blood_bank/test_tenant_isolation_nr021.py` | Server-decided tenancy |
| `scripts/tests/test_quality_changed_files_gate.py` | A check that did not run is never PASS |

## 6. Preservation rule

Runtime code may be retired. **Discovery knowledge must not disappear because a
runtime implementation is deferred.** Before retiring anything, check this index;
if the item appears here, or materially helps answer the questions in §1, it is
`PRESERVE_FOR_GLOBAL_VISION` regardless of runtime reachability.
