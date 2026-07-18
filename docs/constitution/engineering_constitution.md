# GULA Engineering Constitution

**Version:** 1.0  
**Status:** RATIFIED  
**Classification:** INTERNAL  
**Effective Date:** 2026-07-18  
**Supersedes:** All previous engineering guidelines

---

## Preamble

We, the engineers of GULA, establish this Constitution as the supreme engineering charter for the platform. Every line of code, every architectural decision, every review, and every deployment shall be measured against this Constitution. No feature, no deadline, no external pressure justifies deviation from these principles.

---

## Article I: Core Principles

### Section 1: Stability First

1.1. No change shall break working production functionality.  
1.2. Every change must be validated by automated tests before merge.  
1.3. Every change must pass the full CI pipeline before deployment.  
1.4. Rollback capability must exist before every deployment.  
1.5. Database migrations must be reversible (downgrade path required).  

### Section 2: Data Integrity Above All

2.1. No change may risk patient data loss, corruption, or unauthorized access.  
2.2. All data mutations must be audited with immutable hash-chain records.  
2.3. All patient-data queries must enforce tenant isolation via `lab_id`.  
2.4. Optimistic locking must be checked on every clinical data mutation.  
2.5. Soft delete is the default; hard delete requires explicit architectural approval.  

### Section 3: Security by Default

3.1. Every endpoint requires authentication unless explicitly whitelisted.  
3.2. Every API must validate input, enforce authorization, and sanitize output.  
3.3. Secrets never appear in code, logs, or error messages.  
3.4. Encryption at rest is mandatory for all PII and clinical data.  
3.5. Rate limiting applies to all public endpoints.  

### Section 4: Privacy by Design

4.1. Patient data access follows least-privilege principle.  
4.2. Consent must be verified before data sharing with third parties.  
4.3. Audit logs must capture who accessed what data, when, and why.  
4.4. Data minimization: collect only what is necessary.  

### Section 5: Quality is Mandatory

5.1. No code is merged without passing all quality gates.  
5.2. Test coverage shall not decrease.  
5.3. Lint errors are merge blockers.  
5.4. Performance budgets must be respected.  
5.5. Documentation must accompany every feature.  

### Section 6: Backward Compatibility

6.1. Public APIs must not break existing clients without a deprecation cycle.  
6.2. API versioning is mandatory for all breaking changes.  
6.3. Database schemas must maintain forward compatibility for one release cycle.  

---

## Article II: Architecture Principles

### Section 7: Modularity

7.1. The platform shall be composed of independent, replaceable modules.  
7.2. Every module must have a well-defined contract (interface) and boundary.  
7.3. Modules communicate through stable interfaces, never through shared state.  
7.4. Circular dependencies between modules are forbidden.  

### Section 7: Clean Architecture

7.1. Dependencies point inward: Infrastructure → Interface → Application → Domain.  
7.2. Domain layer depends on nothing external (no frameworks, no databases).  
7.3. Application layer defines ports (interfaces); infrastructure layer implements adapters.  
7.4. Cross-layer communication uses interfaces, not concrete implementations.  

### Section 9: Domain-Driven Design

9.1. Module boundaries align with business domains, not technical layers.  
9.2. Every domain has a bounded context with explicit relationships.  
9.3. Ubiquitous language must be consistent across code, documentation, and conversation.  
9.4. Aggregates enforce consistency boundaries within a domain.  

### Section 10: API First

10.1. Every capability must have a well-defined API contract.  
10.2. API contracts are defined in OpenAPI 3.x before implementation begins.  
10.3. APIs are versioned and backward-compatible within a major version.  
10.4. Internal and external APIs follow the same design standards.  

### Section 11: Observability by Default

11.1. Every service must expose health, metrics, logs, and traces.  
11.2. Every request must carry a correlation ID across all services.  
11.3. Every error must be logged with sufficient context for root cause analysis.  
11.4. Alerts must be actionable and routed to the correct on-call team.  

---

## Article III: Development Principles

### Section 12: Simple Before Clever

12.1. The simplest solution that satisfies requirements is preferred.  
12.2. Premature abstraction is not permitted.  
12.3. YAGNI: You Aren't Gonna Need It — do not build for hypothetical futures.  
12.4. KISS: Keep It Simple — if the solution is not simple, the design is wrong.  

### Section 13: Composition Before Inheritance

