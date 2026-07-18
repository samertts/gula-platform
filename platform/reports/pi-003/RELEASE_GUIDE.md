# PI-003 — Release Guide

## National Applications Release Process

**Version:** 2.1.0

---

## 1. Version Numbering

GULA follows **Semantic Versioning (SemVer 2.0.0)**:

```
MAJOR.MINOR.PATCH
```

| Component | Current Version | Meaning |
|-----------|----------------|---------|
| @gula/ui-platform | 1.0.0 | Shared UI library |
| @gula/citizen-app | 2.1.0 | Citizen PWA |
| @gula/doctor-app | 2.1.0 | Doctor web app |
| @gula/laboratory-app | 2.1.0 | Laboratory LIS |
| @gula/radiology-app | 2.1.0 | Radiology RIS |
| @gula/pharmacy | 2.1.0 | Pharmacy system |
| @gula/hospital-app | 2.1.0 | Hospital admin |
| @gula/nurse-app | 2.1.0 | Nurse mobile |
| @gula/ministry-app | 2.1.0 | Ministry dashboard |
| @gula/update-platform | 2.1.0 | Update system |

**Version bump rules:**
- **MAJOR**: Breaking API changes, breaking UI changes, data migration required
- **MINOR**: New features, non-breaking enhancements
- **PATCH**: Bug fixes, performance improvements, dependency updates

---

## 2. Release Branches

```
main ← production-ready code
  └── develop ← integration branch
       ├── feature/APP-XXX-description ← feature branches
       └── fix/APP-XXX-description ← bug fix branches
```

### Branch naming convention

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/APP-<id>-<kebab-description>` | `feature/CIT-123-offline-wallet` |
| Bugfix | `fix/APP-<id>-<kebab-description>` | `fix/DOC-456-broken-pagination` |
| Hotfix | `hotfix/APP-<id>-<kebab-description>` | `hotfix/LAB-789-security-fix` |
| Release | `release/v<version>` | `release/v2.2.0` |

---

## 3. Quality Gates

### Gate 1: Code Quality (Pre-merge)

| Check | Tool | Pass Condition |
|-------|------|----------------|
| TypeScript compilation | `tsc -b` | No errors |
| Linting | `eslint .` | 0 errors, 0 warnings |
| Unit tests | `jest --passWithNoTests` | 100% pass, >= 95% coverage |
| Bundle size check | `vite build` comparison | No increase > 5% |
| Dependency audit | `pnpm audit` | 0 critical, 0 high |

### Gate 2: Integration (Post-merge to develop)

| Check | Description |
|-------|-------------|
| Build all apps | `pnpm --filter "*" build` passes |
| E2E tests (Playwright) | All critical paths pass |
| Lighthouse CI | PWA >= 90, Performance >= 85, Accessibility >= 95 |
| Visual regression (Chromatic) | No unexpected visual changes |
| Cross-browser tests | Chrome, Firefox, Safari, Edge latest |

### Gate 3: Pre-production (Release branch)

| Check | Description |
|-------|-------------|
| Staging deployment | All apps deployed to staging |
| Smoke tests | All critical user journeys pass |
| Performance tests | Lighthouse scores met, no regressions |
| Security scan | OWASP ZAP no high findings |
| Manual QA | Signed off by QA lead |

### Gate 4: Production (Pre-release)

| Check | Sign-off Required |
|-------|-------------------|
| All quality gates passed | QA Lead |
| Security review passed | Security Lead |
| Clinical safety review | Clinical Lead |
| Documentation updated | Tech Writer |
| Release notes approved | Product Manager |

---

## 4. Sign-Off Process

### Release Candidate Sign-Off

```
1. Developer raises PR → feature/ → develop
2. CI runs (Gate 1)
3. Code review (2 approvals required)
4. Merge to develop
5. CI runs (Gate 2)
6. QA team validates on staging
7. Release branch cut from develop
8. CI runs (Gate 3)
9. Product Manager reviews release notes
10. Stakeholder sign-off
11. Merge to main + tag
12. Production deployment
```

### Emergency Hotfix Process

```
1. Hotfix branch from main
2. CI runs (Gate 1) — expedited
3. Single reviewer approval (any senior engineer)
4. Merge to main + tag patch version
5. Production deployment immediately
6. Backport to develop within 24 hours
```

---

## 5. Rollback Procedure

### Automated Rollback (CI/CD)

```bash
# Rollback to previous version
aws s3 sync s3://gula-apps-prod/<app>/releases/v<prev-version>/ \
  s3://gula-apps-prod/<app>/current/ \
  --delete

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id <DIST_ID> \
  --paths "/*"
```

### Manual Rollback Steps

1. **Identify failure**: Monitor alerts (error rate > 1%, 5xx > 0.5%)
2. **Trigger rollback**: Run `./scripts/rollback-app.sh <app> <version>`
3. **Verify**: Health checks pass, error rate normalizes
4. **Post-mortem**: Within 24 hours, document root cause
5. **Re-deploy**: After fix, repeat release process

### Rollback Criteria

| Signal | Threshold | Action |
|--------|-----------|--------|
| Error rate | > 2% in 5 minutes | Automatic rollback |
| API 5xx | > 1% in 5 minutes | Automatic rollback |
| PWA install failure | > 5% decrease | Manual rollback |
| User-reported critical bug | Any | Manual rollback |
| Security vulnerability | Any | Emergency rollback |

---

## 6. Release Artifacts

Each release produces:

```
artifacts/v2.1.0/
├── citizen-app/
│   ├── dist/              # Built application
│   ├── citizen-app-v2.1.0.tar.gz
│   └── citizen-app-v2.1.0.sha256
├── doctor-app/
│   ├── dist/
│   ├── doctor-app-v2.1.0.tar.gz
│   └── doctor-app-v2.1.0.sha256
├── ... (per app)
└── sbom/
    ├── sbom-v2.1.0.json       # SPDX 2.3
    └── sbom-v2.1.0.cyclonedx  # CycloneDX 1.5
```

---

## 7. Release Communication

| Audience | Medium | Content |
|----------|--------|---------|
| Internal team | Slack #releases | Version, changelog, deployment window |
| Stakeholders | Email | Executive summary, key changes |
| End users | In-app notification | What's new modal (triggered by SW update) |
| Ministry | Formal document | Release notes, certification status |
| Public | Website/blog | Major feature announcements |
