# DEPLOYMENT GUIDE — PI-003 National Applications Suite

## 1. Overview

PI-003 deploys four application types across multiple platforms. Each application
type has its own deployment pipeline, but all share the same backend infrastructure
and authentication platform.

### Deployment Targets

| Platform | Application | Pipeline |
|----------|------------|----------|
| Windows | Desktop (PySide6) | Signed MSI installer + auto-update |
| Linux | Desktop (PySide6) | AppImage + APT repo |
| Android | Mobile (Kotlin) | Google Play + APK sideload |
| iOS | Mobile (iOS-ready) | TestFlight + App Store |
| Web | React/PWA | Docker + CDN |
| PWA | Service Worker | Same as Web |

## 2. Backend Deployment

### 2.1 Primary: Docker Compose

```bash
# Production stack
docker compose up -d postgres redis gula-backend api-gateway

# Verify readiness
make health-deep  # Should report GREEN

# Monitoring
make ps           # Container status table
make logs-backend # Tail backend logs
```

### 2.2 Blue/Green Deployment (`blue-green-deploy.yml`)

The blue-green workflow swaps traffic atomically between two backend stacks:

```
Current state:
  Blue  (live)    → api-gateway upstream blue:8000
  Green (standby) → idle

Deployment:
  1. Build new image → tag as gula-backend:green
  2. docker compose up -d gula-backend-green
  3. Run health checks against green:8000/health/ready
  4. Swap api-gateway upstream → green
  5. Keep blue running for 5 minutes (rollback window)
  6. Tear down blue

Rollback:
  Reverse step 4 → traffic back to blue
```

### 2.3 Canary Releases

Canary deploys use the `docker-compose.scale.yml` HAProxy configuration:

```bash
# Deploy canary (1/10 traffic)
docker compose -f docker-compose.yml -f docker-compose.scale.yml \
  up -d --scale gula-backend=9 --scale gula-backend-canary=1

# Monitor metrics at http://localhost:8404/stats
# Check error rates before promoting
```

Canary promotion:
```bash
docker compose up -d --scale gula-backend=10 --scale gula-backend-canary=0
```

### 2.4 Rollback Procedure

```bash
# 1. Revert Docker image tag
docker tag gula-backend:previous gula-backend:latest

# 2. Restart with previous image
docker compose up -d gula-backend

# 3. Verify
make health-deep

# 4. If database migration was applied:
#    cd backend && alembic downgrade -1
```

## 3. Desktop Application Deployment

### 3.1 Windows (PySide6)

**Build pipeline:**
- PyInstaller → single MSI installer
- Signed with EV code signing certificate
- Version embedded in `backend/app/config.py:APP_VERSION`

**Distribution:**
- Primary: Auto-update via built-in update checker
- Fallback: Download from GULA Portal (authenticated)
- Enterprise: SCCM/Intune deployment via MSI

**Auto-update mechanism:**
```python
# On launch, check:
GET /api/v1/desktop/version
Response: {"latest": "2.1.0", "download_url": "...", "sha256": "..."}

# Download + verify SHA256 + install silently
# Rollback supported for 3 previous versions
```

**Version management:**
| Channel | Update Frequency | Audience |
|---------|-----------------|----------|
| Stable | Monthly | All labs |
| Beta | Weekly | Pilot labs |
| Canary | Per-commit | Internal QA |

### 3.2 Linux

**Distribution:**
- AppImage (self-contained, portable)
- APT repository for Debian/Ubuntu (`apt install gula-desktop`)
- RPM for Fedora/RHEL

**Auto-update:**
Same endpoint as Windows — binary is replaced on update.

## 4. Mobile Application Deployment

### 4.1 Android

**Build pipeline:**
- Gradle build → AAB (Android App Bundle)
- Signed with Google Play App Signing
- Version: `major.minor.patch` + build number

**Google Play:**
```yaml
# Build flavors in app/build.gradle
flavorDimensions: ["environment"]
productFlavors:
  production:
    applicationId: "org.gula.platform"
  staging:
    applicationId: "org.gula.platform.staging"
  development:
    applicationId: "org.gula.platform.dev"
```

**Release tracks:**
| Track | Rollout | Update |
|-------|---------|--------|
| Internal | 100% QA team | Immediate |
| Closed Alpha | 20 testers | Manual opt-in |
| Open Beta | 10% of users | Staged 1%→5%→10% |
| Production | 100% | Staged 1%→25%→50%→100% |

**Incremental updates:**
- Play Feature Delivery for on-demand modules (lab results, radiology)
- In-app updates API for critical patches (min 48h Play review bypass)
- delta updates via Play asset delivery

**APK sideload:**
- For air-gapped labs: signed APK distributed via USB
- Version locked to `MIN_SUPPORTED_VERSION` enforced by API

