# ADR-031: Audit Re-Point to Canonical (doc-intel + task_engine → identity AuditService)

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — applies ADR-028 to the `audit` capability)
**Related:** ADR-028, ADR-029, ADR-032, ADR-033, ADR-035, ADR-024, ADR-011

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers
(`SHARED_CORE_CATALOG` in `backend/app/domain_platform/shared_core.py`).

Wave 4 orders 16 and 17 target the `audit` capability (classification §2.2).
The canonical provider is the **complete, live, hash-chained audit service**:

- `backend/app/identity/services/audit_service.py::AuditService` — `record()`
  (enum-typed actions), `record_event()` (free-form actions), and
  `verify_chain_integrity()`, persisting immutable SHA-256 hash-chained rows to
  the `niam_audit_entries` table (`backend/app/identity/models/audit.py`).
- The immutable hash chain is constitutionally required ("Immutable Audit
  Log", PROGRAM-CONSTITUTION-001). Any audit implementation that does not
  persist to the canonical hash-chained log is a duplicate or a silent drop.

### Finding #5 (order 16)

`backend/app/document_intelligence/application/wiring.py` — `DefaultAuditService`
is a **no-op logger**: `log_event` only emits `logger.info("AUDIT: …")` and
`get_document_history` always returns `[]`. It is injected into six doc-intel
services (`DefaultIngestionService`, `DefaultOcrPipelineService`,
`DefaultClassifierService`, `DefaultEntityExtractionService`,
`DefaultFhirMappingService`, `DefaultKnowledgePipelineService`) and the
`DocumentIntelligenceOrchestrator` composition root. The doc-intel domain
`AuditService` ABC (`application/interfaces.py`) is **retained as Domain-Owned**
(classification #4) — only the concrete no-op is a reimplementation.

The doc-intel orchestrator is **dormant**: `build_orchestrator()` is exported
and the `/document-intelligence` router is registered in `factory.py`, but the
router's `get_orchestrator()` dependency raises unless `build_orchestrator()`
has been called, and nothing calls it in production or tests. Today any audit
event is silently dropped.

### Finding #9 (order 17)

`backend/app/national/task_engine/infrastructure/repository.py` —
`SQLAlchemyTaskAuditLogRepository` is a **silent no-op** that drops audit
records: it implements the retained domain contract
`national/task_engine/domain/repository.py::TaskAuditLogRepository` (ABC,
classification #8) but persists nothing. Same defect class as #5 — audit rows
that should exist never appear, with no error.

**Behavioral equivalence:** the canonical provider is complete and stronger
than either finding (DB-backed, immutable, hash-chained, verified). Both
findings are stubs, so re-pointing them is **behavior-additive**: audit rows
begin appearing where nothing was recorded before. This is the intended,
positive behavior change.

**Consumer inventory (complete):**
- `DefaultAuditService` is referenced only inside `wiring.py`
  (definition line 67, composition line 1056). It is not exported by
  `app.document_intelligence.__init__`, and no test or other module imports it.
- `SQLAlchemyTaskAuditLogRepository` consumers are determined in the order-17
  commit (commit 3.5).

Both changes are not removals of working behavior and not promotions of a
canonical-equivalent — they are re-points of duplicate no-op stubs onto the
existing canonical provider, so they are recorded as an ADR (Documentation
Policy).

## Decision

Re-point both audit stubs onto the canonical `identity` `AuditService`, per
ADR-028 and ADR-029:

1. **#5 — archive the no-op, re-point the doc-intel composition root.**
   - The `DefaultAuditService` class is removed from
     `document_intelligence/application/wiring.py` and preserved verbatim in
     `archive/platform-shared-core/document_intelligence_default_audit_service.py`.
   - The doc-intel domain `AuditService` ABC (interfaces.py) is untouched
     (Retain as Domain-Owned, classification #4).
   - `build_orchestrator()` gains an optional `audit_session_factory`
     parameter (default: lazy async session factory derived from the
     `DATABASE_URL` environment, mirroring the platform's sync URL) and
     constructs `CanonicalAuditAdapter(audit_session_factory)`, a thin
     composition-root adapter that implements the retained doc-intel ABC by
     delegating to the canonical provider:
     - `log_event(event_type, document_id, details)` →
       `canonical AuditService(session).record_event(action=event_type,
       target_type="document", target_id=str(document_id),
       metadata=details)` then `commit()`.
     - `get_document_history(document_id)` → selects canonical
       `IdentityAuditEntry` rows by `target_type="document"` and
       `target_id`, returning `to_dict()` shapes.
   - The adapter is **fail-closed**: if the async session cannot persist
     (no `DATABASE_URL`, missing table, driver error), the call raises —
     audit is never silently dropped. The doc-intel orchestrator remains
     dormant; nothing constructs it in production or tests, so no startup
     behavior changes.
2. **#9 — archive the no-op, re-point the task_engine repository.**
   The task_engine `SQLAlchemyTaskAuditLogRepository` is archived and its
   composition/consumer re-pointed to the canonical `AuditService` via the
   same `record_event(..., target_type="task", ...)` contract. The retained
   domain ABC (#8) is untouched. Detailed re-point (consumers, route wiring)
   is executed in the order-17 commit (commit 3.5) per ADR-028 Rule 1.
3. **No schema change.** The canonical `niam_audit_entries` table and its
   migration are untouched; no new tables are added.
4. **No API change.** No HTTP route, request, or response shape changes;
   OpenAPI must remain byte-identical (verified in the Wave-4 full cycle).
5. **ADR-028 Rules 1–7 apply verbatim.** Both commits preserve behavior,
   carry evidence, keep the backend authoritative, produce Migration Impact
   Reports, stay reversible via a single `git revert`, and execute one commit
   at a time with a stop for approval.
6. **The shared canonical provider is never duplicated again.** The
   architecture gate continues to fail any NEW `audit` signal outside the
   canonical path (ADR-028 Rule 3).

The first application is Commit 3.4 (order 16), resolving finding #5
(31 → 30). The second is Commit 3.5 (order 17), resolving finding #9
(30 → 29).

## Alternatives Considered

### A. Do nothing (keep the no-ops)

Rejected. A no-op audit is a **silent audit drop** — a direct violation of the
Immutable Audit Log constitution and the same defect class as #9. The two
findings exist precisely because these stubs shadow the canonical provider.

### B. Reimplement a local DB-backed audit inside each domain

Rejected. This recreates the Shared Core `audit` reimplementation inside a
domain (inverted dependency, domain-sovereignty violation) and forks the
immutable hash chain into multiple DBs. The canonical provider already exists,
is complete, and is tested.

### C. Promote the doc-intel stub into canonical and complete it

Rejected. The canonical provider is already complete and stronger (immutable,
hash-chained, verified). Promoting a weaker no-op stub backwards would
downgrade the canonical provider and recreate the finding.

### D. Keep a synchronous adapter writing to `niam_audit_entries`

Rejected. The canonical `AuditService` is async (`AsyncSession`); reimplementing
synchronous persistence against the same table would duplicate the canonical
write logic (the exact duplication being removed) and fork the hash chain
computation.

### E. Create a re-export facade at the old class path

Rejected. ADR-029 Rule 4 forbids a facade under the vacated path; all in-repo
consumers are re-pointed atomically in the same commit instead.

## Consequences

**Positive**

- The `audit` Shared Core capability has exactly ONE implementation: the
  canonical immutable hash-chained `AuditService` in `identity`.
- The acknowledged-findings baseline shrinks (31 → 30 → 29) and never
  re-opens either duplicate.
- Behavior-additive improvement: doc-intel and task_engine audit events begin
  appearing as immutable, verifiable rows instead of being silently dropped.
- Fail-closed semantics guarantee audit is never silently lost.

**Negative**

- `build_orchestrator()` changes its audit wiring (a `CanonicalAuditAdapter`
  replaces `DefaultAuditService`); any out-of-repo caller that imported
  `DefaultAuditService` directly would break (none exist in-repo).
- If an operator runs the doc-intel orchestrator without a configured
  `DATABASE_URL`/async driver, audit calls raise instead of no-op — intended
  (fail-closed), but a deliberate behavior difference from the old stub.
- The task_engine audit repository's exact consumers are re-pointed in the
  order-17 commit, which must be atomic (ADR-028 Rule 5).

**Neutral**

- The doc-intel `AuditService` ABC and task_engine `TaskAuditLogRepository`
  ABC remain Domain-Owned (classification #4/#8).
- The `/document-intelligence` and task-engine HTTP surfaces are unchanged.

## References

- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-032 — Notifications Queue Completion (`docs/adr/ADR-032-notifications-queue-completion.md`)
- ADR-033 — Search + PDF Completion (`docs/adr/ADR-033-search-pdf-completion.md`)
- ADR-035 — Rule Engine Promotion (`docs/adr/ADR-035-rule-engine-promotion.md`)
- ADR-024 — Platform Constitution (`docs/adr/ADR-024-Platform-Constitution.md`)
- `backend/app/identity/services/audit_service.py` — canonical `AuditService`
- `backend/app/identity/models/audit.py` — `AuditAction`, `IdentityAuditEntry` (`niam_audit_entries`)
- `backend/app/document_intelligence/application/wiring.py` — `DefaultAuditService` (archived), `CanonicalAuditAdapter`
- `backend/app/national/task_engine/infrastructure/repository.py` — `SQLAlchemyTaskAuditLogRepository` (archived)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`audit`)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2.2 (#5/#9), Wave 4 table
