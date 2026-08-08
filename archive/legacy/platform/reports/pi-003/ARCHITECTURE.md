# PI-003 — Application Architecture Report

## National Applications Platform — Architecture Overview

**Version:** 2.1.0
**Date:** July 2026
**Platform:** @gula/national-applications

---

## 1. Architecture Philosophy

The GULA National Applications Platform follows a **micro-frontend architecture** built on a shared UI platform (`@gula/ui-platform`). Each application is an independently deployable SPA (Single Page Application) that consumes the same design system, hooks, utilities, and i18n infrastructure. All apps communicate with the GULA backend monolith (FastAPI) via RESTful API endpoints, with offline-first capabilities provided by IndexedDB (via `idb`) and Workbox service workers.

---

## 2. Component Architecture

### 2.1 Shared UI Platform (`@gula/ui-platform`)

```
@gula/ui-platform v1.0.0
├── design-system/
│   └── tokens/
│       ├── colors.ts        # Full semantic color palette (light + dark)
│       ├── typography.ts    # Arabic/English font stacks + type scale
│       ├── spacing.ts       # Spacing, border-radius, shadows
│       └── breakpoints.ts   # Responsive breakpoints (xs-2xl)
├── theme/
│   ├── theme.ts             # createTheme(), applyThemeToDocument()
│   ├── ThemeProvider.tsx     # React context provider with CSS variable injection
│   └── useTheme.ts          # Theme consumption hook
├── components/
│   ├── Button/              # 5 variants × 5 sizes, RTL-aware icon positioning
│   ├── Card/                # CardHeader, CardBody, CardFooter
│   ├── Input/               # With validation, RTL support
│   ├── Select/              # Multi-language select with search
│   ├── Modal/               # Accessible modal (focus trap, ESC close)
│   ├── Table/               # Sortable, filterable, paginated
│   ├── DataTable/           # Advanced: column visibility, export, actions
│   ├── Badge/               # Status badges with color mapping
│   ├── Alert/               # 4 variants: success, warning, danger, info
│   ├── Tabs/                # Accessible tab panel
│   ├── Sidebar/             # Collapsible, multi-level navigation
│   ├── Header/              # Breadcrumbs + actions
│   ├── Layout/              # Layout + LayoutSplit
│   ├── SearchInput/         # Debounced search with keyboard nav
│   ├── Pagination/          # Page selector with item count
│   ├── StatusIndicator/     # Online/offline/busy/away
│   ├── LoadingSpinner/      # 3 sizes + LoadingOverlay
│   ├── EmptyState/          # Illustration + action CTA
│   ├── ErrorBoundary/       # Crash recovery with retry
│   └── ProtectedRoute/      # Auth guard with role-based redirect
├── hooks/
│   ├── useRTL.ts            # Direction detection + RTL utilities
│   ├── useLocalization.ts   # Locale detection (ar/en/ku/tr/sy)
│   ├── useMediaQuery.ts     # Responsive breakpoint hooks
│   ├── useDebounce.ts       # Input debouncing
│   ├── useOffline.ts        # Network status tracking
│   ├── usePWA.ts            # BeforeInstallPrompt, PWA lifecycle
│   ├── useNotification.ts   # Toast notification management
│   └── usePagination.ts     # Client-side pagination state
├── i18n/
│   ├── i18n.ts              # Locale switching + pluralization
│   ├── I18nProvider.tsx      # Context provider
│   ├── useTranslation.ts    # Translation hook with template interpolation
│   └── locales/
│       ├── ar.json           # 149 Arabic keys
│       └── en.json           # 149 English keys
├── icons/                   # SVG icon library (60+ icons)
└── utils/
    ├── cn.ts                # Tailwind class merging
    ├── constants.ts         # APP_NAME, ROLES, STATUSES, ROUTES, LANGUAGES
    ├── format.ts            # Date, number, phone, ID formatting
    ├── validation.ts        # Iraqi national ID, phone, email, password validation
    └── storage.ts           # localStorage wrapper with type safety
```

