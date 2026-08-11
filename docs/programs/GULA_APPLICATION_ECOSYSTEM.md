# GULA — Application Ecosystem

**Document class:** AUTHORITATIVE inventory of every application / client surface
**Date:** 2026-08-11
**Basis:** Verified at HEAD `f735a7a1` (GULA_CURRENT_REPOSITORY_STATE.md §3).

---

## 1. Ecosystem Map

```
┌──────────────────────────── GULA PLATFORM ─────────────────────────────┐
│                                                                       │
│  WEB (frontend-v3) — ACTIVE, production-grade surface                 │
│  Android (mobile/android) — REAL, buildable                           │
│  iOS (mobile/ios) — BROKEN (no build system)                          │
│  Desktop (mobile/desktop) — PARTIAL (drift gen missing)               │
│  Store metadata (mobile/store + fastlane) — REAL                      │
│  Experimental root app (server + client) — EXPERIMENTAL (Node/express/│
│     tRPC/React) — root Dockerfile targets it                          │
│                                                                       │
│  All clients → ONE GULA CORE (backend) → PostgreSQL / Redis / MinIO   │
└───────────────────────────────────────────────────────────────────────┘
```

## 2. Per-Surface Detail

### 2.1 Web — `frontend-v3/` (ACTIVE)

| Property | Value |
|---|---|
| Stack | React 19.2, react-router 8.3, Vite 8, TanStack Query 5, Tailwind |
| i18n | ar/en, RTL (dir="rtl" in index.html) |
| PWA | Service worker + offline shell |
| Pages | 45+ page areas (auth, MFA, workspaces, labs, results, admin, AI, settings) |
| Auth | Real API auth + MFA flow; tokens in storage |
| Authorization | **Client-side only (S4)** — must remain presentation-only |
| Tests | 122 vitest (9 files) + 8 e2e (Playwright) |
| Legal pages | **MISSING** (privacy/terms/consent) — P0 |
| Build | tsc --noEmit 0 errors; vite build ~5 s |

**Verdict:** REAL. The primary production surface. Gap: legal pages (P0),
a11y (P2), component consolidation (P2), offline IndexedDB (P2), test expansion (P2).

### 2.2 Android — `mobile/android/` (REAL)

| Property | Value |
|---|---|
| App | Single `:app`, package `io.gula.android` |
| Stack | Kotlin 2.1.20, AGP 8.13.2, Compose, Hilt, Room, Retrofit |
| minSdk / target | 26 / 35 |
| Security | Encrypted prefs, cert pinning |
| Offline | Room + sync queue |
| Signing | env-driven (secrets) |

**Verdict:** REAL and buildable. Gap: signing/Play CI secret hygiene (P1), test expansion.

### 2.3 iOS — `mobile/ios/` (BROKEN)

| Property | Value |
|---|---|
| Scaffold | SwiftUI + Core Data sources (107 tracked .swift) |
| Build system | `Gula.xcodeproj/` is EMPTY — no `project.pbxproj`, no workspace, no scheme |
| Core Data model | **MISSING** |
| CI | `mobile-ios.yml` references `Gula.xcworkspace` in 6 steps (does not exist) → cannot build |

**Verdict:** BROKEN. Store metadata + fastlane exist but nothing buildable ships.
**Action (P0):** regenerate the Xcode project + Core Data model, or formally defer
iOS with an explicit decision. CI job (S9) must be fixed or gated.

### 2.4 Desktop — `mobile/desktop/` (PARTIAL, Flutter 2.1.0)

| Property | Value |
|---|---|
| Stack | Flutter 2.1.0, drift, riverpod |
| Feature surface | Real (LIMS-oriented) |
| DB layer | `database.g.dart` is a placeholder → drift generated code missing → DB/offline path cannot compile |
| Device discovery | Lab device discovery is a stub (returns empty) |

**Verdict:** PARTIAL. Decision required (P1): **FIX** (regenerate drift code +
implement discovery) or **ARCHIVE** (document and archive until justified).

### 2.5 Store metadata — `mobile/store/` + `fastlane` (REAL)

- App Store + Google Play listing metadata, terms/privacy docs.
- fastlane team IDs are placeholders; secrets env-driven.
- **Gap:** no web legal pages behind these listings (P0). Fastlane placeholders
  must be filled before store production release.

### 2.6 Root experimental app — `server/` + `client/` (EXPERIMENTAL)

- Node 24, express 5, tRPC 11, React 19.
- `dist/` gitignored.
- **Risk:** root Dockerfile targets it, creating ambiguity with `frontend-v3`
  for anyone reading deployment files.
- **Action:** document the experimental status explicitly in the root README and
  Dockerfile, or retire/archive if superseded by frontend-v3. (P2)

---

## 3. Shared Client Concerns

| Concern | Status |
|---|---|
| One canonical API base domain | **BROKEN** — 3 divergent domains across clients → unify (P1) |
| Token refresh | Android + Web implemented; align expiry/rotation |
| Offline semantics | Not unified; Android Room real, Web SW-only, Desktop broken |
| Secure storage | Android encrypted prefs; Web localStorage (tokens); iOS missing (Keychain once rebuilt) |
| Crash/error reporting | Sentry wired in Web build (source maps) |

---

## 4. Decisions Required (from ecosystem)

| ID | Decision | Priority |
|---|---|---|
| D-1 | iOS: rebuild now vs formal defer | P0 |
| D-2 | Desktop: fix drift gen + discovery vs archive | P1 |
| D-3 | Unify API base domain across Web/Android/iOS/Desktop | P1 |
| D-4 | Root experimental app: keep + document vs archive | P2 |
| D-5 | Web legal pages before any production store linkage | P0 |
| D-6 | Fastlane placeholders → real values gated on store launch | P1 |

---

*Companion documents: `GULA_MASTER_GAP_MATRIX.md` (B/F/M rows),
`GULA_MASTER_EXECUTION_PLAN.md` (sequencing), `GULA_RISK_REGISTER.md` (R-01/R-08).*
