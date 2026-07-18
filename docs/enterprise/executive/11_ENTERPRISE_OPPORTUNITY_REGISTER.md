# GULA Platform — Enterprise Opportunity Register

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18
**Scoring:** Effort (1-5, 5=highest effort), Impact (1-5, 5=highest impact), ROI = Impact / Effort

---

## P0 Opportunities (Immediate, < 30 days)

| Opp ID | Category | Opportunity | Effort | Impact | ROI | Timeline | Prerequisites |
|--------|----------|-----------|-------|--------|-----|---------|-------------|
| O-001 | Legal | Add AGPL v3 LICENSE and resolve contradictory metadata | 1 | 5 | 5.0 | Week 1 | — |
| O-002 | Legal | Incorporate legal entity (Iraq or UAE) | 2 | 5 | 2.5 | Month 1 | Legal counsel |
| O-003 | Security | Lockdown Firebase to admin-only; proxy through backend API | 2 | 5 | 2.5 | 2 weeks | Backend route audit |
| O-004 | Infrastructure | Implement automated backup restore testing | 1 | 4 | 4.0 | Week 1 | Existing backup scripts |
| O-005 | Compliance | Remove or gate external AI provider calls (Gemini, Groq, OpenAI) | 1 | 4 | 4.0 | Week 1 | Code audit of all AI calls |
| O-006 | Business | Start Enterprise Edition presales | 1 | 5 | 5.0 | Immediate | Legal entity + license |
| O-007 | Quality | Fix 268 test fixture errors to restore CI green status | 2 | 3 | 1.5 | Week 2 | Test infrastructure |
| O-008 | DevOps | Unify version to single source (config.py as canonical) | 1 | 3 | 3.0 | Week 1 | — |

---

## P1 Opportunities (Short-term, 30-90 days)

| Opp ID | Category | Opportunity | Effort | Impact | ROI | Timeline | Prerequisites |
|--------|----------|-----------|-------|--------|-----|---------|-------------|
| O-009 | Infrastructure | Deploy PostgreSQL HA with Patroni + PgBouncer | 3 | 5 | 1.7 | 2-3 weeks | docker-compose.full.yml config |
| O-010 | Infrastructure | Create staging environment mirroring production | 3 | 4 | 1.3 | 3-4 weeks | K8s overlay for staging |
| O-011 | AI | Implement AI Gateway for unified AI operations | 4 | 4 | 1.0 | Month 2-3 | Architecture approval |
| O-012 | AI | Expand clinical interpretation to 50+ test types | 3 | 4 | 1.3 | Month 2-3 | Clinical SME input |
| O-013 | AI | Deploy pgvector for persistent AI embeddings / RAG | 2 | 4 | 2.0 | Month 1 | PostgreSQL extension |
| O-014 | Quality | Increase route test coverage from 35% to 60% | 4 | 4 | 1.0 | Month 2-3 | Test infrastructure |
| O-015 | Quality | Increase service test coverage from 30% to 60% | 4 | 4 | 1.0 | Month 2-3 | Service refactoring |
| O-016 | Standards | Implement FHIR R4 core resources (10+ resources) | 4 | 5 | 1.25 | Month 2-3 | Existing FHIR mappers |

---

## P2 Opportunities (Medium-term, 90-180 days)

| Opp ID | Category | Opportunity | Effort | Impact | ROI | Timeline | Prerequisites |
|--------|----------|-----------|-------|--------|-----|---------|-------------|
| O-017 | Standards | Populate LOINC codes for all test catalog entries | 2 | 4 | 2.0 | Month 3-4 | Test catalog audit |
| O-018 | Standards | Populate SNOMED CT for clinical findings and procedures | 3 | 4 | 1.3 | Month 3-5 | Terminology license |
| O-019 | Security | Migrate JWT signing from HS256 to RS256 with JWKS | 3 | 4 | 1.3 | Month 3-4 | Key management infrastructure |
| O-020 | Security | Implement automated secrets rotation pipeline | 3 | 4 | 1.3 | Month 3-4 | Vault integration |
| O-021 | Security | Add CSRF protection middleware | 1 | 3 | 3.0 | Month 3 | Middleware stack approval |
| O-022 | AI | Implement RAG with medical knowledge base | 4 | 4 | 1.0 | Month 4-6 | pgvector, embedding pipeline |
| O-023 | AI | Add confidence scoring to clinical AI outputs | 3 | 3 | 1.0 | Month 4-6 | AI Gateway from Phase 1 |
| O-024 | Quality | Implement E2E testing with Playwright (10-20 workflows) | 3 | 4 | 1.3 | Month 3-5 | Test infrastructure |
| O-025 | Architecture | Split main.py (1,948 lines) into lifecycle, middleware, routing modules | 2 | 3 | 1.5 | Month 3 | Architecture review |
| O-026 | Governance | Create Architecture Review Board with meeting cadence | 1 | 4 | 4.0 | Month 3 | Stakeholder buy-in |

