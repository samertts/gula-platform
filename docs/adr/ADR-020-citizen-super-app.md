# ADR-020: National Citizen Super App

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Product Owner, Mobile Lead

---

## Context

Iraqi citizens currently interact with the healthcare system through fragmented channels: paper records, different hospital systems, laboratory walk-ins, and multiple unconnected mobile applications. There is no single application that gives citizens access to their complete health information, laboratory results, appointment management, prescription history, and direct communication with healthcare providers.

**Requirements:**
- Single application for citizens to access their complete longitudinal health record
- View laboratory results, diagnostic reports, prescriptions, immunizations, and visit history
- Appointment management (book, reschedule, cancel) across all connected healthcare facilities
- Secure messaging with healthcare providers
- Push notifications for result availability, appointment reminders, and health alerts
- Multi-platform support: Android, iOS, and Progressive Web App (PWA)
- Offline support for low-connectivity regions
- Arabic-first interface with English language option
- Accessibility support for elderly and disabled users
- Integration with national identity (SNDHS Health ID, Iraqi National ID)

**Constraints:**
- Must reuse existing `citizen_platform/` module rather than building from scratch
- Must not duplicate APIs — all data comes from existing national platform services
- Must work in low-bandwidth and offline environments common in Iraqi regions
- Must comply with Iraqi data privacy regulations and patient consent requirements
- Must support gradual rollout with feature flags

## Decision

Reuse and extend the existing `citizen_platform/` module with offline-first support, creating a multi-platform citizen super app. The app is a thin client that composes data from national platform APIs (EHR, notifications, appointments) through a unified citizen-facing gateway.

### Architecture

```
+------------------------------------------------------------------+
|                     Citizen Super App                            |
+------------------------------------------------------------------+
|                                                                   |
|  +----------------------------------------------------------+    |
|  |                    Presentation Layer                     |    |
|  |  Flutter (Android/iOS/PWA)  |  Arabic-first UI            |    |
|  |  Offline-first (SQLite)     |  Accessibility (WCAG 2.1)   |    |
|  +--------------------------+-------------------------------+    |
|                              |                                    |
|  +--------------------------+-------------------------------+    |
|  |                    Service Layer                          |    |
|  |  Cache Manager  |  Sync Engine  |  Notification Handler   |    |
|  |  Auth (OAuth 2.0 + biometric)   |  Location Services     |    |
|  +--------------------------+-------------------------------+    |
|                              |                                    |
|  +--------------------------+-------------------------------+    |
|  |                    Data Layer                             |    |
|  |  Local DB (SQLite)  |  Secure Storage  |  API Client      |    |
|  +--------------------------+-------------------------------+    |
|                              |                                    |
+------------------------------+------------------------------------+
                               |
+------------------------------+------------------------------------+
|                    Citizen API Gateway                             |
|  (Authentication, rate limiting, consent enforcement)              |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------+  +-----------+  +-----------+  +--------------+    |
|  | EHR API   |  | Notification | | Appointment| | Health       |  |
|  | (ADR-016) |  | API        |  | API       | | Intelligence  |  |
|  +-----------+  +-----------+  +-----------+  +--------------+   |
|                                                                   |
+------------------------------------------------------------------+
```

### Key Design Decisions

1. **Reuse citizen_platform/ module** — The existing module is the foundation. Extensions are added as new submodules rather than modifications, preserving backward compatibility with any existing users.

2. **Offline-first architecture** — The app stores a local copy of health data in SQLite. When connectivity is available, the sync engine reconciles local changes with the server. This ensures usability in rural Iraqi regions with intermittent connectivity.

3. **Thin client, thick API** — The app is intentionally thin. All business logic, data composition, and authorization checks happen server-side. The app is a presentation layer with local caching.

4. **Flutter for multi-platform** — Flutter is selected for its single-codebase approach to Android, iOS, and PWA. This avoids maintaining three separate codebases and speeds up feature delivery.

5. **Consent-first design** — The app respects the patient consent records managed by the EHR platform. Citizens see only data they have consented to access, and can manage their consent preferences within the app.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | Flutter app shell, authentication, EHR read-only (results, reports), Arabic UI | 10 weeks |
| **Phase 2** | Offline support, local caching, sync engine, notifications | 8 weeks |
| **Phase 3** | Appointment management, secure messaging, consent management | 8 weeks |
| **Phase 4** | PWA, accessibility, performance optimization, production release | 6 weeks |

## Consequences

### Positive
- **Multi-platform reach** — Android, iOS, and PWA from a single codebase
- **Offline capability** — Usable in low-connectivity regions across Iraq
- **Zero API duplication** — All data served by existing national platform APIs
- **Rapid delivery** — Starting from existing `citizen_platform/` module reduces time-to-market
- **Consent-controlled** — Patients control who sees their data, built into the app from day one
- **Arabic-first** — Native Arabic experience with right-to-left (RTL) support

### Negative
- **App store dependency** — Android/iOS versions require app store approval for updates
- **Offline complexity** — Conflict resolution in offline sync is non-trivial, especially for health data
- **Device fragmentation** — Android device diversity in Iraq (budget devices, older OS versions) creates testing burden
- **Flutter learning curve** — Team must develop or hire Flutter expertise

### Risks
- **Offline data staleness** — Citizens may see outdated results if sync is delayed. Mitigated by: clear staleness indicators ("Last updated: 2 hours ago"), forced refresh on critical views (e.g., new lab results), configurable sync intervals.
- **Data privacy on device** — Health data stored locally on the device could be accessed if the phone is compromised. Mitigated by: SQLite encryption (SQLCipher), biometric authentication for app access, remote wipe capability, no full health record stored offline (only recent and cached data).
- **Network cost** — Syncing health data over mobile data may be expensive for citizens. Mitigated by: configurable sync over Wi-Fi only, compressed API responses, incremental sync (only changed data).

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 1** — Patient-centric design; the app puts citizens in control
- **Engineering Constitution Section 3** — Data integrity in offline sync with conflict resolution
- **ADR-016** — EHR platform provides the health data the app displays
- **ADR-011** — Notification platform powers push notifications
- **ADR-019** — Ecosystem gateway provides secure API access for the app
- **WCAG 2.1 AA** — Accessibility for disabled users
- **Iraqi Data Privacy Regulations** — Consent management and data minimization
- **GDPR-aligned** — Right to access, rectification, and data portability
