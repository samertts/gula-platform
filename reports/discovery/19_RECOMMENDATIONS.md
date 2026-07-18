# GULA Platform — Recommendations
**Date:** 2026-07-17

---

## Classification Key
| Priority | Definition | Timeline |
|----------|-----------|----------|
| **CRITICAL** | Immediate action required | Within 1 week |
| **HIGH** | Must address before next release | Within 1 month |
| **MEDIUM** | Should address within quarter | Within 3 months |
| **LOW** | Nice to have | Within 6 months |
| **FUTURE** | Long-term strategic | Beyond 6 months |

---

## CRITICAL Recommendations

### C01 — Eliminate Firebase Security Bypass
- **Problem**: frontend-v2 writes directly to Cloud Firestore, bypassing all backend security controls (RBAC, ABAC, audit logging, rate limiting, encryption).
- **Evidence**: frontend-v2 uses Firebase SDK; backend has no visibility into Firestore reads/writes.
- **Impact**: Patient data can be accessed without audit trail, tenant isolation, or encryption.
- **Risk**: Score 25/25 (Catastrophic).
- **Dependencies**: frontend-v2 architecture.
- **Estimated Effort**: 2-3 months (full migration) or 2 weeks (Firestore security rules lockdown).
- **Recommended Solution**: Option A (preferred): Migrate all Firestore data access to backend API via tRPC/FHIR. Option B (immediate fix): Lock down Firestore security rules to admin-only; all client reads via backend proxy.
- **Potential Side Effects**: Frontend rewrite effort; temporary feature regression.
- **Success Criteria**: No Firestore client reads without backend audit trail.

### C02 — Implement Automated Backup Restore Testing
- **Problem**: Backups are configured but there is zero evidence of automated restore testing.
- **Evidence**: docker-compose.full.yml has backup-cron; no restore test script found.
- **Impact**: In a disaster, backups may be corrupt or incomplete.
- **Risk**: Score 20/25 (Catastrophic).
- **Estimated Effort**: 1 week.
- **Recommended Solution**: Add `scripts/test_restore.sh` that: starts clean PG, restores latest backup, runs integrity checks, reports success/failure. Integrate into weekly CI.
- **Success Criteria**: Restore verified within SLA (RPO < 5 min, RTO < 5 min).

### C03 — Deploy PostgreSQL with High Availability
- **Problem**: MVP docker-compose.yml has a single PostgreSQL instance. No failover, no replication.
- **Evidence**: docker-compose.yml defines one postgres:16-alpine service.
- **Impact**: Any PostgreSQL failure causes complete platform outage.
- **Risk**: Score 15/25 (Critical).
- **Estimated Effort**: 2-3 weeks.
- **Recommended Solution**: Deploy from docker-compose.full.yml with Patroni HA (primary + 2 replicas + PgBouncer). Alternatively, use managed PostgreSQL (DO Managed DB or RDS).
- **Success Criteria**: Automated failover with < 30s downtime.

### C04 — Remove External AI Providers or Update Executive Orders
- **Problem**: Executive Orders 3 & 4 mandate local Ollama-only AI, but Gemini and Groq integrations exist in production code.
- **Evidence**: `routes/ai.py` uses `google.generativeai` and Groq API; `gateways/google_ai.py` exists.
- **Risk**: Score 20/25 (Critical regulatory non-compliance).
- **Estimated Effort**: 1-2 days (remove) or 1 week (update EOs + add guardrails).
- **Recommended Solution**: Either: (a) Remove Gemini/Groq integrations to comply with EOs, or (b) Formally update EOs to allow external providers and add privacy guardrails.
- **Success Criteria**: AI provider matches documented policy.

---

## HIGH Recommendations

### H01 — Add Integration Tests for Critical Routes (35% → 80%)
- **Problem**: Only 35% of route modules have tests. ehr.py (73KB), compliance.py (47KB), and clinical.py (41KB) are essentially untested.
- **Estimated Effort**: 4-6 weeks.
- **Priority**: HIGH.

### H02 — Add Service Layer Tests (30% → 80%)
- **Problem**: Only 30% of service modules have tests. Core services (interpretation, clinical_service, ehr_service) under-tested.
- **Estimated Effort**: 3-4 weeks.
- **Priority**: HIGH.

### H03 — Create Staging Environment
- **Problem**: No staging environment exists. Changes go from dev → production with no pre-production validation.
- **Estimated Effort**: 2-3 weeks.
- **Priority**: HIGH.

### H04 — Migrate JWT from HS256 to RS256
- **Problem**: Symmetric key (HS256) requires secret sharing across services. No key rotation possible.
- **Estimated Effort**: 1 week.
- **Priority**: HIGH.

