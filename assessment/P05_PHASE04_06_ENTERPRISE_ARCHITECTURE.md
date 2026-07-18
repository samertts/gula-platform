# GULA PROGRAM-05: Integration, Data & Security Architecture

---

# PHASE 04: INTEGRATION ARCHITECTURE

## API Gateway Architecture

```
Internet → API Gateway (Nginx/Envoy)
              │
              ├── Rate Limit (per-tenant, per-endpoint)
              ├── Auth (JWT validation, API key check)
              ├── Route (path-based to modules)
              ├── Version Header (Accept: application/vnd.gula.v2+json)
              ├── CORS (restricted to known origins)
              └── Access Log (structured JSON)
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
  Public API    Partner API  Internal API
  /api/v1/      /api/v1/     /internal/
  FHIR R4       Webhooks     Service Mesh
  HL7 v2        AsyncAPI     (gRPC)
```

## Internal Service Communication

```
Module A ──gRPC──▶ Module B (synchronous, typed contracts)
Module A ──event──▶ Event Bus ──▶ Module C (asynchronous, via outbox)

Supported Protocols:
  - REST: External API, public endpoints, FHIR/HL7
  - gRPC: Inter-module service calls (typed, streaming)
  - Events: State change notifications (RabbitMQ/Redis Streams)
  - ASTM: Serial/TCP for analyzer communication
  - HL7 v2: MLLP for hospital/EMR integration
  - FHIR R4: RESTful healthcare interoperability
```

## Analyzer Integration Architecture

```
Device Bridge (services/device_bridge/)
├── Connectors: Serial (RS-232), TCP/IP (Port 5000)
├── Parsers: ASTM E1394, HL7 v2 ORU^R01
├── Vendor Adapters: Sysmex, Roche, Mindray, Abbott, Siemens, Generic
├── Pipeline: Buffer → Frame → Checksum → Parse → Transform → Normalize → Match → Route → Event
├── Edge Buffer: Local storage → Retry queue → Sync when online
└── Simulator: Built-in test harness for all protocols
```

## External Integration Standards

| Standard | Status | Target |
|----------|--------|--------|
| FHIR R4 | ✅ Read/Search/Validate | ➕ Create/Update/Delete/Export/Subscription |
| HL7 v2.5.1 | ✅ ORU^R01 (results) | ➕ ADT (admit), ORM (orders), MDM (documents), MFN (master files) |
| ASTM E1394/1381 | ✅ Complete | LIS2-A2 bidirectional enhancement |
| DICOM | ✅ Study/Series/Instance management | Modality worklist, MWL SCU |
| IHE Profiles | ⬜ Registered only | PIX, XDS, XCA, ATNA transactions |

## Plugin Connector Framework

Supports connectors for: ERP (SAP/Oracle), Finance, HR/Payroll, Identity Providers (Keycloak/Azure AD), Email (SMTP/SendGrid), SMS (Twilio/Vonage), Payment Gateways, Cloud Storage (S3/MinIO/GCS), AI Providers (OpenAI/Anthropic/Gemini/DeepSeek/Ollama)

---

# PHASE 05: ENTERPRISE DATA ARCHITECTURE

## Canonical Data Model (FHIR-Aligned)

| Entity | FHIR Resource | Key Fields |
|--------|--------------|------------|
| Patient | Patient | identifier, name, birthDate, gender, telecom, address, generalPractitioner |
| Practitioner | Practitioner | identifier, name, qualification, telecom |
| Organization | Organization | identifier, name, type, address, partOf |
| Encounter | Encounter | subject, period, status, type, serviceProvider, diagnosis |
| Observation | Observation | subject, code (LOINC), valueQuantity, referenceRange, interpretation |
| DiagnosticReport | DiagnosticReport | subject, result (Observation), issued, status, conclusion |
| Specimen | Specimen | subject, type, collection, receivedTime, condition |
| ServiceRequest | ServiceRequest | subject, code, requester, occurrenceTiming, status |
| Device | Device | identifier, type, status, owner, location |

## Master Data Architecture

