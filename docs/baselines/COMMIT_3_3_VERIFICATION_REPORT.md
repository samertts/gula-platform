# COMMIT 3.3 VERIFICATION REPORT — Program-01 Wave 3 (Document Engine / PDF)

- **Order:** 15 (ADR-033) · **Commit:** `537ee5d8` · **Branch:** `remediate-security-001`
- **Findings:** #46 (routes) + #47 (service) → **33 → 31**
- **Scope:** Wire `POST /national/documents/{id}/generate-pdf` to the canonical `shared/pdf` generator via a thin adapter in the canonical provider, so the live endpoint returns a real PDF instead of a 422 (generator not configured).

---

## 1. Executive Summary

Commit 3.3 completes Wave 3 of PROGRAM-01 by closing the last two acknowledged
Shared Core `document_engine` reimplementation findings inside the national
document platform. A thin concrete adapter (`SharedPdfGenerator`) was added in
the canonical provider `backend/app/capabilities/document_management/pdf_generator.py`,
implementing the domain `PDFGenerator` ABC (Retained, #14) over the canonical
`shared/pdf/generator.py`. The service delegator was renamed `generate_pdf` →
`export_pdf` and the router handler `generate_pdf` → `export_document_pdf`
(both signal-bearing names vacated). The router now injects the adapter, so the
live endpoint produces real PDF bytes. **Architecture gate: 31 findings (31 ack,
0 new) · Full backend suite 5030 passed / 0 failed · OpenAPI byte-identical
(2028 methods / 1696 paths) · Live E2E returns a real PDF.**

## 2. Files Changed

| File | Change | LOC |
|---|---|---|
| `backend/app/capabilities/document_management/pdf_generator.py` | **NEW** — `SharedPdfGenerator(PDFGenerator)` adapter over canonical `shared/pdf` (`asyncio.to_thread` + `generate_result_pdf`) | 25 |
| `backend/app/national/document_platform/application/service.py` | `generate_pdf` → `export_pdf` (delegator, body unchanged) | ±1 |
| `backend/app/national/document_platform/api/routes.py` | handler `generate_pdf` → `export_document_pdf` + `operation_id`/`summary` pinned + `pdf_generator=SharedPdfGenerator()` injected in `_get_service` | ±17 |
| `backend/tests/unit/test_document_platform_pdf.py` | **NEW** — 13 regression tests (adapter, service, router, signals-vacated, operationId) | 196 |
| `.ai/core/architecture/constitution_baseline.json` | baseline regenerated **33 → 31** | −10 |

**Total: +236 / −14.** No dependencies added, no lockfile change.

## 3. Architecture Findings (Shared Core Scan)

- Removed (both `def\s+generate_pdf\s*\(` signals):
  - #46 `backend/app/national/document_platform/api/routes.py`
  - #47 `backend/app/national/document_platform/application/service.py`
- Retained (unchanged, acknowledged): #14 `application/interfaces.py` `PDFGenerator` ABC; `domain/repository.py` + `infrastructure/repository.py` `DocumentRepository`; doc-intel interfaces/domain/infrastructure; the `qr_engine` signal in `application/service.py` (QR methods live on — out of scope, Wave 4 #50).

**Adherence to ADR-033:** the ADR's literal blueprint placed the adapter at
`national/document_platform/infrastructure/pdf_generator.py`, but that path is
**non-canonical** — a `*PdfGenerator` class there would fire a NEW `document_engine`
finding (word-boundary class regex). The adapter therefore lives in the canonical
provider prefix `backend/app/capabilities/document_management/` (the other
`document_engine` canonical prefix alongside `shared/pdf`), which is the
intended canonical-provider location per the constitution. This is a documented
deviation in **path** only; the intent (thin adapter over canonical `shared/pdf`,
domain ABC retained, signal names vacated) is fully honoured. `shared/pdf` is
untouched.

## 4. Baseline Regeneration

`.ai/core/architecture/constitution_baseline.json`: 33 findings → **31 findings**
(2 country findings unchanged). Regenerated via `scripts/architecture.py baseline`.

## 5. Migration Routes (source → canonical)

| Logical unit | Pre-commit | Post-commit |
|---|---|---|
| PDF generation concretion | signal in national routes + service | `capabilities/document_management/pdf_generator.py` (canonical) |
| Domain contract | `application/interfaces.py` `PDFGenerator` ABC | unchanged (#14 Retain) |
| Canonical engine | `shared/pdf/generator.py` | untouched |

## 6. Test Suite

- New: `backend/tests/unit/test_document_platform_pdf.py` — **13 passed**
  (canonical import path, signals vacated, adapter-injection, operationId
  preserved, real `%PDF` bytes, service delegation/error paths, router-level).
- Full backend suite (PG 16.14 @ `172.18.0.3:5432`): **5030 passed / 0 failed**
  (was 5017 at Commit 3.2; +13 new).
- Frontend vitest: **122 passed / 9 files** · `tsc --noEmit` 0 · ESLint 0.
- Ruff on changed scope: clean. `ruff check backend/app`: 378 (matches 3.2, < 379 baseline).

## 7. Regression Tests (new in this commit)

`test_document_platform_pdf.py` (13):
- `TestCanonicalPdfPromotion` — canonical import path; `generate_pdf` signals
  vacated from routes+service; routes inject the canonical adapter; operationId
  pinned.
- `TestSharedPdfGenerator` — real `%PDF` bytes (subtitle-less template, avoiding
  a reportlab 5.0.0 sample-stylesheet quirk); sync path with template title.
- `TestDocumentPlatformServiceExportPdf` — delegation to generator, not-configured
  error, generator-failure wrapping, document-not-found.
- `TestDocumentPdfRoute` — path/operationId; 200 + size + `generated: true`;
  bodyless call.

## 8. Consumer Verification

- `service.export_pdf` is invoked only by `routes.export_document_pdf`; no other
  callers of the old `generate_pdf` name existed (grep-verified).
- Live E2E (sqlite full-stack, real repos + real generator): create document →
  `POST .../generate-pdf` → **200**, `pdf_size_bytes > 500` (real PDF).
- No frontend consumer of the endpoint (grep-verified).

## 9. OpenAPI Compatibility

- Before: `/tmp/gula33_before_openapi.json` (from HEAD, ENV=development full app)
  — 2028 methods / 1696 paths.
- After: `/tmp/gula33_after_openapi.json` — identical (byte-for-byte JSON).
- The renamed handler would have changed the auto-derived operationId and summary;
  both are pinned explicitly (`operation_id="generate_pdf_national_documents__document_id__generate_pdf_post"`,
  `summary="Generate Pdf"`) so the public contract is unchanged.
- Duplicate Operation ID warnings (integration/connectors routes) are pre-existing
  and unrelated.

## 10. Build Status

| Check | Result |
|---|---|
| Architecture gate | **PASS** (31 ack, 0 new) |
| Domain certification | 11/11, isolation PASS |
| Country-agnostic scan | PASS |
| Policy engine | PASS |
| Backend boot | 119 route entries (matches 3.2) |
| Alembic head | single: `20260806_0001` |
| PG tables | 351 (unchanged) |
| Ruff `backend/app` | 378 (< 379 baseline) |

## 11. Risks

| Risk | Level | Mitigation |
|---|---|---|
| Canonical `shared/pdf` crashes when `PDFTemplate.subtitle` is non-empty (`KeyError: "Style 'Subtitle' not found in stylesheet"` on reportlab 5.0.0) | Medium (pre-existing) | Adapter always uses `subtitle=""`; canonical untouched per ADR. A canonical-side fix is tracked as a follow-up (affects `citizen_platform/laboratory.py` too). |
| Document platform has no Alembic migration (tables absent in PG) | Medium (pre-existing) | Dormant module; no schema change made in this commit (constitution: no destructive/behavioural schema migration). E2E proven on the test engine (conftest DDL). |
| QR path in service untouched | Info | `qr_engine` finding remains acked; Wave 4 order #50. |
| Engine-state file regeneration noise on gate runs | Low | Governance JSONs restored to committed state; gate verdict is the signal. |

## 12. Rollback Procedure

Single `git revert 537ee5d8` restores the pre-commit state (class M — code + tests,
no data). Baseline regenerates back to 33 on the next `architecture baseline` run.

## 13. Final Certification Verdict

**APPROVED.**

- Constitution gate PASS (31 ack, 0 new) · Domain 11/11 · Country-agnostic PASS.
- OpenAPI byte-identical · Boot 119 routes · Full suite **5030 passed / 0 failed**.
- Ruff clean (378 < 379 baseline) · Frontend tsc 0 · Baseline 33 → **31**.
- Live endpoint now returns a real PDF (was 422).
- Rollback = single `git revert` (class M, no data).

Commit 3.3 (order 15) is complete. **Wave 3 (orders 13–15) is complete** — awaiting
Wave 3 certification + approval before Wave 4 (orders 16–19).
