# GULA Platform — Release Checklist

**Program:** PROGRAM-REPO-01 Wave 4 (Release Engineering)
**Version applied to:** v1.0.0 stream
**Last Updated:** 2026-08-08

## 1. Version Single Source (Wave 4 policy)

The platform release version has ONE canonical source: the root `VERSION`
file. Derived package surfaces are aligned to it at every release:

| Surface | Role | Value at v1.0.0 |
|---|---|---|
| `VERSION` (root) | **CANONICAL** platform release version | `1.0.0` |
| `package.json` (root) | **CANONICAL** (Vercel/build source) | `1.0.0` |
| `backend/app/config.py` → `APP_VERSION` | DERIVED | `1.0.0` |
| `backend/pyproject.toml` → `version` | DERIVED | `1.0.0` |
| `frontend-v3/package.json` + `package-lock.json` | DERIVED | `1.0.0` |
| `contracts/sdk/typescript/package.json` | DERIVED | `1.0.0` |
| `contracts/sdk/python/setup.py` | DERIVED | `1.0.0` |
| `mobile/desktop/pubspec.yaml` | INDEPENDENT component (managed by `release.yml` `bump-version`) | `2.1.0` |

**Rule:** independent component versions (mobile/desktop Flutter stream) are
NOT forced to match the platform version. Only platform-release surfaces above
must be synchronized.

## 2. Release Prerequisites

- [ ] Working tree clean on `remediate-security-001` (no uncommitted changes).
- [ ] No open GitHub Security Advisories without a triage owner.
- [ ] Branch synced with `origin/remediate-security-001`.
- [ ] `refs/archive/*` recoverability verified (if branch/tag hygiene performed).

## 3. Version Bump

For platform releases, bump the CANONICAL + DERIVED surfaces to the target
semver in one atomic commit:

1. `VERSION` → new version.
2. `backend/app/config.py` → `APP_VERSION`.
3. `backend/pyproject.toml` → `version`.
4. `frontend-v3/package.json` + `frontend-v3/package-lock.json` → new version.
5. `contracts/sdk/typescript/package.json` + `contracts/sdk/python/setup.py` →
   new version (only if the SDK surface changed).
6. Leave `mobile/desktop/pubspec.yaml` and all `mobile/` component versions to
   `release.yml` (`bump-version` job) — do not edit manually.

For the automated mobile/desktop release pipeline, use `.github/workflows/release.yml`
(workflow_dispatch `version` input). It validates SemVer, checks the tag is
absent, bumps `mobile/version.json`, Android, iOS, Flutter desktop, backend
config, commits, tags `vX.Y.Z`, builds all artifacts, drafts a GitHub Release,
and (unless skipped) deploys to stores.

## 4. Quality Gates (run before tagging)

- [ ] Backend full suite passes (integration + unit + governance).
- [ ] ruff baseline not exceeded (target 379).
- [ ] `tsc --noEmit` zero errors.
- [ ] eslint zero errors.
- [ ] vitest frontend tests pass (122).
- [ ] `make validate` verdict PASS (enterprise validation engine).
- [ ] Architecture constitution gate PASS (0 new findings).
- [ ] Domain certification 11/11 PASS.
- [ ] Migrations chain intact (`alembic upgrade head` dry-run).
- [ ] Vercel configuration valid (frontend deploy dry-run).
- [ ] Docker images build (backend multi-stage, non-root).

## 5. Release Artifacts / Documentation

- [ ] `CHANGELOG.md` updated with a `## [x.y.z] — <date>` section.
- [ ] `docs/releases/vX.Y.Z/RELEASE_NOTES.md` created (mirror CHANGELOG).
- [ ] `docs/release/KNOWN_LIMITATIONS.md` version header updated.
- [ ] `docs/release/SUPPORT_POLICY.md` supported-version table updated.
- [ ] `SECURITY.md` supported-version table updated.
- [ ] SemVer tag `vX.Y.Z` created (annotated).

## 6. Tag & Release Discipline (Wave 4 policy)

- **Release tags only:** `vX.Y.Z` (+ optional `-rc.N` pre-release). Feature
  tags are archived to `refs/archive/tags/*`, never created on the live stream.
- **Every release tag must have a GitHub Release** (CHANGELOG section +
  assets), matching `release.yml`'s `v*` validation.
- **No automatic production declaration:** publishing a GitHub Release does not
  by itself declare the platform production-ready. Production readiness is a
  separate Program Director decision with its own certification.

## 7. Post-Release

- [ ] GitHub Release published with assets (AAB/APK/IPA/desktop bundles).
- [ ] `mobile/CHANGELOG.md` present (required by `release.yml`).
- [ ] Release notifications fired (Slack/Telegram) — optional, env-gated.
- [ ] Rollback path documented: `git revert` of the version-bump commit, or
  re-release previous tag.

## 8. Rollback Procedure

A release is independently reversible per commit:

```bash
git revert <version-bump-commit>        # restores previous version surfaces
git tag -d vX.Y.Z                        # remove tag (local)
git push origin :refs/tags/vX.Y.Z        # remove tag (remote)
```

Archived branches/tags remain recoverable from `refs/archive/*` (see
`docs/governance/GIT_STRATEGY.md`).