### 2.2 Application Layer (7 Apps + 1 Update Platform)

Each application follows a consistent internal structure:

```
app/
├── App.tsx                  # Root component with routing, providers
├── main.tsx                 # Vite entry point, register SW
├── pages/                   # Page-level components (1 file per route)
├── components/              # Domain-specific components
├── contexts/                # AuthContext, OfflineContext, domain contexts
├── hooks/                   # Domain-specific hooks
├── services/                # API client, sync, offline, auth services
└── utils/                   # Constants, routes, validation
```

---

## 3. Application-Specific Architecture

### 3.1 Citizen App (@gula/citizen-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Android/iOS/PWA, mobile-first |
| **Frameworks** | React 19, react-router-dom v7, Firebase v11 |
| **PWA** | Full offline support, background sync, install prompt |
| **QR** | html5-qrcode for health ID scanning |
| **Storage** | idb (IndexedDB) for offline wallets, health records |
| **Auth** | Firebase Auth + OTP + biometric (platform) |
| **Key Pages** | Home, HealthID, Appointments, LabResults, Prescriptions, EmergencyCard, FamilyAccounts, Telemedicine, ConsentManagement, OfflineWallet, HealthAssistant |

**Citizen Data Flow:**
```
Citizen Device
    ├── Online: API → gula-backend → PostgreSQL
    ├── Offline: IndexedDB (idb) → Sync on reconnect
    ├── QR: html5-qrcode → Scan doctor/lab QR → Decode token → View health ID
    └── Notifications: Firebase Cloud Messaging → Push alerts
```

### 3.2 Doctor App (@gula/doctor-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop/Web/Tablet/Mobile (responsive) |
| **Frameworks** | React 19, recharts v2, react-router-dom v7 |
| **PWA** | Offline clinical records, background sync for orders |
| **Key Features** | Decision support, digital signature, voice dictation, FHIR search |
| **Charts** | recharts for vitals, lab trends, epidemiology |
| **Offline** | Clinical notes, patient summaries cached via idb |

**Doctor Data Flow:**
```
Doctor Device
    ├── Dashboard: Aggregated patient counts, alerts, schedule
    ├── PatientSearch: FHIR-compliant search across MPI
    ├── Orders: Create lab/radiology orders → API → Outbox pattern
    ├── Prescriptions: e-Prescription with digital signature
    ├── DecisionSupport: Clinical pathways, drug interaction alerts
    └── Telemedicine: WebRTC video calls (future)
```

### 3.3 Laboratory App (@gula/laboratory-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop (primary), Tablet (mobile) |
| **Frameworks** | React 19, recharts v2, html5-qrcode |
| **PWA** | Critical path: sample registration, result entry, QC |
| **Instrument Integration** | Via device-bridge (ASTM/HL7) → gula-backend |
| **Workflow** | Sample Registration → Worklist → Result Entry → Review → Validation → Publish |

**Laboratory Workflow Architecture:**
```
Device (Sysmex/Roche/Mindray)
    ↓ ASTM/HL7
device-bridge service
    ↓ REST
gula-backend → samples API
    ↓
Lab App Worklist (real-time via polling + SW)
    ↓
Technician enters/validates results
    ↓
Reviewer approves
    ↓
Publish to patient portal
```

### 3.4 Radiology App (@gula/radiology-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop (high-res, multi-monitor) |
| **Frameworks** | React 18, @cornerstonejs, dicom-parser, dicomweb-client |
| **DICOM** | Full DICOM viewer with Cornerstone.js |
| **Calendar** | react-big-calendar for scheduling |
| **Dates** | date-fns + date-fns-jalali (Hijri calendar support) |

### 3.5 Pharmacy App (@gula/pharmacy)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop |
| **Frameworks** | React 18, react-router-dom v6 |
| **QR** | html5-qrcode for prescription scanning |
| **Key Functions** | Prescription fulfillment, inventory, drug interaction check |

### 3.6 Hospital Admin App (@gula/hospital-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop |
| **Frameworks** | React 19, recharts v2 |
| **PWA** | Offline-capable admin dashboards |
| **Key Features** | Bed management, staff scheduling, resource allocation, department analytics |

