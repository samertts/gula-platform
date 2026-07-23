# GULA Platform — Support Policy

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Release Lifecycle](#1-release-lifecycle)
2. [Versioning Scheme](#2-versioning-scheme)
3. [Current Release Status](#3-current-release-status)
4. [Support Tiers](#4-support-tiers)
5. [Security Fixes](#5-security-fixes)
6. [Deprecation Policy](#6-deprecation-policy)
7. [Upgrade Path](#7-upgrade-path)
8. [End of Life Policy](#8-end-of-life-policy)
9. [Backward Compatibility Guarantees](#9-backward-compatibility-guarantees)
10. [Related Documents](#10-related-documents)

---

## 1. Release Lifecycle

GULA defines six release channels per the Engineering Constitution (Article 6.3):

| Phase | Description | Duration | Example |
|-------|-------------|----------|---------|
| Nightly | Syntax-only gate, daily builds | Per commit | 2.6.0-nightly.20260724 |
| Beta | All gates pass, weekly cadence | 1-2 weeks | 2.5.0-beta.1 |
| Release Candidate | Full certification, pre-production | Until stable | 2.5.0-rc.1 |
| Current (Stable) | Fully supported release | Monthly | 2.5.0 |
| LTS | Full audit + security backports | 2 years | 2.5.x LTS |
| End of Life | No support | — | < 2.0.0 |

Releases progress through stages: **Development** (local/dev) → **Integration** (CI) → **Staging** (E2E + perf) → **Canary** (production subset, 24h monitoring) → **Production** (full rollout).

## 2. Versioning Scheme

GULA follows **Semantic Versioning**: `MAJOR.MINOR.PATCH` with pre-release tags (`-rc.N`, `-beta.N`).

| Bump | When | Downtime | Example |
|------|------|----------|---------|
| **MAJOR** | Breaking API/database changes, architecture changes | <15 min | 2.5.0 → 3.0.0 |
| **MINOR** | New features, backward-compatible | <5 s | 2.4.0 → 2.5.0 |
| **PATCH** | Bug fixes, security patches | None | 2.5.0 → 2.5.1 |
| **Hotfix** | Emergency security / production outage | Immediate | 2.5.0 → 2.5.1 (expedited) |

Version is defined in `backend/app/config.py` (`APP_VERSION`) and reflected in API response headers (`X-API-Version`), health endpoints, and all Docker image tags.

## 3. Current Release Status

| Component | Version | Status | Release Date |
|-----------|---------|--------|-------------|
| GULA Backend | 2.5.0 | Current (Stable) | 2026-07-23 |
| GULA Frontend (v3) | 2.5.0 | Current (Stable) | 2026-07-23 |
| GULA Frontend (v2) | — | Legacy | — |
| Device Bridge | 0.1.0 | Development | — |
| NHOP Platform | 0.1.0 | Development | — |
| Edge Agent | 0.1.0 | Development | — |
| GULA Shared SDK | 2.5.0 | Current (Stable) | 2026-07-23 |
| Mobile Apps | 2.5.0 | Current (Stable) | 2026-07-15 |

### Recent Release History

| Version | Date | Highlights |
|---------|------|------------|
| 2.5.0 | 2026-07-23 | FHIR R4 Completion, Financial Engine Phase B, 1,841 tests |
| 2.3.2 | 2026-07-16 | National Notification Platform Tests (53 new tests) |
| 2.3.1 | 2026-07-16 | Identity Governance Persistence Tests (35 new tests) |
| 2.3.0 | 2026-07-16 | Missions 025-028 (Hospital, Nursing, Pharmacy, Radiology) |
| 2.2.0 | 2026-07-16 | Sprint-001: Repository Transformation, Missions 017-024 |
| 2.1.0 | 2026-07-14 | Engineering Program M4.x |
| 1.0.0 | 2026-07-14 | Foundation Complete |

## 4. Support Tiers

| Tier | SLA | Coverage | Customers |
|------|-----|----------|-----------|
| Platinum | 24/7, 1h response | All issues (critical, high, medium, low) | Enterprise |
| Gold | Business hours, 4h response | Critical and High severity | Standard |
| Silver | Business hours, 8h response | Critical only | Basic |
| Community | Best effort | Documentation, GitHub Issues | Open source |

### Severity Definitions

| Severity | Definition | Example |
|----------|------------|---------|
| **Critical** | Platform unavailable, data loss, patient safety, active exploit | Production outage, CVE ≥ 9.0 |
| **High** | Major feature broken, no workaround | Search down, result entry blocked |
| **Medium** | Feature impaired, workaround exists | Non-critical UI issue |
| **Low** | Cosmetic, documentation, enhancement | Typo, feature request |

## 5. Security Fixes

| Severity | Patch Timeline | Backport to LTS |
|----------|---------------|-----------------|
| Critical (CVSS ≥ 9.0) | Within 72 hours | Yes (12 months) |
| High (CVSS ≥ 7.0) | Within 2 weeks | Yes (12 months) |
| Medium (CVSS ≥ 4.0) | Next release cycle | Yes (12 months) |
| Low (CVSS < 4.0) | Next release cycle | Case-by-case |

- **Emergency releases** bypass normal process for CVSS ≥ 9.0, active exploitation, production data loss, or clinical safety incidents (Release Policy Article 15).
- Security scanning uses `safety` (CVE), `bandit` (SAST), `gitleaks` (secrets), and `trivy` (container) in CI.
- LTS releases receive security backports for 12 months after superseded.

## 6. Deprecation Policy

| Deprecation Type | Notice Period | Mechanism |
|-----------------|---------------|-----------|
| API endpoint | Minimum 2 minor versions (≥ 6 months) | `Deprecation: true` + `Sunset: {date}` headers |
| Feature / capability | Minimum 1 minor version | CHANGELOG announcement + migration guide |
| Database column | 1 full release cycle (dual-write period) | Write to both old and new columns |
| SDK / client library | 1 previous MAJOR version (3 months minimum) | Package deprecation notice |
| Plugin API | Same MAJOR version guaranteed | New MAJOR with migration path |

### Deprecation Workflow

```
ADR + API Decision → CHANGELOG Announcement (6-month notice)
  → Deprecation + Sunset HTTP Headers + Monitoring
  → 410 GONE response (3 months)
  → Code Removal
```

Usage of deprecated APIs is tracked via metrics to inform removal timing.

## 7. Upgrade Path

| From | To | Method |
|------|----|--------|
| 2.4.x → 2.5.x | 2.5.x | Direct upgrade, zero-downtime |
| 2.3.x → 2.5.x | 2.5.x | Requires intermediate upgrade to 2.4.x first |
| < 2.0.0 → 2.5.x | 2.5.x | Fresh deployment + data migration required |
| 2.x → 3.x | 3.x | Migration guide + coexistence window (≥ 6 months) |

### Upgrade Rules

- Database migrations are always applied **before** application code.
- Migrations are forward-only and backward-compatible for one version.
- New columns are nullable or have `server_default`.
- Rolling upgrade supported: new code works with old schema during deployment.
- Rollback is supported: `alembic downgrade -1` reverts the last migration.

## 8. End of Life Policy

- Releases enter EOL **12 months** after being superseded by a newer stable release.
- No security fixes, bug fixes, or support of any kind after EOL date.
- EOL announced **3 months in advance** via CHANGELOG and Deprecation headers.
- Archive Docker images remain available in GHCR.
- LTS releases receive 2 years of support from initial release date.

### Current EOL Schedule

| Version | Status | EOL Date |
|---------|--------|----------|
| 2.5.x | Current (Active) | — |
| 2.4.x | Maintenance (LTS) | 2027-07 |
| 2.3.x | Maintenance (LTS) | 2027-07 |
| 2.2.x | Maintenance | 2026-07 |
| 2.1.x | End of Life | 2026-07 |
| 1.x | End of Life | EOL |

## 9. Backward Compatibility Guarantees

Per the Backward Compatibility Policy (Constitution Article 23) and Engineering Constitution (Article 8):

### API

- All public `/api/v1/` endpoints remain functional within the same MAJOR version.
- Request/response schemas are additive only: new fields may be added, existing fields are never removed or changed in type.
- Error codes and formats remain consistent.
- Authentication and authorization mechanisms remain unchanged.
- Support window: **2 previous MAJOR versions**.

### Database

- All migrations are forward-only and backward-compatible for one version.
- New columns are nullable or have default values.
- Existing indexes and constraints are not removed without deprecation notice.
- Data backfill scripts support online migration (no downtime).
- Migration round-trip (`downgrade -1 && upgrade head`) is validated in CI.

### Integration

- FHIR endpoints maintain the same resource structure within MAJOR version.
- Event schemas are backward-compatible (additive only).
- Webhook payloads remain compatible.

### Exceptions

- Security patches may break compatibility if security risk outweighs compatibility cost (CISO approval required).
- Bug fixes correcting obviously broken behavior (500 error, data corruption) may change behavior without deprecation.

## 10. Related Documents

| Document | Location |
|----------|----------|
| RELEASE_CRITERIA.md | `docs/engineering/RELEASE_CRITERIA.md` |
| RELEASE_CHECKLIST.md | `docs/production/RELEASE_CHECKLIST.md` |
| CHANGELOG.md | `CHANGELOG.md` |
| BACKWARD_COMPATIBILITY.md | `docs/constitution/23_BACKWARD_COMPATIBILITY.md` |
| RELEASE_POLICY.md | `docs/constitution/22_RELEASE_POLICY.md` |
| ENGINEERING_CONSTITUTION.md | `docs/constitution/ENGINEERING_CONSTITUTION.md` |
| MIGRATION_GUIDE.md | `docs/deployment/MIGRATION_GUIDE.md` |
| ARCHITECTURE_PRINCIPLES.md | `docs/constitution/05_ARCHITECTURE_PRINCIPLES.md` |
| DATA_PRESERVATION_CONSTITUTION.md | `docs/constitution/31_DATA_PRESERVATION_CONSTITUTION.md` |
