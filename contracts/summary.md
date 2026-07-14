# GULA Platform — Contract Freeze Summary

**Contract Tag:** `integration-contracts-v1.0`
**Version:** 2.1.0
**Freeze Date:** 2026-07-14
**Status:** ✅ FROZEN

---

## What Was Frozen

The GULA Platform **Foundation v1.0** — all public contracts between the platform and external consumers. These contracts will not change without a version bump, migration window, and stakeholder notification.

### Frozen Artifacts

| Artifact | File | Status |
|---|---|---|
| Integration Guide | `contracts/INTEGRATION_GUIDE.md` | ✅ Frozen |
| Changelog | `contracts/CHANGELOG.md` | ✅ Frozen |
| Architecture Diagrams | `contracts/diagrams/architecture.md` | ✅ Frozen |
| Sequence Diagrams | `contracts/diagrams/sequence.md` | ✅ Frozen |
| ADRs | `contracts/ADR.md` (10 records) | ✅ Frozen |
| SBOM | `contracts/SBOM.md` | ✅ Frozen |
| DTO Catalog | `contracts/dto/catalog.json` | ✅ Frozen |
| Event Catalog | `contracts/events/catalog.json` | ✅ Frozen |
| FHIR CapabilityStatement | `contracts/fhir/capability-statement.json` | ✅ Frozen |
| FHIR Profiles | `contracts/fhir/profiles.json` (8 profiles) | ✅ Frozen |
| HL7 Protocol | `contracts/hl7/protocol.json` | ✅ Frozen |
| ASTM Protocol | `contracts/astm/protocol.json` | ✅ Frozen |
| Python SDK | `contracts/sdk/python/` | ✅ Frozen |
| TypeScript SDK | `contracts/sdk/typescript/` | ✅ Frozen |

---

## Contract Catalog Counts

| Category | Count | Notes |
|---|---|---|
| REST API endpoints | 100+ | 36 route modules + health/internal |
| Domain events | 85+ | 5 domains (lims, identity, audit, financial, governance) |
| DTO schemas | 146+ | Request + response schemas with field-level constraints |
| SDK shared enums | 28 | Roles, statuses, types, tiers across both SDKs |
| FHIR R4 resource types | 10 | Patient, Practitioner, Organization, Encounter, Observation, DiagnosticReport, Specimen, ServiceRequest, Device, Bundle |
| FHIR profiles | 8 | Custom profiles with complete field mapping rules |
| FHIR identifier systems | 8 | Health number, national ID, license, org, etc. |
| FHIR code systems | 8 | LOINC, SNOMED CT, UCUM, HL7 v2/v3, custom |
| HL7 message types | 1 active / 3 planned | ORU^R01 active; ADT, ORM planned |
| HL7 segments | 10 | MSH, PID, PV1, ORC, OBR, SPM, NTE, OBX, MSA, TQ1 |
| HL7 test profiles | 16 | Chemistry panel (GLU, CRE, BUN, etc.) |
| ASTM frame types | 8 | H, P, O, R, C, L, Q, M |
| ASTM test profiles | 21 | Hematology (6) + Chemistry (15) |
| ASTM vendor adapters | 4 | Sysmex, Mindray, Roche, Generic |
| Architecture Decision Records | 10 | ADR-001 through ADR-010 |

---

## Architecture Overview

```
Internet → nginx TLS → api-gateway :8080 → FastAPI monolith → PostgreSQL 16 + Redis 7
                                                                      ↓
                                                               Outbox Worker → Webhooks
                                                                      ↓
                                                               Edge Agent ← Device Bridge
```

### Key Principles

1. **Monolith-first:** Single FastAPI deployment with prepared microservice decomposition path
2. **Arabic-first bilingual:** All APIs return bilingual responses (en/ar); PDF and UI are Arabic-first
3. **Transactional outbox:** Atomic DB writes + events; at-least-once delivery
4. **SDK-first:** Python and TypeScript SDKs generated from canonical contract definitions
5. **Defense in depth:** JWT + RBAC + ABAC + consent + break-glass + circuit breaker + rate limiting

---

## Security Posture

| Layer | Mechanism |
|---|---|
| Transport | TLS (nginx termination) |
| Authentication | JWT HS256, 60-min access, 30-day refresh, Redis revocation |
| Authorization | RBAC (9 roles × 13 permissions) + ABAC (attribute-based conditions) |
| Tenant isolation | `lab_id = current_user.lab_id` on every query |
| Data encryption | Passwords: bcrypt; National ID: HMAC-SHA256; Transport: TLS; At rest: PostgreSQL TDE |
| Consent | Time-bounded citizen consent for data access |
| Emergency access | Break-glass protocol with audit trail and lab admin notification |
| Rate limiting | Per-worker in-flight cap (200), exempts clinical writes |
| Circuit breaker | DB/Redis failure isolation → degraded mode (read-only) |
| Audit | Every mutation logged to `audit_log` table with before/after state |
| Security headers | CSP, HSTS, X-Frame-Options, Permissions-Policy, Referrer-Policy, COOP |
| CVE scanning | Trivy in CI; Safety for Python; Gitleaks for secrets |

---

## Key Decisions

| Decision | Rationale |
|---|---|
| Monolith-first | Ship fast, decompose later. Prepared microservice tree in `services/`. |
| FHIR R4 | Industry standard for healthcare interoperability. CapabilityStatement + 8 profiles. |
| HL7 v2.5.1 | Lab instrument standard. ORU^R01 for result ingestion. |
| ASTM E1394 | Primary instrument protocol for hematology/chemistry analyzers. |
| Transactional outbox | Atomic events without 2PC. At-least-once delivery with retry/DLQ. |
| HMAC patient cards | Stateless, tamper-proof QR authentication. |
| Encrypted national ID | HMAC-SHA256 at rest; never plaintext; exact-match only. |
| SDK-first | Compile-time safety for external developers. Contracts are source of truth. |

---

## Integration Points

| Integrator | Protocol | Endpoint |
|---|---|---|
| Lab Instruments | ASTM E1394 (serial/TCP) | Device Bridge → `POST /device/results` |
| Lab Instruments | HL7 v2.5.1 | `POST /lims/integration/hl7/receive` |
| HIS/EMR | HL7 v2.5.1 (planned) | ADT, ORM (P) |
| Ministry of Health | FHIR R4 | `/compliance/fhir/{resource}/{id}` |
| EMR Systems | REST API | Full set of 100+ endpoints |
| Mobile Apps | REST + SDK + Webhooks | Full set + Push notifications |
| Edge Devices | REST + Sync | `/edge/devices/register`, `/sync/*` |
| Webhook Consumers | HTTP POST | Configured per-lab |
| Citizen Portal | REST + Firebase | `/test-results/citizen/{health_id}` |

---

## Tag Information

```bash
git tag -a integration-contracts-v1.0 \
  -m "GULA Platform Integration Contracts v1.0

  Freeze Date: 2026-07-14
  Platform Version: 2.1.0
  Status: FROZEN

  This tag marks the frozen state of all public integration
  contracts for the GULA Platform Foundation v1.0.

  Included contracts:
  - 100+ REST API endpoints
  - 85+ domain events (transactional outbox)
  - 146+ DTO schemas
  - FHIR R4 (10 resource types, 8 profiles)
  - HL7 v2.5.1 (ORU^R01)
  - ASTM E1381/E1394 (8 frames, 21 test profiles)
  - Python SDK
  - TypeScript SDK
  - 10 Architecture Decision Records

  Any changes to these contracts require a version bump,
  migration window, and stakeholder notification."

# Verify
git tag -v integration-contracts-v1.0
```
