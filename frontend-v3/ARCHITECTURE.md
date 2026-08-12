# Frontend Architecture

## Overview
React 19 SPA with TypeScript strict mode, RTL/Arabic-first i18n, connected to FastAPI backend.

## Stack
- **Framework:** React 19 + TypeScript 5.8
- **Routing:** react-router-dom v7 (createBrowserRouter, lazy loading)
- **Data Fetching:** @tanstack/react-query v5 (useQuery/useMutation)
- **HTTP Client:** Axios with JWT refresh interceptor
- **UI:** Custom component library (radix-inspired), Tailwind CSS v4
- **Bundle:** Vite 8 (code splitting, tree shaking)
- **Internationalization:** i18next + react-i18next (ar/en)
- **Real-time:** WebSocket with auto-reconnect, Server-Sent Events

## Directory Structure
```
src/
├── api/          # API client + endpoint definitions
│   ├── client.ts     # Axios instance, interceptors, JWT refresh
│   └── endpoints.ts  # 55 API modules, 500+ typed functions
├── components/   # Reusable UI components
│   ├── ui/           # Primitives (Button, Card, DataTable, Dialog...)
│   └── shared/       # Page-level (PageHeader, LoadingSpinner, ErrorDisplay...)
├── contexts/     # React context providers
│   ├── AuthContext.tsx    # JWT auth + user state
│   ├── LocaleContext.tsx  # RTL/i18n
│   └── ThemeContext.tsx   # dark/light/system
├── hooks/        # Custom React hooks
│   ├── useApi.ts        # 50+ typed useQuery/useMutation wrappers
│   ├── useRealtime.ts   # WebSocket + SSE hooks
│   ├── useToast.ts      # Toast notification system
│   ├── useDebounce.ts   # Input debouncing
│   ├── useMediaQuery.ts # Responsive breakpoints
│   ├── usePermissions.ts# RBAC permission checks
│   └── useApiError.ts   # API error handling
├── i18n/         # Translation dictionaries
│   ├── ar.ts  # 195+ Arabic keys
│   └── en.ts  # 195+ English keys
├── layouts/      # Page layouts
│   ├── AuthLayout.tsx      # Centered auth pages
│   ├── DashboardLayout.tsx # Sidebar + topbar + content
│   └── Sidebar.tsx          # Collapsible role-based navigation
├── lib/          # Utilities
│   └── utils.ts            # cn(), formatDate(), formatNumber(), etc.
├── pages/        # 29 page components (lazy loaded)
│   ├── admin/        # AdminLabs, AdminUsers, AdminAudit
│   ├── ai/           # AI v1 assistant
│   ├── ai-platform/  # AI Platform v2 (search, RAG, agents, sessions)
│   ├── alerts/       # Critical alerts
│   ├── auth/         # Login
│   ├── compliance/   # Compliance dashboard
│   ├── dashboard/    # Main dashboard
│   ├── edge/         # Edge device management
│   ├── ehr/          # Electronic Health Records
│   ├── fhir/         # FHIR resource explorer
│   ├── financial/    # Financial management
│   ├── hospital/     # Hospital management
│   ├── identity/     # Health identity
│   ├── labs/         # Lab management
│   ├── national-data/# National health data
│   ├── notifications/# Notification sender
│   ├── orders/       # Lab orders
│   ├── patient-card/ # QR patient cards
│   ├── patients/     # Patient records
│   ├── profile/      # User profile
│   ├── qc/           # Quality control
│   ├── results/      # Test results
│   ├── samples/      # Sample tracking
│   ├── security/     # Security settings
│   ├── settings/     # App settings
│   ├── stats/        # Analytics & statistics
│   └── tiers/        # Subscription tiers
├── permissions/  # RBAC definitions
│   └── index.ts     # 11 roles, 17 permissions, sidebar nav
├── routes/
│   └── index.tsx    # 31 routes, lazy loaded, protected
└── types/        # TypeScript interfaces
    ├── api.ts       # API request/response types
    ├── backend.ts   # Backend entity types (50+ interfaces)
    ├── index.ts     # Re-exports
    └── models.ts    # Domain model types
```

## Data Flow
```
User → React Component
         → useQuery/useMutation hook (useApi.ts)
              → API function (endpoints.ts)
                   → Axios client (client.ts)
                        → JWT interceptor → Backend FastAPI
```

## Route Architecture (31 routes)
| Category | Routes | Auth |
|----------|--------|------|
| Auth | 1 (/login) | Public |
| Core Lab | 6 | JWT required |
| Clinical | 4 | JWT required |
| Enterprise | 4 | JWT required |
| Admin | 4 | JWT + admin role |
| Settings | 4 | JWT required |
| Tools | 4 | JWT required |

## API Coverage
| Metric | Value |
|--------|-------|
| Backend router files | 55 |
| API client modules | 55 |
| Typed API functions | 500+ |
| React Query hooks | 50+ |
| Full-coverage pages | 29 |
