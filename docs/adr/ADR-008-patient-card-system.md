# ADR-008: Patient Card System

**Status:** Accepted
**Date:** 2026-07-08
**Deciders:** Engineering Lead, Product Manager

## Context

Medical laboratories need to provide patients with a portable, verifiable record of their clinical history. The card must be usable offline, support Arabic text, and prevent tampering. Requirements include HMAC-signed tokens, QR code encoding, and full longitudinal history with tenant isolation.

## Decision

Implement a QR-backed digital patient card system with HMAC-signed tokens, printable Arabic-first HTML format, and server-side verification before revealing patient data.

### Design
- **Card Token:** HMAC-SHA256 signed token containing `patient_id`, `lab_id`, and expiry
- **QR Code:** Encodes the signed token for scanning
- **Format:** Arabic-first printable HTML with clinical history
- **Verification:** Token signature verified before any patient data is returned
- **History:** Full longitudinal history respecting `lab_id` tenant isolation
- **Scanning:** Token validated on scan, patient data revealed only after verification

### Routes
- `POST /v1/patient-card/generate` — Generate card with signed token
- `GET /v1/patient-card/{token}` — Verify token and return patient data
- `GET /v1/patient-card/{token}/scan` — Scan endpoint for QR readers

## Alternatives Considered

### 1. JWT-based Cards

**Pros:** Standard, widely supported, built-in expiry.
**Cons:** Larger token size, standard libraries may not be HMAC-SHA256 specific.
**Rejected because:** HMAC provides simpler, more predictable signing for the specific use case.

### 2. Smart Card / Physical Card

**Pros:** High security, offline capability.
**Cons:** Requires card readers, distribution logistics, higher cost.
**Rejected because:** QR-based digital cards are immediately usable on any smartphone.

### 3. Database-only (No Token)

**Pros:** Simplest implementation.
**Cons:** No offline verification, requires database lookup for every scan, potential for enumeration attacks.
**Rejected because:** HMAC token provides offline verifiability and prevents token tampering.

## Consequences

### Positive
- Patients receive a portable, verifiable medical record
- QR scanning works with any smartphone camera
- HMAC tokens prevent forgery and tampering
- Full clinical history available at scan time
- Arabic-first design serves the target user base

### Negative
- Token must be regenerated on data change (no automatic invalidation)
- QR code size limited by data encoded
- Scanning requires network connectivity for full data reveal

### Neutral
- HMAC key (`NID_HMAC_KEY`) managed alongside other secrets
- Cards complement, don't replace, the full digital record
- System can be extended to support additional card formats

## References
- `backend/app/routes/patient_card.py` — Patient card routes
- `backend/app/config.py` — `NID_HMAC_KEY` configuration
- `CLAUDE.md` — Security invariants (HMAC verification required)