| Registry | Engine | Technology |
|----------|--------|-----------|
| Master Patient Index | Fellegi-Sunter probabilistic + exact + fuzzy | `services/mpi/` + `health_data/mdm/` |
| Organization Registry | Exact match + hierarchy | SQLAlchemy + materialized paths |
| Facility Registry | Exact + geo-spatial | SQLAlchemy + PostGIS |
| User Registry | Identity service (canonical) | PostgreSQL + Redis cache |
| Terminology Registry | LOINC, SNOMED, ICD-10/11, UCUM | PostgreSQL + version tracking |
| Reference Data Registry | Labs, tests, panels, instruments | PostgreSQL with versioning |

## Data Tier Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Operational Tier (OLTP)                                     │
│  Module-specific schemas (schema-per-module)                  │
│  PostgreSQL 16 + pgvector for embeddings                     │
│  Optimized for transactional reads/writes                    │
├──────────────────────────────────────────────────────────────┤
│  Analytics Tier (OLAP)                                       │
│  Star schema warehouse (facts + dimensions)                  │
│  Materialized views refreshed from outbox events             │
│  Optimized for BI queries and reporting                      │
├──────────────────────────────────────────────────────────────┤
│  Event Store Tier                                            │
│  Immutable event log for every aggregate                     │
│  Enables state reconstruction and audit                      │
│  Based on outbox pattern + event sourcing                    │
├──────────────────────────────────────────────────────────────┤
│  Data Lake Tier                                              │
│  Raw data in MinIO/S3 (partitioned by tenant/date)           │
│  Parquet format for analytics                                │
│  Export pipelines from operational tier                      │
├──────────────────────────────────────────────────────────────┤
│  Vector Tier (AI)                                            │
│  pgvector for embedding storage and similarity search        │
│  Knowledge graph (SQLAlchemy-backed) for relationships       │
│  Indexed for RAG query performance                           │
└──────────────────────────────────────────────────────────────┘
```

## Data Security Architecture

| Protection | Mechanism | Scope |
|-----------|-----------|-------|
| Encryption at rest | Fernet (AES-128-CBC) | PHI fields (national_id, etc.) |
| Encryption in transit | TLS 1.3 | All network communication |
| Column-level encryption | Application-layer | Sensitive clinical data |
| Data masking | Dynamic query-based | Role-restricted PHI display |
| Anonymization | Statistical | Research datasets |
| Pseudonymization | Token mapping | De-identified analytics |
| Backup encryption | AES-256 | All backup archives |
| Key rotation | Scheduled + emergency | HMAC + encryption keys |

## Data Lifecycle

```
Create → Validate → Approve → Activate → Update → Archive → Retain → Purge
                    ↓                                               ↓
              Retention policy                                After retention
              (per data class)                                period expires
              H: 7yr clinical
              M: 3yr operational
              L: 1yr logs
```

## Data Governance Architecture

- **Data Classification:** 5 levels (public, internal, confidential, restricted, top_secret)
- **Data Ownership:** Each domain owns its data; governance oversees cross-domain policies
- **Retention Policies:** Per data class with automated enforcement daemon
- **Quality Rules:** Declarative validation framework (not scattered service code)
- **Lineage Tracking:** Event-sourced change history for every aggregate
- **Compliance Reporting:** Automated ISO 15189, HIPAA, national regulation reports

## Scalability Strategy

| Scale Level | Architecture |
|-------------|-------------|
| Single Lab (~100K patients) | Single PostgreSQL + Redis; all modules co-located |
| Hospital (~1M patients) | Read replicas + connection pooling + caching |
| Directorate (~10M patients) | Schema-per-tenant + read replicas + sharded audit |
| Ministry (~50M patients) | Multi-region PostgreSQL + patroni HA + geographic sharding |
| National (~100M+) | Cross-region active-active + CQRS + event sourcing + data lake |

---

# PHASE 06: ENTERPRISE SECURITY ARCHITECTURE

## Zero Trust Architecture

```
Every Request:
  ├── Verify Identity (JWT + MFA + device trust)
  ├── Verify Authorization (RBAC + ABAC + consent)
  ├── Verify Device (trust score, fingerprint)
  ├── Verify Location (geo-fence, IP reputation)
  ├── Verify Risk Score (behavioral analytics)
  ├── Verify Session (not revoked, not expired)
  └── Audit (immutable log of decision)
