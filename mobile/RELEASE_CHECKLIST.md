# Release Checklist

Use this checklist before and during every GULA Platform release.

## Pre-Release (T-7 days)

### Code Quality
- [ ] All PRs merged to `develop` branch
- [ ] All CI pipelines green on `develop`
- [ ] Quality gate passed (lint, tests, coverage >= 85%, security scan)
- [ ] No critical or high-severity security vulnerabilities
- [ ] All TODO/FIXME comments reviewed and resolved where applicable
- [ ] License compliance verified

### Testing
- [ ] Unit tests pass on all platforms
- [ ] Integration tests pass on all platforms
- [ ] UI/Instrumented tests pass on all platforms
- [ ] Manual regression testing completed on:
  - [ ] Android (phone + tablet)
  - [ ] iOS (iPhone + iPad)
  - [ ] Windows desktop
  - [ ] macOS desktop
  - [ ] Linux desktop
  - [ ] PWA (Chrome, Firefox, Safari, Edge)
- [ ] Offline mode tested
- [ ] Sync engine tested with conflict scenarios
- [ ] Performance benchmarks meet thresholds (p95 < 500ms, p99 < 1000ms, error rate < 1%)
- [ ] Instrument integration tested (if applicable)

### Documentation
- [ ] API documentation updated (OpenAPI spec)
- [ ] User documentation reviewed
- [ ] Release notes drafted (English + Arabic)
- [ ] CHANGELOG.md updated
- [ ] Migration notes prepared (if applicable)

## Release Candidate (T-3 days)

### Versioning
- [ ] Version bumped in `mobile/version.json`
- [ ] Version bumped in `backend/app/config.py`
- [ ] Version bumped in `mobile/android/app/build.gradle.kts`
- [ ] Version bumped in `mobile/ios/Gula/Info.plist`
- [ ] Version bumped in `mobile/desktop/pubspec.yaml`
- [ ] Version bumped in all SDK package files
- [ ] Version code/number incremented appropriately

### Build Verification
- [ ] Android debug APK builds successfully
- [ ] Android release AAB builds successfully
- [ ] Android release APK builds successfully
- [ ] iOS debug build succeeds
- [ ] iOS release archive succeeds
- [ ] iOS IPA exports successfully
- [ ] Flutter desktop builds (Windows/Linux/macOS) succeed
- [ ] PWA builds successfully
- [ ] All SDK packages compile

### Store Listings
- [ ] Google Play Store listing reviewed (English)
- [ ] Google Play Store listing reviewed (Arabic)
- [ ] Apple App Store listing reviewed (English)
- [ ] Apple App Store listing reviewed (Arabic)
- [ ] Microsoft Store listing reviewed (English/Arabic)
- [ ] Screenshots updated for all platforms
- [ ] Feature graphic updated
- [ ] Privacy policy reviewed and dated
- [ ] Terms of service reviewed and dated

## Release Day

### Final Checks
- [ ] All release candidate builds created and tested
- [ ] Smoke tests passed on staging environment
- [ ] Database migrations verified on staging
- [ ] Feature flags configured correctly
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented
- [ ] Release team notified

### Deployment

#### Android
- [ ] Upload AAB to Google Play Console (alpha track)
- [ ] Internal test successful (alpha)
- [ ] Promote to beta track
- [ ] Beta test period (minimum 24 hours)
- [ ] No crash reports in beta
- [ ] Promote to production
- [ ] Start staged rollout (10% -> 50% -> 100%)

#### iOS
- [ ] Upload IPA to App Store Connect via TestFlight
- [ ] Internal TestFlight testing successful
- [ ] External TestFlight testing (minimum 24 hours)
- [ ] Submit for App Store review
- [ ] App Store review approved
- [ ] Release with phased rollout enabled

#### Desktop
- [ ] Upload MSIX to Microsoft Store
- [ ] Upload DMG distribution
- [ ] Upload Linux packages (AppImage, deb, rpm)
- [ ] Update website download links

#### PWA
- [ ] Deploy to production (Vercel)
- [ ] Verify CDN cache purged
- [ ] Test PWA functionality post-deploy

#### SDK
- [ ] Publish TypeScript SDK to npm
- [ ] Publish Dart SDK to pub.dev
- [ ] Publish Kotlin SDK to Maven Central / GitHub Packages
- [ ] Publish Python SDK to PyPI

### Post-Deployment
- [ ] Monitor error rates and crash reports (first 24 hours)
- [ ] Verify Sentry issue ingestion
- [ ] Monitor API response times
- [ ] Check server resource utilisation
- [ ] Verify database connection pool health
- [ ] Confirm feature flags are properly enabled/disabled

### Communication
- [ ] Internal release announcement sent
- [ ] Customer-facing release notes published
- [ ] Help centre articles updated
- [ ] Social media announcement prepared
- [ ] Key stakeholders notified

## Rollback Plan

### If critical issues are found post-release:

1. **Immediate**: Revert backend to previous version via Docker Compose:
   ```bash
   docker compose down && docker compose up -d
   ```
   Or use the blue-green deployment workflow:
   ```bash
   gh workflow run blue-green-deploy.yml -f action=rollback
   ```

2. **Android**: Halt staged rollout in Google Play Console and unpublish version.

3. **iOS**: Reject release in App Store Connect and re-submit with fix.

4. **Desktop**: Replace download links with previous version.

5. **Communication**: Notify users via in-app notification, email, and status page.

### Quick Rollback Commands
```bash
# Backend rollback
git revert HEAD --no-edit && git push

# Database rollback
cd backend && alembic downgrade -1

# Full stack restart
make restart
```

## Emergency Contact
- **DevOps**: +964-XXX-XXXXXXX
- **On-Call Engineer**: Via PagerDuty
- **Security Incident**: security@gulaplatform.com
