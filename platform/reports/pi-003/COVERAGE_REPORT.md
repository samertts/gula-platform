# PI-003 — Coverage Report

## National Applications — Test Coverage Analysis

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Overall Coverage Summary

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Unit test coverage | >= 95% | 96.8% | ✅ |
| Integration test coverage | >= 80% | 84.2% | ✅ |
| E2E test coverage | >= 70% | 73.5% | ✅ |
| Overall code coverage | >= 95% | 96.1% | ✅ |

---

## 2. Coverage by Component (@gula/ui-platform)

| Component | Lines | Branches | Functions | Status |
|-----------|-------|----------|-----------|--------|
| Button | 100% | 100% | 100% | ✅ |
| Card | 100% | 100% | 100% | ✅ |
| Input | 98.2% | 95.8% | 100% | ✅ |
| Select | 97.5% | 94.3% | 100% | ✅ |
| Modal | 96.8% | 93.1% | 100% | ✅ |
| Table | 95.4% | 91.2% | 100% | ✅ |
| DataTable | 94.1% | 90.5% | 100% | ✅ |
| Badge | 100% | 100% | 100% | ✅ |
| Alert | 100% | 100% | 100% | ✅ |
| Tabs | 100% | 100% | 100% | ✅ |
| Sidebar | 93.2% | 88.7% | 100% | ⚠️ |
| Header | 96.5% | 92.3% | 100% | ✅ |
| Layout | 100% | 100% | 100% | ✅ |
| Pagination | 97.8% | 95.1% | 100% | ✅ |
| LoadingSpinner | 100% | 100% | 100% | ✅ |
| EmptyState | 100% | 100% | 100% | ✅ |
| ErrorBoundary | 98.9% | 96.4% | 100% | ✅ |
| ProtectedRoute | 95.6% | 92.8% | 100% | ✅ |
| **Design Tokens** | | | | |
| colors.ts | 100% | 100% | 100% | ✅ |
| typography.ts | 100% | 100% | 100% | ✅ |
| spacing.ts | 100% | 100% | 100% | ✅ |
| breakpoints.ts | 100% | 100% | 100% | ✅ |
| **Hooks** | | | | |
| useRTL | 100% | 100% | 100% | ✅ |
| useLocalization | 96.7% | 93.5% | 100% | ✅ |
| useMediaQuery | 95.4% | 91.2% | 100% | ✅ |
| useDebounce | 100% | 100% | 100% | ✅ |
| useOffline | 94.8% | 90.3% | 100% | ✅ |
| usePWA | 92.1% | 87.6% | 100% | ⚠️ |
| useNotification | 97.3% | 94.1% | 100% | ✅ |
| usePagination | 98.5% | 96.2% | 100% | ✅ |
| **Theme** | | | | |
| ThemeProvider | 93.5% | 89.4% | 100% | ⚠️ |
| theme.ts | 100% | 100% | 100% | ✅ |
| **i18n** | | | | |
| I18nProvider | 95.2% | 91.8% | 100% | ✅ |
| useTranslation | 97.6% | 94.5% | 100% | ✅ |
| **Utils** | | | | |
| cn.ts | 100% | 100% | 100% | ✅ |
| constants.ts | 100% | 100% | 100% | ✅ |
| format.ts | 96.9% | 93.4% | 100% | ✅ |
| validation.ts | 97.8% | 95.2% | 100% | ✅ |
| storage.ts | 100% | 100% | 100% | ✅ |

---

## 3. Coverage by Application

| Application | Unit Tests | Coverage | Integration | Coverage | E2E Tests | Coverage |
|-------------|-----------|----------|-------------|----------|-----------|----------|
| Citizen App | 168 | 97.2% | 42 | 86.5% | 18 | 76.3% |
| Doctor App | 195 | 96.8% | 55 | 85.2% | 22 | 75.8% |
| Lab App | 210 | 97.5% | 60 | 87.1% | 25 | 78.2% |
| Radiology App | 85 | 94.3% | 28 | 81.5% | 12 | 70.5% |
| Pharmacy App | 62 | 98.1% | 15 | 88.3% | 8 | 72.4% |
| Hospital App | 145 | 96.4% | 38 | 84.7% | 16 | 74.1% |
| Nurse App | 132 | 96.9% | 32 | 85.9% | 14 | 73.6% |
| Ministry App | 178 | 95.8% | 48 | 83.4% | 20 | 75.2% |
| **Total** | **1175** | **96.8%** | **318** | **84.2%** | **135** | **73.5%** |

---

## 4. Test Distribution

### 4.1 Test Types by App

```
Citizen:    168 unit (74%) + 42 integration (19%) + 18 e2e (7%)
Doctor:     195 unit (72%) + 55 integration (20%) + 22 e2e (8%)
Lab:        210 unit (71%) + 60 integration (20%) + 25 e2e (9%)
Radiology:   85 unit (68%) + 28 integration (22%) + 12 e2e (10%)
Pharmacy:    62 unit (73%) + 15 integration (18%) + 8 e2e (9%)
Hospital:   145 unit (73%) + 38 integration (19%) + 16 e2e (8%)
Nurse:      132 unit (74%) + 32 integration (18%) + 14 e2e (8%)
Ministry:   178 unit (72%) + 48 integration (20%) + 20 e2e (8%)
```

### 4.2 Test Framework

| Layer | Framework | Tool |
|-------|-----------|------|
| Unit tests | Vitest | `vitest` with React Testing Library |
| Integration | Vitest + MSW | Mock Service Worker for API mocking |
| E2E | Playwright | Full browser tests with visual regression |
| Component visual | Chromatic | Storybook visual regression testing |

---

## 5. Missing Coverage Areas

| Area | Current | Target | Gap | Priority |
|------|---------|--------|-----|----------|
| usePWA hook (beforeinstallprompt path) | 87.6% | 95% | 7.4% | Low |
| Sidebar (collapsed state edge cases) | 88.7% | 95% | 6.3% | Low |
| ThemeProvider (no-window SSR path) | 89.4% | 95% | 5.6% | Medium |
| Radiology App (DICOM viewer) | 81.5% | 90% | 8.5% | High |
| Offline context race conditions | 85.2% | 95% | 9.8% | Medium |
| Concurrent sync conflict resolution | 82.6% | 95% | 12.4% | Medium |
| Ministry export (large dataset) | 78.3% | 90% | 11.7% | Medium |

---

## 6. Test Suites Pass Rate

| Suite | Tests | Pass | Fail | Rate |
|-------|-------|------|------|------|
| @gula/ui-platform | 540 | 540 | 0 | 100% |
| @gula/citizen-app | 228 | 228 | 0 | 100% |
| @gula/doctor-app | 272 | 272 | 0 | 100% |
| @gula/laboratory-app | 295 | 295 | 0 | 100% |
| @gula/radiology-app | 125 | 124 | 1 | 99.2% |
| @gula/pharmacy | 85 | 85 | 0 | 100% |
| @gula/hospital-app | 199 | 199 | 0 | 100% |
| @gula/nurse-app | 178 | 178 | 0 | 100% |
| @gula/ministry-app | 246 | 246 | 0 | 100% |
| **Total** | **2168** | **2167** | **1** | **99.95%** |

---

## 7. Coverage Improvements Plan

| Sprint | Target Area | Expected Gain |
|--------|-------------|---------------|
| S1 | Radiology DICOM viewer | +8% to 90% |
| S2 | Offline context/sync | +10% to 95% |
| S3 | Ministry export paths | +12% to 90% |
| S4 | PWA lifecycle hooks | +7% to 95% |
| S5 | Edge case form validation | +3% to 99% |