13.1. Favor composition, delegation, and interfaces over inheritance.  
13.2. Inheritance is permitted only for framework integration and base classes.  
13.3. Deep inheritance hierarchies (depth > 3) require architecture review.  

### Section 14: Explicit Before Implicit

14.1. Dependencies must be explicit (constructor injection, not service location).  
14.2. Configuration must be explicit (environment variables, not magic constants).  
14.3. Errors must be explicit (typed exceptions, not generic failures).  

### Section 15: Immutable Before Mutable

15.1. Immutable data structures are preferred.  
15.2. Function purity (no side effects) is preferred.  
15.3. State mutation must be explicit and controlled.  

---

## Article IV: AI Development Principles

### Section 16: Human Control

16.1. AI always suggests; humans always approve clinical actions.  
16.2. AI must never autonomously modify or delete patient data.  
16.3. All AI-generated clinical content must be marked as AI-generated.  
16.4. Critical clinical decisions require explicit human validation.  

### Section 17: Safety First

17.1. Every AI component must have guardrails.  
17.2. Guardrails must include input validation, output validation, and content filtering.  
17.3. Prompt injection protection is mandatory.  
17.4. Hallucination detection must be implemented for clinical AI.  

### Section 18: Transparency

18.1. AI decisions must be explainable.  
18.2. Every AI suggestion must carry provenance (model, version, confidence).  
18.3. AI system boundaries must be documented.  

---

## Article V: Healthcare Principles

### Section 19: Patient Safety

19.1. Clinical safety trumps all other concerns.  
19.2. Critical values must always trigger alerts.  
19.3. Result validation workflow must enforce dual verification for critical results.  
19.4. Patient identity must be verified before any clinical action.  

### Section 20: Standards Compliance

20.1. All clinical data must use standard terminologies (LOINC, SNOMED CT, ICD, UCUM).  
20.2. Interoperability must follow FHIR R4, HL7 v2.x, or ASTM standards.  
20.3. Clinical decision support must follow evidence-based guidelines.  

---

## Article VI: Documentation Principles

### Section 21: Documentation First

21.1. Every feature requires documentation before or concurrent with implementation.  
21.2. ADRs must be written for every architectural decision.  
21.3. API documentation is generated from code (OpenAPI).  
21.4. Runbooks and playbooks must accompany every operational procedure.  

### Section 22: Knowledge Evolution

22.1. Every completed mission must produce new knowledge or lessons learned.  
22.2. Documentation must be updated when related code changes.  
22.3. Outdated documentation is technical debt.  

---

## Article VII: Governance

### Section 23: Review Requirements

23.1. Every code change requires peer review.  
23.2. Architectural changes require Architecture Board approval.  
23.3. Security-sensitive changes require Security Board approval.  
23.4. Clinical changes require Clinical Board approval.  

### Section 24: Decision Authority

24.1. Strategic decisions require Executive approval.  
24.2. Architecture decisions require Architecture Board approval.  
24.3. Engineering decisions require senior engineer approval.  
24.4. Emergency decisions follow documented escalation procedures.  

---

## Article VIII: Compliance

### Section 25: Engineering Compliance

25.1. All code must pass lint, type-check, and test gates.  
25.2. All dependencies must pass security and license review.  
25.3. All secrets must be managed through approved secrets infrastructure.  
25.4. All migrations must be reversible and tested.  

### Section 26: Healthcare Compliance

26.1. All patient data handling must comply with Iraqi health privacy regulations.  
26.2. Audit logs must be immutable and tamper-evident.  
26.3. Tenant isolation must prevent cross-lab data access.  

---

## Article IX: Enforcement

### Section 27: Violations

27.1. Any violation of this Constitution must be documented.  
27.2. Repeated violations require escalation to Architecture Board.  
27.3. Emergency exceptions require documented justification and retroactive review.  

### Section 28: Amendments

28.1. Amendments require 2/3 majority of the Architecture Board.  
28.2. Amendments must be documented as ADRs.  
28.3. The Constitution is reviewed annually.  

---

## Signatories

| Role | Name | Date |
|------|------|------|
| Chief Platform Architect | | 2026-07-18 |
| Chief Security Architect | | 2026-07-18 |
| Chief AI Architect | | 2026-07-18 |
| Chief Healthcare Architect | | 2026-07-18 |
| Chief Quality Officer | | 2026-07-18 |

---

*This Constitution is effective immediately upon ratification.*
