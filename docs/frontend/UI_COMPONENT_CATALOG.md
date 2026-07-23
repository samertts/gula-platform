# GULA Platform — UI Component Catalog

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

1. [Frontend Applications Overview](#1-frontend-applications-overview)
2. [Reusable Components (frontend-v2)](#2-reusable-components-frontend-v2)
3. [Layouts](#3-layouts)
4. [Forms](#4-forms)
5. [Tables and Lists](#5-tables-and-lists)
6. [Charts and Visualizations](#6-charts-and-visualizations)
7. [Dialogs and Modals](#7-dialogs-and-modals)
8. [Custom Hooks](#8-custom-hooks)
9. [Styling and RTL Support](#9-styling-and-rtl-support)
10. [Component Status](#10-component-status)
11. [Design Token References](#11-design-token-references)
12. [Accessibility Score](#12-accessibility-score)
13. [Dark Mode Support](#13-dark-mode-support)
14. [Component Dependency Graph](#14-component-dependency-graph)
15. [Reusability Score](#15-reusability-score)
16. [Screens Using Each Component](#16-screens-using-each-component)
17. [Performance Notes](#17-performance-notes)
18. [Storybook Status](#18-storybook-status)
19. [Related Documents](#19-related-documents)

## 1. Frontend Applications Overview

The platform has four frontend applications:

| Application | Stack | Purpose | Location |
|-------------|-------|---------|----------|
| frontend-v2 | React 19 + TypeScript + Vite | Rich SPA (citizen, doctor, lab, ministry portals) | `frontend-v2/` |
| frontend | Static HTML/CSS/JS | Lightweight PWA (offline-capable, service worker) | `frontend/` |
| client | React + TypeScript | Lightweight SPA connected to backend (single dashboard) | `client/` |
| frontend-v3 | React 19 + TypeScript + TanStack Query | Emerging feature-rich frontend | `frontend-v3/` |

### Dependency Comparison

| Feature | frontend-v2 | frontend-v3 | client |
|---------|-------------|-------------|--------|
| Routing | react-router-dom v7 | react-router-dom v7 | — |
| HTTP Client | fetch-based (`api/client.ts`) | axios | — |
| State/Server Data | — | @tanstack/react-query, @tanstack/react-table | — |
| Icons | lucide-react | lucide-react | — |
| Animation | motion (framer-motion) | — | — |
| CSS | Tailwind CSS v4 | Tailwind CSS v4 | — |
| i18n | Custom translations (`translations.ts`) | i18next + react-i18next | — |
| Charts | recharts | — | — |
| AI | @google/generative-ai, @google/genai | — | — |
| Toasts | sonner | Custom `ToastContainer` | — |
| QR/Barcode | html5-qrcode, react-barcode | — | — |

## 2. Reusable Components (frontend-v2)

### Common UI Components (`frontend-v2/src/components/ui/`)

| Component | File | Status | Description |
|-----------|------|--------|-------------|
| `Button` | `Button.tsx` | Production-ready | 6 variants (primary, secondary, ghost, danger, premium, outline), 4 sizes (sm, md, lg, icon), loading state |
| `Badge` | `Badge.tsx` | Production-ready | Status/category badge |
| `Avatar` | `Avatar.tsx` | Production-ready | User avatar with fallback |
| `Tooltip` | `Tooltip.tsx` | Production-ready | Hover tooltip |
| `Kbd` | `Kbd.tsx` | Production-ready | Keyboard shortcut display |
| `Skeleton` | `Skeleton.tsx` | Production-ready | Loading skeletons: `DashboardSkeleton`, `StatGridSkeleton`, `TableSkeleton`, `ListSkeleton`, `CardSkeleton` |
| `EmptyState` | `EmptyState.tsx` | Production-ready | Empty state with icon, description, CTA actions; 3 sizes (sm, md, lg) |
| `ErrorBoundary` | `ErrorBoundary.tsx` | Production-ready | Route-level error boundary (`RouteErrorBoundary`) |
| `ContextualMenu` | `ContextualMenu.tsx` | Production-ready | Context/right-click menu |
| `QuickActions` | `QuickActions.tsx` | Beta | Floating quick action panel |

### Form Components (`frontend-v2/src/components/auth/`)

| Component | File | Description |
|-----------|------|-------------|
| `OTPInput` | `OTPInput.tsx` | One-time password input for phone verification |
| `PasswordStrength` | `PasswordStrength.tsx` | Password strength indicator |

### Cross-Cutting Components (`frontend-v2/src/components/`)

| Component | File | Description |
|-----------|------|-------------|
| `PermissionGuard` | `PermissionGuard.tsx` | RBAC gate — wraps children, checks resource/action/scope; renders lock fallback if denied |
| `Sidebar` | `Sidebar.tsx` | Adaptive navigation sidebar with role-based wings, favorites, pinned items, search |
| `TopBar` | `TopBar.tsx` | Top bar with search, notifications, quick-create, language switcher (EN/AR/KU/TR/SY), profile |
| `Breadcrumbs` | `Breadcrumbs.tsx` | Route-based breadcrumb navigation |
| `ScrollToTop` | `ScrollToTop.tsx` | Scroll-to-top on route change |
| `PageTransition` | `PageTransition.tsx` | Animated page transition wrapper (motion) |
| `CommandPalette` | `CommandPalette.tsx` | Cmd+K command palette (cmdk) |
| `HelpAssistant` | `HelpAssistant.tsx` | Contextual help assistant panel |
| `GlobalAiAssistant` | `GlobalAiAssistant.tsx` | Global AI assistant panel |
| `ShortcutsModal` | `ShortcutsModal.tsx` | Keyboard shortcuts reference modal |
| `NotificationCenter` | `NotificationCenter.tsx` | Notification dropdown with mark-read |
| `ClickToCopy` | `ClickToCopy.tsx` | Click-to-copy utility |
| `OfflineSyncManager` | `OfflineSyncManager.tsx` | Offline sync status and queue management |
| `SystemDiagnosticsDrawer` | `SystemDiagnosticsDrawer.tsx` | System health diagnostics drawer |
| `TaskQueue` | `TaskQueue.tsx` | Background task queue monitor |
| `LabDeviceMonitor` | `LabDeviceMonitor.tsx` | Real-time lab device monitoring |
| `LabStatsTrends` | `LabStatsTrends.tsx` | Lab statistics and trends |
| `DashboardInsight` | `DashboardInsight.tsx` | Dashboard insight cards |
| `HealthTrendChart` | `HealthTrendChart.tsx` | Health trend visualization |
| `SmartAlertSystem` | `SmartAlertSystem.tsx` | Decision intelligence alert queue (critical/warning/info) |
| `AISummary` | `AISummary.tsx` | AI-powered test results explanation with follow-up Q&A (Markdown, suggested questions) |
| `ExplainableAI` | `ExplainableAI.tsx` | Explainable AI diagnostic breakdown |
| `AuditLogViewer` | `AuditLogViewer.tsx` | Audit log entry display with severity filtering |
| `PredictiveAnalytics` | `PredictiveAnalytics.tsx` | Predictive analytics dashboard component |
| `PredictiveOutbreak` | `PredictiveOutbreak.tsx` | Outbreak prediction visualization |
| `NeuralConnectivityHub` | `NeuralConnectivityHub.tsx` | Neural network connectivity visualizer |
| `NeuralSparkline` | `NeuralSparkline.tsx` | Mini sparkline chart for neural metrics |
| `QuantumHealthGrid` | `QuantumHealthGrid.tsx` | Health grid visualization |
| `ImageEditor` | `ImageEditor.tsx` | Image editor (react-easy-crop) |
| `BiometricStatus` | `BiometricStatus.tsx` | Biometric authentication status indicator |
| `DigitalTwinSimulation` | `DigitalTwinSimulation.tsx` | Digital twin simulation viewer |
| `OrganAnalysis` | `OrganAnalysis.tsx` | Organ analysis visualization |
| `MinistryCommandCenter` | `MinistryCommandCenter.tsx` | Ministry-level command center panel |

### Lab Components (`frontend-v2/src/components/lab/`)

| Component | File | Description |
|-----------|------|-------------|
| `ResultEntryUI` | `ResultEntryUI.tsx` | Lab result data entry form |

### Doctor Components (`frontend-v2/src/components/doctor/`)

| Component | File | Description |
|-----------|------|-------------|
| `AdvancedTriageDetails` | `AdvancedTriageDetails.tsx` | Advanced triage details panel |
| `AITriageAssistant` | `AITriageAssistant.tsx` | AI triage assistant |
| `ClinicalNotes` | `ClinicalNotes.tsx` | Clinical notes editor |
| `ClinicalSummaryBento` | `ClinicalSummaryBento.tsx` | Bento-grid clinical summary |
| `DoctorPriorityQueue` | `DoctorPriorityQueue.tsx` | Doctor priority queue |
| `PrescriptionBuilder` | `PrescriptionBuilder.tsx` | Digital prescription builder |

### Citizen Components (`frontend-v2/src/components/citizen/`)

| Component | File | Description |
|-----------|------|-------------|
| `DigitalTwin` | `DigitalTwin.tsx` | Personal health digital twin |
| `FamilySwitcher` | `FamilySwitcher.tsx` | Family member profile switcher |
| `MedicineCabinet` | `MedicineCabinet.tsx` | Personal medicine cabinet |
| `NationalIDCard` | `NationalIDCard.tsx` | Digital national ID card display |
| `SymptomChecker` | `SymptomChecker.tsx` | AI symptom checker |

### Ministry Components (`frontend-v2/src/components/ministry/`)

| Component | File | Description |
|-----------|------|-------------|
| `CrisisResponsePipeline` | `CrisisResponsePipeline.tsx` | National crisis response pipeline |

## 3. Layouts

### frontend-v2 (`frontend-v2/src/`)

| Layout | Implementation | Description |
|--------|---------------|-------------|
| App Shell | `App.tsx` | BrowserRouter, Sidebar + TopBar + AnimatedRoutes, offline banner, providers stack (Auth, Language, Notification, Navigation, Workspace) |
| Sidebar | `components/Sidebar.tsx` | Role-adaptive wings (Doctor, Lab, Citizen, Admin, Ministry, Researcher), favorites/pinned/recent, search, collapsible |
| TopBar | `components/TopBar.tsx` | Search bar, quick actions, notification bell (unread count), language switcher (5 languages), profile dropdown |

### frontend-v3 (`frontend-v3/src/layouts/`)

| Layout | File | Description |
|--------|------|-------------|
| `AuthLayout` | `AuthLayout.tsx` | Authentication page shell |
| `DashboardLayout` | `DashboardLayout.tsx` | Main dashboard layout wrapper |
| `Sidebar` | `Sidebar.tsx` | Navigation sidebar |

### Application Views (frontend-v2, by wing)

**Doctor Wing** (`frontend-v2/src/views/`):
`DashboardView`, `RecordsView`, `PatientProfile`, `AppointmentsView`, `DoctorIntelligence`, `ImagingLabView`

**Lab Wing** (`frontend-v2/src/views/lab/`):
`LabDashboard`, `WorkQueue`, `DeviceManagement`, `DeviceMonitoring`, `InventoryManagement`, `SampleTracking`, `QualityControl`

**Citizen Wing** (`frontend-v2/src/views/citizen/`):
`CitizenDashboard`, `CitizenHealth`, `CitizenAssistant`, `FamilyManagement`, `MedicationCenter`, `SmartResultsView`, `MedicalHistoryView`, `PatientRegistration`, `IdentityVerificationView`, `ConsentManagementView`, `SecurityAuditView`

**Ministry Wing** (`frontend-v2/src/views/ministry/`):
`MinistryDashboard`, `NationalHealthGrid`, `EpidemiologicalIntelligence`, `DataSovereigntyAudit`

**Admin Wing** (`frontend-v2/src/views/admin/`):
`AuditLog`, `InfrastructureView`, `IntegrationHub`, `SystemsArchitectureView`

**Research Wing** (`frontend-v2/src/views/research/`):
`ResearcherDashboard`

### Application Pages (frontend-v3, `frontend-v3/src/pages/`)

27 page directories: `admin`, `ai-platform`, `ai`, `alerts`, `auth`, `compliance`, `dashboard`, `edge`, `ehr`, `fhir`, `financial`, `hospital`, `identity`, `labs`, `national-data`, `notifications`, `orders`, `patient-card`, `patients`, `profile`, `qc`, `results`, `samples`, `security`, `settings`, `stats`, `tiers`

## 4. Forms

| Form | Application | Description |
|------|-------------|-------------|
| Login/Register | frontend-v2 `LandingAuthView` | Authentication with OTP, phone, email/password, biometric |
| Patient Registration | frontend-v2 `PatientRegistration` | Multi-step patient intake with identity verification |
| Identity Verification | frontend-v2 `IdentityVerificationView` | Biometric verification, document upload, OTP |
| Consent Management | frontend-v2 `ConsentManagementView` | Granular consent toggles, time-bound access |
| Result Entry | frontend-v2 `ResultEntryUI` | Lab result entry with validation |
| Prescription Builder | frontend-v2 `PrescriptionBuilder` | Digital prescription form with dosage/frequency |
| Order Creation | frontend-v2 via `api/endpoints/orders.ts` | Lab order creation (including batch) |

## 5. Tables and Lists

### frontend-v3

| Component | File | Technology | Features |
|-----------|------|------------|----------|
| `DataTable` | `components/ui/DataTable.tsx` | @tanstack/react-table | Sorting, column filtering, pagination, Arabic localization, row click |

### frontend-v2

Tables are rendered inline within views. Common patterns include:
- Paginated list endpoints via `api/client.ts` (skip/limit pattern)
- Empty state fallback via `EmptyState` component
- Loading skeleton via `TableSkeleton` / `ListSkeleton`
- `AuditLogViewer` provides a filtered/sorted log entry list with severity badges

## 6. Charts and Visualizations

| Component | Application | Library | Purpose |
|-----------|-------------|---------|---------|
| `HealthTrendChart` | frontend-v2 | recharts | Health metric trend lines |
| `PredictiveAnalytics` | frontend-v2 | recharts | Predictive analytics charts |
| `PredictiveOutbreak` | frontend-v2 | recharts | Outbreak heatmap/propagation |
| `NeuralSparkline` | frontend-v2 | SVG/CSS | Mini sparkline metrics |
| `LabStatsTrends` | frontend-v2 | recharts | Lab statistics trends |
| `DashboardInsight` | frontend-v2 | — | Stat cards with trend indicators |

## 7. Dialogs and Modals

| Component | Application | File | Description |
|-----------|-------------|------|-------------|
| `Modal` | frontend-v3 | `components/ui/Modal.tsx` | Generic modal with sizes (sm/md/lg/xl/full), backdrop blur, Esc-to-close |
| `Dialog` | frontend-v3 | `components/ui/Dialog.tsx` | Alert/confirm dialog with title, description, footer actions |
| `ShortcutsModal` | frontend-v2 | `components/ShortcutsModal.tsx` | Keyboard shortcuts reference |
| `SmartAlertSystem` | frontend-v2 | `components/SmartAlertSystem.tsx` | Alert queue with dismiss |

## 8. Custom Hooks

### frontend-v2 (`frontend-v2/src/hooks/`)

| Hook | File | Description |
|------|------|-------------|
| `usePersonalization` | `hooks/usePersonalization.ts` | Navigation personalization: favorites, pinned, recent, usage tracking, adaptive ordering |

### frontend-v3 (`frontend-v3/src/hooks/`)

| Hook | File | Description |
|------|------|-------------|
| `useApi` | `hooks/useApi.ts` | Generic API fetch hook |
| `useApiError` | `hooks/useApiError.ts` | API error handling |
| `useDebounce` | `hooks/useDebounce.ts` | Debounced value hook |
| `useMediaQuery` | `hooks/useMediaQuery.ts` | Responsive media query |
| `usePermissions` | `hooks/usePermissions.ts` | Permission check hook |
| `useRealtime` | `hooks/useRealtime.ts` | Real-time data subscription |
| `useToast` | `hooks/useToast.ts` | Toast notification hook |

### client (`client/src/_core/hooks/`)

| Hook | File | Description |
|------|------|-------------|
| `useAuth` | `_core/hooks/useAuth.ts` | Authentication hook |

### Contexts (frontend-v2)

| Context | File | Description |
|---------|------|-------------|
| `AuthContext` | `contexts/AuthContext.tsx` | Authentication state, login/logout, token management |
| `LanguageContext` | `contexts/LanguageContext.tsx` | Multi-language (EN/AR/KU/TR/SY), RTL detection, translation map |
| `NotificationContext` | `contexts/NotificationContext.tsx` | Notification polling (30s interval), unread count, mark-read |

### Contexts (frontend-v3)

| Context | File | Description |
|---------|------|-------------|
| `AuthContext` | `contexts/AuthContext.tsx` | Auth state provider |
| `LocaleContext` | `contexts/LocaleContext.tsx` | i18n locale management |
| `ThemeContext` | `contexts/ThemeContext.tsx` | Light/dark theme toggle |

### Stores (frontend-v2)

| Store | File | Type | Description |
|-------|------|------|-------------|
| `navigationStore` | `stores/navigationStore.tsx` | Context | Navigation state (React context-based) |
| `workspaceStore` | `stores/workspaceStore.tsx` | Context | Workspace layout state |

### Lib Utilities (frontend-v2)

| File | Contents |
|------|----------|
| `lib/utils.ts` | `cn()` (tailwind-merge + clsx), `formatDate`, `formatTime`, `getDir` |
| `lib/useOptimistic.ts` | Optimistic update hook |
| `lib/useShortcut.ts` | Keyboard shortcut sequence binding (`useKeySequence`) |
| `lib/offline-engine.ts` | Offline data persistence engine |
| `lib/commandRegistry.ts` | Command palette command registry |
| `lib/telemetry.ts` | PostHog telemetry |
| `lib/aiTelemetry.ts` | AI-specific telemetry |

## 9. Styling and RTL Support

### Design System

Both frontend-v2 and frontend-v3 use **Tailwind CSS v4** with custom theme configuration.

**frontend-v2** (`frontend-v2/src/index.css`):
- Font stack: Outfit (headline), Inter (body), Noto Kufi Arabic (Arabic headline), Noto Naskh Arabic (Arabic body), JetBrains Mono (code)
- Design tokens: Primary (indigo-600), surface colors, error/success/warning containers, custom shadows, border radii
- Custom utility classes: `.glass-panel`, `.card-sleek`, `.card-precise`, `.btn-premium`, `.focus-ring`, `.rtl-aware`
- CSS variables via `@theme` directive

**frontend-v3** (`frontend-v3/src/styles/theme.css`):
- OKLCH color palette with light/dark variants
- CSS custom properties for background, foreground, card, primary, secondary, muted, accent, destructive, border, ring
- Sidebar-specific theme variables
- Chart color scale (5 levels)

### RTL Support

- `LanguageContext` provides `dir` and `isRtl` — set on `<html dir>` attribute
- All layouts use `dir={isRtl ? 'rtl' : 'ltr'}` at root level
- Custom `.rtl-aware` utility flips flex direction in RTL mode
- `[dir="rtl"]` CSS selectors for RTL-specific overrides
- DataTable (frontend-v3) uses Arabic pagination labels
- Animated route transitions with `slideInLeft`/`slideInRight` adapted to RTL
- Translation system with 5 languages: English, Arabic, Kurdish (Kurmanji), Turkish, Syriac

### Accessibility

- `prefers-reduced-motion` media query reduces all animations
- `prefers-contrast: high` enhances border visibility
- Skeleton components use `aria-busy`, `role="status"`, `aria-label`
- Empty state uses `role="status"`
- Focus ring utility on all interactive elements
- Keyboard shortcut system (`?` opens shortcuts modal, `g d` etc. for navigation)

## 10. Component Status

| Tier | Criteria | Components |
|------|----------|------------|
| **Production-ready** | Used in active routes, covered by patterns | Button, Badge, Avatar, Tooltip, Kbd, Skeleton (all variants), EmptyState, PermissionGuard, Sidebar, TopBar, Breadcrumbs, ScrollToTop, ErrorBoundary, NotificationCenter, ClickToCopy, SmartAlertSystem, DataTable (v3), Modal (v3), Dialog (v3), all Card variants, Input, Select, Textarea, Badge (v3) |
| **Beta** | Functional but may need edge-case hardening | CommandPalette, HelpAssistant, GlobalAiAssistant, ShortcutsModal, OfflineSyncManager, AISummary, AuditLogViewer, QuickActions, LabDeviceMonitor, LabStatsTrends, HealthTrendChart, ContextualMenu, OTPInput, PasswordStrength, ImageEditor, DashboardInsight, PredictiveAnalytics |
| **Alpha** | Recently added, actively evolving | DigitalTwinSimulation, NeuralConnectivityHub, NeuralSparkline, QuantumHealthGrid, OrganAnalysis, MinistryCommandCenter, CrisisResponsePipeline, PredictiveOutbreak, ExplainableAI, BiometricStatus, AITriageAssistant, AdvancedTriageDetails, ClinicalSummaryBento, DoctorPriorityQueue, PrescriptionBuilder, SymptomChecker, MedicineCabinet, NationalIDCard, FamilySwitcher, DigitalTwin, SystemDiagnosticsDrawer, TaskQueue |
| **Planned** | Identified as needed, not yet built | None currently identified — all listed components are implemented |

### Component Maturity Criteria

- **Production-ready**: Exported from index, used in route/component tests, handles loading/error/empty states, has TypeScript types
- **Beta**: Functional with basic prop interface, minimal edge-case handling, used in at least one view
- **Alpha**: Recently added, basic implementation, may lack loading/error/empty states

## 11. Design Token References

Design tokens are defined at three levels in the platform:

| Source | Format | Tokens Defined |
|--------|--------|----------------|
| `frontend-v2/src/index.css` | Tailwind CSS v4 `@theme` directive | Color palette (primary indigo-600, surface, error/success/warning containers), font stack (Outfit/Inter/Noto Kufi Arabic/Noto Naskh Arabic/JetBrains Mono), custom shadows, border radii, RTL-aware utilities |
| `frontend-v3/src/styles/theme.css` | CSS custom properties (OKLCH color space) | Background/foreground, card, primary/secondary/muted/accent/destructive, sidebar theme, chart color scale (5 levels), light/dark dual variants |
| `packages/uap-tokens/` (planned) | Design token package | Shared cross-app token definitions |

**Key CSS variable groups (frontend-v3 `theme.css`):**
```
--background, --foreground              # Page-level colors
--card, --card-foreground               # Card surface colors
--primary, --primary-foreground         # Primary action colors
--secondary, --secondary-foreground     # Secondary action colors
--muted, --muted-foreground             # Muted/de-emphasized text
--accent, --accent-foreground           # Accent/highlight colors
--destructive, --destructive-foreground # Error/destructive action colors
--border, --ring                        # Border and focus ring colors
--sidebar-*                             # Sidebar-specific background/foreground/group colors
--chart-1 through --chart-5             # Chart color scale (5 levels for categorical data)
```

**Custom utility classes (frontend-v2 `index.css`):**
- `.glass-panel` — Frosted glass background effect
- `.card-sleek`, `.card-precise` — Card variants with specific elevation and border
- `.btn-premium` — Premium button variant with gradient
- `.focus-ring` — Consistent focus ring on interactive elements
- `.rtl-aware` — Flips flex direction in RTL mode

## 12. Accessibility Score

Based on the comprehensive `ACCESSIBILITY_CERTIFICATION.md` audit and `docs/ux-audit/` findings:

| Metric | Score | Tier |
|--------|-------|------|
| **Overall** | **85/100** | **GOLD** |

| Category | Score | Notes |
|----------|-------|-------|
| WCAG 2.1 AA Compliance | 92% | All AA criteria met; AAA for some text/contrast still in progress |
| Keyboard Navigation | 88% | Full keyboard traversal; Tab, Arrow, Enter, Escape work across all components |
| Screen Reader Support | 84% | ARIA labels present on interactive elements; charts need improvement |
| Color Contrast | 78% | Meets AA (4.5:1) for normal text; dark mode has some muted variants below threshold |
| Focus Management | 90% | Visible focus rings, logical tab order, skip-to-content link |
| ARIA Implementation | 82% | Roles, states, properties on custom components; missing on recharts SVGs |
| Reduced Motion Support | 95% | `prefers-reduced-motion` disables all animations; PageTransition respects |
| High Contrast Support | 80% | `prefers-contrast: high` enhances borders; Windows High Contrast mode not fully tested |

**Strengths:**
- `prefers-reduced-motion` fully supported across all animations and transitions
- `prefers-contrast: high` media query enhances border visibility
- Skeleton components use `aria-busy="true"`, `role="status"`, descriptive `aria-label`
- Empty state components use `role="status"` for screen reader announcement
- Keyboard shortcut system (`?` opens ShortcutsModal, `g d` etc. for navigation)
- Focus ring utility on all interactive elements via `.focus-ring` class
- ErrorBoundary provides accessible error recovery (button, message)

**Areas for improvement:**
- Color contrast in dark mode for some muted text variants
- ARIA labels on recharts-based chart components
- Form error announcements for screen readers (live regions)

**Source files:**
- `ACCESSIBILITY_CERTIFICATION.md` — Full accessibility certification report
- `docs/ux-audit/` — UX audit artifacts and findings
- `frontend-v2/src/hooks/useAccessibility.ts` — Accessibility hooks

## 13. Dark Mode Support

| Feature | Status | Implementation |
|---------|--------|---------------|
| Toggle | **Implemented** | `ThemeContext` in frontend-v3 provides `isDark` / `toggleTheme` via React context |
| Persistence | **LocalStorage** | Theme preference persisted across browser sessions |
| CSS Strategy | **Class-based** | `class="dark"` on `<html>` element triggers CSS variable swap |
| frontend-v2 | **Partial** | Tailwind `dark:` variant used in select components; not globally theme-switched |
| frontend-v3 | **Full** | All colors in `theme.css` as light/dark CSS custom properties; single class toggle switches entire palette |

**Dark mode color strategy (frontend-v3):**
- Uses OKLCH color space for perceptually uniform dark variants
- All color tokens have corresponding dark values (swap via `:root` / `.dark` selectors)
- Sidebar has dedicated dark mode variables (`--sidebar-*`)
- Chart colors scale naturally between light and dark (perceptually uniform)

**Frontend-v2 limitations:**
- Currently uses Tailwind `dark:` class variant pattern (not CSS custom properties)
- Not all components have explicit dark mode styling
- Migration to CSS custom property approach planned for future version

## 14. Component Dependency Graph

Key dependency relationships between components (frontend-v2):

```
App (App.tsx)
├── AuthContext.Provider
├── LanguageContext.Provider
│   └── dir="rtl" / dir="ltr" on <html>
├── Sidebar
│   ├── PermissionGuard
│   ├── Tooltip
│   └── ContextualMenu
├── TopBar
│   ├── NotificationCenter
│   │   ├── Badge
│   │   └── ClickToCopy
│   └── LanguageContext (language switcher)
├── AnimatedRoutes (PageTransition wrapper)
│   └── ScrollToTop
├── CommandPalette (cmdk)
├── HelpAssistant
├── GlobalAiAssistant
├── ShortcutsModal
├── OfflineSyncManager
├── SystemDiagnosticsDrawer
└── TaskQueue

DataTable (frontend-v3)
└── @tanstack/react-table (sorting, filtering, pagination, Arabic localization)

Modal (frontend-v3)
├── Button
└── Portal (teleport to body)

Dialog (frontend-v3)
├── Button
├── Badge
├── Portal
└── Esc-to-close handler
```

**Shared dependency relationships:**
- `PermissionGuard` — consumed by Sidebar and all view-level components that need RBAC gating
- `Button` — consumed by almost every component (the single most-depended-upon component)
- `Badge` — consumed by NotificationCenter, AuditLogViewer, SmartAlertSystem, status displays
- `Skeleton` variants — consumed by all loading states across dashboard and list views
- `EmptyState` — consumed by all list/detail views with no-data state
- `Breadcrumbs` — consumed by all detail views (PatientProfile, LabDashboard, etc.)

## 15. Reusability Score

Component reuse frequency across frontend applications (estimated from import references):

| Component | Applications | Est. Import Count | Reuse Tier |
|-----------|-------------|-------------------|------------|
| `Button` | v2, v3, client | 20+ | **High** |
| `Badge` | v2, v3 | 10+ | **High** |
| `Skeleton` (all variants) | v2 | 8+ | **High** |
| `Avatar` | v2 | 5+ | **Medium** |
| `Tooltip` | v2 | 5+ | **Medium** |
| `EmptyState` | v2 | 5+ | **Medium** |
| `PermissionGuard` | v2 | 5+ | **Medium** |
| `Breadcrumbs` | v2 | 3+ | **Low** |
| `DataTable` | v3 | 3+ | **Low** |
| `Modal` | v3 | 3+ | **Low** |
| `ClickToCopy` | v2 | 2+ | **Low** |
| `Dialog` | v3 | 2+ | **Low** |
| `ScrollToTop` | v2 | 1 | **Singleton** |
| `Sidebar` | v2, v3 | 1 each | **Singleton** |
| `TopBar` | v2 | 1 | **Singleton** |
| `ErrorBoundary` / `RouteErrorBoundary` | v2 | 1 | **Singleton** |

**Reuse Strategy:**
- **High reuse** components: Exported from barrel files (`components/ui/index.ts`), documented in this catalog
- **Singleton** components: App-shell-specific (Sidebar, TopBar, ErrorBoundary) — not intended for reuse outside the shell
- **Cross-app sharing**: No formal component library (Bit/Storybook/etc.) exists; each app duplicates common primitives

## 16. Screens Using Each Component

Mapping of key components to the views/pages that consume them:

| Component | Used In (View/Page) |
|-----------|---------------------|
| `PermissionGuard` | All guarded views: DoctorDashboard, LabDashboard, MinistryDashboard, AdminPanel, PatientProfile, RecordsView, etc. |
| `Sidebar` | App shell (all views, all wings) |
| `TopBar` | App shell (all views, all wings) |
| `Breadcrumbs` | All detail views (PatientProfile, LabDashboard, WorkQueue, DeviceManagement, etc.) |
| `NotificationCenter` | All views (via TopBar — persistent bell icon) |
| `SmartAlertSystem` | LabDashboard, DoctorIntelligence, MinistryDashboard |
| `AISummary` | SmartResultsView, PatientProfile (test results explanation) |
| `AuditLogViewer` | SecurityAuditView (citizen), AdminPanel (admin) |
| `HealthTrendChart` | CitizenHealth, DoctorIntelligence, NationalHealthGrid |
| `PredictiveAnalytics` | DoctorIntelligence, MinistryDashboard |
| `PredictiveOutbreak` | EpidemiologicalIntelligence, NationalHealthGrid |
| `LabDeviceMonitor` | DeviceManagement, DeviceMonitoring (lab wing) |
| `LabStatsTrends` | LabDashboard |
| `ResultEntryUI` | WorkQueue (lab wing — result data entry) |
| `PrescriptionBuilder` | DoctorIntelligence, PatientProfile (doctor wing) |
| `ClinicalNotes` | PatientProfile, RecordsView (doctor wing) |
| `SymptomChecker` | CitizenAssistant (citizen wing) |
| `DigitalTwin` | CitizenHealth (citizen wing) |
| `NationalIDCard` | IdentityVerificationView, CitizenDashboard |
| `CrisisResponsePipeline` | MinistryDashboard (ministry wing) |
| `DataTable` (v3) | All list pages: patients, results, orders, samples, labs, admin, compliance, stats, etc. |
| `Modal` (v3) | Detail forms and creation dialogs across all v3 pages |
| `Dialog` (v3) | Confirmation dialogs and alerts across all v3 pages |
| `OTPInput` | LandingAuthView (login flow) |
| `PasswordStrength` | LandingAuthView (registration flow) |
| `ImageEditor` | IdentityVerificationView (document photo capture) |
| `DoctorPriorityQueue` | DoctorIntelligence (doctor wing) |
| `AdvancedTriageDetails` | DoctorIntelligence (doctor wing) |
| `AITriageAssistant` | DoctorIntelligence (doctor wing) |
| `ClinicalSummaryBento` | PatientProfile (doctor wing) |
| `FamilySwitcher` | CitizenDashboard (citizen wing) |
| `MedicineCabinet` | MedicationCenter (citizen wing) |
| `NeuralConnectivityHub` | DoctorIntelligence, EpidemiologicalIntelligence |
| `QuantumHealthGrid` | NationalHealthGrid (ministry wing) |
| `OrganAnalysis` | DoctorIntelligence (doctor wing) |
| `DigitalTwinSimulation` | CitizenHealth (citizen wing) |

## 17. Performance Notes

Component-level performance characteristics from `PERFORMANCE_GUIDE.md`, `PERFORMANCE_CERTIFICATION.md`, and `frontend-v3/PERFORMANCE.md`:

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| First Contentful Paint (FCP) | < 1.5s | ~1.8s | Needs improvement |
| Largest Contentful Paint (LCP) | < 2.5s | ~2.2s | On target |
| First Input Delay (FID) | < 100ms | ~50ms | Good |
| Time to Interactive (TTI) | < 3.5s | ~3.0s | On target |
| Bundle Size (gzip) | < 200 KB | ~280 KB | Needs code splitting |
| Lighthouse Performance | > 90 | ~85 | Needs improvement |
| Lighthouse Accessibility | > 90 | ~88 | Near target |
| Lighthouse Best Practices | > 90 | ~92 | Good |

**Performance patterns:**
- **Lazy loading:** All route-level components use `React.lazy()` + `Suspense` in frontend-v2
- **Code splitting:** View-level code splitting via route-based dynamic imports
- **Memoization:** Heavy chart components (`HealthTrendChart`, `PredictiveAnalytics`) use `React.memo()`
- **Debounced search:** All search inputs use debouncing (300ms default) via `useDebounce` hook
- **Virtualization:** `DataTable` uses `@tanstack/react-virtual` for large list rendering (frontend-v3)
- **Image optimization:** Images use lazy loading with blur placeholder; SVGs inline where possible
- **Animation:** `motion` library (framer-motion) components use `will-change: transform` GPU acceleration
- **State management:** Context-based stores (navigationStore, workspaceStore) minimize re-renders via selective subscriptions

**Areas for improvement:**
- Bundle size reduction through tree-shaking unused icon imports (lucide-react)
- Server-side rendering or static generation for initial page load
- Image CDN for citizen portal profile photos and document uploads
- App shell caching via service worker (currently only `frontend/` PWA has this)
- Component-level code splitting for heavy visualization packages (recharts)

## 18. Storybook Status

**Storybook is NOT implemented** in any of the four frontend applications:

| Application | Storybook | Component Docs Alternative |
|-------------|-----------|---------------------------|
| frontend-v2 | ❌ | This catalog (`docs/frontend/UI_COMPONENT_CATALOG.md`) |
| frontend-v3 | ❌ | This catalog + `frontend-v3/ARCHITECTURE.md`, `frontend-v3/QUALITY.md` |
| frontend (PWA) | ❌ | Minimal (static HTML/CSS — no component system) |
| client | ❌ | Minimal (lightweight SPA — few reusable components) |

**Recommendation:** Consider implementing Storybook for:
1. **frontend-v3 components** — highest potential value (emerging component system with DataTable, Modal, Dialog, form primitives)
2. **Shared UI primitives** (Button, Badge, Skeleton, EmptyState) — highest reuse; visual regression testing would prevent regressions
3. **Complex visualization components** (HealthTrendChart, PredictiveAnalytics, NeuralConnectivityHub) — hardest to manually verify

## 19. Related Documents

| Document | Location | Description |
|----------|----------|-------------|
| frontend-v2 README | `frontend-v2/README.md` | Development setup and overview |
| frontend-v3 README | `frontend-v3/README.md` | Vite + React + Oxlint setup |
| frontend-v3 Architecture | `frontend-v3/ARCHITECTURE.md` | Frontend-v3 architecture decisions |
| frontend-v3 Quality | `frontend-v3/QUALITY.md` | Quality benchmarks |
| frontend-v3 Performance | `frontend-v3/PERFORMANCE.md` | Performance targets and measurements |
| frontend-v3 Coverage | `frontend-v3/COVERAGE.md` | Test coverage report |
| frontend PWA | `frontend/sw.js` | Service worker for offline static PWA |
| Security Spec | `frontend-v2/security_spec.md` | Frontend security specification |
| Accessibility Certification | `ACCESSIBILITY_CERTIFICATION.md` | Full accessibility audit report |
| UX Audit | `docs/ux-audit/` | UX audit artifacts and findings |
| Performance Certification | `PERFORMANCE_CERTIFICATION.md` | Performance benchmarks and targets |
| Design Tokens (v2) | `frontend-v2/src/index.css` | CSS-based design tokens via Tailwind `@theme` |
| Design Tokens (v3) | `frontend-v3/src/styles/theme.css` | CSS custom property design tokens (OKLCH) |
| CLAUDE.md | `CLAUDE.md` | Full repository architecture guide |
