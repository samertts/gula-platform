# PI-003 — Release Notes

## national-applications-v1.0

**Release Date:** July 2026
**Version:** 2.1.0

---

## Overview

This is the inaugural national release of the GULA National Applications Platform — 7 healthcare applications serving the Iraqi Ministry of Health ecosystem, built on the shared `@gula/ui-platform` v1.0.0. This release delivers the complete front-end application suite for citizens, doctors, laboratories, radiology centers, pharmacies, hospitals, nurses, and the Ministry of Health.

---

## New Applications

### 1. Citizen App (@gula/citizen-app v2.1.0)
- Unified national health ID with QR-based digital patient card
- Secure login via OTP, biometric, or password
- Personal health record access (lab results, prescriptions, radiology reports)
- Appointment management with calendar integration
- Family account management (up to 10 family members)
- Offline wallet for health data access without internet
- Telemedicine consultation requests
- Consent management for data sharing
- Vaccination record tracking
- Emergency card with critical medical info
- **Platform:** PWA (Android/iOS via browser install), mobile-first

### 2. Doctor App (@gula/doctor-app v2.1.0)
- Comprehensive clinical dashboard with patient overview
- Patient search across national MPI (Master Patient Index)
- Order management (lab tests, radiology, prescriptions)
- Clinical decision support with drug interaction checking
- Digital signature for prescriptions and orders
- Voice dictation for clinical notes
- FHIR-compliant patient data access
- Patient timeline with complete clinical history
- Telemedicine integration
- Offline clinical records access
- **Platform:** Desktop/Web/Tablet/Mobile (responsive PWA)

### 3. Laboratory App (@gula/laboratory-app v2.1.0)
- Complete LIS workflow: registration → worklist → results → validation → publish
- Instrument integration via ASTM/HL7 device bridge
- Barcode/QR sample tracking
- Quality control module with Levey-Jennings charts
- Inventory management for reagents and consumables
- Results validation workflow (technician → reviewer)
- Patient result publishing with reference ranges
- Offline sample registration with background sync
- **Platform:** Desktop (PWA)

### 4. Radiology App (@gula/radiology-app v2.1.0)
- Full DICOM viewer powered by Cornerstone.js
- DICOMweb client for PACS integration (WADO + QIDO)
- Study scheduling with calendar (Gregorian + Hijri)
- Reporting workflow with structured templates
- Multi-monitor support for high-resolution diagnostic viewing
- **Platform:** Desktop

### 5. Pharmacy App (@gula/pharmacy v2.1.0)
- Prescription fulfillment with QR scanning
- Drug inventory management
- Drug interaction checking
- Patient medication history
- Insurance claim processing
- **Platform:** Desktop

### 6. Hospital Admin App (@gula/hospital-app v2.1.0)
- Bed management and occupancy tracking
- Staff scheduling and resource allocation
- Department analytics and performance dashboards
- Patient flow monitoring (admission → discharge)
- Financial operations overview
- **Platform:** Desktop (PWA)

### 7. Nurse App (@gula/nurse-app v2.1.0)
- Patient round management with offline support
- Medication administration tracking (eMAR)
- Vital signs entry with trend charts
- Task management and shift handover
- Patient QR scanning for positive identification
- **Platform:** Tablet/Mobile (PWA)

### 8. Ministry Dashboard (@gula/ministry-app v2.1.0)
- National epidemiology dashboard with disease surveillance
- Healthcare facility management (hospitals, labs, pharmacies)
- National bed occupancy and capacity monitoring
- Report generation (PDF, CSV, Excel)
- Data export with anonymization
- Ministry-level analytics and KPI tracking
- Resource allocation planning
- **Platform:** Desktop

---

## Shared Platform Releases

### @gula/ui-platform v1.0.0
- 20 reusable React components (Button, Card, Input, Select, Modal, Table, DataTable, etc.)
- 8 custom hooks (RTL, localization, media query, offline, PWA, notification, etc.)
- Full design token system (colors, typography, spacing, breakpoints)
- Arabic-first i18n with 5 languages (Arabic, English, Kurdish, Turkish, Syriac)
- Light/dark theme with CSS variable injection
- RTL/LTR layout system with automatic mirroring
- WCAG 2.1 AA accessibility compliant
- SVG icon library (60+ healthcare icons)

### @gula/update-platform v2.1.0
- Update lifecycle management (check, download, verify, install)
- Version comparison with semver and channel management
- Package integrity verification (SHA-256 checksums)
- Release manifest with phased rollout support
- Feature flag management for remote toggling
- Desktop auto-update channel (Electron/Tauri)

---

## Breaking Changes

- **Authentication token format updated:** All apps now use RS256-signed JWT tokens. Previous HMAC-signed tokens are deprecated and will be rejected after the migration window.
- **API base URL changed to:** `https://api.gula.health/api/v1/` (previous beta URLs will redirect for 90 days)
- **Patient ID format:** All patient identifiers now use the unified national format (IQNID-XXXXXXXXXXXXX). Legacy IDs are supported in read-only mode.
- **Offline storage schema:** IndexedDB schema updated to v2. Existing offline data will be migrated automatically on first launch.

---

## Migration Guide

### For End Users
1. **Citizen App:** Clear browser cache or reinstall the PWA. Your health data will sync automatically.
2. **Doctor/Lab/Nurse Apps:** The service worker will auto-update on next visit. No manual action needed.
3. **Desktop Apps:** The Update Platform will download and apply the update automatically.

### For Developers
1. Update `@gula/ui-platform` to v1.0.0 in your package.json
2. Replace `@gula/update-platform` with v2.1.0
3. Review JWT token handling (update to RS256 verification)
4. Update API endpoint URLs to new base path
5. Test offline data migration (IndexedDB v1 → v2)

---

## Known Issues

| ID | Description | Severity | Workaround | Target Fix |
|----|-------------|----------|------------|------------|
| GULA-APP-001 | Radiology DICOM viewer: memory leak on very large studies (>5000 frames) | Medium | Radiologists should close and reopen large studies | v2.2.0 |
| GULA-APP-002 | Citizen App: offline wallet QR generation fails on iOS Safari | Low | Use Chrome/install PWA | v2.1.1 |
| GULA-APP-003 | Ministry Dashboard: export > 100K rows may timeout | Medium | Use date range filters to limit data | v2.2.0 |
| GULA-APP-004 | Doctor App: drug interaction database sync delay of up to 5 minutes | Low | Pull-to-refresh for immediate sync | v2.1.1 |
| GULA-APP-005 | Nurse App: vital signs chart does not render in offline mode | Medium | Vital signs entry works offline; charts load on reconnect | v2.2.0 |

---

## Future Roadmap

### v2.2.0 (Next Quarter)
- Radiology DICOM viewer memory optimization
- Enhanced FHIR R4 support for interoperability
- Ministry Dashboard: real-time national health surveillance
- Push notification improvements (targeted campaigns)

### v2.3.0
- AI-powered clinical decision support integration
- Citizen telemedicine: video consultation with WebRTC
- Smart card / PKI authentication support
- Multi-language expansion (Kurdish Sorani + Kurmanji)

### v3.0.0
- Full FHIR R4 compliance certification
- International deployment support (multi-region)
- Advanced analytics with ML-powered predictions
- Interoperability with DZ (DHIS2) and international health systems

---

## Acknowledgments

This release represents the collaborative effort of the GULA engineering team, clinical advisors, the Iraqi Ministry of Health IT department, and pilot participants across 15 facilities in Baghdad, Basra, Erbil, and Mosul.
