# GULA Governance Framework

**Version:** 1.0  
**Status:** RATIFIED  
**Classification:** INTERNAL  

---

## 1. Governance Structure

```
                    ┌─────────────────────────┐
                    │   Executive Committee    │
                    │  (Strategic Decisions)   │
                    └───────────┬─────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
 ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
 │ Architecture    │  │  Security Board │  │   AI Board      │
 │ Board           │  │                 │  │                 │
 └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
          │                    │                     │
 ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
 │ Clinical Board  │  │  Quality Board  │  │  Release Board  │
 │                 │  │                 │  │                 │
 └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
          │                    │                     │
 ┌────────┴────────┐  ┌────────┴────────┐  ┌────────┴────────┐
 │ Data Governance │  │Technical Review │  │Product Advisory │
 │ Board           │  │Board            │  │Board            │
 └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 2. Board Responsibilities

### Architecture Board
- Review and approve all architectural decisions
- Maintain the Engineering Constitution
- Enforce architecture principles and standards
- Review ADRs for compliance
- Approve new module creation
- Resolve cross-module boundary disputes
- Review technical debt and architectural improvement roadmap
- **Meeting cadence:** Bi-weekly
- **Members:** Chief Architect, Platform Architect, Security Architect, Domain Leads

### Security Board
- Review and approve security architecture
- Conduct threat modeling for major features
- Review penetration test results
- Approve security exceptions
- Maintain security policies and standards
- Oversee vulnerability management
- Review security incidents and post-mortems
- **Meeting cadence:** Monthly
- **Members:** Chief Security Architect, Security Engineers, Infrastructure Lead

### AI Board
- Review and approve AI system designs
- Ensure AI safety and ethics compliance
- Review AI evaluation results
- Approve new model providers
- Maintain AI constitution adherence
- Review AI incidents
- **Meeting cadence:** Monthly
- **Members:** Chief AI Architect, AI Engineers, Clinical Safety Officer

### Clinical Board
- Review clinical feature designs for patient safety
- Validate clinical decision support rules
- Approve critical value thresholds
- Review clinical safety incidents
- Ensure clinical standards compliance (LOINC, SNOMED, ICD, FHIR, HL7)
- Validate AI clinical suggestions
- **Meeting cadence:** Monthly
- **Members:** Chief Healthcare Architect, Clinical Specialists, Lab Directors

### Quality Board
- Set and enforce quality standards
- Review quality metrics and trends
- Drive quality improvement initiatives
- Oversee testing strategy and coverage targets
- Review quality gate results
- **Meeting cadence:** Monthly
- **Members:** Chief Quality Officer, QA Lead, Engineering Leads

### Release Board
- Approve releases to production
- Review release readiness
- Manage release calendar
- Approve emergency releases
- Review release metrics and incidents
- **Meeting cadence:** Per release cycle
- **Members:** Release Manager, Engineering Leads, Security Lead, QA Lead

### Data Governance Board
- Define data policies and standards
- Oversee data quality
- Manage data classification
- Approve data sharing agreements
- Ensure data privacy compliance
- Oversee data retention and archiving
- **Meeting cadence:** Quarterly
- **Members:** Data Officer, Security Lead, Legal/Compliance, Clinical Lead

### Technical Review Board
- Review complex technical designs
- Ensure engineering best practices
- Review performance and scalability
- Evaluate technology choices
- **Meeting cadence:** Weekly
- **Members:** Senior Engineers, Subject Matter Experts

## 3. Decision Hierarchy

| Decision Type | Who Decides | Who Approves | Who Reviews |
|--------------|-------------|--------------|-------------|
| Strategic platform direction | Executive Committee | Executive Committee | Architecture Board |
| Architecture principles | Architecture Board | Executive Committee | All boards |
| Module creation/removal | Architecture Board | Executive Committee | - |
| API contract changes | Engineering Lead | Architecture Board | Security Board |
| Database schema changes | Data Lead | Architecture Board | Security Board |
| Security policy changes | Security Board | Architecture Board | - |
| AI model approval | AI Board | Security Board | Clinical Board |
| Clinical feature approval | Clinical Board | Architecture Board | Security Board |
| Release approval | Release Board | Quality Board | Security Board |
| Emergency hotfix | On-call Engineer | Engineering Lead | Post-hoc review |
| Technology adoption | Technical Review Board | Architecture Board | - |

## 4. Change Management Process

```
1. Request ──→ 2. Triage ──→ 3. Impact Assessment
                │
                ├── Minor → Direct Implementation
                ├── Moderate → Engineering Lead Approval
                └── Major → Board Review + ADR
                                │
                    4. Design Review ──→ 5. Security Review
                                │
                    6. Implementation ──→ 7. Quality Gates
                                │
                    8. Approval ──→ 9. Deployment
                                │
                    10. Verification ──→ 11. Documentation
