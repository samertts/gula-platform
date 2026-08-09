# GULA Platform — Release Readiness

**Program:** PROGRAM-REPO-01 Wave 4 (Release Engineering)
**Date:** 2026-08-08
**Assessment target:** v1.0.0 stream

## 1. Purpose

This document records the platform's **release readiness** — the ability to
produce and publish a repeatable, verifiable, reversible software release —
without declaring the platform **production ready** (a separate, Program
Director-approved decision).

## 2. Release Readiness Dimensions

| Dimension | Status | Evidence |
|---|---|---|
| Single version source | ✅ | `VERSION` = 1.0.0; derived surfaces aligned (B-6) |
| Version consistency | ✅ | root/backend/frontend/contracts = 1.0.0; desktop = 2.1.0 (independent) |
| Release stream discipline | ✅ | 35 non-semver tags archived; 3 semver tags remain (B-5) |
| Branch hygiene | ✅ | 2 remote heads; 61 branches archived to `refs/archive/branches/*` (B-5) |
| Automated release pipeline | ✅ | `.github/workflows/release.yml` (validate → bump → build → GitHub Release → stores) |
| CHANGELOG discipline | ✅ | `CHANGELOG.md` maintained; Wave 4 section added |
| Release notes | ✅ | `docs/releases/v1.0.0/RELEASE_NOTES.md` exists; RC2 DEPLOYMENT.md preserved |
| Support policy | ✅ | `docs/release/SUPPORT_POLICY.md`; SECURITY.md 1.0.x policy |
| Known limitations | ✅ | `docs/release/KNOWN_LIMITATIONS.md` tracked |
| Recoverability | ✅ | `refs/archive/*` mirrored locally + origin; SHA-verified |
| Rollback path | ✅ | per-commit `git revert`; archive recovery documented |
| Public release artifacts | ⚠️ | NO GitHub Release v1.0.0 created (intentional — pending PD) |

## 3. What This Does NOT Certify

- **Production readiness** — the platform is NOT automatically declared
  production-ready. The v1.0.0 tag recommendation in RELEASE_NOTES.md is a
  certification-of-stability statement, not a production deployment order.
- **Store deployments** — mobile store uploads are gated on PD approval and
  the `release.yml` `deploy-to-stores` job.
- **Clinical safety** — no clinical-safety module is implemented or claimed
  (see `docs/programs/PROGRAM_NEXT_PHASE_PLAN.md`).

## 4. Release Readiness Checklist Summary

Refer to `docs/release/RELEASE_CHECKLIST.md` for the full per-release checklist.
Key release-readiness invariants:

1. `VERSION` == all DERIVED platform surfaces == latest release tag.
2. No open un-triaged security advisory blocks the release.
3. All quality gates pass before tagging (see checklist §4).
4. Every release tag has a GitHub Release; no feature tags on the stream.
5. Any archived ref is recoverable via `refs/archive/*`.

## 5. Outstanding Items Before a Public v1.0.0 GitHub Release

| # | Item | Owner | Depends on |
|---|---|---|---|
| 1 | Program Director approval to create GitHub Release v1.0.0 | PD | this document |
| 2 | Production-readiness certification decision | PD | PRODUCTION_READINESS.md + deployment review |
| 3 | (Optional) store credentials verification for `deploy-to-stores` | DevSecOps | release.yml |

## 6. Related Documents

- `docs/release/RELEASE_CHECKLIST.md`
- `docs/release/SUPPORT_POLICY.md` / `docs/release/KNOWN_LIMITATIONS.md`
- `docs/releases/v1.0.0/RELEASE_NOTES.md`
- `docs/governance/GIT_STRATEGY.md`
- `docs/programs/PROGRAM_REPO_01_FINAL_CERTIFICATION.md`
- `.github/workflows/release.yml`
