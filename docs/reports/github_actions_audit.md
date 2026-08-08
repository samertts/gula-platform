# GitHub Actions Audit — PROGRAM-SECURITY-001

## Summary

- **Total workflows**: 26
- **Reusable actions**: 3 (build-android, build-flutter, build-ios)
- **Total jobs**: ~80
- **Issues found**: 12

---

## Critical Issues

### 1. ci.yml — Error suppression with `|| true`

**File**: `.github/workflows/ci.yml`
**Lines**: 165, 170, 172
**Issue**: `ruff check ... || true`, `npm install || true`, `npm run lint 2>/dev/null || echo "No lint script"` — all suppress failures silently. CI passes even when linting/formatting fails.
**Fix**: Remove `|| true` and `2>/dev/null`. Fail when lint or dependency install fails.

### 2. ci.yml — Test output truncated

**File**: `.github/workflows/ci.yml`
**Line**: 222
**Issue**: `python -m pytest ... 2>&1 | head -200` truncates test output. CI shows "pass" even if only the first 200 lines are printed.
**Fix**: Remove `head -200`.

### 3. dependency-review.yml — Overly restrictive license deny-list

**File**: `.github/workflows/dependency-review.yml`
**Lines**: 24-34
**Issue**: Deny-list includes BSD, CC0, CC-BY, CC-BY-SA, OSL, Artistic — all common permissive open-source licenses. This will block legitimate PRs.
**Fix**: Deny only GPL, AGPL, proprietary, and copyleft licenses.

---

## High Issues

### 4. ci.yml — Security scan `continue-on-error: true`

**File**: `.github/workflows/ci.yml`
**Lines**: 237, 242
**Issue**: `continue-on-error: true` on `safety check` and `bandit check`. Vulnerabilities are never surfaced.
**Fix**: Remove `continue-on-error: true`. Add proper reporting.

### 5. codeql-analysis.yml — Action versions not pinned

**File**: `.github/workflows/codeql-analysis.yml`
**Lines**: 35, 42
**Issue**: `github/codeql-action/init@v3` and `analyze@v3` use major-version pinning. Supply-chain risk.
**Fix**: Pin to exact minor version (e.g., `@v3.28.0`).

### 6. deploy.yml — SSH key written to disk unencrypted

**File**: `.github/workflows/deploy.yml`
**Line**: 56
**Issue**: `printf '%s\n' "$SSH_KEY" > ~/.ssh/id_ed25519` writes SSH private key to disk. Standard but could be improved.
**Fix**: Use `ssh-agent` for key management. Ensure cleanup happens in `always()`.

### 7. deploy.yml — Destructive git operations

**File**: `.github/workflows/deploy.yml`
**Lines**: 111-113
**Issue**: `git reset --hard origin/main; git clean -fd -e .env` — destructive if main moves during deploy. No validation before reset.
**Fix**: Add safety checks. Use `git merge --ff-only` instead of reset.

---

## Medium Issues

### 8. Version inconsistencies across workflows

- `ci.yml` uses Python 3.12, Node 24
- `formatting.yml` uses Python 3.12, Node 22
- `foundation-gate.yml` uses Python 3.12
- Should use a consistent version matrix or env variables

### 9. frontend-pwa.yml — Missing `frontend-v3` path triggers

**File**: `.github/workflows/frontend-pwa.yml`
**Lines**: 7, 12
**Issue**: Workflow only triggers on `frontend-v2/**` paths. `frontend-v3` changes won't trigger it.
**Fix**: Add `frontend-v3/**` to path triggers.

### 10. No workflow validation step

No workflow validates YAML syntax or uses `action-validator` to check workflow correctness.

---

## Low Issues

### 11. Hardcoded configuration in env vars

**File**: `.github/workflows/frontend-pwa.yml`
**Lines**: 82-90
**Issue**: REACT_APP_* vars include Firebase config, Sentry DSN in env block. These are build-time only but visible in CI logs.
**Fix**: Move all to secrets.

### 12. quality-gate.yml — Ineffective Dockerfile check

**File**: `.github/workflows/quality-gate.yml`
**Line**: 45
**Issue**: `grep -r "^FROM " --include="Dockerfile" . | sort | uniq` only prints base images, doesn't validate anything.
**Fix**: Add validation (check for pinned versions, no `latest` tags, no `root` user).

---

## Issues Fixed

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | `|| true` suppression | ci.yml:165 | Removed `|| true` from ruff check |
| 2 | `|| true` suppression | ci.yml:170 | Changed `npm install || true` to `npm ci` |
| 3 | Test truncation | ci.yml:222 | Removed `head -200` |
| 4 | Security scan suppressed | ci.yml:237,242 | Removed `continue-on-error: true` |
| 5 | ESLint not running in frontend-v3 | ci.yml:172 | Added `working-directory: frontend-v3`, added tsc and build steps |
| 6 | Overly restrictive license deny-list | dependency-review.yml:24-34 | Simplified to only deny AGPL/GPL/LGPL/BUSL/SSPL/RPL |
| 7 | Version inconsistency | formatting.yml:21 | Changed Python 3.12 → 3.14 |
| 8 | Version inconsistency | formatting.yml:34 | Changed Node 22 → 24 |
| 9 | CodeQL action unpinned | codeql-analysis.yml:35,42 | Pinned to `@v3.28.0` |
| 10 | CodeQL upload-sarif unpinned | scorecard.yml:35 | Pinned to `@v3.28.0` |
| 11 | Missing frontend-v3 paths | frontend-pwa.yml:7,12 | Added `frontend-v3/**` to path triggers |
| 12 | SSH key written to disk | deploy.yml:56 | Changed to use `ssh-agent` with `ssh-add -` |
| 13 | Destructive git operations | deploy.yml:111-113 | Added safety check: verify behind-count, try `merge --ff-only` |
| 14 | Missing cleanup | deploy.yml | Added `always()` SSH agent cleanup |
| 15 | Ineffective Dockerfile check | quality-gate.yml:45 | Added validation for pinned base images |
| 16 | No workflow YAML validation | quality-gate.yml | Added .github/workflows YAML validation |
| 17 | legacy-peer-deps flag | frontend-e2e.yml:29 | Removed `--legacy-peer-deps` |
| 18 | npm ci at wrong directory | ci.yml:170 | Added cache config and `working-directory: frontend-v3` |

---

## Workflow Count by Purpose

| Purpose | Count |
|---------|-------|
| CI | 1 |
| Security | 3 (CodeQL, Dependency Review, Scorecard) |
| Deploy | 5 (deploy, blue-green, canary, rollback, auto-rollback) |
| Frontend | 3 (PWA, E2E, formatting) |
| Mobile | 3 (Android, iOS, Flutter Desktop) |
| Quality | 2 (Quality Gate, Foundation Gate, Constitution Compliance) |
| Release | 2 (release, preview-deploy) |
| Nightly | 1 |
| SDK | 1 |
| Formatting | 1 |
| Preview | 1 |
