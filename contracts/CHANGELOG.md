# GULA Platform — Contract Freeze Changelog

**Release Date:** 2026-07-14
**Version:** 2.1.0
**Contract Tag:** `integration-contracts-v1.0`
**Status:** FROZEN — no further contract changes without version bump

---

## Version 2.1.0 — Foundation Complete & Contract Freeze

### Foundation Complete (MISSION-FINAL)

The GULA Platform foundation has reached its final frozen state. All core infrastructure, domain models, integration protocols, and public contracts are now locked. No further infrastructure development is planned — the platform is production-ready.

### Breaking Changes

**None.** v2.1.0 is a fully backward-compatible superset of all prior releases.

### New Features

#### FHIR R4 Interoperability
- **10 FHIR R4 resource types** with full CapabilityStatement
- Two endpoint families: Government Compliance (`/compliance/fhir`) and LIMS (`/lims`)
- National data layer with Patient, Practitioner, Organization, Encounter
- 8 custom FHIR profiles with complete field mapping rules
- LOINC, SNOMED CT, UCUM terminology bindings
- Full bilingual support (ar/en) with Arabic title/summary fields

#### HL7 v2.5.1 Integration
- ORU^R01 unsolicited observation result message support
- ER7 (pipe-delimited) encoding with full segment parsing
- ACK generation with AA/AE/AR codes
- Vendor profiles for Roche, Abbott, Siemens instruments
- 16 chemistry test profiles with reference ranges
- API endpoint at `POST /lims/integration/hl7/receive`
- Simulation endpoint for testing

#### ASTM E1381/E1394 Integration
- Full ASTM frame protocol (H, P, O, R, C, L, Q, M frames)
- Frame-level checksum validation (STX/ETX/checksum)
- ENQ/ACK handshake protocol for bidirectional instruments
- Device bridge parser in `services/device_bridge/` for serial/TCP transport
- Monolith parser in `backend/app/lims/integration/astm.py`
- Vendor adapters: Sysmex, Mindray, Roche, Generic
- 21+ test profiles (hematology + chemistry)
- Full data pipeline: raw bytes → NormalizedResult → persistence
- Retry queue and offline edge buffer for failed transmissions

#### Event Platform
- **Transactional outbox** with `outbox_events` table (at-least-once delivery)
- **85+ domain events** across specimen lifecycle, order lifecycle, result lifecycle, QC, identity, and audit
- Snapshot engine for aggregate state recovery
- Recovery engine with sequential/parallel/batched replay
- Dead letter queue, retry queue, replay, snapshot, versioning patterns
- 5 max attempts with exponential backoff (1s→2s→4s→8s→16s)

#### Integration Connector Framework
- Connector Registry: type-indexed, tag-indexed with health tracking
- Connector SDK: auto-generates Python client code from specs
- HTTP/REST, GraphQL, WebSocket, gRPC, DICOM connectors
- All with metrics, health checks, and auto-reconnect

#### Identity & Governance
- Identity Governance Service: full lifecycle for citizen, newborn, foreigner, resident, visitor, unknown patient
- Birth certificate, passport, visa document workflows
- Family Registry: family creation, member management, guardian linking
- Identity Merge Engine: confidence scoring, merge proposals, approval workflow
- Health Number as primary healthcare identifier
- National ID as primary legal identifier (never exposed in healthcare views)

#### Reference Services
- Master Reference Data: countries, governorates, languages, currencies, timezones, medical specialties
- Universal Identifier Service: 12 identifier types (HN, ORD, SPC, ACC, RPT, VIS, ENC, APT, INV, NTF, WF, AUD)
- National Laboratory Catalog: 29 seeded lab tests, 3 panels, 7 specimen types with LOINC mapping

#### Patient Card System
- Digital patient cards with HMAC-signed QR tokens
- Arabic-first printable HTML format
- Full longitudinal clinical history
- Token verification before data disclosure

#### Clinical AI
- Clinical interpretation analysis (`POST /ai/analyze`)
- AI suggestion engine with accept/reject workflow (`POST /ai/suggest`)
- Gemini 2.0 Flash powered chat assistant (`POST /ai/chat`)
- Safety columns for hallucination tracking and content moderation
- Google AI Studio gateway with raw HTTPS fallback

#### Edge Computing Platform
- Edge device registration with public key authentication
- Device trust scoring and lifecycle (pending/active/quarantined/revoked)
- Task submission and execution on edge devices
- Heartbeat protocol with health monitoring
- Offline result buffering and sync

#### Financial Engine (Phase A)
- Schema-only bootstrap: `fin_campaigns`, `fin_conversions`, `fin_fraud_flags`
- Feature-gated behind `ENABLE_FINANCIAL_ENGINE` (default: off)
- Insurance claims management API with full lifecycle

