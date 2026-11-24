# GULA National Identity Architecture Study — OCR & Document Intelligence Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests run, no DB contacted, no application file modified. No OCR benchmark, confidence threshold, or cost figure is asserted; all must be calibrated with representative, legally authorized de-identified or synthetic Iraqi data.

---

## 1. Governing decision

**D-IDENTITY-10** — OCR is a core but **non-proof** capability: Arabic/English, Iraqi documents, quality assessment, field extraction, confidence, human review; extraction is never proof of identity or authenticity. This is a product-design decision only; no implementation is authorized.

---

## 2. Current source inventory (verified directly)

There are **two distinct OCR surfaces** with very different maturity, plus a dormant capability stub.

### 2.1 `/id-scan` — the strongest actually-wired OCR surface — `PARTIAL`

`backend/app/routes/id_scan.py`:

| Aspect | Verified detail | Evidence |
|---|---|---|
| Purpose | Iraqi National ID card camera capture; extract NID number, full name, DOB | `:1-10` |
| Routing | Router registered in `factory.py` at `:539` and `:570` (live include) | `factory.py:539,570` |
| OCR engine | `pytesseract.image_to_string(pil_img, lang="ara+eng")`; OpenCV preprocessing; on import failure returns `""` (regex runs only over OCR text, **not** OCR-free extraction despite the docstring at `:9`) | `:63-88` |
| Arabic | `lang="ara+eng"`; Arabic response `message_ar` `:191` | `:82,191` |
| Quality gates | Strict MIME allowlist (jpeg/png/webp/bmp) `:155-160`; 2 MB max / 1 KB min `:162-167`; rate limit 5/min `:151-153` | `:151-167` |
| Extraction | NID 12–13 digits, date with year range 1900–2025, name heuristic | `:28-30,90-133` |
| Privacy | Image **not stored**; only extracted text fields returned `:147-149` | `:147-149` |
| Human review | `needs_confirmation: True` and "verify before confirming" message `:189-191` | `:189-191` |
| NID protection | Reuses canonical `hash_national_id()` (digit-normalized HMAC) `:23,173-175` | `:23,173-175` |
| Confidence | **No confidence value is returned** to the caller (only boolean `success`) `:181-188` | `:181-188` |

**Verified limitations:** when OCR libraries are absent, `extract_text_ocr()` returns `""` (`:84-87`) and `success` becomes false — honest degradation, but no quality/confidence signal is surfaced. The year upper bound `2025` (`:113`) will reject current-year dates. There is **no authenticity check** (a photo of any card is accepted); the endpoint explicitly requires human confirmation.

### 2.2 `document_intelligence/` — large platform, effectively non-functional — `PARTIAL` / `BLOCKED`

`backend/app/document_intelligence/` (≈30 modules). Routing mounted at `factory.py:792-793` under `/document-intelligence` with `require_permission("system:admin")` on all primary routes (`api/routes.py:39-43`).

**Verified defects and stubs (all static; runtime `UNVERIFIABLE`):**

