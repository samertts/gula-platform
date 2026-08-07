# ADR-033: Search & PDF Completion (doc-intel search → capabilities/search_service; national document PDF → shared/pdf)

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO
**Supersedes:** (none — applies ADR-029 to the `search` and `document_engine` capabilities)
**Related:** ADR-028, ADR-029, ADR-024

---

## Context

The structural migration phase (ADR-028) reduces the acknowledged Shared Core
reimplementation findings in
`.ai/core/architecture/constitution_baseline.json` to canonical providers.

Wave 3 orders 14 and 15 are both **Canonical Provider Completions**
(ADR-029): the canonical provider is real but incomplete, and the finding is
either a duplicate live implementation that must become the canonical one
(search) or a delegator that is unwired to an already-complete canonical
implementation (PDF). The two orders are recorded in one ADR per the
classification Wave 3 table (ADR-033).

### Order 14 — Search (classification §2.11)

- **Finding #35:** `document_intelligence/application/service.py` —
  `DefaultSearchService` (real in-memory implementation of the `SearchService`
  ABC in `application/interfaces.py`).
- **Finding #36:** `document_intelligence/infrastructure/services.py` —
  `InfrastructureSemanticSearchService` (real in-memory semantic/hybrid/
  Arabic search).
- **Canonical provider:** `capabilities/search_service` — a scaffold whose
  router **IS live** at `/search-service` (registered in `factory.py`) but
  returns **hardcoded stub responses** (empty items, `success: True`). The
  real implementations are exercised by the `document_intelligence` composition
  root (`application/wiring.py`: `DefaultSearchIndexer` at 1129,
  `DefaultSearchService(search_indexer)` at 1172,
  `InfrastructureSemanticSearchService(doc_repo)` at 1186) behind a dormant
  orchestrator.

The canonical provider's live HTTP surface is a stub, while the real search
lives in the domain. Completion means the canonical provider becomes the real
search, and the domain consumes it.

### Order 15 — Document Engine / PDF (classification §2.4)

- **Finding #46:** `national/document_platform/api/routes.py` — `generate_pdf`
  (live endpoint that always returns HTTP 422).
- **Finding #47:** `national/document_platform/application/service.py` —
  `generate_pdf` (delegator that raises `DocumentValidationError` when
  `self.pdf_generator is None`).
- **Canonical provider:** `shared/pdf/generator.py` — **real** (reportlab A4
  platypus; `PDFTemplate`, `generate_result_pdf`, `generate_pdf`) — complete
  and exported via `shared/pdf/__init__.py`.
- The domain keeps its `PDFGenerator` ABC (interface only — classified Retain,
  not a finding). `DocumentPlatformService.__init__` accepts
  `pdf_generator: PDFGenerator | None = None`, but `_get_service`
  (`api/routes.py` lines 37–57) never supplies one → every `POST
  /national/documents/{id}/pdf` fails with 422. The endpoint simply needs
  wiring to the complete canonical generator.

## Decision

Adopt both completions as Canonical Provider Completions per ADR-029:

### Order 14 — Search (Commit 3.2)

1. **Promote the real implementations into the canonical provider.**
   `DefaultSearchIndexer`, `DefaultSearchService`, and
   `InfrastructureSemanticSearchService` move (via `git mv`, history
   preserved) into `capabilities/search_service/` so the canonical search
   provider is self-contained and populated.
2. **Complete the stub routes.** The live `/search-service/*` router keeps its
   paths, methods, parameters, and `get_current_user` dependency; the
   hardcoded stub responses are replaced by real index/search behavior
   through a canonical composition root. Route shapes are unchanged — only
   the stub responses become populated.
3. **Re-point the domain consumers atomically.** `document_intelligence`
   (`application/wiring.py` imports at 58/1089 and instantiations at
   1129/1172/1186) consumes the canonical provider in the same commit;
   **no facade** is created under the vacated module paths (ADR-029 Rule 4).
   The document_intelligence API surface remains domain-owned and keeps
   working, now backed by canonical search.
4. **The dormant orchestrator stays dormant.** Promotion does not activate
   unfinished functionality; it makes the canonical provider real and keeps
   the dependency direction correct.

### Order 15 — Document Engine / PDF (Commit 3.3)

1. **Add a thin concrete adapter.** `national/document_platform/infrastructure/
   pdf_generator.py` implements the domain `PDFGenerator` ABC over the
   canonical `shared/pdf/generator.py` (async wrapper delegating to the sync
   reportlab generator; document fields passed in the content dict).
