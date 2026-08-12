# GULA Platform — Frontend Analysis
**Date:** 2026-07-17

---

## 1. Frontend Inventory

The platform contains 4 distinct frontend applications:

| Project | Location | Framework | State | Purpose |
|---------|----------|-----------|-------|---------|
| **frontend-v2** | `frontend-v2/` | React + Firebase | Active development | Citizen portal, Ministry CC, predictive analytics, doctor/lab dashboards |
| **client** | `client/` | tRPC + React SPA | Active | Lightweight connected SPA |
| **frontend** | `frontend/` | Static HTML + PWA | Stable | Offline-capable PWA |
| **hospital_desktop** | `hospital_desktop/` | Unknown | Unknown | Desktop hospital application |

---

## 2. frontend-v2 (Primary Frontend — Formerly samertts/Front-end-)

### Quick Facts
- **Framework**: React (TypeScript)
- **Backend**: Firebase (Firestore + Auth)
- **Build**: Vite + pnpm
- **Portals**: Citizen, Doctor, Lab, Ministry Command Centre
- **Features**: Predictive analytics, Arabic-first UI

### Architecture
The frontend-v2 appears to be a Firebase-native application that communicates primarily with Firestore rather than the FastAPI backend. This creates an architectural concern:

```
┌──────────────────────────────────────────────────────────┐
│                    frontend-v2 (React)                    │
│                          │                               │
│          ┌───────────────┼───────────────┐               │
│          │               │               │               │
│   Firebase Auth    Firestore (Read/Write)  │ (minimal?)  │
│          │               │               │               │
│     ┌────▼────┐    ┌─────▼──────┐    ┌───▼────────┐    │
│     │Firebase │    │ Cloud      │    │ FastAPI    │    │
│     │ Auth    │    │ Firestore  │    │ Backend    │    │
│     └─────────┘    └────────────┘    └────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Key Risk**: Firebase-native architecture means patient data flows through Firestore, potentially bypassing the backend's security controls (RBAC, ABAC, audit log, rate limiting, encryption).

### Dependencies (from `package.json`)
- React, React Router, Redux/Zustand (TBD)
- Firebase SDK (auth, firestore, storage)
- Chart.js / D3 (analytics dashboards)

---

## 3. client (tRPC + React SPA)

### Quick Facts
- **Framework**: React (TypeScript)
- **Backend**: tRPC → FastAPI (native connection)
- **State**: Likely tRPC cache + React state
- **Build**: Vite

### Architecture
This frontend connects directly to the FastAPI backend via tRPC, benefiting from:
- End-to-end type safety
- Backend-managed auth (JWT)
- Backend RBAC/ABAC enforcement
- Full audit trail

```
┌────────────────────────────────────────┐
│        client (React + tRPC)           │
│              │                         │
│         tRPC client                    │
│              │                         │
│     ┌────────▼────────┐               │
│     │  FastAPI Backend │               │
│     │  (JWT + RBAC +   │               │
│     │   Audit + Perms) │               │
│     └─────────────────┘               │
└────────────────────────────────────────┘
```

---

## 4. frontend (Static HTML PWA)

### Quick Facts
- **Type**: Static HTML/CSS/JS
- **Feature**: Progressive Web App (offline-capable)
- **Service Worker**: Yes (offline support)
- **Backend**: Direct API calls to FastAPI

### Architecture
Lightweight, mobile-friendly PWA for:
- Result viewing (token-based, no login required)
- Basic patient lookup
- Offline-capable result caching

---

## 5. hospital_desktop

### Status
- Directory exists at `hospital_desktop/`
- Purpose unknown (desktop application for hospital use)
- Requires further investigation

---

## 6. Cross-Frontend Concerns

### Authentication
| Frontend | Auth Method | Token Storage |
|----------|-------------|---------------|
| frontend-v2 | Firebase Auth | Firebase-managed |
| client | JWT (tRPC) | Cookie/LocalStorage |
| frontend (PWA) | Token-based (QR) | URL param / Session |

### Tenant Isolation
- `client` and `frontend` (PWA) benefit from backend-enforced `lab_id` filtering
- `frontend-v2` uses Firestore security rules (independent of backend)

### Arabic Support
- All frontends support Arabic-first UI
- `frontend-v2` appears fully localized
- RTL layout support

---

## 7. Critical Findings

| Finding | Evidence | Risk |
|---------|----------|------|
| **Firebase bypasses backend security** | frontend-v2 talks directly to Firestore | **CRITICAL** — patient data may bypass RBAC, audit, rate limiting |
| **Dual auth systems** | Firebase Auth + JWT (FastAPI) | **HIGH** — inconsistent user identity across apps |
| **frontend-v2 complexity** | Large monolith frontend | **HIGH** — maintainability risk |
| **No frontend test evidence** | No comprehensive test suites found | **HIGH** — quality unknown |
| **PWA limited functionality** | Static HTML | **LOW** — by design |
| **hospital_desktop unknown** | No code inspected | **MEDIUM** — unknown risk |
