# Constitution Validation Report

**PROGRAM-01A PHASE-01** | GULA Platform
**Date:** 2026-07-18 | **Status:** COMPLETE

## Authority Hierarchy (Validated)

| Rank | Document | Version | Date | Status |
|------|----------|---------|------|--------|
| 1 | PLATFORM-CONSTITUTION.md | v1.0.0 | 2026-07-16 | FROZEN |
| 2 | ENGINEERING_CONSTITUTION.md | v1.0.0 | 2026-07-17 | ADOPTED |
| 3 | digital_dna.md | v1.0 | — | RATIFIED |
| 4 | platform_identity.md | v1.0 | — | RATIFIED |
| 5 | NATIONAL-TRUST-PLATFORM.md | v1.0.0 | 2026-07-16 | FROZEN |
| — | DIGITAL-CONSTITUTION.md | v1.0.0 | 2026-07-08 | SUPERSEDED |
| — | CLAUDE.md | — | — | OPERATIONAL (day-to-day) |

## Contradictions Found

### C1. Coverage Target Conflict (CRITICAL)
| Source | Target |
|--------|--------|
| Platform Constitution Q1 | ≥95% overall |
| Digital Constitution §6.2 | 70% overall, 90%+ in security/models/integration |
| TESTING.md Gate C | 54% actual coverage |

### C2. UUID PK Mandate vs Integer PKs (CRITICAL)
| Source | Mandate |
|--------|---------|
| Engineering Constitution §2.4 | "PostgreSQL 16 with UUID primary keys" |
| Code reality | Most models use Integer/BigInteger PKs; only some use UUID |

### C3. Architecture Layer Naming (MAJOR)
| Source | Layer naming |
|--------|-------------|
| CLAUDE.md | routes → services → models |
| Platform Constitution | Routes → Services → Domain → Infrastructure |
| Engineering Constitution §5 | Routes → Services → Domain → Infrastructure (detailed rules) |

### C4. Version Mismatch (MINOR)
| Source | Reports |
|--------|---------|
| config.py (CLAUDE.md) | 2.1.0 |
| pyproject.toml | 2.2.0 |

### C5. FHIR Mandate Ambiguity (MAJOR)
| Source | Stance |
|--------|--------|
| Engineering Constitution §14.1 | "All clinical data exchange… via FHIR R4" |
| Platform Constitution §3.3 | FHIR content-type on every endpoint |
| routes/ | FHIR implemented as separate route (`/fhir/`), not content-type on all |

### C6. mTLS Mandate vs HTTP Comms (CRITICAL)
| Source | Mandate |
|--------|---------|
| Platform Constitution §4.3 | "All inter-service communication MUST use mutual TLS" |
| docker-compose.yml | device-bridge talks HTTP to gula-backend on port 8000 |

### C7. SBOM Mandate vs No SBOM in CI (MAJOR)
| Source | Mandate |
|--------|---------|
| Platform Constitution §4.6 | "SBOM generated on every build" |
| .github/workflows/ci.yml | No SBOM generation step |

### C8. Duplicate Files (MINOR)
| Path 1 | Path 2 |
|--------|--------|
| ENGINEERING_CONSTITUTION.md | engineering_constitution.md (same dir) |
| quality_gates.md | QUALITY-GATES.md |

### C9. DIGITAL-CONSTITUTION.md Status (MAJOR)
- Dated 2026-07-08, superseded by Platform Constitution 2026-07-16
- Claims authority derivation from CLAUDE.md
- Contains 7 Articles with internal standards that may conflict with Platform Constitution
- Explicitly supersedes 'prior README and local docs' — this needs formal deprecation

### C10. No README per Module (MAJOR)
Platform Constitution Q5 mandates: "No module without documentation — README.md for every package/module"
- Many backend modules lack README files

### C11. Circular Dep Check Missing from CI (MAJOR)
Platform Constitution Q5 mandates: "Circular dependencies — 0"
- No automated circular dependency check in current CI pipeline

### C12. Failed Tests Contradiction (MAJOR)
- TESTING.md reports 268 test errors and 3 test failures
- Quality Gate Q12 mandates: "Failed tests — 0"

### C13. Retention Policy Enforcement Missing (MAJOR)
- National Trust Platform §3.10 mandates: clinical records 25y, lab results 10y, audit logs 7y
- No automated enforcement mechanism exists

## Gaps Found

### G1. No ADR for Layer Restructuring
Transition from CLAUDE.md 3-layer (routes→services→models) to Constitutional 4-layer (routes→services→domain→infrastructure) has no ADR.

### G2. No ADR for UUID Migration
Platform/Engineering Constitution mandates UUID PKs but migration path is undocumented.

### G3. Constitution Enforcer Gaps
Existing `scripts/constitution_enforcer.py` (20 rules, 54K lines):
- Lacks SBOM check
- Lacks migration policy check
- Lacks naming convention check
- References `ARCHITECTURE_GUARDIAN` script that may not exist
- Not integrated into CI pipeline

### G4. No ADR for mTLS
The decision to NOT use mTLS for inter-service comms is undocumented.

### G5. No ADR for FHIR Strategy
Decision to implement FHIR as separate route vs content-type-on-every-endpoint is undocumented.

### G6. No ADR for SBOM
Decision to not generate SBOM in CI is undocumented.

## Recommendations

1. **Fix C1**: Align all documents to single coverage target (recommend: 70% overall, 90% critical modules)
2. **Fix C2**: Create migration to UUID PKs or file ADR to keep Integer PKs
3. **Fix C3**: Create ADR documenting the 4-layer architecture transition
4. **Fix C4**: Align version to single source (recommend: config.py as source of truth)
5. **Fix C5**: File ADR documenting FHIR deployment model (separate route vs content-type)
6. **Fix C6**: File ADR documenting why mTLS is not used in current deployment
7. **Fix C7**: Add SBOM generation to CI pipeline
8. **Fix C8**: Deduplicate ENGINEERING_CONSTITUTION.md files
9. **Fix C9**: Formally deprecate DIGITAL-CONSTITUTION.md with a note
10. **Fix C10**: Add README.md to all backend modules
11. **Fix C11**: Add circular dependency check to CI
12. **Fix C12**: Fix or document failing tests
13. **Fix C13**: Implement automated retention policy enforcement
14. **Fix G3**: Extend constitution_enforcer.py or adopt architecture_compliance_engine.py

## Remediation Priority
- IMMEDIATE (P0): C1, C2, C6, C11
- SHORT-TERM (P1): C3, C5, C7, C10, C12
- MEDIUM (P2): C4, C8, C9, C13, G3
- LONG-TERM (P3): G1, G2, G4, G5, G6

---
*Report generated by PROGRAM-01A PHASE-01 of the GULA Foundation Validation & Hardening program.*
