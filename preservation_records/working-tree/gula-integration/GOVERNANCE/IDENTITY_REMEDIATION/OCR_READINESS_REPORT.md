# OCR / Document-Intelligence Readiness Report — P0 Tranche

> Readiness assessment only. **No OCR capability was activated, benchmarked, or
> certified in this tranche.** No OCR model was run and no document sample —
> real or synthetic — was processed. Source classification derives from the 22
> document identity study, reconciled against current source.

## 1. Verdict

| Dimension | Status |
|---|---|
| OCR readiness | **BLOCKED — NOT READY** |
| ID Scan (`/id-scan`) | **Advisory only** — `needs_confirmation: True`; not authenticity verification |
| OCR / NFC level | **L0** (advisory extraction / read) |
| Benchmarks | **UNMEASURED** — no valid benchmark executed |
| External samples | **BLOCKED_BY_EXTERNAL_DEPENDENCY** |
| Activation / release claim | **NONE** — HOLD unchanged |

## 2. What the study and source establish

- `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/DOCUMENT_VERIFICATION_DESIGN.md` §2.4
  records `/id-scan` (`backend/app/routes/id_scan.py`) as **advisory only**: it
  extracts fields with `needs_confirmation: True` (`:189`) and performs **no
  authenticity check** — a photograph of any card can be uploaded. It must
  never be promoted to verification without separate evidence.
- `.../OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` defines OCR as Layer 0
  (advisory capture/extraction). Output always carries `needs_confirmation`;
  extraction is never proof of identity or authenticity (D-IDENTITY-10).
- Provider adapters exist but are non-certified:
  `backend/app/document_intelligence/providers/paddle_ocr.py` and `easy_ocr.py`
  import their engines lazily (e.g. `import paddleocr` in `version`), which is
  consistent with the study's "undeclared OCR libraries" finding (backlog
  P2-03, `SECURITY_REVIEW_REQUIRED`).
- `.../providers/manager.py:87-88` falls back to a default benchmark score
  (`benchmark.get("avg_latency_ms", 1000)`) when no measurement exists — a
  placeholder, not evidence of measured performance.

No part of this was changed in the P0 tranche.

## 3. Why OCR benchmarks are blocked

A meaningful OCR engine comparison (PaddleOCR / Tesseract / docTR / EasyOCR,
backlog P2-04) requires a representative, legally authorized corpus of Iraqi
identity documents (front/back, varied governorates, scripts, lighting,
damage). No such corpus exists in the repository, and this program has no
authority to:
- collect real identity documents or patient data, or
- interpret Iraqi document/privacy law to authorize a de-identified set
  (all Iraqi statutory items are `UNVERIFIABLE` / `LEGAL_REVIEW_REQUIRED`).

Inventing metrics or generating fake "benchmark results" would be fabrication.
Accordingly, **no benchmark numbers are reported**.

## 4. Related blocked items

| Item | Classification | Status |
|---|---|---|
| P2-03 DocIntel no-op encryption/audit/events, placeholder benchmarks, undeclared OCR libs | `SECURITY_REVIEW_REQUIRED` | BLOCKED — not activated |
| P2-04 OCR engine benchmark | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | Needs synthetic / legally authorized de-identified Iraqi samples |
| P2-05 Document verification / government source / NFC | `BLOCKED_BY_EXTERNAL_DEPENDENCY` + `LEGAL_REVIEW_REQUIRED` | OCR/NFC stay `L0` |
| Government ID / civil registry / NFC integrations | `BLOCKED_BY_EXTERNAL_DEPENDENCY` / `LEGAL_REVIEW_REQUIRED` | No external integration attempted |

## 5. What is explicitly NOT claimed

- No OCR accuracy, latency, or engine-comparison figure.
- No claim that `/id-scan` verifies document authenticity.
- No claim that OCR output can be used as proof of identity.
- No NFC read, government-source check, or civil-registry integration.
- No activation of any dormant document-intelligence router or engine.

## 6. Unblock path (requires owner/legal action, not code)

1. Provide a synthetic or legally authorized de-identified Iraqi-document
   corpus with a documented provenance and retention basis.
2. Legal review of document/privacy/consent/retention questions (currently
   `UNVERIFIABLE`).
3. Security review of DocIntel no-op encryption/audit/events and undeclared
   OCR dependencies (P2-03).
4. Only then execute a recorded benchmark and decide on any gated activation.

Until all four are satisfied, OCR remains `L0` advisory and NOT READY.
