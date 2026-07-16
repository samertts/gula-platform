# ADR-023: National Laboratory Desktop Professional

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Lab Product Manager, Platform Architect

---

## Context

Medical laboratories in Iraq use a wide variety of laboratory information systems (LIS) with inconsistent interfaces, capabilities, and reliability. Even within the GULA platform, laboratory staff interact with a web-based interface that, while functional, does not meet the full needs of a high-throughput clinical laboratory: real-time instrument integration, barcode/RFID scanning, rapid data entry, offline resilience, and desktop-native performance.

**Requirements:**
- Single approved laboratory desktop application for all connected Iraqi laboratories
- ASTM/HL7 native instrument integration for real-time result capture from analyzers
- Barcode and RFID support for sample tracking, accessioning, and inventory management
- Rapid data entry optimized for high-throughput laboratory workflows
- Offline-first operation — full functionality during internet outages with automatic sync
- FHIR-compatible data exchange for interoperability with national platforms
- Windows desktop native (the standard OS in Iraqi laboratories)
- Role-based access for lab technicians, supervisors, and managers
- QC/QA workflows with Westgard rules, lot tracking, and proficiency testing
- Integration with the NHDP (ADR-018) for national operations visibility

**Constraints:**
- Must be a Windows-native desktop application — laboratory computers run Windows
- Must support direct serial/USB/TCP connection to laboratory analyzers
- Must operate with or without internet connectivity (offline-first is mandatory)
- Must reuse the existing `lims/` module for business logic rather than rebuilding
- Must not disrupt existing GULA web-based workflows (both coexist)
- Must support laboratory environments with limited IT support

## Decision

Build **National Laboratory Desktop Professional (Lab Desktop)** — a Windows-native desktop application built with PySide6 (Qt for Python) that reuses the existing `lims/` module for core business logic. The application provides a native desktop experience with ASTM/HL7 instrument integration, offline-first architecture, and FHIR-compatible data exchange.

### Architecture

```
+------------------------------------------------------------------+
|            National Laboratory Desktop Professional              |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------------------------------------------------------+   |
|  |                 Presentation Layer (PySide6/Qt)            |   |
|  |  Arabic-first UI  |  Barcode/RFID Integration             |   |
|  |  High-throughput workflows  |  Desktop-native performance |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Application Layer                        |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Sample   |  | Result   |  | QC/QA    |  | Inventory|     |   |
|  |  | Workflow |  | Entry    |  | Manager  |  | Manager  |     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |                                                              |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  |  | Instrument|  | Orders   |  | Reports  |  | Admin    |     |   |
|  |  | Manager   |  | Worklist |  | Generator|  | Console  |     |   |
|  |  +----------+  +----------+  +----------+  +----------+     |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Domain Layer (lims/ module)              |   |
|  |  Sample Model  |  Result Model  |  QC Rules (Westgard)    |   |
|  |  Order Model   |  Instrument Model  |  Barcode Logic       |   |
|  +--------------------------+--------------------------------+   |
|                              |                                    |
|  +--------------------------+--------------------------------+   |
|  |                    Integration Layer                        |   |
|  |                                                              |   |
|  |  +------------+  +------------+  +------------+             |   |
|  |  | ASTM/HL7   |  | FHIR API   |  | SQLite     |             |   |
|  |  | Device I/O  |  | Client     |  | Local DB   |             |   |
|  |  | (serial/   |  | (sync)     |  | (offline)  |             |   |
|  |  |  USB/TCP)  |  |            |  |            |             |   |
|  |  +------+-----+  +------+-----+  +------+-----+             |   |
|  +---------+--------------+--------------+---------------------+   |
|            |              |              |                         |
+------------+--------------+--------------+-------------------------+
             |              |              |
    +--------+-------+      |              |
    | Lab Analyzers  |  +---+----+     +---+----------+
    | (Sysmex,       |  | GULA   |     | Local        |
    |  Roche,        |  | Backend|     | SQLite DB    |
    |  Mindray, ...) |  +--------+     +--------------+
    +----------------+
```

### Key Design Decisions

