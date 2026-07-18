# Release Notes — National Applications Suite v1.0 (PI-003)

**Release:** national-applications-v1.0  
**Date:** 2026-07-16  
**Platform Version:** 2.1.0  
**Documentation Freeze:** PI-003 — National Applications Suite

---

## Overview

PI-003 delivers the **National Applications Suite** — a unified set of four
application types (Desktop, Mobile, Web, PWA) all backed by a single backend,
a single SDK (`shared/sdk/client.py`), and a single authentication platform
(`shared/auth/`). This release completes the National Applications layer on top
of the existing National Platform (Missions 017-024).

---

## New in This Release

### 1. National Laboratory Desktop Professional (Mission 024)

Native Windows desktop application for laboratory professionals.

- **Specimen lifecycle:** Registration, barcode, collection, receiving, acceptance,
  aliquot, storage, tracking, chain of custody, disposal
- **Analyzer integration:** ASTM E1394, HL7 ORU^R01, POCT, bidirectional support,
  driver abstraction, offline buffer (`services/device_bridge/`)
- **Quality management:** IQC, EQA, Westgard rules, Levey-Jennings charts,
  calibration tracking, reagent monitoring, lot management
- **Result management:** Auto-validation, manual validation, delta check,
  critical results, electronic signatures, version history
- **Offline-first:** Local SQLite encrypted with AES-256-GCM, background sync
  with delta sync (~70% bandwidth reduction), conflict resolution

### 2. Citizen Super App — Mobile (Mission 021)

Native Android mobile application (iOS-ready).

- **Digital health card:** QR-backed identity with HMAC-signed tokens (`routes/patient_card.py`)
- **Biometric login:** Fingerprint + Face ID, device registration
- **Health dashboard:** Summary, appointments, lab results, prescriptions, vaccinations
- **Offline-first:** Encrypted Room DB, WorkManager background sync, queue-based mutations
- **Family platform:** Guardian access, children, parents, dependents, growth charts

### 3. Citizen Super App — PWA (Mission 021)

Progressive Web Application served from the same `frontend-v2/` codebase.

- **React 19 + Vite 6 + TypeScript** (`frontend-v2/package.json`)
- **PWA:** Service worker (`frontend/sw.js`), manifest.json (`"display": "standalone"`),
  cache-first shell, background sync
- **RTL/Arabic-first:** `"dir": "rtl"`, `"lang": "ar"` in manifest
- **Offline:** IndexedDB local cache, queued mutations, reconnect replay
- **Responsive:** All breakpoints (480px → 1440px+)

### 4. One Design System

Unified design tokens across all applications (`shared/design_system/`).

- **Tokens:** Colors, typography, spacing, breakpoints, shadows, z-index
  (`shared/design_system/tokens.py`)
- **RTL:** Arabic-first layout with bidirectional support
  (`shared/design_system/rtl.py`)
- **Components:** Button, Card, Dialog, Form, Input, Table, Icon
  (`shared/design_system/components.py`)
- **Dark mode:** Automatic via `prefers-color-scheme` + manual override
- **Accessibility:** WCAG 2.2 AA compliant, keyboard navigation, screen reader support

### 5. One SDK (`shared/sdk/client.py`)

Single HTTP client used by all applications:

```python
client = GulaClient(base_url="https://api.gula-platform.org", api_key=token)
patient = client.get_patient(patient_id)
results = client.list_results(order_id=order_id)
```

### 6. One Auth Platform

| Protocol | Support | Implementation |
|----------|---------|---------------|
| JWT (access + refresh) | All apps | `shared/auth/jwt.py`, `app/security/auth.py` |
| OAuth2 / OIDC | Third-party | `app/security/oauth2_provider.py` |
| SAML 2.0 | Government SSO | `app/security/saml_service.py` |
| MFA (TOTP) | Web + Mobile | `app/security/mfa_service.py`, `shared/auth/mfa.py` |
| WebAuthn / FIDO2 | Web + Mobile | `shared/auth/webauthn.py` |
| Service Accounts | M2M integrations | `routes/service_accounts.py` |

---

## Architecture Highlights

### Shared Backend Pattern

All four application types connect to the same `gula-backend` (FastAPI monolith)
through the same API gateway:

```
Desktop (PySide6)  ─┐
Mobile (Kotlin)    ─┤
Web (React)         ─┤── api-gateway (nginx) → gula-backend (FastAPI)
PWA (SW)           ─┘
```

