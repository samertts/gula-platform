# WAVE 3 CERTIFICATION — Program-01 Structural Migration (Orders 13–15)

- **Wave:** 3 (Notifications Queue → Search → Document/PDF) · **Branch:** `remediate-security-001`
- **ADR:** ADR-032 (notifications), ADR-033 (search + PDF)
- **Baseline:** 37 findings → **31 findings** (target met: 33 at Wave start → 31)

---

## 1. Wave Scope (orders 13–15)

| Order | Finding(s) | Unit | Commit | Findings |
|---|---|---|---|---|
| 13 | #24 + #49 | Identity notification queue → canonical `app/notifications` | `09773f84` (+ docs `4976cf50`) | 37 → 35 |
| 14 | #35 + #36 | doc-intel search → canonical `app/capabilities/search_service` | `57d829eb` (+ docs `b7aadcf5`) | 35 → 33 |
| 15 | #46 + #47 | document PDF → canonical `shared/pdf` (adapter in `capabilities/document_management`) | `537ee5d8` | 33 → 31 |

## 2. Overall Verification (full Wave)

| Check | Result |
|---|---|
| Architecture gate | **PASS** at every commit (31 ack, **0 new** cumulative) |
| Domain certification | 11/11, isolation PASS |
| Country-agnostic scan | PASS |
| Policy engine | PASS |
| Full backend suite (PG) | **5030 passed / 0 failed** (5017 @ 3.2 → +13 @ 3.3) |
| Frontend vitest | 122 passed / 9 files |
| Frontend tsc / eslint | 0 errors |
| Ruff `backend/app` | 378 (< 379 baseline) |
| OpenAPI | byte-identical before/after each commit (2028 methods / 1696 paths) |
| Boot | 119 route entries (unchanged across Wave) |
| Alembic head | single: `20260806_0001` (no schema change in Wave) |
| PG tables | 351 (unchanged) |
| Per-commit reports | `COMMIT_3_1`, `COMMIT_3_2`, `COMMIT_3_3` `_VERIFICATION_REPORT.md` |

## 3. Behaviour Preservation

- Runtime: boot identical (119 routes), OpenAPI byte-identical after every commit.
- API: paths, methods, operationIds, summaries, payloads unchanged.
- Business rules: delegation bodies moved verbatim; only signal-bearing names renamed.
- Security/authorization: no permission changes; router auth untouched.
- Audit: no audit path modified.
- Database: no schema changes; PG head/tables unchanged (351).

## 4. Dead-Code / Duplicate Elimination

- Notifications: old `identity/notifications/{models,services,routes}.py` namespace
  fully vacated; queue + delivery co-located in canonical `app/notifications`.
- Search: old doc-intel search namespace fully vacated (indexer/search/semantic/
  composition) — no facade remains.
- PDF: `generate_pdf` signal names removed from national routes + service; concretion
  is now the single canonical adapter.

## 5. Rollback

Each commit is independently reversible via a single `git revert` (class M — code +
tests, no data). Cumulative revert of Wave = `git revert` of `537ee5d8`, `57d829eb`,
`09773f84` in reverse order.

## 6. Remaining Findings (31, all acknowledged — never grow)

12 canonical + retained items remain, including: doc-intel interfaces/wiring/repos
(6), national document platform `PDFGenerator` ABC (#14) + DocumentRepository
repos + qr_engine (#50), national task_engine audit repos, fhir search_engine,
workflow_runtime, notification_platform routes, authorization_service (identity/
authorization/audit), citizen_platform (identity/notifications), kernel scheduler/
events/DI, barcode sample, encryption (ecosystem + doc-intel security).

## 7. Wave 4 Readiness (orders 16–19)

| Order | Findings | Unit | ADR |
|---|---|---|---|
| 16 | #5 + #9 | identity + audit → canonical | ADR-031 |
| 17 | #50 | QR engine → canonical | ADR-032 |
| 18 | #44 | document intelligence wiring/encryption → canonical | ADR-036 |

All 4 Wave-4 orders are prepared (signal inventory verified); **Wave 4 shall not
begin without explicit approval.**

## 8. Certification Verdict

**WAVE 3 CERTIFIED.**

- All three orders complete: 37 → **31** findings (6 resolved), 0 new.
- Full verification green: 5030 backend tests, gates PASS, OpenAPI byte-identical,
  119-route boot, 351 tables, ruff 378.
- Every commit independently reversible; behaviour fully preserved.
- Risks: pre-existing canonical `shared/pdf` subtitle quirk (reportlab 5.0.0) and
  missing document-platform Alembic migration — both tracked, neither caused by
  the Wave, both scheduled for follow-up.
