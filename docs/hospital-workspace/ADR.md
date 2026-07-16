# Architecture Decision Records — National Hospital Desktop Workspace (NHDW)

---

## ADR-001: PySide6 for Desktop (Why Qt over Electron/Tauri)

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, Desktop Product Manager

### Context

NHDW requires a Windows-native desktop application for hospital operations. The technology choice must support Python (the team's primary language), provide native performance, and allow code reuse with the existing GULA backend. The main candidates were Electron (Node.js/Chromium), Tauri (Rust/Webview), and PySide6 (Qt for Python).

### Decision

Use **PySide6 (Qt for Python)** as the desktop UI framework.

### Rationale

1. **Python ecosystem reuse** — The team's primary language is Python. PySide6 allows direct import of shared business logic modules (`hospital/models/`, `services/hospital_service.py`, `services/audit_service.py`) without an IPC bridge or rewrite. Electron/Tauri would require wrapping Python in a sidecar process or rewriting logic in JavaScript/Rust.
2. **Performance** — Qt native widgets render directly on the Windows desktop without a browser engine. Memory footprint is ~40 MB vs ~200+ MB for Electron, critical for hospital computers that often have limited RAM.
3. **RTL support** — Qt has mature, well-tested RTL layout support (`QApplication.setLayoutDirection`). Electron's RTL support is browser-based and less consistent across platforms.
4. **Licensing** — PySide6 is LGPL-licensed (permissive for commercial distribution). Electron is MIT but bundles Chromium (large download). Tauri is MIT/Apache but would require Rust for native plugins.
5. **Hardware integration** — Qt provides direct access to serial ports, USB, and file system without Node.js bindings. The existing desktop already uses serial port monitoring via PySide6's `QSerialPort`.
6. **Threading** — Qt's signal/slot mechanism provides a proven concurrency model for UI thread safety during background sync operations.
7. **Distribution** — PyInstaller bundles Python + Qt into a single executable. PyInstaller supports Windows, and the team already has packaging experience.

### Consequences

- **Positive**: Full code reuse, native performance, mature RTL, small footprint, direct hardware access
- **Negative**: Qt is a less popular choice for new desktop apps (smaller community than Electron); developer familiarity with Qt must be built; QSS theming is more verbose than CSS

---

## ADR-002: RTL-First Design for Arabic Healthcare

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** UX Lead, Engineering Lead, Product Manager

### Context

NHDW serves Iraqi hospitals where the primary clinical language is Arabic. The application must be fully functional in Arabic without degradation in user experience.

### Decision

Design the application **RTL-first** — Arabic is the default layout direction, with English as the secondary option.

### Rationale

1. **Clinical safety** — Medical errors increase when practitioners work in a non-native language. Defaulting to RTL/Arabic reduces cognitive load for Iraqi clinicians.
2. **Cultural appropriateness** — Government hospitals in Iraq require Arabic-language software. English-only would disqualify NHDW from public hospital deployment.
3. **Technical implementation** — Qt allows setting layout direction at application level before any widget is created (`QApplication.setLayoutDirection(Qt.RightToLeft)`). This is simpler than per-widget RTL handling.
4. **Consistency** — All UI strings stored in `ArStrings` class (530+ entries). A single `TranslationManager` handles runtime switching, ensuring uniform terminology across the application.
5. **Data model alignment** — Hospital models already include `name_ar` fields. The UI naturally maps to these fields when in Arabic mode.

### Consequences

- **Positive**: Native Arabic experience, reduced clinical error risk, government compliance
- **Negative**: English text may overflow in RTL-designed layouts; bidirectional text (numbers in Arabic sentences) requires careful testing

---

## ADR-003: Offline-First with Encrypted SQLite

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect

### Context

Iraqi hospital internet connectivity is unreliable. NHDW must support full CRUD operations during internet outages and synchronise automatically when connectivity is restored.

### Decision

Implement an **offline-first architecture** using local SQLite for storage and an outbox pattern for synchronisation.

### Rationale

1. **Reliability** — Hospital operations cannot depend on internet connectivity. Admissions, discharges, transfers, and clinical tasks must work 100% of the time.
2. **SQLite simplicity** — SQLite is zero-configuration, file-based, and included in Python's standard library. No separate database server is needed on the client machine.
3. **Outbox pattern** — All local changes are logged to a `sync_log` table before execution. On connectivity restoration, changes are pushed in order with conflict resolution (last-writer-wins).
4. **Delta sync** — After initial full sync, only changes since the last sync timestamp are transferred, minimising bandwidth usage on slow connections.
5. **Future encryption** — SQLCipher integration is planned for local data encryption at rest, protecting patient data on shared hospital computers.

### Consequences

- **Positive**: Full offline capability, simple implementation, low bandwidth usage
- **Negative**: Conflict resolution complexity (last-writer-wins may lose concurrent changes); local data at risk if machine is stolen (mitigated by planned SQLCipher); sync timing can create temporary data inconsistency

---

## ADR-004: Module Extends Hospital Module Without Modifying It

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect

### Context

The GULA platform already has a hospital module (`backend/app/hospital/`) with 13 models and routes. NHDW needs additional functionality (clinical tasks, department alerts, KPI dashboard) that should not be tightly coupled to the existing module.

### Decision

NHDW adds endpoints under a **new `/nhdw/` prefix** and uses a **separate `NHDWBase` declarative base** for its models. NHDW code imports from the hospital module but never modifies it.

### Rationale

1. **Stability** — The hospital module is in production. Modifying it risks regression in existing functionality.
2. **Separation of concerns** — NHDW-specific features (desktop sync, clinical tasks, department alerts) are conceptually separate from core hospital entity management.
3. **Independent deployment** — NHDW features can be deployed, rolled back, or scaled independently of the hospital module.
4. **Future refactoring** — If NHDW eventually becomes a separate service, the clean module boundary makes extraction straightforward.

### Consequences

- **Positive**: No regression risk, clear boundaries, independent deployment
- **Negative**: Some data duplication between hospital module and NHDW models; queries that join hospital and NHDW tables require explicit cross-base queries

---

## ADR-005: NHDWBaseEntity with ULID PK

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead

### Context

NHDW entities created on the desktop client need unique identifiers before they are synced to the backend. Auto-incrementing integer IDs (used by the hospital module) require a database round-trip.

### Decision

Use **ULID (Universally Unique Lexicographically Sortable Identifier)** as the primary key type for NHDW entities.

### Rationale

1. **Offline generation** — ULIDs are generated client-side without database access, enabling offline entity creation.
2. **Lexicographic sorting** — ULIDs are time-sortable, making them suitable for ordered lists without additional timestamp columns.
3. **Efficiency** — ULIDs are 26 characters (128 bits), comparable to UUIDs but more readable and sortable.
4. **Existing pattern** — The GULA platform already uses ULIDs in some models (patient cards, edge platform).

### Consequences

- **Positive**: Client-side ID generation, sortable, readable
- **Negative**: String primary keys are slightly slower than integer keys for indexed joins; requires consistent ULID generation across all NHDW clients

---

## ADR-006: KPI Engine as Separate Module

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Product Manager

### Context

The NHDW dashboard displays clinical KPIs (occupancy rate, average length of stay, readmission rate, etc.) that require data aggregation across multiple hospital and NHDW tables.

### Decision

Implement the KPI engine as a **separate service module** (`backend/app/services/kpi_engine.py`) rather than inline in route handlers.

### Rationale

1. **Reusability** — The KPI engine can be consumed by the NHDW desktop dashboard, web dashboard, and future mobile apps.
2. **Testability** — Isolated KPI computation logic can be unit-tested without route handler overhead.
3. **Caching** — A separate module enables transparent caching of KPI results in Redis with configurable TTL.
4. **Performance optimisation** — Heavy aggregation queries can be optimised independently of API response formatting.

### Consequences

- **Positive**: Reusable, testable, cacheable, optimisable
- **Negative**: Additional module to maintain; KPI definitions must be versioned when formulas change