| Finding | Evidence | Status |
|---|---|---|
| **Orchestrator never initialized at startup** — `build_orchestrator()` is defined/exported but has **no caller** anywhere in `backend/`; `get_orchestrator()` raises `RuntimeError("…not initialized. Call build_orchestrator() first.")`. Every orchestrator-dependent route (ingest, batch, search, classify, statistics, etc.) would fail. | `wiring.py:880,1039-1042`; repo-wide grep: only definition + export in `__init__.py:4,263` | `BLOCKED` |
| **Encryption is a no-op** — `DefaultEncryptionService.encrypt()/decrypt()` return input unchanged; `verify_digital_signature()` always returns `False`. | `wiring.py:75-96` | `NOT_IMPLEMENTED` |
| **Audit is log-only** — `DefaultAuditService.log_event()` writes a log line; `get_document_history()` returns `[]`. | `wiring.py:67-72` | `NOT_IMPLEMENTED` |
| **Event publisher is a no-op** — `publish()` logs debug; `subscribe()` is `pass`. | `wiring.py:99-104` | `NOT_IMPLEMENTED` |
| **Benchmarks run on dummy bytes** — `_run_benchmark()` calls `ocr_image(b"dummy_benchmark", ...)`; reported latency/throughput are not based on real documents. | `providers/base.py:51-72` | `NOT_IMPLEMENTED` |
| **OCR engine libraries are undeclared optional imports** — Tesseract path uses `pytesseract`, `cv2`, `numpy` behind `try/import`; when missing it returns `DocumentPage(text="", confidence=0.0)`. `requirements.txt`/`pyproject.toml` declare only `Pillow`. | `providers/tesseract.py:41-64,81-84`; `requirements.txt:19`; `pyproject.toml:26` | `BLOCKED` |
| **Hardcoded extraction confidence** — entity extractor assigns `confidence=0.9` (entities) and `0.85` (lab fields) constants, not model-derived. | `wiring.py:454-522` | `PARTIAL` |
| **Layout detection entirely empty** — `detect_layout/tables/forms/handwriting/qr/barcodes/signatures` all return `{}`/`[]`. | `wiring.py:788-809` | `NOT_IMPLEMENTED` |
| **SNOMED/ICD mapping empty** — `map_to_snomed()`/`map_to_icd()` return `""`. | `wiring.py:781-785` | `NOT_IMPLEMENTED` |
| **DB model base unregistered** — `DocIntelBase = declarative_base()` with 21 model classes is not registered in `backend/migrations/env.py` (F-085); tables not migrated by Alembic. | `infrastructure/models.py:64,67-886`; `env.py` grep: no DocIntel | `BLOCKED` |
| **SQLite default storage** — `build_orchestrator()` defaults to `sqlite:///docint.db` and `/data/documents`. | `wiring.py:880-889` | `PARTIAL` |

**Capabilities declared in enums/entities (source present, not proof of function):** `OcrEngine` = unlimited_ocr / paddle_ocr / tesseract / easy_ocr / future_provider (`domain/enums.py:66-71`); `OcrLanguage` = ara / eng / kur / ara+eng / ara+eng+kur / auto (`:81-87`); `DocumentPage.confidence` float default `0.0` (`domain/entities.py:102-113`); `DocumentCategory` covers laboratory, radiology, prescription, national_id, passport, government/circular/decision categories (`:8-34`). Provider registration in `build_orchestrator()` registers Tesseract unconditionally; PaddleOCR/EasyOCR only if their constructors do not raise (`wiring.py:963-975`).

**Human-review surface:** collaboration routes (`assign_reviewer`, `submit_review`, annotations) exist (`api/routes.py:397-470`) but depend on the uninitialized orchestrator → currently unreachable.

### 2.2b Additional source-confirmed gaps (from detailed inventory)

