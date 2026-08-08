# GITHUB GOVERNANCE REPORT

**Program:** PROGRAM-REPO-01 v1.0 — Repository Engineering & Open Source Excellence
**Phase:** 4 / 8 — GitHub Governance (ANALYSIS ONLY — no mutations, no commits)
**Date:** 2026-08-08
**Status:** DRAFT — awaiting Program Director approval before execution

---

## 1. Current State (from Phase 1 Audit)

| Area | Present | Gap |
|---|---|---|
| SECURITY.md | ✅ | content review needed (national health platform → responsible disclosure wording) |
| CONTRIBUTING.md | ✅ | likely stale (references legacy dirs); must align with Phase 2 layout |
| SUPPORT.md | ✅ | verify contact channels current |
| GOVERNANCE.md | ✅ | verify ADR-028/030/034 + program governance referenced |
| CODE_OF_CONDUCT.md | ✅ | standard Contributor Covenant (verify) |
| LICENSE | ✅ | verify license file + headers consistency (see §5) |
| NOTICE | ✅ | verify |
| CODEOWNERS | ✅ (root @samertts) | single-owner; propose team-based owners for OSS scale |
| Issue templates | ✅ (bug/feature/documentation/question) | add SECURITY issue flow via `SECURITY.md`; consider `config.yml` contact links |
| PR template | ✅ | align with Conventional Commits + changelog requirement |
| Dependabot | ✅ (`dependabot.yml`) | verify ecosystems + cadence; add `directory` for npm/pip/pnpm |
| Branch protection | ❓ | **unknown** — must be verified/configured on `main` |
| CODEOWNERS scope | ⚠️ | backend/governance only; mobile/docs/scripts/security missing |

## 2. Proposed Repository Settings (GitHub)

> NOTE: GitHub settings are configured in the web UI/API — these are recommendations for the Program
> Director; configuration itself is execution-phase work (Wave 4), not a code mutation.

| Setting | Recommendation |
|---|---|
| Default branch | `main` (already) |
| Branch protection `main` | Require PR + 1 review; require status checks (all CI + architecture-gate + validate --fast); **block force-push**; require up-to-date; require conventional commits |
| Allow squash merging | ✅ (single squash-merge per feature → linear history) |
| Allow merge/rebase | rebase merge allowed; merge commit OFF (matches GIT_STRATEGY) |
| Auto-delete head branches | ✅ ON (prevents 125-branch recurrence) |
| Issues | ✅ enabled; labels taxonomy (bug/feature/security/documentation/tech-debt/epic/help-wanted/good-first-issue) |
| Discussions | optional (advisory) |
| Security | CodeQL ✅, Dependabot ✅, secret scanning ✅, Scorecard ✅ — all present |
| Releases | GitHub Releases for every SemVer tag (assets: source zip is automatic) |
| Environments | `production` (required reviewers, wait timer) if deploy envs exist |

## 3. CI Governance (26 workflows → consolidate)

### 3.1 Current overlap analysis (from Phase 1)
- **7 deploy-family:** `blue-green-deploy`, `canary-deploy`, `auto-rollback`, `rollback`, `deploy`, `preview-deploy`, `release`.
- **5 quality-family:** `ci`, `quality-gate`, `foundation-gate`, `constitution-compliance`, `ai-governance`, `ai-governance-enforcement`.

### 3.2 Recommended target workflow set (12 workflows)
| Workflow | Purpose | Merged from |
|---|---|---|
| `ci.yml` | Lint (ruff/tsc/eslint) + backend unit tests + frontend vitest | ci + formatting |
| `quality-gate.yml` | enterprise validation `--scope fast` + architecture gate + domain cert | quality-gate + foundation-gate + constitution-compliance + ai-governance(-enforcement) |
| `security.yml` | CodeQL + dependency-review + secret-scanning + semgrep + bandit | codeql + dependency-review + secret-scanning |
| `deploy.yml` | production deployment (single entry; env-gated) | deploy + blue-green + canary + auto-rollback + rollback (retained as steps/actions) |
| `preview.yml` | preview deployments for PRs | preview-deploy |
| `release.yml` | SemVer tag → CHANGELOG + GitHub Release + version-sync | release + sdk-publish |
| `frontend.yml` | frontend-v3 build + e2e + PWA | frontend-e2e + frontend-pwa |
| `mobile-android.yml` | android build | mobile-android |
| `mobile-ios.yml` | ios build | mobile-ios |
| `mobile-flutter.yml` | flutter desktop | mobile-flutter-desktop |
| `nightly.yml` | nightly full suite + DR drill + perf | nightly |
| `repo-hygiene.yml` | **NEW**: root-file count, branch/tag count, git gc check, broken-markdown-link check | — |

**Result:** 26 → 12 workflows (−14), ~4,388 lines → ~2,800. No functional loss (deploy strategies become actions/steps). This is execution-phase work; only the report documents it.

### 3.3 CODEOWNERS expansion
```
# default
*                 @samertts
# platform areas
backend/          @samertts
frontend/         @samertts        (post Phase 2 rename)
mobile/           @samertts
shared/           @samertts
security/         @samertts
scripts/          @samertts
docs/             @samertts
.github/          @samertts
infra/            @samertts        (post Phase 2)
contracts/        @samertts
```
(Owner names resolved at execution time if a team is created.)

## 4. Contribution Workflow (OSS-ready)

1. Contributor creates `feature/issue-<n>-desc` from `main`.
2. PR template auto-fills: description, checklist (tests, lint, docs, changelog), conventional-commit title.
3. Required checks run: CI, quality-gate (incl. architecture gate + domain cert), security.
4. Reviewer approves; branch auto-deleted after squash merge.
5. Release train: `release.yml` tags `vX.Y.Z` → GitHub Release + CHANGELOG.

## 5. License Consistency (verify in execution)

- Root `LICENSE` + `NOTICE` present; verify header standard matches across `backend/`, `shared/`, `mobile/`, `frontend/`.
- If MIT/Apache-2.0: add SPDX headers optionally; ensure `CITATION.cff` and `package.json` license fields match.
- Add `LICENSES/` for any third-party license obligations (SBOM tooling present in repo).

## 6. Security Governance (national health context)

- `SECURITY.md` must add a **coordinated disclosure section**: PGP contact, expected response SLA, "do not test on production", national-data confidentiality statement.
- Branch protection on `main` blocks accidental leak paths; secret scanning + gitleaks pre-commit already active.
- Verify `CODEOWNERS` security-sensitive paths (`backend/app/security`, `shared/security`, `.github/workflows/security*`) require owner review.

## 7. Rollback & Risk Register

| Risk | Mitigation |
|---|---|
| Workflow consolidation breaks CI | Merge one workflow at a time; full validation gate before merge; revert = restore previous workflow file |
| Branch protection blocks current flow | Add maintainers to admin overrides; test on a shadow branch first |
| CODEOWNERS requires reviews that stall | Set `*` owner fallback; per-area owners = same person initially |
| Public tag/version changes | Documented in GIT_STRATEGY; release-only |

## 8. Success Criteria

- 12 workflows running green; repo-hygiene gate active.
- `main` protected (PR required, checks required, force-push blocked, auto-delete ON).
- CODEOWNERS covers all platform areas.
- OSS governance surface complete + verified (SECURITY/CONTRIBUTING/SUPPORT/GOVERNANCE/CoC/LICENSE).
- First GitHub Release created from SemVer tag.