2. **Wire it at the composition root.** `_get_service` (`api/routes.py`
   lines 49–57) supplies `pdf_generator=<adapter>`, so `POST
   /national/documents/{id}/pdf` returns a real PDF instead of 422.
3. **Canonical stays untouched.** `shared/pdf` is already complete; no change.
   The `PDFGenerator` ABC is retained as the domain contract (interface only).

### Common rules

Both orders: behavior is preserved or strictly additive at the targeted
stub/failing endpoints only; everything else is byte-identical. ADR-028
Rules 1–7 and ADR-029 Rules 1–6 apply verbatim (evidence, backend authority,
Migration Impact Report, single-`git-revert` reversibility, one commit at a
time with a stop for approval).

Baseline trajectory: 35 → 33 (search, Commit 3.2) → 31 (PDF, Commit 3.3).

## Alternatives Considered

### Order 14 — Search

**A. Archive-and-repoint the doc-intel search → canonical stub.**
Rejected: the canonical scaffold has no implementation to re-point to;
re-pointing real code at a stub would delete working search behavior and
leave `/search-service` hardcoded forever.

**B. Register doc-intel search as canonical by exception.**
Rejected: whitelisting `document_intelligence` search modules without moving
them keeps Shared Core implementation inside a domain and requires a
constitution exception.

**C. Reimplement search inside the canonical provider from scratch.**
Rejected: duplicates complete, working, test-covered implementations with no
behavior gain; promotion carries the proven code instead.

### Order 15 — PDF

**D. Reimplement PDF inside the document platform.**
Rejected: `shared/pdf/generator.py` is complete; reimplementing it in the
domain duplicates the canonical capability.

**E. Remove the PDF endpoint.**
Rejected: deletes a live (albeit 422) HTTP surface; completion is
behavior-additive and cheaper, with no data or contract loss.

**F. Leave the endpoint unwired.**
Rejected: the endpoint stays broken (422) and the finding stays open — the
exact defect this migration exists to close.

## Consequences

**Positive**

- The `search` Shared Core capability finally has a real, populated canonical
  provider: `capabilities/search_service` becomes a working search service.
- The canonical `shared/pdf` is finally consumed; the national document
  platform's PDF endpoint works.
- The acknowledged-findings baseline shrinks by ownership correction
  (35 → 33 → 31) and never re-opens the duplicates.
- Domain Sovereignty improves: document intelligence and the national document
  platform consume Shared Core capabilities instead of implementing them.
- Behavior is preserved or strictly additive — verified by the identical
  backend suite, identical boot route count, and unchanged OpenAPI contract
  (the targeted endpoints' *response values* become real, never their shapes).

**Negative**

- The vacated doc-intel module paths for the search implementations would
  break any out-of-repo direct importer (none exist in-repo; consumers are
  re-pointed atomically in the same commits).
- The canonical search provider gains the promoted implementations
  (~500 LOC); the document platform gains one thin PDF adapter — both
  intended ownership shifts.

**Neutral**

- Frontend generated clients already reference `/search-service/` and
  `/national/documents/` — no frontend contract change.
- Dormant shells and orchestrators remain dormant; no unfinished
  functionality is activated.

## References

- ADR-029 — Canonical Provider Promotion (`docs/adr/ADR-029-canonical-provider-promotion.md`)
- ADR-028 — Structural Migration Rules (`docs/adr/ADR-028-structural-migration.md`)
- ADR-024 — Platform Constitution (`docs/adr/ADR-024-Platform-Constitution.md`)
- `backend/app/domain_platform/shared_core.py` — `SHARED_CORE_CATALOG` (`search`, `document_engine`)
- `backend/app/capabilities/search_service/` — canonical search provider (scaffold → populated)
- `backend/app/document_intelligence/` — `application/service.py`, `infrastructure/services.py`, `application/wiring.py` (promoted + re-pointed)
- `shared/pdf/generator.py` + `shared/pdf/__init__.py` — canonical PDF (complete)
- `backend/app/national/document_platform/` — `api/routes.py`, `application/service.py`, `application/interfaces.py` (wired to canonical PDF)
- `docs/baselines/ARCHITECTURAL_MIGRATION_CLASSIFICATION.md` — §2.11 (#35/#36), §2.4 (#46/#47), Wave 3 table
- `docs/baselines/COMMIT_3_2_VERIFICATION_REPORT.md` / `COMMIT_3_3_VERIFICATION_REPORT.md` — execution evidence