| Finding | Evidence | Status |
|---|---|---|
| **Stored-document OCR read path returns empty bytes** — the pipeline calls `self._parser._read_storage(document)` but `_read_storage()` returns `b""`, so OCR-over-stored-document cannot work. | `service.py:281`; `wiring.py:340-341` | `BLOCKED` |
| **Encryption flags ignored by local storage** — `save(data, encrypt=True)` / `read(decrypt=True)` ignore the flags; a real Fernet utility exists but is not the default. | `infrastructure/repository.py:441-451`; `security.py:16-30`; `wiring.py:75-80` | `NOT_IMPLEMENTED` |
| **DocIntel upload lacks id-scan's controls** — only empty-file rejection; no MIME allowlist, size cap, filename sanitization or malware policy (contrast `id_scan.py:155-167`). | `api/routes.py:59-81` | `PARTIAL` |
| **No image quality scoring** — no blur/sharpness, glare, perspective or document-boundary gate; `correct_rotation()` is a no-op. | `wiring.py:125-232` (esp. `:162-163`); `id_scan.py:33-60` | `NOT_IMPLEMENTED` |
| **No document-image tampering/forgery detection** in scoped source. | `document_intelligence/` | `NOT_IMPLEMENTED` |
| **Duplicate detection is exact SHA-256 only**, no perceptual/near-duplicate; no API route calls `deduplicate`. | `repository.py:208-217`; `infrastructure/services.py:149-153` | `PARTIAL` |
| **Reviewer identity not bound to authenticated principal** — `reviewer_id` is accepted from form input; no field-level approval state; no confidence-gated review. | `api/routes.py:408-435`; `infrastructure/models.py:553-600` | `PARTIAL` |
| **Fake semantic embeddings** — SHA-256 digest scaled to floats; index returns only text length; knowledge-graph edges empty. | `wiring.py:702-714` | `NOT_IMPLEMENTED` |
| **Process-dependent version/preservation checksums** — `str(hash(data))` instead of SHA-256; retention calculation result discarded; collaboration sessions in-memory. | `infrastructure/services.py:55-86,104-113,335-368`; `wiring.py:811-816` | `PARTIAL` |
| **Paddle/Easy adapters present but undeclared** — `PaddleOCR(lang="ar")`, `easyocr.Reader(["ar","en"])` behind lazy imports; no dependency declarations found. | `providers/paddle_ocr.py:39-73`; `providers/easy_ocr.py:38-71`; `requirements.txt:16,18-20` | `BLOCKED` |
| **No birth/death certificate categories** in the document-classification taxonomy (has `national_id`, `passport` only). | `domain/enums.py:8-34` | `PARTIAL` |
| **No Arabic-Indic numeral normalization** in OCR/extraction (display-only conversion exists in `citizen_platform/accessibility.py:122-127`). | `wiring.py:454-465`; `accessibility.py:122-127` | `NOT_IMPLEMENTED` |
| **Statutory document connectors are stubs with hard-coded `confidence: 1.0`** for birth/death/civil/passport. | `governance/services/connector_service.py:69-180` | `BLOCKED` |

### 2.3 Capability command stub — `NOT_IMPLEMENTED`

`backend/app/capabilities/document_management/commands/ocr_document.py` is a bare dataclass `Ocr_documentCommand` envelope only — no OCR logic.

### 2.4 Verification policy correctly treats OCR as non-proof — `VERIFIED_IN_SOURCE`

`backend/app/identity/services/verification_service.py`:

- `VerificationPolicy._levels` maps `ocr → AssuranceLevel.L0` and `nfc → L0` (`:132-148`) — OCR and NFC are **not** trusted as identity proof.
- `verify()` "never claims success" and delegates to `start_verification()` (`:128-130`).
- This is strong source-level alignment with D-IDENTITY-10: OCR is advisory only.

---

## 3. Target design (recommendations)

### 3.1 Two-tier OCR architecture

```
Tier 1 — Capture & extraction (advisory)            Tier 2 — Trust & use (gated)
 id-scan / document-intelligence ingest                  human confirmation
   → image quality assessment (target)                   → verification policy (L0 for OCR)
   → Arabic/English OCR engine (calibrated)             → never auto-verifies identity
   → field extraction + per-field confidence            → MPI/authorization uses confirmed data only
   → NO authenticity claim                              → full audit of who confirmed what
```

- **Keep `/id-scan` as the near-term user-facing capability** after adding per-field confidence + quality score; it is wired, Arabic-first, privacy-conscious, and already requires confirmation.
- **Do not activate `document_intelligence/` as-is.** It requires: orchestrator startup wiring, real encryption, real audit, real event bus, registered `DocIntelBase`, declared dependencies, and removal of dummy benchmarks before any trust. Treat as `BLOCKED`, not a foundation to build on blindly. (`SECURITY_REVIEW_REQUIRED` / `NEEDS_OWNER_DECISION`.)

### 3.2 Arabic/Iraqi document support

- Engines must be calibrated for Arabic + English and Iraqi document layouts using **representative, legally authorized de-identified or synthetic Iraqi samples**. No accuracy figure is claimed in this study.
- Quality assessment (blur, glare, skew, resolution, card-boundary detection) must gate extraction; low-quality captures must be rejected, not silently returned with confidence 0.0.
- Field schemas: NID (digit-normalized), name (Arabic + Latin), DOB, document type, issuing authority, expiry. No field is authoritative until confirmed.

### 3.3 Confidence & human review

- Per-field confidence with **thresholds calibrated from data** (none asserted here). Below-threshold fields route to assisted/human review.
- OCR output always carries `needs_confirmation`; confirmation is attributed and audited. Extraction is never proof of identity or authenticity (D-IDENTITY-10, §2.4).