### 3.7 Nurse App (@gula/nurse-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Tablet/Mobile |
| **Frameworks** | React 19, recharts v2, html5-qrcode |
| **PWA** | Full offline for patient rounds, medication admin |
| **Key Features** | Patient rounds, medication administration, vital signs entry, task management |

### 3.8 Ministry Dashboard (@gula/ministry-app)

| Aspect | Detail |
|--------|--------|
| **Target** | Desktop (large screens, multi-monitor) |
| **Frameworks** | React 19, recharts v2, lucide-react, date-fns, papaparse, jspdf, html2canvas |
| **Key Features** | National epidemiology dashboard, facility management, report generation, data export |

### 3.9 Update Platform (@gula/update-platform)

```
@gula/update-platform v2.1.0
├── core/
│   ├── UpdateManager.ts      # Orchestrates full update lifecycle
│   ├── UpdateScheduler.ts    # Scheduled/periodic check for updates
│   ├── UpdateValidator.ts    # Package integrity verification
│   └── VersionManager.ts     # Semantic version comparison + channel management
├── platform/
│   ├── ReleaseManager.ts     # Release manifest, rollout percentages, phased deployment
│   ├── FeatureFlagManager.ts # Remote feature flag toggling
│   └── PackageSigner.ts      # Cryptographic signing + verification
├── channels/
│   └── DesktopAutoUpdater.ts # Electron/Tauri desktop auto-update channel
├── react/
│   └── components/           # Update notification UI components
└── types.ts                  # Shared type definitions
```

---

## 4. Offline Architecture

All applications implement a three-tier offline strategy:

```
Tier 1 — Static Assets (Service Worker)
    ├── App shell (HTML/CSS/JS) cached on install
    ├── Fonts (StaleWhileRevalidate, 1 year)
    └── Images (CacheFirst, 30 days)

Tier 2 — API Data (NetworkFirst + Background Sync)
    ├── Clinical data cached with NetworkFirst (7 day expiry)
    ├── Write operations queued via BackgroundSync
    └── Conflict resolution on reconnect (last-write-wins with version check)

Tier 3 — Local Database (IndexedDB via idb)
    ├── Patient summaries
    ├── Offline wallet (citizen)
    ├── Clinical notes (doctor)
    ├── Worklist (lab)
    ├── Medication schedule (nurse)
    └── Sync status tracking
```

### PWA Registration Flow

```
User visits app
    ↓
VitePWA plugin generates service worker at build time
    ↓
main.tsx registers SW with autoUpdate
    ↓
SW install event → precache app shell + static assets
    ↓
SW activate event → claim clients, clean old caches
    ↓
Runtime: SW intercepts fetch requests
    ├── API calls → NetworkFirst with background sync queue
    ├── Static assets → CacheFirst
    └── Fonts/images → StaleWhileRevalidate
    ↓
User goes offline → SW serves cached responses
    ↓
User reconnects → BackgroundSync replays queued mutations
```

---

## 5. RTL / i18n Architecture

```
Request/Response
    ↓
I18nProvider (detects locale from:
    1. URL query (?lang=ar)
    2. localStorage (gula-locale)
    3. Browser navigator.language
    4. Default 'ar')
    ↓
useTranslation() hook provides:
    ├── t(key, vars?) → translated string with variable interpolation
    ├── tpl(key, vars?) → template with HTML-safe interpolation
    └── getDirection() → 'rtl' | 'ltr'
    ↓
ThemeProvider consumes locale direction:
    ├── Sets dir="rtl" on root
    ├── Flips icon positions (Button, Sidebar, etc.)
    └── Applies Arabic font family (Tajawal/Cairo)
    ↓
Supported locales: ar (Arabic), en (English), ku (Kurdish), tr (Turkish), sy (Syriac)
```

---

## 6. State Management Architecture

