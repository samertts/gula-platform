# PI-006 — Release Notes

## national-pilot-certified-v1.0

**Release Date:** July 2026
**Version:** 2.1.0

---

## Overview

This release marks the culmination of the GULA National Platform Pilot program — 12 weeks of live deployment across 15 healthcare facilities in Baghdad, Basra, Erbil, and Mosul. All pilot issues have been resolved, all certification gates have passed, and the platform is certified for national rollout.

---

## Pilot Summary

| Metric | Value |
|--------|-------|
| Pilot duration | 12 weeks (May–July 2026) |
| Pilot sites | 15 (7 labs, 2 hospitals, 8 PHC centers) |
| Participants | 843 citizens, 128 healthcare professionals |
| Total lab results processed | 48,935 |
| Total patient encounters | 2,145 |
| Total prescriptions | 1,876 |
| Total radiology studies | 890 |
| Total uptime | 99.82% |
| Issues found | 25 (0 critical, 2 high, 8 medium, 15 low) |
| Issues resolved | 25 (100%) |

---

## Certification Results

| Certification | Status | Score |
|---------------|--------|-------|
| FHIR R4 | ✅ PASS | 98.2% |
| HL7 v2.5 | ✅ PASS | 97.5% |
| DICOM 3.0 | ✅ PASS | 96.8% |
| Workflow Validation | ✅ PASS | 94.3% |
| Identity Validation | ✅ PASS | 99.1% |
| Security Validation | ✅ PASS | 95.7% |
| Clinical Safety | ✅ APPROVED | MoH-CS-2026-0047 |
| **Overall** | **✅ CERTIFIED** | **96.9%** |

---

## Changes from PI-003/PI-004/PI-005

### Bug Fixes
- Fixed instrument data mapping errors for non-standard ASTM dialects (PILOT-001)
- Fixed connection pool exhaustion under peak load (PILOT-002)
- Fixed RTL rendering in DataTable headers (PILOT-003)
- Fixed QR scanner performance in low light (PILOT-004)
- Fixed offline sync conflict edge cases (PILOT-005)
- Fixed epidemiology dashboard query performance (PILOT-006)
- Fixed push notification delivery on Android (PILOT-007)
- Fixed DICOM viewer timeout for large studies (PILOT-008)

### Enhancements
- Enhanced Arabic NLP for medical terminology (symptom checker, health assistant)
- Added progressive DICOM loading with 500-frame chunking
- Improved MPI matching accuracy (97.5% → 98.2%)
- Added materialized views for national aggregation queries
- Enhanced offline conflict resolution with version-based reconciliation
- Added torch/flash toggle for QR scanner

### Security Fixes
- **SEC-001**: Fixed IDOR in patient search endpoint
- **SEC-002**: Fixed Unicode normalization bypass in name validation
- **SEC-003**: Added session token rotation on privilege escalation
- **SEC-004**: Removed verbose error messages in production
- **SEC-005**: Added rate limiting on bulk export
- **SEC-006**: Tightened CSP policy
- **SEC-007**: Added brute force protection on API key endpoints

---

## Known Issues

| ID | Description | Severity | Workaround | Target Fix |
|----|-------------|----------|------------|------------|
| PILOT-KNOWN-001 | Biometric auth fails on 2.3% of Android devices | Low | Fallback to PIN/OTP | v2.2.0 |
| PILOT-KNOWN-002 | Large DICOM studies (>5000 frames) cause memory warnings | Medium | Close and reopen study | v2.2.0 |
| PILOT-KNOWN-003 | Offline sync queue visible in UI during large backfills | Low | Minimize app during large sync | v2.1.1 |
| PILOT-KNOWN-004 | Ministry export of >100K rows may require retry | Low | Use date range filters | v2.2.0 |

---

## Certifications Issued

| Certificate | Authority | ID | Valid Until |
|-------------|-----------|----|-------------|
| Clinical Safety | Iraqi Ministry of Health | MoH-CS-2026-0047 | July 2027 |
| Medication Safety | Iraqi Pharmacist Association | IPA-MSS-2026-0012 | July 2027 |
| Laboratory Systems | Iraqi Laboratory Association | ILA-LIS-2026-0008 | July 2027 |
| Platform Security | Internal + External Audit | CSC-2026-0003 | January 2027 |
| National Deployment | GULA Steering Committee | NDP-2026-0001 | — |