1. **PySide6 (Qt for Python)** — Selected for Windows-native desktop development because: (a) Python is the team's primary language, maximizing code reuse with the backend, (b) Qt provides mature, professional-grade desktop UI components, (c) the `lims/` business logic module can be directly imported (no rewrite), (d) PySide6 is LGPL-licensed (permissive for commercial distribution).

2. **lims/ module reuse** — The core business logic (sample processing, result validation, QC rules, order management) is in the shared `lims/` module. The desktop app imports this module directly. Any changes benefit both desktop and web interfaces.

3. **Offline-first with SQLite** — The app runs a local SQLite database that mirrors the subset of data relevant to the laboratory. All operations work offline. When connectivity is restored, the sync engine reconciles changes with the GULA backend via FHIR APIs.

4. **ASTM/HL7 native instrument integration** — Direct serial, USB, or TCP connection to laboratory analyzers using ASTM E1381/E1394 and HL7 v2 protocols. Device Bridge (ADR-007) integration provides instrument management, but Lab Desktop can also connect directly for low-latency result capture.

5. **Windows-native distribution** — Packaged as a Windows installer (NSIS or Inno Setup) for simple deployment by laboratory IT staff. Auto-update mechanism for seamless version upgrades.

### Implementation Strategy

| Phase | Scope | Timeline |
|-------|-------|----------|
| **Phase 1** | PySide6 app shell, `lims/` module integration, Windows packaging, local SQLite | 10 weeks |
| **Phase 2** | ASTM/HL7 device integration, result capture, barcode/RFID support | 10 weeks |
| **Phase 3** | Offline sync engine, QC/QA workflows, inventory management | 8 weeks |
| **Phase 4** | FHIR compatibility, NHDP integration, performance optimization, production distribution | 8 weeks |

## Consequences

### Positive
- **Desktop-native performance** — No browser overhead, instant UI response, native file system access
- **ASTM/HL7 native** — Direct instrument integration without intermediate gateways
- **Offline-first** — Full laboratory operations during internet outages with automatic reconciliation
- **lims/ module reuse** — Shared business logic means web and desktop stay in sync
- **Single approved application** — Standardized laboratory desktop across all connected laboratories
- **Barcode/RFID native** — Hardware integration for high-throughput sample tracking

### Negative
- **Windows-only** — Mac and Linux laboratories are not supported (acceptable given Iraqi context)
- **Distribution complexity** — Desktop app requires installer, updates, and per-machine configuration
- **PySide6 learning curve** — Team must develop Qt desktop expertise alongside web development
- **Offline sync complexity** — Conflict resolution for concurrent offline changes is non-trivial
- **Larger attack surface** — Desktop app requires different security model than web app (local file access, device IO)

### Risks
- **Update fragmentation** — Laboratories may delay updates, creating version fragmentation. Mitigated by: automatic background updates, forced security updates, telemetry on active versions, backward compatibility guarantee.
- **Local data loss** — If the laboratory computer crashes, local offline data could be lost. Mitigated by: periodic local backups, transaction-level SQLite WAL mode, immediate sync when connectivity is restored, cloud backup of all committed data.
- **Device driver compatibility** — Analyzer manufacturers may change protocols or require proprietary drivers. Mitigated by: adapter pattern for instrument drivers, community driver repository, abstraction layer that isolates driver changes.
- **IT support burden** — Laboratory staff may not have IT skills to troubleshoot desktop issues. Mitigated by: self-diagnosis tools, remote diagnostics capability, detailed administrator guide, dedicated laboratory support channel.

## Compliance

This ADR is consistent with:
- **Engineering Constitution Section 1** — Empowering laboratory professionals with purpose-built tools
- **Engineering Constitution Section 3** — Data integrity; offline-first with transactional safety
- **ADR-007** — Device Bridge ASTM/HL7 integration is reused for instrument connectivity
- **ADR-016** — FHIR compatibility ensures interoperability with the national EHR
- **ADR-018** — NHDP integration provides operational visibility for laboratory operations
- **ADR-019** — Ecosystem enables integration with external laboratory systems
- **ASTM E1381/E1394** — Standard specification for laboratory instrument communication
- **HL7 v2.5.1** — Health Level 7 messaging standard
- **Iraqi Laboratory Standards** — Ministry of Health laboratory information system guidelines