```
┌──────────────────────────────────────────────────┐
│                   React Contexts                   │
│  ┌──────────┐  ┌──────────┐  ┌────────────────┐   │
│  │  Auth    │  │  Theme   │  │  I18n          │   │
│  │  Context │  │  Context │  │  Context       │   │
│  └────┬─────┘  └────┬─────┘  └───────┬────────┘   │
│       │             │                │            │
│  ┌────▼─────────────▼────────────────▼────────┐   │
│  │         App-Specific Contexts              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │Clinical  │ │ Patient  │ │ Offline  │   │   │
│  │  │Context   │ │ Context  │ │ Context  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────┘   │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │         Service Layer (stateless)            │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐  │   │
│  │  │ API   │ │ Auth  │ │ Sync  │ │ Offline│  │  │
│  │  │ Client│ │ Service│ │ Service│ │ Service│  │  │
│  │  └────────┘ └────────┘ └────────┘ └──────┘  │   │
│  └──────────────────────────────────────────────┘  │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │         Persistent Storage                   │  │
│  │  ┌──────────────┐  ┌──────────────────────┐ │  │
│  │  │  IndexedDB   │  │  localStorage         │ │  │
│  │  │  (idb)       │  │  (preferences, token) │ │  │
│  │  └──────────────┘  └──────────────────────┘ │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## 7. Service Layer Design

Each app's `services/` directory contains:

| Service | Responsibility |
|---------|---------------|
| `api.ts` | Axios/fetch wrapper with JWT refresh, error normalization, request/response interceptors |
| `auth.ts` | Login/register/logout, token management, MFA/OTP verification, biometric registration |
| `offline.ts` | Network status monitoring, queue management, conflict resolution, sync triggers |
| `sync.ts` | Data synchronization between IndexedDB and server, conflict detection |
| `notifications.ts` | Push notification registration, FCM token management, notification routing |

Specialized services per app:
- **Citizen:** `healthData.ts`, `family.ts`, `payments.ts`
- **Doctor:** `clinical.ts`, `decisionSupport.ts`, `digitalSignature.ts`, `orders.ts`, `prescriptions.ts`, `voiceDictation.ts`, `patient.ts`
- **Laboratory:** `samples.ts`, `results.ts`, `qualityControl.ts`, `instruments.ts`, `inventory.ts`
- **Radiology:** `dicom.ts`, `imaging.ts`, `reporting.ts`
- **Pharmacy:** `prescriptions.ts`, `inventory.ts`, `drugInteraction.ts`
- **Hospital:** `beds.ts`, `staff.ts`, `departments.ts`, `resources.ts`
- **Nurse:** `rounds.ts`, `medication.ts`, `vitals.ts`, `tasks.ts`
- **Ministry:** `epidemiology.ts`, `facilities.ts`, `reports.ts`, `exports.ts`

---

## 8. Network Topology

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  Client  │───▶│   API Gateway│───▶│  gula-backend│
│  Apps    │    │  (nginx)     │    │  (FastAPI)   │
└──────────┘    └──────────────┘    └──────┬───────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
            ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
            │  PostgreSQL  │      │    Redis 7    │      │  RabbitMQ    │
            │    16 HA     │      │  (Cache/Sess) │      │  (Async)     │
            └──────────────┘      └──────────────┘      └──────────────┘
```

---

## 9. Build & Deployment Architecture

```
Monorepo (pnpm workspace)
    │
    ├── @gula/ui-platform (shared library, built with tsc)
    │
    ├── @gula/citizen-app    │
    ├── @gula/doctor-app     │
    ├── @gula/laboratory-app │── Each built with: tsc -b && vite build
    ├── @gula/radiology-app  │   Output: dist/ (static S3/CloudFront)
    ├── @gula/pharmacy       │
    ├── @gula/hospital-app   │
    ├── @gula/nurse-app      │
    ├── @gula/ministry-app   │
    │
    └── @gula/update-platform (npm package, built with tsc)
        Output: dist/ (published to npm registry/GHCR)
```

All apps produce fully static builds (HTML + JS + CSS + assets) deployable to any CDN or static hosting.