### 4.2 iOS

**Build pipeline:**
- Xcode build → IPA
- App Store Connect distribution
- TestFlight for beta testing

**Version management:**
| Channel | Distribution | Notes |
|---------|-------------|-------|
| TestFlight | Internal + External | Max 10,000 testers |
| App Store | Production | Phased release (7d ramp) |

**iOS-specific constraints:**
- PWA as fallback when native app is not available
- Biometric auth via Face ID / Touch ID
- Push notifications via APNS
- Background sync via BGTaskScheduler (limited to 15 min)

## 5. PWA Deployment Strategy

### 5.1 Build & Serve

```bash
cd frontend-v2
npm run build  # Vite → dist/
```

Served via the same `api-gateway` nginx:
```nginx
location / {
    root /var/www/gula/frontend-v2/dist;
    try_files $uri /index.html;
}
```

### 5.2 Service Worker Lifecycle

The service worker (`frontend/sw.js`) uses cache-first for static assets and
network-only for API calls:

```
Install  → Pre-cache shell (/, /index.html, assets)
Activate → Clean old caches
Fetch    → Network-first for JS/CSS, network-only for API, stale-while-revalidate for images
```

**Update flow:**
1. New SW detected on page load
2. New SW installs, waits for all tabs to close
3. `skipWaiting()` on reload prompt
4. User prompted: "Update available — refresh to get the latest version"
5. On accept: `postMessage('SKIP_WAITING')` → new SW activates

### 5.3 Offline First

- App shell cached on install — works offline immediately
- API failures gracefully degrade to cached UI state
- Mutations queued in IndexedDB for retry when online
- Background Sync API re-plays queued mutations

## 6. CI/CD Pipeline

### 6.1 CI Pipeline (`.github/workflows/ci.yml`)

Jobs in dependency order:
1. **syntax-gate** — `py_compile` + `flake8 E9/F821`
2. **migration-check** — `alembic upgrade head` on fresh DB
3. **smoke-test** — curl health endpoints
4. **backend-test** — `pytest tests/` (28 test modules)
5. **security-scan** — safety, bandit, hadolint, gitleaks
6. **build-and-push** — Matrix build (8 images → GHCR)

### 6.2 Deploy Pipeline (`.github/workflows/deploy.yml`)

```
Build → Push to GHCR → Migration → Health Check → Traffic Switch
```

### 6.3 Rollback Triggers

Automatic rollback on:
- Health check failure (>3 consecutive failures)
- Error rate > 5% above baseline
- P99 latency > 2x baseline
- Migration failure

## 7. Environment Configuration

### 7.1 Environment Files

| File | Git | Purpose |
|------|-----|---------|
| `.env.example` | Tracked | Template for all env vars |
| `.env` | Ignored | Real secrets |
| `.env.production` | Tracked | Production template (no secrets) |

### 7.2 Key Variables for Deployment

```bash
# Docker Compose
COMPOSE_PROJECT_NAME=gula

# Backend
DATABASE_URL=postgresql://gula:${POSTGRES_PASSWORD}@gula-postgres:5432/gula
REDIS_URL=redis://:${REDIS_PASSWORD}@gula-redis:6379/0
SECRET_KEY=<64-byte-random>
REFRESH_TOKEN_SECRET=<64-byte-random>
ENCRYPTION_KEY=<32-byte-key>
NID_HMAC_KEY=<64-byte-key>
JWT_EXPIRE_MINUTES=120

# Scaling
WEB_CONCURRENCY=3
MAX_CONCURRENT_REQUESTS=200
DB_POOL_SIZE=6
DB_MAX_OVERFLOW=12
```

## 8. Release Checklist

### 8.1 Pre-Deployment

- [ ] `make ci` passes (syntax, lint, docker build)
- [ ] All 28+ test modules pass: `cd backend && python -m pytest tests/ -v`
- [ ] Migration tested round-trip: `alembic upgrade head && alembic downgrade -1 && alembic upgrade head`
- [ ] Security scan passed (bandit, safety, gitleaks)
- [ ] CHANGELOG updated
- [ ] Version bumped in `backend/app/config.py`
- [ ] `.env.example` synced with new variables
- [ ] Tag created: `git tag national-applications-v1.0`

### 8.2 Deployment

- [ ] Database backup: `make backup`
- [ ] Blue/green deploy triggered
- [ ] Health check GREEN confirmed
- [ ] Canary (10% traffic) stable for 15 minutes
- [ ] Full rollout to 100%
- [ ] Monitoring dashboards verified

### 8.3 Post-Deployment

- [ ] Sentry error rate normal
- [ ] P99 latency within baseline
- [ ] All labs reachable
- [ ] Audit logs flowing
- [ ] Rollback plan ready (undo tag + `alembic downgrade`)