```

## Identity Architecture

| Identity Type | Source | Attributes |
|--------------|--------|-----------|
| Citizen | National ID / SNDHS | National ID, health ID, biometrics |
| Healthcare Worker | National registry | License, credentials, facility affiliation |
| Organization | National registry | License type, directorate, hierarchy |
| Facility | National registry | Type, location, capabilities, accreditation |
| Service/API | API key + JWT | Scopes, rate limits, tenant |
| AI Agent | Service account + JWT | Agent type, permissions, tool access |
| Analyzer/Device | Device certificate | Serial number, model, lab, firmware |

## Authentication Architecture

| Method | Level | Use Case |
|--------|-------|----------|
| Passwordless (Passkeys/FIDO2) | High | Healthcare workers, government users |
| MFA (TOTP + WebAuthn) | High | Admin roles, PHI access |
| OTP (SMS/Email) | Medium | Password reset, step-up auth |
| SAML 2.0 / OpenID Connect | Enterprise | SSO with government/national identity |
| API Keys (gula_*) | Service | Machine-to-machine, analyzers |
| Biometric | High | Clinical workstation unlock |

## Authorization Architecture

```
┌──────────────────────────────────────────────┐
│  Policy Engine                                │
│                                               │
│  RBAC: 9 roles × 13 base permissions          │
│  ABAC: Context-aware (patient, lab, time,     │
│        location, device, risk)                │
│  Consent: Patient-gated access (4-rule eval)  │
│  Break Glass: Emergency override with audit   │
│  Delegation: Temporary privilege transfer     │
│  Purpose of Use: Treatment, Payment, Ops, etc │
└──────────────────────────────────────────────┘
```

## Secrets Management

```
Environment Variables ──▶ HashiCorp Vault (production)
                              │
                              ├── Dynamic DB credentials (auto-rotated)
                              ├── API keys for AI providers
                              ├── JWT signing keys (auto-rotated)
                              ├── TLS certificates (auto-renewed)
                              └── Encryption keys (HSM-backed)
```

## Network Security Architecture

```
DMZ (Public)
  └── API Gateway (Nginx, rate-limited, WAF-enabled)
        │
        ├── mTLS ──▶ Application Tier
        │                ├── Backend API (FastAPI workers)
        │                ├── Device Bridge (analyzer connections)
        │                └── AI Gateway (LLM providers)
        │
        ├── mTLS ──▶ Data Tier
        │                ├── PostgreSQL (Patroni HA)
        │                ├── Redis Cluster
        │                └── RabbitMQ
        │
        └── mTLS ──▶ Observability Tier
                     ├── Prometheus
                     ├── Grafana
                     └── Alertmanager
```

## Security Monitoring & Incident Response

**Detection:** Wazuh SIEM + Snort IDS + fail2ban + behavioral analytics + AI anomaly detection

**Response:** Automated (circuit breaker, rate limiting, IP blocking) + Manual (runbook-driven)

**Recovery:** Self-healing (auto-repair engine) + Kill switch (traffic block) + DR failover

## Compliance Architecture

| Standard | Status | Target |
|----------|--------|--------|
| ISO 27001 | PENDING | Certification Q4 2026 |
| ISO 15189 | PENDING (self-attested) | Formal certification Q1 2027 |
| ISO 22301 (BC) | PLANNED | Business continuity certification |
| OWASP ASVS L2 | PARTIAL | Full compliance Q4 2026 |
| NIST CSF | PARTIAL | Target profile alignment |
| Iraqi National Standards | COMPLIANT | SNDHS-lite deployed |

## P0 Security Remediation (from P04 Gap Analysis)

| # | Action | Timeline |
|---|--------|----------|
| 1 | Separate NID_HMAC_KEY from ENCRYPTION_KEY | Week 1 |
| 2 | Add SAML XML signature verification | Week 1-2 |
| 3 | Create incident response plan | Week 3-4 |
| 4 | Add password strength validation | Week 2-3 |
| 5 | Add CSRF protection middleware | Week 3-4 |
| 6 | Add network segmentation | Month 2 |
| 7 | Add mTLS between services | Month 2-3 |
