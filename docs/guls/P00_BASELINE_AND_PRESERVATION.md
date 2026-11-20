# P00 - Baseline and Preservation

Date: 2026-11-20  
Program: GULA-GULS-020  
Repository: `samertts/gula-platform`  
Base revision: current `main` (`2ee9e8bcb9d81e9cac6801f5dea9b86d59beaffa` at program start)  
Base tree: `f5747ce8078b94304b321311a022d4dc4eb7b210`  
Isolated branch: `execution/gula-guls-020`  
Source archive SHA-256: `24a5566d86a72c31ee07291ecbe681b5a7b0bcdf6709250a87e21f1a6120aa62`

## Protected workspace

| Property | Value |
|---|---|
| Path | `/home/samertts/workspace/projects/gula-platform` |
| Branch | `remediate-security-001` |
| HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` |
| Status manifest SHA-256 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Worktrees | 6 |
| Stashes | 2 |
| Origin | `ssh://git@ssh.github.com:443/samertts/gula-platform.git` |

The protected workspace was inspected only. No file, branch, worktree, stash, Git configuration, database, or deployment in that workspace was modified.

## Isolation

A dedicated shallow clone was created at `/tmp/opencode/gula-guls-020` and a new branch `execution/gula-guls-020` was prepared. No existing branch was reused. No corresponding GULS branch or pull request existed on the remote before this program.

## Existing localization capabilities found

| Component | Existing behavior |
|---|---|
| `frontend-v3/src/i18n/` | i18next with `ar`, `en`, `ku`, `tk`, `syr`; English fallback; localStorage key `gula.locale`. Arabic/English catalogs contain 241 leaf strings; other catalogs contain 125. |
| `platform/ui/i18n/` | Separate `ar`/`en` runtime and React provider; localStorage key `gula-locale`; direction derived from `ar` only. |
| `packages/uap/src/runtime/i18n/` | Zustand store with `ar`, `en`, `ku`, `tr`, `fa`, `ckb`; no bundled translations; missing keys returned raw. |
| `backend/app/platform/i18n.py` | Hardcoded dictionaries for `ar`, `en`, `ku`, `ckb`; unknown locale previously fell back to Arabic. |
| `shared/localization.py` | JSON file helper with default Arabic locale. |
| `backend/app/national/reference/languages.py` | `ref_languages` reference entity with ISO codes, native name, and RTL flag. |
| `backend/app/routes/user_preferences.py` | Existing accessibility profile API already stores a language field in `accessibility_profiles.preferences`. |
| Android resources | Default and Arabic string resources under `mobile/android` and a small resource set under `apps/gula-web-suite/android`. |
| `docs/certification/arabic_localization_audit_report.md` | 2026-07-23 automated Arabic/RTL coverage claim; no dynamic-pack or clinical-localization evidence. |

## Missing capabilities

No existing implementation was found for: centralized validated language registry, BCP 47 validation, dynamic language-pack manager, signed pack delivery, SHA-256/Ed25519 verification, atomic installation, rollback, offline pack runtime, clinical terminology localization registry, translation approval records, or localization API under `/api/v1/localization/`.

## Dependency review

Required capabilities are already available:

- Frontend: `i18next`, `react-i18next`, Vitest, Playwright, vite-plugin-pwa.
- Backend: FastAPI, Pydantic, SQLAlchemy, Alembic, `cryptography`, `arabic-reshaper`, `python-bidi`, ReportLab.

No new external dependency is introduced.

## Preservation outcome

No product code was modified during P00. All subsequent changes are additive or narrowly corrective and confined to the isolated branch.

## Local verification status

This document records the baseline established through live GitHub API evidence and the isolated clone. Exact local hashes, test outputs, and commands are retained in `TEST_EVIDENCE.md` and the implementation log.
