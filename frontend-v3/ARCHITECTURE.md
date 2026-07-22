# Frontend Architecture Report

## Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Presentation                          │
│  Pages (22), Components (12), Layouts (3), Contexts (3)  │
├─────────────────────────────────────────────────────────┤
│                     State Management                      │
│  React Query (server) + Context (client)                  │
├─────────────────────────────────────────────────────────┤
│                     API Layer                              │
│  Axios client (interceptors, refresh, timeout)            │
│  Endpoints (18 domain groups, 90+ functions)              │
├─────────────────────────────────────────────────────────┤
│                     Backend (FastAPI)                      │
│  583 endpoints, 52 modules, 27 models                     │
└─────────────────────────────────────────────────────────┘
```

## Architecture Scorecard

| Principle | Status |
|-----------|--------|
| Separation of Concerns | ✅ Pages ↔ API ↔ Types ↔ UI |
| Single Responsibility | ✅ Each file has one purpose |
| DRY | ✅ Shared components, hooks, utils |
| Dependency Inversion | ✅ API client abstracts HTTP |
| Feature-based structure | ✅ Pages grouped by domain |
| Lazy loading | ❌ Not implemented (all eager) |
| Code splitting | ❌ Route-level splitting needed |
| Tree shaking | ⚠ Vite handles automatically |

## Component Hierarchy

```
App
├── QueryClientProvider (React Query)
├── ThemeProvider (dark/light/system)
├── LocaleProvider (ar/en, RTL)
├── AuthProvider (JWT, login/logout)
├── ToastProvider (global toast system)
└── RouterProvider
    ├── AuthLayout
    │   └── LoginPage
    └── ProtectedRoute
        └── DashboardLayout
            ├── Sidebar (permission-filtered nav)
            ├── Header (theme/lang toggles)
            └── <Outlet>
                ├── DashboardPage
                ├── PatientsPage
                ├── OrdersPage
                ├── ResultsPage
                ├── FHIRPages (NEW)
                └── ...
```

## Data Flow

```
Backend API → Axios → React Query → Component → User
                  ↕
           Cache (stale-while-revalidate)
                  ↕
           Optimistic Updates (mutations)
```

## State Inventory

| State Type | Location | Scope |
|-----------|----------|-------|
| Server data | React Query cache | Global |
| Auth (JWT, user) | AuthContext + localStorage | Global |
| Theme preference | ThemeContext + localStorage | Global |
| Locale preference | LocaleContext + localStorage | Global |
| Toast notifications | useToast hook (subscriber) | Global |
| Media queries | useMediaQuery hook | Local |
| Debounced values | useDebounce hook | Local |