### H05 — Implement Secrets Rotation Pipeline
- **Problem**: No automated rotation for SECRET_KEY, ENCRYPTION_KEY, NID_HMAC_KEY, etc.
- **Estimated Effort**: 2 weeks.
- **Priority**: HIGH.

### H06 — Add Edge/Interop Tests (0% → 70%)
- **Problem**: Zero test coverage for edge platform and interoperability components.
- **Estimated Effort**: 2-3 weeks.
- **Priority**: HIGH.

### H07 — Stabilize National Platform Schema
- **Problem**: 17 migrations added on 2026-07-16 with 200+ tables and no corresponding routes. Schema may drift.
- **Estimated Effort**: 2-4 weeks to either implement routes or remove schema.
- **Priority**: HIGH.

### H08 — Resolve Duplicate AI Engine
- **Problem**: Two AI engines exist (services/ai/main.py for Ollama-only; routes/ai.py for multi-provider).
- **Estimated Effort**: 1 week.
- **Priority**: HIGH.

---

## MEDIUM Recommendations

### M01 — Split Monster Route Files
- **Problem**: ehr.py (73KB), compliance.py (47KB), clinical.py (41KB) are too large.
- **Estimated Effort**: 2 weeks.

### M02 — Add Baseline Load Tests
- **Problem**: k6 scripts exist but no baseline results captured.
- **Estimated Effort**: 1 week.

### M03 — Add Synthetic Monitoring
- **Problem**: No synthetic user monitoring (only health endpoints).
- **Estimated Effort**: 1 week.

### M04 — Populate Clinical Terminology Data
- **Problem**: LOINC, SNOMED CT, ICD-10/11 models exist but tables are empty.
- **Estimated Effort**: 2 weeks.

### M05 — Implement or Remove Microservice Stubs
- **Problem**: 6 of 9 microservices are stubs with 0 tests.
- **Estimated Effort**: 2 weeks to remove; 3 months to implement properly.

### M06 — Implement HL7 v2.x Beyond ASTM
- **Problem**: Only ASTM protocol is supported for device integration.
- **Estimated Effort**: 1 month.

### M07 — Add Feature Flag UI
- **Problem**: Feature flags are DB-only; no admin UI to toggle.
- **Estimated Effort**: 2 weeks.

### M08 — Update Documentation to Match Code
- **Problem**: CLAUDE.md claims 36 routes / 17 models; actual is 53+/60+.
- **Estimated Effort**: 1 week.

---

## LOW Recommendations

### L01 — Remove services/shared (deprecated bridge)
- **Effort**: 1 day.

### L02 — Fix MySQL reference in INFRASTRUCTURE_GUIDE.md
- **Effort**: 1 hour.

### L03 — Add Arabic user manual
- **Effort**: 2 weeks.

### L04 — Add on-premise deployment guide
- **Effort**: 3 days.

### L05 — Align version tags (config.py vs CHANGELOG)
- **Effort**: 1 day.

---

## FUTURE Recommendations

### F01 — Expand FHIR Coverage (6 → 100+ resources)
- **Problem**: Only 6 FHIR resource types implemented.
- **Strategic Value**: Interoperability with national and international systems.

### F02 — Implement Vector Database for RAG
- **Problem**: No vector DB means AI cannot reference documents or perform semantic search.
- **Strategic Value**: AI quality improvement.

### F03 — Internationalization Framework
- **Problem**: Arabic-only limits market expansion.
- **Strategic Value**: MENA market expansion.

### F04 — Implement DICOM Server
- **Problem**: Radiology schema exists but no DICOM image storage.
- **Strategic Value**: Complete radiology workflow.

### F05 — Full HL7 v2.x Interface Engine
- **Problem**: Only ASTM protocol; no ADT, ORM, ORU, MFN, SIU support.
- **Strategic Value**: Hospital system integration.

### F06 — Obtain ISO 15189 and ISO 27001 Certification
- **Problem**: No formal certification for medical lab quality or information security.
- **Strategic Value**: Government procurement requirement.

### F07 — Implement Full Clinical Decision Support
- **Problem**: CDS tables exist but no executing code.
- **Strategic Value**: Clinical safety.

---

## Summary

| Priority | Count | Key Areas |
|----------|-------|-----------|
| CRITICAL | 4 | Firebase, backup restore, PG HA, AI compliance |
| HIGH | 8 | Test coverage, staging, JWT, secrets rotation, edge tests, schema stability |
| MEDIUM | 8 | File splitting, load tests, monitoring, terminology, microservices, HL7 |
| LOW | 5 | Cleanup, docs, user manual |
| FUTURE | 7 | FHIR, RAG, i18n, DICOM, HL7, certification, CDS |
| **Total** | **32** | |
