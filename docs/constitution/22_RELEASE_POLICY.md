# GULA Release Policy

## Release Philosophy

GULA follows continuous delivery with semantic versioning. Releases are frequent, small, and reversible. The platform is always in a deployable state.

## Versioning

1. **Semantic Versioning:** `MAJOR.MINOR.PATCH`
   - **MAJOR** — Backward-incompatible API or database changes
   - **MINOR** — New features, backward-compatible
   - **PATCH** — Bug fixes, security patches, performance improvements

2. **Pre-release tags:** `MAJOR.MINOR.PATCH-rc.N` (release candidate), `MAJOR.MINOR.PATCH-beta.N` (beta)

3. **Version is defined** in `backend/app/config.py` (`APP_VERSION`) and reflected in the API response headers.

## Release Process

4. **Main branch is always deployable.** Every commit to main passes all quality gates.

5. **Feature branches** are created from main, developed, tested, and merged back via PR.

6. **Release branches** (`release/v{Major}.{Minor}`) are created from main at release time. Bug fixes are backported.

7. **Hotfix branches** are created from the release branch for emergency fixes.

## Release Stages

| Stage | Environment | Criteria |
|-------|-------------|----------|
| **Development** | Local / Dev | Feature complete, unit tests pass |
| **Integration** | CI | Build passes, integration tests pass, security scan passes |
| **Staging** | Staging | E2E tests pass, performance tests pass, clinical review (if applicable) |
| **Canary** | Production (subset) | Monitoring shows no regressions after 24 hours |
| **Production** | Production (full) | All previous stages passed, release approved |

## Rollback

8. **Every release has a rollback plan.** Database migrations are backward-compatible for one version.

9. **Rollback triggers:** error rate increase > 1%, p95 latency increase > 50%, critical alert triggered, clinical safety concern reported.

10. **Rollback procedure** is documented in `docs/operations/rollback.md`.

## Release Artifacts

11. **Every release produces:** Docker images (tagged with version), Helm charts, migration scripts, release notes, and updated documentation.

12. **Docker images** are tagged with `{version}`, `latest` (stable releases only), and git commit SHA.

13. **Release notes** include: new features, bug fixes, breaking changes, deprecation notices, upgrade instructions, and credits.

## Emergency Releases

14. **Emergency releases** bypass the normal process for critical security vulnerabilities or production outages.

15. **Emergency release criteria:** CVE with CVSS >= 9.0, active exploitation, production data loss, or clinical safety incident.

16. **Post-emergency retrospective** is conducted within 48 hours to improve the process.
