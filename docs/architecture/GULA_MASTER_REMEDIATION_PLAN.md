# GULA Master Remediation Plan

**Generated:** 2026-09-08 · **Head:** `604b245` · **production_ready:** `false`
**Source register:** [`GULA_MASTER_NEGATIVE_REGISTER.md`](./GULA_MASTER_NEGATIVE_REGISTER.md)

## 0. Principle

Move from feature-driven to **risk-driven, evidence-driven, domain-driven, safety-driven**
development. A fix is complete only when an **executed** verification exists. No item is
marked verified on inspection alone.

## 1. Priority order

### P0 — must be resolved before any production certification

| ID | Item | State | Next action |
|---|---|---|---|
| NR-001 | `clinical_command_receipts` unreachable (8 domains affected) | **DONE** | none — guarded by `tests/migrations/test_migration_graph_integrity.py` |
| NR-002 | Three unmerged Alembic heads | **DONE** | none — guarded by the same test |
| NR-003 | Pharmacy PK type divergence blocks `upgrade head` | **OPEN — the only true blocker** | Architecture decision, then a migration strategy for 23 tables |

### P1

| ID | Item | State | Next action |
|---|---|---|---|
| NR-004 | Blood-unit `reserved` transition shadowed | **DONE** | none |
| NR-005 | Unguarded duplicate index | **DONE** | none |
| NR-006 | `national_facilities` dual ownership | OPEN | Ownership decision; then one writable mapping + a test enforcing one owner per table |
| NR-007 | Entity-agnostic clinical state machine | OPEN | Key transitions by `(entity, state)`; property-based test over all pairs |

### P2

NR-008 lock-file drift · NR-009 artifact quota · NR-010 CI failure masking ·
NR-011 frontend accessible name · NR-012 replay contract documentation.

### P3+

NR-013 audit coverage · NR-014 capacity numbers · NR-015 Postgres auth noise.

## 2. Wave mapping

Existing waves are reused; no new wave was invented.

| Wave | Content | Exit criteria |
|---|---|---|
| **WAVE 1** — Blood Bank + migration integrity | NR-001, NR-002, NR-004, NR-005 done; NR-009 external | Blood Bank suite green; single Alembic head; clean-DB Blood Bank lineage. **Wave 1 cannot be certified while NR-003 blocks `upgrade head`.** |
| **WAVE 2** — Deployment integrity + ownership | NR-003, NR-006, NR-007, NR-008, NR-010, NR-011, NR-012, NR-015 | `upgrade head` exits 0 on an empty database; one owner per table; per-entity state machine |
| **WAVE 3** — Scale + capacity | NR-014 | Capacity model validated by load test |
| **WAVE 4..10** — Category audits | NR-013 (identity/MPI, consent/privacy, offline/sync, interoperability, AI, security, DR, domain audits) | Each category has executed evidence and a status |

## 3. Top architectural remediations — status against §24 of the brief

Only genuinely missing artefacts are listed as new. Existing documents are linked.

| Artefact | Verdict |
|---|---|
| Domain & Data Ownership Constitution | **NEEDED** — NR-006 proves ownership is unenforced. Extend `CANONICAL_ARCHITECTURE.md` rather than starting fresh |
| National Identity + MPI specification | **UNKNOWN** — not audited; see `identity-platform.md` before authoring |
| Authorization & Privacy Constitution | **PARTIAL** — `IAM_PHASE_08/09` exist; privacy/consent unaudited |
| Clinical Integrity & State-Machine Standard | **NEEDED** — NR-007 |
| Distributed Systems / Offline / Sync Standard | **NEEDED** — nothing verified |
| Interoperability & Terminology Standard | **PARTIAL** — `ADR-011-fhir-strategy.md` exists; conformance unverified |
| Production / DR / Security Certification Standard | **NEEDED** |
| Master Evidence Matrix | **STARTED** — §9 of the register |
| Platform Idempotency Standard | **MOSTLY EXISTS in code** — `ClinicalCommandGuard` is the de-facto standard and is proven; write it up rather than redesign |
| Event / Outbox / Inbox Standard | **UNKNOWN** — not audited |
| Graceful Degradation Matrix, Clinical Downtime Procedure | **NEEDED** |
| National Reference Data Governance, Provider Identity, Device Identity, AI Governance | **NOT AUDITED** |
| Platform Error Taxonomy | **PARTIAL** — a safe error envelope exists and is proven (NR-012) |
| National Data Classification | **NOT AUDITED** |

## 4. Anti-overengineering rules for this plan

- Do not convert a finding into a new service or framework.
- Do not provision infrastructure before NR-014 produces numbers (Green GULA).
- Do not author a standard where one already exists — extend it.
- Do not mark anything verified without an executed result.

## 5. Recommended next single action

**Resolve NR-003.** It is the only remaining item that makes production deployment
impossible, and it blocks Wave 1 certification. It needs an architecture decision first
(canonical pharmacy primary-key type), not code. Everything else can proceed in parallel.