### 3.4 Dependencies & deployment

- OCR is CPU/GPU-bound: isolate in a worker pool; never run inline on the request event loop (id-scan already uses `run_in_executor` — `:169-179`).
- Declare and pin engine dependencies explicitly; self-hosted/open-source first (Tesseract/PaddleOCR class), no vendor lock-in, no per-page external cost assumed.
- No new orchestration engine: reuse existing queue/outbox; the dormant DOCINT distributed modules (`distributed/`) must not be activated.

---

## 4. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | Arabic/English field extraction (synthetic Iraqi ID samples); NID normalization parity with `hash_national_id`; date-boundary regression (current year); quality-gate rejection. |
| Integration | id-scan → confirm → MPI resolve; no image persisted; rate-limit enforcement; document-intelligence orchestrator initialization (regression for missing startup wiring). |
| Security | No authenticity claim; OCR result cannot raise verification above L0; no raw NID in returned/logs; MIME/size validation; no raw image at rest. |
| Calibration | Measure accuracy/confidence distributions on authorized de-identified/synthetic Iraqi data; set thresholds from evidence; record engine version + data provenance. |

Synthetic / legally authorized de-identified data only.

---

## 5. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OCR-01 | Make `/id-scan` the near-term OCR capability; add confidence + quality gates | Only wired OCR surface lacks confidence | Build on dormant DOCINT | Reuses live, Arabic-first, privacy-conscious path | Needs hardening | Data-protection basis for ID images | Positive | Low | Calibration data | False field confidence | Reversible | §2.1 | `RECOMMENDED` |
| OCR-02 | Do not activate `document_intelligence/` until blockers cleared | Orchestrator uninitialized, encryption/audit stubs, unregistered base | Activate as-is | Avoids false capability | Deferred features | Document retention law | Positive | High to fix | Owner decision, migrations, deps | Silent data exposure/failure | N/A (no activation) | §2.2 | `SECURITY_REVIEW_REQUIRED` |
| OCR-03 | OCR always L0 / needs-confirmation; never proof | Misuse risk | Trust OCR output | Matches D-IDENTITY-10 | Extra UX step | Identity-proofing law | Positive | Low | Verification policy | Wrongful verification | Reversible | §2.4 | `OWNER_APPROVED` (D-IDENTITY-10) |
| OCR-04 | Calibrate Arabic/Iraqi accuracy + thresholds on authorized data | No benchmarks exist | Assume vendor numbers | Honest, defensible | Data access effort | Data-sharing agreement | Neutral | Moderate | De-identified/synthetic data | Unsafe thresholds | Reversible | §0, §3.2 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| OCR-05 | Declare/pin OCR engine deps; self-hosted worker pool | Undeclared imports, inline CPU risk | Managed OCR API | Deterministic, no per-page cost | Ops overhead | No external data transfer | Positive | Moderate | Infra | Missing libs → empty OCR | Reversible | §2.2, §3.4 | `RECOMMENDED` |
| OCR-06 | Remove dummy-byte benchmarks; measure real docs | Misleading metrics | Keep | Truthful capacity data | Test corpus needed | None | Neutral | Low | Calibration data | Bad sizing | Reversible | §2.2 | `RECOMMENDED` |

---

## 6. Open questions

1. Which OCR engine(s) are acceptable given Arabic/Iraqi accuracy and self-hosting constraints? (`NEEDS_OWNER_DECISION`.)
2. Is there legally authorized access to representative de-identified Iraqi document images for calibration? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
3. Should `document_intelligence/` be rehabilitated, archived, or left dormant? (`SECURITY_REVIEW_REQUIRED`.)
4. What per-field confidence thresholds are safe for assisted vs self-service flows? (Data-driven; none asserted here.)
5. Who owns the confirmation audit trail and retention period? (`LEGAL_REVIEW_REQUIRED`.)

---

## 7. Cross-references

`MASTER_ARCHITECTURE.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `EXISTING_CAPABILITY_INVENTORY.md` · `NATIONAL_IDENTITY_MODEL.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `API_AND_INTEGRATION_CONTRACTS.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 4, 9).