---

## P3 Opportunities (Long-term, 180-365 days)

| Opp ID | Category | Opportunity | Effort | Impact | ROI | Timeline | Prerequisites |
|--------|----------|-----------|-------|--------|-----|---------|-------------|
| O-027 | Healthcare | Implement HL7 v2.x ADT/ORM/ORU message support | 4 | 4 | 1.0 | Month 6-9 | HL7 parser |
| O-028 | Healthcare | Deploy DICOM server (Orthanc) for radiology imaging | 3 | 3 | 1.0 | Month 6-9 | Infrastructure planning |
| O-029 | Standards | Implement ISO 15189 compliance framework | 4 | 5 | 1.25 | Month 6-12 | Gap analysis |
| O-030 | Standards | Complete ISO 27001 certification | 4 | 4 | 1.0 | Month 6-12 | ISMS implementation |
| O-031 | Business | Open source launch on GitHub (AGPL v3) | 2 | 5 | 2.5 | Month 7 | LICENSE, docs, CLA |
| O-032 | Business | Launch connector marketplace | 4 | 4 | 1.0 | Month 9-12 | SCG infrastructure |
| O-033 | Business | Regional expansion to KSA/UAE | 5 | 5 | 1.0 | Month 9-12 | Legal entity, localization |
| O-034 | AI | Build model registry with version tracking | 3 | 3 | 1.0 | Month 6-9 | AI Gateway |
| O-035 | AI | Implement AI audit trail with immutable logging | 3 | 4 | 1.3 | Month 6-9 | AI Gateway |

---

## Strategic Opportunities (12-24 months)

| Opp ID | Category | Opportunity | Effort | Impact | ROI | Timeline | Prerequisites |
|--------|----------|-----------|-------|--------|-----|---------|-------------|
| O-036 | Business | Secure government contract (Iraqi MoH national deployment) | 5 | 5 | 1.0 | Month 12-18 | SNDHS Phase 2, MoH certification |
| O-037 | Business | Series A fundraising ($10M) | 5 | 5 | 1.0 | Month 12-18 | Revenue traction, enterprise customers |
| O-038 | Healthcare | Multi-disciplinary hospital platform productionization | 5 | 4 | 0.8 | Month 12-24 | Schema → code conversion |
| O-039 | AI | Production AI agent runtime with real LLM integration | 5 | 4 | 0.8 | Month 12-24 | SAP Phase 3 |
| O-040 | International | Country pack architecture for multi-language expansion | 4 | 4 | 1.0 | Month 18-24 | Internationalization framework |

---

## Opportunity Heat Map

| Impact \ Effort | Low (1) | Medium (2-3) | High (4-5) |
|----------------|---------|--------------|------------|
| **Very High (5)** | O-001 License | O-002 Legal entity | O-009 PG HA, O-027 HL7, O-029 ISO 15189, O-036 Gov contract, O-037 Series A |
| **High (4)** | O-004 Backup testing, O-005 AI gating, O-022 RAG | O-008 Version unify, O-013 pgvector, O-017 LOINC, O-018 SNOMED, O-019 RS256, O-020 Secrets rotation | O-011 AI Gateway, O-016 FHIR, O-028 DICOM, O-030 ISO 27001, O-032 Marketplace, O-033 Regional expansion, O-040 Country packs |
| **Medium (3)** | O-021 CSRF, O-025 main.py split | O-007 Fix fixture errors, O-023 Confidence scoring, O-024 E2E tests | O-034 Model registry, O-035 AI audit trail |
| **Low (1-2)** | — | — | — |

---

## Quick Wins (Effort ≤ 2, Impact ≥ 4)

| Rank | Opp ID | Opportunity | ROI |
|------|--------|-----------|-----|
| 1 | O-001 | Add AGPL v3 LICENSE | 5.0 |
| 2 | O-006 | Start Enterprise Edition presales | 5.0 |
| 3 | O-004 | Implement automated backup restore testing | 4.0 |
| 4 | O-005 | Remove/gate external AI provider calls | 4.0 |
| 5 | O-008 | Unify version to single source | 3.0 |
| 6 | O-013 | Deploy pgvector for RAG | 2.0 |
| 7 | O-017 | Populate LOINC codes | 2.0 |
| 8 | O-021 | Add CSRF protection | 3.0 |
| 9 | O-025 | Split main.py into modules | 1.5 |
| 10 | O-002 | Incorporate legal entity | 2.5 |