No separate backends per application type. The `shared/` package ensures code
reuse across all layers: SDK, auth, design system, RBAC, validators.

### Offline-First Architecture

| Application | Local Storage | Sync Engine | Conflict Resolution |
|-------------|---------------|-------------|-------------------|
| Desktop | SQLite (AES-256-GCM) | Background thread + delta sync | LWW + manual override |
| Mobile | Room DB (encrypted) | WorkManager / BGTaskScheduler | LWW |
| PWA | IndexedDB | Background Sync API | LWW |

### Code Reuse (shared/)

| Module | Lines of Code | Consumed By |
|--------|--------------|-------------|
| `shared/sdk/client.py` | 107 | Desktop, Mobile, Web |
| `shared/auth/` | 120 | Backend, Desktop, Mobile, Web |
| `shared/design_system/` | 220 | Desktop, Web |
| `shared/rbac/` | 200 | Backend, Desktop, Web |
| `shared/security/` | 85 | Backend, Desktop, Mobile |

---

## Performance Summary

| Metric | Budget | Actual | Status |
|--------|--------|--------|--------|
| API P95 latency | <500ms | 130ms | ✓ |
| API P99 latency | <1s | 300ms | ✓ |
| DB query (indexed) | <20ms | 8ms | ✓ |
| Web page load (4G) | <2s | 0.8s | ✓ |
| Cache hit rate | >90% | 96% | ✓ |
| Error rate | <0.5% | 0.1% | ✓ |
| Max throughput | 1,000 req/s | 1,800 req/s | ✓ |

---

## Security Summary

| Requirement | Status |
|------------|--------|
| JWT authentication | ✓ |
| OAuth2 / OIDC | ✓ |
| SAML 2.0 SSO | ✓ |
| MFA (TOTP + WebAuthn) | ✓ |
| RBAC (9+ roles) + ABAC | ✓ |
| Encryption at rest (AES-256-GCM) | ✓ |
| TLS 1.3 in transit | ✓ |
| Audit log (hash chain) | ✓ |
| Tenant isolation (lab_id) | ✓ |
| Rate limiting | ✓ |
| Security headers (CSP, HSTS, XFO) | ✓ |
| Secret scanning in CI | ✓ |

---

## Migration Notes

No schema migrations are required for this release. PI-003 is purely an
application-layer release — all National Platform tables were introduced in
prior releases (Missions 017-024, v2.2.0).

---

## Breaking Changes

**None.** This release adds four application types without modifying existing
backend routes, models, or APIs. All existing integrations continue to work
unchanged.

---

## Known Issues

| Issue | Impact | Workaround | Target Fix |
|-------|--------|------------|------------|
| iOS native app not yet submitted to App Store | iOS users must use PWA | PWA works fully | PI-004 |
| Desktop auto-update requires admin rights | Non-admin users cannot auto-update | IT admin deploys via SCCM | PI-004 |
| Large FHIR bundles (>10MB) timeout on mobile | Slow FHIR search | Use pagination + summary | PI-004 |

---

## Quality Gates

- [x] `make ci` passes (syntax, lint, docker build)
- [x] 28+ test modules pass (`cd backend && python -m pytest tests/ -v`)
- [x] All migrations tested round-trip
- [x] Security scan (bandit, safety, gitleaks) — all clear
- [x] Performance budgets met
- [x] PWA Lighthouse score ≥ 90

---

## Related Tags

- `national-applications-v1.0` ← **This release (PI-003 freeze)**

---

## Document References

| Document | Path |
|----------|------|
| Application Architecture | `docs/freeze/pi-003/APPLICATION_ARCHITECTURE.md` |
| UI/UX Guidelines | `docs/freeze/pi-003/UI_GUIDELINES.md` |
| Deployment Guide | `docs/freeze/pi-003/DEPLOYMENT_GUIDE.md` |
| Performance Report | `docs/freeze/pi-003/PERFORMANCE_REPORT.md` |
| Security Report | `docs/freeze/pi-003/SECURITY_REPORT.md` |
| National Platform Architecture | `docs/national/ARCHITECTURE.md` |
| National Platform Performance | `docs/national/PERFORMANCE.md` |
| National Platform Security | `docs/national/SECURITY.md` |
