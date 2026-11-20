# GULA-GULS-020 Final Report

Date: 2026-11-20  
Program: GULA-GULS-020 — GULA Universal Language System (GULS)  
Repository: `samertts/gula-platform`  
Branch: `execution/gula-guls-020`  
Base revision: `2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa`  
Isolated clone: `/tmp/opencode/gula-guls-020`

## 1. Executive summary

GULA-GULS-020 established the additive foundation for a national multilingual system in an isolated branch. The work covers P00–P20: baseline preservation, architecture and decisions, a data-driven language registry, core Arabic/English/Sorani runtime behavior, RTL/LTR standards, signed language-pack schema and management, secure delivery, preference integration with the existing accessibility profile, clinical terminology approval gating, governance documentation, verification evidence, and a final gate review.

All applicable GULS gates are green. Two full-frontend test failures are pre-existing at HEAD and unrelated to the change. The result is ready for a Draft PR only; it is **not accepted for production** because language standards, human approvals, font licensing, offline client caching, and production key management remain outside this program's authority.

## 2. Isolation and preservation

- Created a fresh branch `execution/gula-guls-020` from current `main` in a dedicated shallow clone. No existing GULS branch or PR was reused.
- Protected workspace `/home/samertts/workspace/projects/gula-platform` remained unchanged: branch `remediate-security-001`, HEAD `f478676b6fc375338648dde46fbf076c015a3f91`, status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`, 6 worktrees, 2 stashes.
- PR #307 (program-013 draft) was not modified.
- No production database, deployment, or human approval was accessed.

## 3. What was built

### Registry and identifiers

- Canonical data registry `shared/guls/language_registry.json` with 14 entries, shared by Python and TypeScript runtimes.
- BCP 47 locale-tag validation; language IDs kept separate from locale tags, scripts, and directions.
- Core languages: `ar`, `en`, `ckb`. Iraqi Turkmen and Syriac remain placeholders with `null` locale tags, inactive and unpublishable.
- Dynamic foreign languages: `fa`, `ur`, `tr`, `fr`, `de`, `ru`, `zh`, `hi`, `bn`, addable without code redesign.
- English is mandatory fallback; unknown locales never fall back to Arabic.

### Runtime and formatting

- Backend `LanguageRuntime` and frontend `src/guls/runtime.ts` provide stable messages, translation-key validation, digit/date/number formatting, and no raw-key leakage.
- RTL/LTR helpers and logical-direction styles in `src/guls/rtl.ts`.
- Legacy backend i18n now uses approved identifiers (`ar`, `en`, `ckb`) and English fallback.
- Frontend locale selector exposes only `ar`, `en`, `ckb` and normalizes retired identifiers (`ku` to `ckb`, `tk`/`syr` to `en`).

### Language packs

- Signed ZIP packs with Ed25519 manifest signatures, SHA-256 file and content hashes, schema validation, path/symlink/size checks, and atomic installation.
- Lifecycle states: `NOT_INSTALLED`, `AVAILABLE`, `QUEUED`, `DOWNLOADING`, `VERIFYING`, `INSTALLING`, `READY`, `UPDATE_AVAILABLE`, `FAILED`, `ROLLBACK_REQUIRED`, `DISABLED`. No `READY` before verification and install.
- Governance enforcement in `verify()` and `install()`: blocked languages, clinical catalogs without approval, and L3/L4 terminology without documented clinical approval are rejected.
- Synthetic packs are environment-gated (`GULS_ALLOW_SYNTHETIC_PACKS=1`) and marked `synthetic_test_only`; the signing CLI defaults to synthetic status.

### APIs

- `GET /api/v1/localization/languages`
- `GET /api/v1/localization/languages/{language_id}/manifest`
- `POST /api/v1/localization/language-packs/{language_id}/download`
- `GET /api/v1/localization/downloads/{download_id}`
- `GET /api/v1/localization/downloads/{download_id}/content` with byte-range resume and cancellation
- `PUT /api/v1/users/me/preferences/language`

All errors carry stable codes and parameters; messages are fixed English diagnostics, never translated prose.

### Preference compatibility

- Reused `accessibility_profiles.preferences["language"]`; no new table or migration.
- GULS preference endpoint rejects blocked/unpublishable languages with `409 LANGUAGE_NOT_ACTIVE`.
- Legacy accessibility endpoint ignores GULS keys, preserves `fallback_language`/`auto_download`, and normalizes retired language identifiers, eliminating a shared-key HTTP 500.

### Clinical governance

- `L1`–`L4` classification with role-separation validation; `L4` requires documented human clinical approval.
- No unreviewed machine translation is used in clinical decisions; clinical values, units, and identifiers are protected from localization changes.
- All clinical catalogs and all `L4` translations remain blocked until documented human approval is supplied.

## 4. Verification summary

| Check | Result |
|---|---|
| Focused backend tests, Python 3.11 | 67 passed |
| Focused backend tests, Python 3.12 | 67 passed |
| Legacy accessibility regression, Python 3.12 | 5 passed |
| Focused frontend tests | 11 passed |
| TypeScript typecheck | passed |
| Frontend lint | passed, zero warnings |
| Ruff | all checks passed |
| Python compile (3.12) | passed |
| Registry JSON schema | PASS, 14 languages |
| Pack JSON schema | PASS, synthetic fixture |
| Full frontend suite | 2 pre-existing failures (unmodified `MobileBottomNav.test.tsx`) |
| Protected workspace | unchanged |

Exact commands and outputs are in `TEST_EVIDENCE.md`. Phase mapping is in `PHASE_EVIDENCE_P03_P20.md`. Coverage details are in `COVERAGE_REPORT.md`.

## 5. Gate decision

**Draft PR: GO.** All GULS-scoped tests and static checks pass, the protected workspace is unchanged, and the only full-suite failures are demonstrably pre-existing from byte-identical HEAD sources.

**Production: NO-GO / HOLD.** This program did not and does not authorize production use. The following remain unresolved:

- Verified standards and human approval for Iraqi Turkmen and Syriac; they stay inactive and unpublishable.
- Documented human clinical approval for `L3`/`L4` content; all clinical catalogs stay blocked.
- Arabic/Sorani font assets and licensing were not found; glyph coverage is not claimed.
- Web Service Worker/IndexedDB pack caching and mobile/desktop dynamic pack storage are not implemented.
- No production signing key was generated, rotated, or used; only ephemeral test keys were used.
- No production deployment, database access, merge, or approval on behalf of humans occurred.

## 6. Documentation index

| Document | Purpose |
|---|---|
| `P00_BASELINE_AND_PRESERVATION.md` | Baseline, isolation, preservation |
| `P01_ARCHITECTURE_AND_GAP_ANALYSIS.md` | Existing capabilities and gaps |
| `P02_ARCHITECTURE_DECISIONS.md` | ADRs and constraints |
| `PHASE_EVIDENCE_P03_P20.md` | P03–P20 evidence matrix |
| `LANGUAGE_REGISTRY_SCHEMA.md` | Registry data contract |
| `PACK_SCHEMA.md` | Signed pack contract |
| `API_CONTRACTS.md` | HTTP API contract |
| `KEY_CONVENTIONS.md` | Translation key rules |
| `TERMINOLOGY_POLICY.md` | Terminology and clinical text policy |
| `RTL_LTR_STANDARD.md` | Direction and formatting standard |
| `APPROVAL_WORKFLOW.md` | Linguistic/clinical approval workflow |
| `THREAT_MODEL.md` | Security threats and mitigations |
| `SIGNING_KEY_MANAGEMENT.md` | Key generation, protection, rotation, revocation |
| `MIGRATION_ASSESSMENT.md` | No-database-migration decision |
| `OFFLINE_GUIDE.md` | Offline behavior and boundaries |
| `ROLLBACK_GUIDE.md` | Pack and deployment rollback |
| `DEPLOYMENT_GUIDE.md` | Configuration and operational checks |
| `COVERAGE_REPORT.md` | Registry and catalog coverage |
| `TEST_EVIDENCE.md` | Exact verification commands and outputs |
| `FINAL_REPORT.md` | This report |

## 7. Final statement

The GULS additive foundation is complete for review. It deliberately fails closed on unverified languages, unapproved clinical content, and malformed security configuration. It does not claim linguistic, clinical, production, or human approval that was not granted.