```

### Change Classification
- **Minor:** Bug fixes, refactoring without API changes, test additions, documentation updates
- **Moderate:** New API endpoints, new features within existing modules, configuration changes
- **Major:** New modules, architecture changes, database schema changes, API breaking changes, security changes, AI model changes

## 5. Architecture Decision Records

Every significant architecture decision must be documented as an ADR.

### ADR Template

```markdown
# ADR-NNN: Title

**Status:** Proposed | Accepted | Deprecated | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** [Names]

## Context
[Description of the problem and context]

## Decision
[The decision made]

## Rationale
[Why this decision was made]

## Consequences
[Positive and negative consequences]

## Alternatives Considered
[Other options and why they were rejected]

## Compliance
[How compliance will be verified]

## References
[Links to related ADRs, documents, code]
```

### Current ADR Index

| ADR | Title | Status |
|-----|-------|--------|
| ADR-001 | Engineering Constitution | Active |
| ADR-002 | Monolith-First Strategy | Active |
| ADR-003 | Multi-Tenant Isolation | Active |
| ADR-004 | Skill Platform | Active |
| ADR-005 | PostgreSQL + Redis Stack | Active |
| ADR-006 | Clinical AI Integration | Active |
| ADR-007 | Device Bridge (ASTM/HL7) | Active |
| ADR-008 | Patient Card System | Active |
| ADR-009 | Self-Healing Infrastructure | Active |
| ADR-010 | SNDHS Government Integration | Active |
| ADR-011 | Notification Platform | Active |
| ADR-012 | Engineering Automation / Identity Platform | Active |
| ADR-013 | Production Platform | Active |
| ADR-014 | Observability Stack | Active |
| ADR-015 | Disaster Recovery | Active |
| ADR-016 | National EHR | Active |
| ADR-017 | National Data Platform | Active |
| ADR-018 | National Operations | Active |
| ADR-019 | National Ecosystem | Active |
| ADR-020 | Citizen Super-App | Active |
| ADR-021 | National Intelligence | Active |
| ADR-022 | Doctor Workspace | Active |
| ADR-023 | Laboratory Desktop | Active |
| ADR-024 | Platform Constitution | Active |

## 6. Review Cadence

| Review Type | Frequency | Owner |
|-------------|-----------|-------|
| Architecture Review | Bi-weekly | Architecture Board |
| Security Review | Monthly | Security Board |
| AI Review | Monthly | AI Board |
| Clinical Review | Monthly | Clinical Board |
| Quality Review | Monthly | Quality Board |
| Data Governance Review | Quarterly | Data Governance Board |
| Code Review | Per PR | Engineering Team |
| Security Code Review | Per security PR | Security Team |
| Performance Review | Per release | Engineering Team |
| Dependency Review | Per dependency addition | Engineering Team |
| Incident Post-Mortem | Per incident | On-call Team |
| Architecture Audit | Quarterly | Architecture Board |
| Security Audit | Annually | External Auditor |
| Penetration Test | Annually | External Security Team |

## 7. Escalation Path

```
Level 1: Engineering Lead (daily operational decisions)
Level 2: Architecture Board (cross-module decisions, principle interpretations)
Level 3: Executive Committee (strategic decisions, budget, timeline)

Emergency: On-call Engineer → Engineering Lead → Architecture Board Chair
```

---

*This Governance Framework is effective immediately. All boards must be established within 30 days.*