#### SDK & Public Contracts
- **Python SDK** (`contracts/sdk/python/`): Full client with all models and enums
- **TypeScript SDK** (`contracts/sdk/typescript/`): Full client for Node.js/browser
- **28 enums** shared across both SDKs
- **146+ DTOs** cataloged with field-level constraints
- **Event contract catalog** with full schema definitions
- **FHIR CapabilityStatement** and profile definitions
- **HL7 protocol contract** with complete message structure
- **ASTM protocol contract** with complete frame definitions

### Enhancements

#### Security Hardening
- ABAC (Attribute-Based Access Control) engine with conditions, priority rules, deny-overrides
- JWT Redis-backed blacklist for immediate token revocation
- `perm_version` claim for permission-change invalidation
- Weak-secret detection on all security-related environment variables
- Enhanced CSP, HSTS, X-Frame-Options, Permissions-Policy headers
- API documentation protected by admin JWT in production
- Break-glass emergency access protocol with audit trail

#### Performance
- Rate limiter optimized: deque-based sliding window (1000x improvement, 219s→0.22s for 100k checks)
- Cursor-based pagination for all list endpoints
- Adaptive concurrency halving on slow DB reads (>300ms)
- Connection pool management with auto-repair

#### Observability
- Structured JSON logging (production) vs text logging (dev)
- Sentry error tracking with FastAPI + SQLAlchemy integration
- Prometheus metrics endpoint (`GET /metrics/prom`)
- Health endpoint suite: `/health`, `/health/live`, `/health/ready`, `/health/status`, `/health/deep`, `/health/kernel`
- Health grading system (GREEN/YELLOW/RED) with alert webhooks
- Request timing middleware with per-request latency tracking

#### Developer Experience
- Enhanced FastAPI docs with bilingual descriptions
- Request ID middleware (`X-Request-ID` header)
- Idempotency key support (`Idempotency-Key` header)
- ETag support for conditional requests
- Bilingual error responses (`detail` + `detail_ar`)
- Consistent error code catalog

### Bug Fixes
- Python 3.10 `datetime.UTC` compatibility across 49 files
- `StrEnum` compatibility for Python 3.10
- Rate limiter: replaced list-based with deque-based sliding window
- Capability generator: fixed mismatched triple-quote strings
- Kernel initialization in test fixture (fixed 5 chaos-survival tests)
- Migration: resolved duplicate revision ID
- AI: removed stale `system` reference in chat fallback
- All SDK paths validated against actual backend routes

### Migration Notes

**From v1.x:** No breaking changes. See `INTEGRATION_GUIDE.md` §13 for full migration checklist.

Key actions:
1. Update client to use cursor pagination (offset-based still works but deprecated)
2. Add `Idempotency-Key` header to mutation requests
3. Add `X-Request-ID` header for request tracing
4. Subscribe to outbox events for real-time updates
5. Update error handlers for bilingual response format

### Deprecation Notices

| Deprecated | Replacement | Sunset |
|---|---|---|
| `GET /api/patients` (v1 prefix) | `GET /patients` | v3.0 |
| `POST /api/orders` (v1 prefix) | `POST /orders` | v3.0 |
| Offset-based pagination (`?page=N`) | Cursor-based (`?cursor=...`) | v2.5 |
| `GET /results?page=N` | `GET /results?cursor=...` | v2.5 |

### Quality Gates
- **1,420+ tests** passing (unit + integration + stress)
- **9 stress tests** passing under concurrent load
- **Bandit:** clean (no high/medium issues)
- **Ruff:** all checks passing
- **py_compile:** all 300+ Python files compile cleanly
- **55 new tests** covering event system, connector framework, identity services
- **CI pipeline:** syntax-gate → migration-check → smoke-test → backend-test → security-scan → build-and-push

### Contract Freeze Inventory

| Contract Artifact | Count |
|---|---|
| REST API endpoints | 100+ |
| Domain events | 85+ |
| DTO schemas | 146+ |
| FHIR R4 resources | 10 |
| FHIR profiles | 8 |
| HL7 message types | 1 active (ORU^R01), 3 planned |
| ASTM frame types | 8 |
| ASTM test profiles | 21 |
| SDK languages | 2 (Python, TypeScript) |
| SDK enums | 28 shared |
| Architecture Decision Records | 10 |

### Full Git History

```bash
$ git log --oneline v2.1.0-engineering-factory..HEAD
44d5771 feat: consolidate shared libraries, engineering kernel, AI modules, edge agent, and platform enhancements
479dc9f MISSION-FINAL: Foundation v1.0 — Complete & Frozen
156ffcf docs: update CHANGELOG with recent production validation and kernel certification
6458049 fix(kernel): certification batch — fix 7 bugs, add enable_modules flag
a5c4cbb fix(production): batch 1 — production validation & compatibility
b1d338f feat: consolidate engineering kernel, notifications, financial, and shared library features
...
```

---

*See `contracts/INTEGRATION_GUIDE.md` for complete integration documentation.*
*See `contracts/ADR.md` for architecture decision records.*
*See `contracts/SBOM.md` for software bill of materials.*
