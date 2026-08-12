# GULA ENGINEERING CONSTITUTION

> **Version:** 1.0.0
> **Date:** 2026-07-17
> **Authority:** Permanent Architecture Review Board
> **Status:** ADOPTED — FROZEN
> **Supersedes:** Nothing (complements PLATFORM-CONSTITUTION.md)

## Preamble

This document is the companion to the PLATFORM-CONSTITUTION.md (v1.0.0, 2026-07-16).
Where PLATFORM-CONSTITUTION.md defines the supreme architecture, engineering,
quality, security, AI, operations, developer, and release standards, this document
provides the detailed engineering governance framework for the long-term maintainability,
security, scalability, adaptability, and evolvability of the GULA National Digital Health
Platform across decades of continuous operation.

PLATFORM-CONSTITUTION.md is the **what** — the immutable principles and mandatory
standards. This ENGINEERING CONSTITUTION is the **how** — the detailed rules, patterns,
processes, and mechanisms that bring those principles to life in every commit, every
deployment, every decision.

This document is authored and maintained by the Permanent Architecture Review Board,
comprising:

| Role | Responsibility |
|------|----------------|
| Enterprise Architects | System-wide architecture integrity, cross-domain coherence |
| Government Architects | National sovereignty, multi-jurisdictional compliance |
| Healthcare Architects | Clinical safety, healthcare domain fidelity |
| Cybersecurity Architects | Threat modeling, security governance |
| Cloud Architects | Infrastructure, deployment, scaling strategy |
| Clinical Safety Experts | Patient safety, clinical risk management |
| AI Researchers | AI governance, model safety, ethical AI |
| Platform Engineers | Engineering automation, developer experience |
| Data Architects | Data modeling, data flow, data governance |
| Legal & Compliance Advisors | Regulatory compliance, legal framework |

**Reading this document:** Each Part is self-contained. Cross-references are marked
as `→ PLATFORM-CONSTITUTION.md §X.Y` and `→ ADR-NNN`. Code blocks provide concrete
examples. Tables define precise rules and matrices. Every section ends with its
enforcement mechanism.

**Document relationship:**

```
PLATFORM-CONSTITUTION.md  ─── supreme authority (the WHAT)
        │
        └── ENGINEERING_CONSTITUTION.md  ─── detailed governance (the HOW)
                │
                ├── docs/architecture/  ─── architecture blueprints
                ├── docs/security/       ─── security standards
                ├── docs/ai/             ─── AI governance
                ├── docs/sovereign/      ─── national sovereignty
                ├── docs/trust/          ─── trust framework
                ├── docs/factory/        ─── engineering automation
                ├── docs/adr/            ─── Architecture Decision Records
                └── CLAUDE.md            ─── operational engineering handbook
```

---

## PART 1: GULA Constitution — Supreme Principles

Every future contribution to the GULA platform — whether code, configuration,
documentation, AI model, workflow, deployment, or third-party integration —
MUST obey these 12 supreme principles. These are derived from and extend the
principles in PLATFORM-CONSTITUTION.md Article I.

### Principle 1: Single Source of Truth

**Statement:** Every data element, business rule, configuration value, and
canonical definition SHALL exist in exactly one authoritative location.

**Detailed explanation:** The platform must never duplicate data definitions
across modules, services, or layers. Duplication creates drift, inconsistency,
and bugs that are difficult to detect. When two pieces of code need the same
data shape, they import it from the canonical definition. When two services
need the same business rule, they reference the rule engine or shared library.

**Concrete implications:**

| Domain | Single Source of Truth Location | What NOT to Do |
|--------|-------------------------------|----------------|
| Patient model | `backend/app/models/patient.py` (SQLAlchemy ORM) | Duplicate patient fields in route DTOs |
| Lab order state machine | `backend/app/domain/order_state.py` | Replicate state logic in frontend |
| FHIR mappings | `backend/app/fhir/mappings/` | Hardcode FHIR paths in multiple routes |
| Feature flags | `backend/app/core/feature_flags.py` per-tenant store | Environment-variable-based feature gating |
| Audit schema | `backend/app/models/audit.py` | Hand-rolled audit in services |
| Error codes | `backend/app/core/errors.py` | Inline error strings |
| Lab IDs | `labs` table (PostgreSQL) | Hardcoded lab identifiers |
| Configuration defaults | `backend/app/config.py` + `.env.example` | Duplicate defaults in Dockerfiles |
| Clinical coding systems | FHIR terminology server | Hardcoded LOINC/SNOMED/ICD codes |

**Enforcement:** Automated architecture validation (Gate Q4, Q6) detects
duplicate definitions. CI fails if the same model field is defined in more
than one place without explicit exemption.

---

### Principle 2: Immutable Core, Modular Extensions

**Statement:** The platform core — data models, auth framework, audit system,
tenant isolation, encryption, API gateway, health infrastructure, event bus,
migration framework, configuration loading, logging, connection pooling, and
middleware stack — SHALL remain stable and change only under the strictest
protocols. All new features SHALL be added as modular extensions.

**Detailed explanation:** The core represents the platform's architectural
investment. Every change to core components risks regression across the entire
system. Therefore, core components follow a "modify rarely, modify carefully"
protocol. New functionality is always added as extensions — modules, plugins,
connectors, country packs, language packs, AI skills, or workflow packs —
that sit on top of the stable core and interface through versioned contracts.

**Concrete implications:**

- Core version is the platform MAJOR version
- Core changes require 3/4 Architecture Review Board supermajority
- Core changes require minimum 2-week review period
- Core changes require full regression suite (all tests, all quality gates)
- Extensions never modify core files
- Extensions import from core; core never imports from extensions
- Extension API surface is versioned and documented

**Enforcement:** Import-linter rules in CI prevent extensions from being
imported by core. Module boundary enforcement via automated dependency
graph validation.

---

### Principle 3: Patient Safety First

**Statement:** No change — whether code, configuration, AI model, workflow,
or deployment — may risk patient harm, data loss, or compromise of clinical
integrity.

**Detailed explanation:** Patient safety is the highest value in the GULA
platform. It transcends all technical considerations. A feature that improves
performance but adds risk to patient data is rejected. A deployment that
offers new capabilities but risks clinical workflow disruption is blocked.
Every change is evaluated through the lens of "what if this fails during a
critical patient event?"

**Concrete implications:**

| Area | Safety Rule | Verification |
|------|-------------|--------------|
| Clinical data | Never silently drop or transform clinical values | Data integrity tests |
| Lab results | Never lose a result, never misattribute a result | Result chain-of-custody |
| Patient identity | Never merge patients without human verification | MPI merge protocol |
| Critical alerts | Never suppress or delay critical value alerts | Alert delivery verification |
| Offline queue | Never lose queued data during sync failures | Sync integrity tests |
| AI recommendations | Never override clinician decision | Human-in-the-loop gate |
| Downtime | Never prevent emergency access during downtime | Emergency access testing |
| Deployments | Never deploy during active patient processing | Deployment window policy |

**Enforcement:** Patient Safety Impact Assessment (PSIA) required for every
change touching clinical data paths. Clinical safety review board sign-off
for any change affecting lab results, orders, or patient identification.
Automated safety tests in CI pipeline.

---

### Principle 4: Data Sovereignty

**Statement:** Patient data SHALL remain under the jurisdiction of the
country in which it was collected. No data SHALL cross national borders
without explicit legal basis, informed consent, and auditable controls.

**Detailed explanation:** Healthcare data is governed by national laws
(Iraq's Health Data Law, GDPR-style regulations, country-specific health
information acts). The GULA platform must support multiple legal regimes
simultaneously. Data storage, processing, and transmission boundaries
must be technically enforceable, not just policy-based.

**Concrete implications:**

- Data stored in regionally-resident databases (per-country sharding or per-country database instances)
- Cross-border data flows logged in separate cross-border audit trail
- Encryption keys per country, controlled by country health authority
- Government-specific API gateways with country-level access controls
- Data classification labels on every record (local, national, regional, international)
- Export controls: no bulk patient data export without regulatory approval
- Right to deletion / right to rectification per national law
- Data residency verification in CI/CD (deployments tagged with region)

**Enforcement:** Data sovereignty compliance checks in deployment pipeline.
Regional deployment restrictions enforced via infrastructure-as-code policies.
Annual data sovereignty audit by external auditor.

---

### Principle 5: Evidence Before Deployment

**Statement:** Every change SHALL be validated with evidence before it reaches
production. No change SHALL be deployed based on untested assumptions.

**Detailed explanation:** In healthcare, untested changes can cause patient
harm. All changes must pass through a chain of validation stages: unit tests,
integration tests, security tests, performance tests, chaos tests, and where
appropriate, clinical validation. Evidence is collected and published with
every release.

**Concrete implications:**

| Validation Stage | What It Proves | Evidence Artifact |
|-----------------|----------------|-------------------|
| Unit tests | Individual functions work correctly | Coverage report |
| Integration tests | Services work together correctly | Test pass report |
| API tests | Endpoints meet contract | OpenAPI compliance report |
| Security tests | No vulnerabilities introduced | SAST/DAST/SCA reports |
| Performance tests | Meets latency/throughput budgets | Load test report |
| Chaos tests | Resilience under failure | Chaos experiment report |
| Clinical validation | Clinical correctness | Clinician sign-off |
| Migration tests | Data integrity preserved | Migration test report |
| Accessibility tests | WCAG compliance met | Accessibility audit report |
| Internationalization tests | All locales work correctly | i18n test report |

**Enforcement:** CI pipeline gates every check. Deployment blocked if any
evidence gate fails. Exemptions require 3-person engineering review + clinical
safety officer sign-off.

---

### Principle 6: Configuration Before Code

**Statement:** Behavior changes SHALL be achieved through configuration
(feature flags, environment variables, config files, policy engines) before
code changes. Code changes are the last resort.

**Detailed explanation:** Changing code introduces risk, requires testing,
and needs deployment. Changing configuration is instant, reversible, and
low-risk. Therefore, every behavioral variation — per-tenant behavior,
deployment-specific behavior, feature gating, A/B testing — should be
achieved through configuration before code modification is considered.

**Concrete implications:**

- Every new feature behind a feature flag (`core/feature_flags.py`)
- Feature flags are per-tenant in the feature matrix
- Deployment-wide flags for SNDHS/Financial/global toggles
- Configuration schema versioned and validated
- Default values for all configuration keys
- Unknown configuration keys ignored (forward compatibility)
- Configuration changes logged in audit trail
- Configuration rollback supported for all flags

```python
# CORRECT: Configuration-driven behavior
if feature_flags.is_enabled(lab_id, "new_result_workflow"):
    use_new_result_workflow()
else:
    use_legacy_result_workflow()

# WRONG: Code-driven behavior branching
if lab_id in [1, 2, 3]:  # hardcoded tenant list
    use_new_result_workflow()
```

**Enforcement:** Architecture review validates every PR that introduces a
new behavioral branch. If it's not behind a feature flag, the PR is rejected.
Automated detection of hardcoded tenant-specific logic.

---

### Principle 7: Open Standards Before Proprietary

**Statement:** The platform SHALL use open standards for all data exchange,
interoperability, and integration. Proprietary standards SHALL only be used
when no open standard exists, and SHALL be wrapped in an adapter layer.

**Detailed explanation:** Healthcare interoperability depends on standards.
The GULA platform mandates FHIR R4 for clinical data exchange, HL7 for
legacy integration, DICOM for imaging, LOINC and SNOMED for clinical coding,
and ICD for diagnoses. Proprietary formats are isolated behind adapters so
the rest of the platform never depends on them.

**Concrete implications:**

| Domain | Mandated Standard | Fallback (with adapter) |
|--------|------------------|------------------------|
| Clinical data exchange | FHIR R4 | Custom JSON/XML |
| Lab instrument data | ASTM E1381/HL7 v2 | Proprietary device protocols |
| Medical imaging | DICOM | Proprietary image formats |
| Clinical coding | LOINC, SNOMED CT, ICD-10/11 | Local coding systems |
| Prescriptions | RxNorm, ATC, national drug codes | Custom drug databases |
| Appointments | FHIR Appointment | Custom scheduling formats |
| Billing | X12 837/835, UB-04 | Proprietary billing formats |
| Device integration | IEEE 11073, HL7 FHIR Device | Custom device APIs |
| Terminology | FHIR Terminology server | Local terminology tables |

**Enforcement:** Architecture compliance checks reject new proprietary
integration paths unless approved by Architecture Review Board with
justification. Adapter pattern enforced via import-linter rules.

---

### Principle 8: API First

**Statement:** Every feature SHALL be accessible via a well-defined,
versioned API before any user interface is built.

**Detailed explanation:** APIs are the platform's contract with all consumers:
frontend applications, mobile apps, third-party integrations, government
systems, device bridges, and AI skills. Building the API first ensures the
feature's contract is well-defined, testable, and consumable by multiple
clients. It also enables parallel development (frontend teams can work
against the API spec while backend teams implement).

**Concrete implications:**

- API specification (OpenAPI 3.1) written before implementation
- API reviewed by API governance board
- API versioned (`/api/v1/`, `/api/v2/`)
- API documented with examples, errors, rate limits
- API tested with contract tests
- API published to API catalog
- SDK auto-generated from API spec
- UI consumes API; never accesses database or services directly
- Internal APIs also versioned and documented

**Enforcement:** CI gate checks that every new route has an OpenAPI spec.
API review required for any endpoint change. Breaking changes require 6-month
deprecation notice.

---

### Principle 9: Offline First

**Statement:** Every feature SHALL function without network connectivity.
The platform SHALL queue operations locally, sync when connectivity is
restored, and resolve conflicts with a deterministic strategy.

**Detailed explanation:** Healthcare cannot depend on reliable connectivity.
Clinics in remote areas, labs during network outages, and field hospitals
in disaster zones all need the platform to work offline. Offline-first design
means the platform is built for disconnection as the normal state, not the
exception. Sync is eventual, conflict resolution is deterministic, and data
is never lost.

**Concrete implications:**

| Capability | Offline Behavior | Sync Strategy |
|------------|-----------------|---------------|
| Patient registration | Works offline, queued locally | Last-writer-wins + audit |
| Lab order creation | Works offline, queued locally | Last-writer-wins + audit |
| Lab result entry | Works offline, queued locally | Append-only, never overwrite |
| Patient lookup | Local cache with last-seen data | Full sync on reconnect |
| Reference data | Local cache with versioning | Incremental sync on reconnect |
| AI inference | On-device model (if available) | Queue inference requests |
| Authentication | Offline token cache | Token refresh on reconnect |
| Audit logging | Local queue, batched upload | Ordered by sequence number |

**Enforcement:** Every feature's acceptance criteria includes: "works in
offline mode." Integration tests verify offline queue, sync, and conflict
resolution. Performance tests verify sync under poor connectivity (high
latency, low bandwidth, packet loss).

---

### Principle 10: Security by Design

**Statement:** Security SHALL be integrated into every stage of the
development lifecycle, not added after the fact. Threat modeling SHALL
be performed for every feature before implementation begins.

**Detailed explanation:** Security is not a separate phase or a checklist
item. It is a continuous practice embedded in every decision: architecture,
design, implementation, testing, deployment, and operations. STRIDE
(Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service,
Elevation of Privilege) threat modeling is required per feature. Security
requirements are non-functional requirements and are treated with the same
rigor as functional requirements.

**Concrete implications:**

- STRIDE threat model per feature (stored in `docs/security/threat-models/`)
- Security requirements in user stories (acceptance criteria include security)
- Security review in PR process (automated SAST + manual review for sensitive changes)
- Penetration testing before major releases
- Vulnerability disclosure program
- Security training for all developers (annual)
- Security champions in each team

```
# Every feature PR must include in its description:
# Threat Model: docs/security/threat-models/feature-name.md
# Security Review: PASSED (reviewer: @username)
# SAST Scan: 0 findings
# Dependency Scan: 0 vulnerabilities
```

**Enforcement:** CI gate: PR blocked if no threat model for new feature,
SAST/DAST findings > 0, dependency vulnerabilities > 0. Security review
required for any change to `backend/app/security/`, `backend/database.py`,
encryption code, authentication, or authorization.

---

### Principle 11: Privacy by Design

**Statement:** Privacy SHALL be embedded into the design of every system,
feature, and data flow. Data minimization, purpose limitation, consent
management, and encryption are mandatory.

**Detailed explanation:** Patient health data is among the most sensitive
personal information. The platform must protect privacy at every level:
collect only what is needed (data minimization), use only for stated purpose
(purpose limitation), obtain and manage consent (consent management), protect
at rest and in transit (encryption), and ensure individuals can exercise their
rights (access, rectification, erasure, portability).

**Concrete implications:**

| Privacy Principle | Implementation | Verification |
|------------------|---------------|--------------|
| Data minimization | Collect only fields needed for clinical purpose | Data flow review |
| Purpose limitation | Data tagged with purpose; access controlled by purpose | Purpose-based access control |
| Consent management | Consent records per patient per purpose | Consent audit trail |
| Encryption at rest | AES-256-GCM for sensitive fields | Encryption verification tests |
| Encryption in transit | TLS 1.3 for all communication | TLS configuration scanning |
| De-identification | Anonymization/pseudonymization for analytics | De-identification verification |
| Right to access | Patient portal for data access | Access request fulfillment |
| Right to erasure | Soft delete + hard delete after retention | Deletion verification |
| Data portability | FHIR export for patient data | Export functionality tests |

**Enforcement:** Privacy Impact Assessment (PIA) required for every feature
touching personal data. Data Protection Officer (DPO) review for high-risk
processing. Automated data classification scanning in CI.

---

### Principle 12: Stability Before Novelty

**Statement:** Working, stable code SHALL never be broken to add new
features. Novelty SHALL never come at the cost of stability.

**Detailed explanation:** The GULA platform operates in a healthcare context
where reliability is a patient safety requirement. A stable system that does
less is always preferable to an unstable system that does more. Every new
feature must prove it does not degrade existing functionality before it is
accepted. "If it ain't broke, don't fix it" is an engineering principle,
not a conservative cop-out.

**Concrete implications:**

- No refactoring without tests (100% coverage of refactored code)
- No dependency upgrade without compatibility testing
- No framework migration without parallel run capability
- No database schema change without migration rollback verification
- No API change without backward compatibility guarantee
- New features are behind feature flags (can be disabled if problems arise)
- Change impact analysis required for every PR
- Stability regression tests run on every PR
- Rollback plan required for every deployment
- Technical debt reduction is planned, not reactive

```
# Stability checklist for every PR:
# [ ] All existing tests pass
# [ ] No regression in performance benchmarks
# [ ] No regression in security scans
# [ ] Backward compatibility verified
# [ ] Rollback plan documented
# [ ] Feature flag present (if new feature)
# [ ] Change impact analysis complete
```

**Enforcement:** CI gate blocks PR if any existing test fails. Performance
regression >5% blocks deployment. Rollback plan required in deployment
checklist. Architecture review board approval required for changes that
affect core stability.

---


## PART 2: Engineering Principles (15 Principles, Expanded)

Each principle below defines a fundamental engineering mandate. Every module, plugin, connector, and deployment MUST comply.

### 2.1 Single Source of Truth

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every data element, business rule, and configuration value is defined exactly once in a canonical location |
| **Why It Matters** | Duplicated data causes drift, bugs, and reconciliation failures |
| **Concrete Rules** | (1) Every DB column has exactly one authoritative model class (2) Every business rule is defined in exactly one service (3) No computed value is stored (4) No configuration value is duplicated across files |
| **Enforcement** | CI detects duplicate model definitions. Architecture review flags repeated business logic. |
| **Violation Example** | Storing `patient_name` in both `patients` and `lab_orders` tables |
| **Compliance Example** | `Patient.name` is canonical; all joins reference the patient table |

### 2.2 API First

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every feature is designed and documented as an API before any user interface is built |
| **Why It Matters** | API-first ensures the platform can be consumed by any client (web, mobile, third-party, AI agent) without rework |
| **Concrete Rules** | (1) OpenAPI 3.1 spec written before implementation (2) Every feature has at least one API endpoint (3) Internal APIs are versioned (4) Public APIs have 6-month deprecation notice |
| **Enforcement** | CI gate requires OpenAPI spec for every new route. PRs without API docs are blocked. |
| **Violation Example** | Building a UI feature without an API endpoint |
| **Compliance Example** | New lab alerting feature: OpenAPI spec first, then route implementation, then frontend consumes API |

### 2.3 Offline First

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every feature must function without network connectivity. Data syncs when connectivity is restored. |
| **Why It Matters** | Iraqi labs frequently experience internet outages. Patient safety cannot depend on connectivity. |
| **Concrete Rules** | (1) All writes are queued locally when offline (2) Conflict resolution uses last-writer-wins with full audit trail (3) Local cache is encrypted (4) Sync is bidirectional and resumable |
| **Enforcement** | Architecture review requires offline mode design for every new feature |
| **Violation Example** | A feature that shows 'No internet' error instead of working offline |
| **Compliance Example** | `edge_agent/` queues lab results locally and syncs when connection restored |

### 2.4 Security by Design

| Aspect | Specification |
|--------|--------------|
| **Definition** | Security requirements are designed into every feature from inception, not added afterward |
| **Why It Matters** | Retrofitting security is expensive and leaves gaps |
| **Concrete Rules** | (1) STRIDE threat model per feature (2) Security review in definition of done (3) All data access authorized and logged (4) Input validation on every endpoint |
| **Enforcement** | Security review gate in CI. Threat model document required for every major feature. |
| **Violation Example** | New endpoint that exposes patient data without `lab_id` filter |
| **Compliance Example** | Every `/patients` query includes `WHERE lab_id = current_user.lab_id` |

### 2.5 Privacy by Design

| Aspect | Specification |
|--------|--------------|
| **Definition** | Data minimization, purpose limitation, and encryption are baked into every data operation |
| **Why It Matters** | Patient data is sensitive. Regulatory frameworks require privacy safeguards. |
| **Concrete Rules** | (1) Collect only data needed for the stated purpose (2) Encrypt all PII at rest (3) Retention policies enforced automatically (4) Consent recorded for every data use |
| **Enforcement** | Data Protection Impact Assessment required for every new data collection |
| **Violation Example** | Logging patient name in plaintext debug logs |
| **Compliance Example** | `patients.national_id` encrypted with `NID_HMAC_KEY`, never logged |

### 2.6 Accessibility First

| Aspect | Specification |
|--------|--------------|
| **Definition** | All user interfaces meet WCAG 2.1 AA minimum, with Arabic-first RTL support |
| **Why It Matters** | Healthcare is for everyone, including people with disabilities |
| **Concrete Rules** | (1) WCAG 2.1 AA compliance required (2) Full RTL support in all UIs (3) Screen reader compatible (4) Color contrast >= 4.5:1 (5) Keyboard navigable |
| **Enforcement** | Automated axe-core checks in CI. Manual accessibility audit before major releases. |
| **Violation Example** | A form that cannot be completed with keyboard only |
| **Compliance Example** | All platform UIs support `dir=rtl` and ARIA labels |

### 2.7 Localization First

| Aspect | Specification |
|--------|--------------|
| **Definition** | Internationalization is built into every component from day one |
| **Why It Matters** | GULA deploys across multiple countries and languages. Retrofitting i18n is expensive. |
| **Concrete Rules** | (1) All strings externalized to locale files (2) No hardcoded text in UI code (3) RTL/LTR auto-detection (4) Unicode/UTF-8 required everywhere |
| **Enforcement** | Lint rule blocking hardcoded strings. CI tests with Arabic locale. |
| **Violation Example** | English-only error message in API response |
| **Compliance Example** | All UI text via `t()` function, all API error messages with `ar` and `en` variants |

### 2.8 AI Assist, Human Decide

| Aspect | Specification |
|--------|--------------|
| **Definition** | AI provides recommendations; humans make final decisions, especially in clinical pathways |
| **Why It Matters** | Patient safety requires human judgment. AI cannot be held legally responsible. |
| **Concrete Rules** | (1) Every AI output requires human review before clinical action (2) AI never auto-executes clinical orders (3) AI recommendations are clearly labeled (4) Human override is always possible |
| **Enforcement** | Architecture review of every AI feature. Mandatory human-in-the-loop gate. |
| **Violation Example** | AI auto-submits lab orders without human approval |
| **Compliance Example** | Clinical AI suggests differential diagnosis; doctor reviews and confirms before action |

### 2.9 Evidence Before Release

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every change is validated with evidence before it reaches production |
| **Why It Matters** | Healthcare software errors can harm patients |
| **Concrete Rules** | (1) All quality gates must pass (2) Clinical features require clinical validation (3) Performance benchmarks must not regress (4) Security scan must pass |
| **Enforcement** | CI pipeline blocks releases that fail any quality gate. Clinical validation requires sign-off. |
| **Violation Example** | Deploying AI diagnostic model without clinical validation |
| **Compliance Example** | New lab test type requires reference range validation by lab director before activation |

### 2.10 Configuration Before Code

| Aspect | Specification |
|--------|--------------|
| **Definition** | Behavior changes should be achieved through configuration, not code changes |
| **Why It Matters** | Configuration can be deployed without code review, testing cycle, and deployment risk |
| **Concrete Rules** | (1) Feature flags for every new feature (2) Environment-specific config files (3) Business rules configurable via admin UI (4) Hardcoded values are code smells |
| **Enforcement** | Code review flags hardcoded values. Feature flag required for every new feature. |
| **Violation Example** | Hardcoding lab reference ranges in business logic |
| **Compliance Example** | Reference ranges stored in `TestType` model, configurable per lab |

### 2.11 Modules Before Forks

| Aspect | Specification |
|--------|--------------|
| **Definition** | Extend the platform by adding modules, never by forking the codebase |
| **Why It Matters** | Forks diverge and cannot receive upstream updates. Modules maintain compatibility. |
| **Concrete Rules** | (1) All new features are modules, not core modifications (2) Plugin API for hot-reloadable extensions (3) No custom forks of core dependencies |
| **Enforcement** | Architecture review. Fork detection in CI. |
| **Violation Example** | Copying core code and modifying it for a specific lab |
| **Compliance Example** | New country-specific regulation implemented as a module implementing the regulatory interface |

### 2.12 Open Standards Before Proprietary

| Aspect | Specification |
|--------|--------------|
| **Definition** | Use open healthcare standards before any proprietary format |
| **Why It Matters** | Open standards ensure interoperability, prevent vendor lock-in, and enable ecosystem growth |
| **Concrete Rules** | (1) FHIR R4 for all clinical data exchange (2) HL7 v2 for legacy system integration (3) LOINC for lab test coding (4) SNOMED CT for clinical terminology (5) DICOM for imaging |
| **Enforcement** | Architecture review mandates open standards. Proprietary formats require exemption. |
| **Violation Example** | Creating a custom lab result format instead of using FHIR DiagnosticReport |
| **Compliance Example** | All lab results exposed via `/ehr/fhir` endpoints using FHIR R4 resources |

### 2.13 Stability Before Novelty

| Aspect | Specification |
|--------|--------------|
| **Definition** | Never break working code to add new features. Stability is the highest priority. |
| **Why It Matters** | Healthcare platforms cannot have regressions. Lab operations depend on consistent behavior. |
| **Concrete Rules** | (1) 100% existing tests pass before new feature merge (2) No architecture changes without ADR (3) Feature flags for all new functionality (4) Canary deployments for risky changes |
| **Enforcement** | CI blocks PRs that break existing tests. Architecture review for any refactoring. |
| **Violation Example** | Renaming a widely-used API function for aesthetic reasons |
| **Compliance Example** | Adding a new lab workflow as a separate module without touching existing workflows |

### 2.14 Trace Everything

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every operation is logged, traced, and auditable. No silent failures. |
| **Why It Matters** | Traceability is required for patient safety, regulatory compliance, and debugging |
| **Concrete Rules** | (1) Every mutation writes to audit log (2) Every request has correlation ID (3) Distributed tracing across all services (4) Structured JSON logging everywhere |
| **Enforcement** | CI checks for audit log writes on all mutation endpoints. Log format enforcement. |
| **Violation Example** | Database update without corresponding audit log entry |
| **Compliance Example** | Every `LabResult` mutation logs: user, lab, timestamp, old value, new value, reason |

### 2.15 Test Everything

| Aspect | Specification |
|--------|--------------|
| **Definition** | Every line of code has automated tests. No untested code reaches production. |
| **Why It Matters** | Healthcare software errors can kill. Testing is the primary quality assurance mechanism. |
| **Concrete Rules** | (1) Coverage >= 95% overall (2) 100% coverage for security-critical code (3) Integration tests for every endpoint (4) Performance tests for critical paths |
| **Enforcement** | CI gates block below-threshold coverage. Coverage reports published per PR. |
| **Violation Example** | New endpoint without integration tests |
| **Compliance Example** | Every route module has corresponding test module with >95% coverage |


## PART 3: Stable Platform Core

The following components are the stable core of the GULA platform. They should almost never change. Modification requires Architecture Review Board approval with supermajority vote.

| Core Component | Purpose | Why Stable | Interface Contract | Modification Protocol |
|---------------|---------|------------|-------------------|----------------------|
| **Core Data Models** | Patient, Lab, User, Order, Result, Sample | Schema changes cascade to all modules; data migration risk | SQLAlchemy ORM models in `models/` | ADR required + migration plan + all modules updated + round-trip migration test |
| **Authentication Framework** | JWT issuing, validation, refresh token rotation | Security-critical; every endpoint depends on it | `security/auth.py` — `create_access_token()`, `get_current_user()` | Security team review + penetration test + gradual rollout with old token compatibility |
| **Authorization (RBAC)** | 9 roles x 13 permissions | Every access control decision depends on it | `security/rbac.py` — `require_permission()` decorator | All permission changes must be backward-compatible; old roles continue working |
| **Audit Log System** | Immutable hash-chain audit trail | All compliance depends on audit trail integrity | `audit/audit_log.py` — `log_action()` | Append-only; never modify existing entries; hash chain structure is frozen |
| **Tenant Isolation Layer** | `lab_id` filter on all patient-data queries | Patient privacy depends on isolation | `security/tenant.py` — `get_current_lab()` | Every query must include lab_id filter; no mechanism to bypass |
| **Encryption Framework** | Fernet, AES-256-GCM, per-field encryption | Data protection at rest | `security/encryption.py` — `encrypt()`, `decrypt()` | Key rotation procedure only; algorithm change requires 6-month migration window |
| **API Gateway** | nginx routing, rate limiting, security headers | All traffic enters through gateway | `docker-compose.yml` — `api-gateway` service | Gateway config changes require load testing + security review |
| **Health Check Infrastructure** | `/health/live`, `/health/ready`, `/health/deep` | Docker orchestration and monitoring depend on it | `routes/health.py` | New health check endpoints must be added to `_ALWAYS_ALLOWED_PATHS` |
| **Event Bus & Outbox** | Async cross-module communication | All module integration depends on event pattern | `services/outbox_service.py` — `publish_event()`, `process_outbox()` | Event schema registry changes require consumer coordination |
| **Migration Framework** | Alembic standards, idempotent migrations | Database schema evolution | `alembic.ini` + migration files | Existing migrations never modified; new migrations always use guards |
| **Configuration Loading** | `config.py` — env var loading, secret validation | Application startup depends on correct config | `config.py` — `Settings` class | New env vars added to `.env.example` and validated in `config.py` |
| **Logging & Correlation** | Structured JSON logging, `X-Request-ID` | Debugging and audit depend on correlation | `core/logging_config.py` — `setup_logging()` | Log format changes require all consumers to be updated |
| **Database Connection Pool** | SQLAlchemy pool management | Application depends on reliable DB connections | `database.py` — `engine`, `SessionLocal` | Pool size changes require capacity planning and connection budget validation |
| **Middleware Stack Order** | 11 middleware layers in fixed order | Request processing pipeline | `main.py` — middleware registration | Never reorder; new middleware added at documented position with ADR |

### 3.1 Immutability Covenant

These components are subject to the **Immutability Covenant**: no change to the stable core may be made without:

1. Architecture Decision Record (ADR) documenting rationale
2. Security review (for security-related components)
3. Impact analysis on all dependent modules
4. Migration plan for backward compatibility
5. Supermajority approval (7/10) of Architecture Review Board
6. 30-day notice period for all platform consumers


## PART 4: Modular Domains

Components that must always remain modular — pluggable, replaceable, independently versioned.

| Domain | Interface Contract | Extension Pattern | Isolation Guarantee | Example |
|--------|-------------------|-------------------|---------------------|---------|
| **Healthcare Modules** | Specialty-specific API + event schemas | Module per specialty (cardiology, oncology, etc.) | Separate DB schema, independent deployment | `backend/app/cardiology/` bounded context |
| **Education & Training** | Course API, CME tracking, assessment events | LMS module + content packs | Separate DB, independent deployment | `backend/app/education/` |
| **Legal & Compliance** | Regulatory rules engine, document templates | Compliance pack per jurisdiction | Read-only access to core data with audit | Regulatory reporting per country |
| **Industry Health** | Occupational health API | Industry-specific module | Isolated data per industry tenant | Factory worker health screening |
| **Agriculture Health** | Rural health API, tele-extension | Agriculture health module | Isolated data, offline-first for rural areas | Farm worker health records |
| **Finance/Insurance** | Claims API, reimbursement engine | Insurance module + payment gateway | Separate financial DB, Sarbanes-Oxley compliance | Medical claims processing |
| **Research Workflows** | IRB API, trial management, data export | Research module + de-identification layer | Isolated research DB, ethics-governed | Clinical trial management |
| **Defense/Military Health** | Military EHR API, field hospital protocols | Defense module + tactical data sync | Air-gapped deployment, MIL-STD compliance | Field medical record |
| **Smart City Integration** | City health API, population sensors | Smart city connector | Aggregated data, privacy-preserving | City-wide health dashboard |
| **Future Domains** | Unknown — must implement Module interface | Adapter pattern via Module API | Always isolated, never modifies core | Future domain TBD |

### 4.1 Module Contract

Every module MUST implement:

```python
class GulaModule:
    name: str
    version: str
    dependencies: list[str]
    def register_routes(self, app): ...
    def register_events(self, bus): ...
    def register_commands(self, registry): ...
    def health_check(self) -> HealthStatus: ...
```


---

## PART 5: Dependency Rules & Matrix

### 5.1 Layer Dependency Rules

| Rule | Description | Violation |
|------|-------------|-----------|
| **R1** | Routes depend on Services only — never on Domain, Models, or Infrastructure | BLOCKER |
| **R2** | Services depend on Domain only — never on Routes, other Services directly (use events), or Infrastructure | BLOCKER |
| **R3** | Domain depends on Nothing — pure business logic, no framework imports | BLOCKER |
| **R4** | Infrastructure depends on Nothing — implements ports defined in Domain | BLOCKER |
| **R5** | No circular dependencies between any modules | BLOCKER |
| **R6** | Cross-module communication only via Events (async) | BLOCKER |
| **R7** | No shared mutable state between modules | BLOCKER |
| **R8** | All external system access through Adapter interfaces | BLOCKER |
| **R9** | Plugins never access the database directly — use plugin API only | BLOCKER |
| **R10** | Frontends never access the database directly — use API gateway only | BLOCKER |

### 5.2 Dependency Matrix

| Layer | Depends On | Cannot Depend On | Communication | Example |
|-------|-----------|------------------|---------------|---------|
| Routes (API) | Services | Domain, Models, DB, Infrastructure | Sync (HTTP) | `routes/patients.py` -> `services/patient_service.py` |
| Services | Domain | Routes, other Services, Infrastructure | Sync (in-module), Events (cross-module) | `services/order_service.py` -> `domain/order.py` |
| Domain | Nothing | Routes, Services, Infrastructure, Framework | None (pure functions) | `domain/order_state.py` |
| Infrastructure | Nothing | Routes, Services, Domain | Via Dependency Injection | `infrastructure/postgres_repository.py` |
| Models (ORM) | DB | Routes, Services, Domain | Via Repository pattern | `models/patient.py` |
| Plugins | Plugin API | DB, Core internals | Via Plugin API hooks | `plugin/hl7_export.py` |
| Connectors | Adapter interface | Core internals | Via Connector API | `connector/fhir_gateway.py` |
| Frontend | API Gateway | Backend internals, DB | REST/GraphQL/WebSocket | `frontend-v2/` -> `api-gateway` |

### 5.3 Communication Patterns

| Pattern | When Used | Technology | Contract |
|---------|-----------|------------|----------|
| Sync Request-Response | Command/Query within same bounded context | FastAPI -> Service | OpenAPI schema |
| Async Events | Cross-boundary notifications | Event Bus / Outbox | Event schema in registry |
| CQRS Commands | Mutations | FastAPI -> Command Handler | Command schema |
| CQRS Queries | Reads | FastAPI -> Query Handler | Query + Response schema |
| Saga/Process Manager | Multi-step business processes | Event sourced state machine | Process definition |
| Adapter Pattern | External system access | Port/Adapter + DI | Port interface |

---

## PART 6: Versioning Strategy

### 6.1 Versioning Schemes

| Component | Scheme | Example | Compatibility Policy |
|-----------|--------|---------|---------------------|
| Core Platform | SemVer MAJOR.MINOR.PATCH | v2.1.0 | MAJOR=breaking, MINOR=features, PATCH=fixes |
| Modules | Independent SemVer | order-service@1.3.2 | Each module versioned independently |
| Country Packs | Country.CORE_MAJOR.MINOR | IQ.2.1 | Tied to Core feature version |
| Language Packs | Lang.VERSION | AR.2.1.0 | Aligned with Core version |
| Plugins | PluginName@SemVer | hl7-export@1.0.4 | Plugin API per Core MAJOR |
| AI Skills | SkillName@SemVer | malaria-detector@2.1.0 | Includes training data version |
| SDKs | Lang.Core_MAJOR.Core_MINOR | python@2.1 | Aligned with Core MAJOR.MINOR |
| API | vMAJOR | v1 | URL prefix with Sunset header |
| Database Schema | Migration-based | migration_20260505_0001 | Forward-only migrations |
| Configuration | Schema version in files | config_version: 2 | Backward-compatible defaults |

### 6.2 Version Compatibility

```
                 Core v1    Core v2    Core v3
Module v1.x       OK         Sunset      X
Module v2.x       X          OK          Sunset
Plugin API v1     OK         OK (compat) X
Plugin API v2     X          OK          OK
SDK v1.x          OK         Sunset      X
SDK v2.x          X          OK          Sunset
API v1            OK         OK          Sunset
API v2            X          OK          OK
```

### 6.3 Release Channels

| Channel | Quality | Frequency | Support | Use Case |
|---------|---------|-----------|---------|----------|
| Nightly | Syntax only | Daily | None | Development testing |
| Beta | All gates pass | Weekly | Best effort | Feature validation |
| RC | Full certification | Before release | High | Pre-production |
| Stable | Production certified | Monthly | LTS (2yr) | General availability |
| LTS | Full audit + security | Quarterly | 2 years | Regulated environments |
| Hotfix | Expedited security | As needed | Immediate | Critical security |

---

## PART 7: Extension Strategy

Every future feature MUST be added as one of the following extension types. Never modify the Core unless absolutely necessary.

| Extension Type | Definition | Requirements | Lifecycle | Example |
|---------------|-----------|--------------|-----------|---------|
| Module | Self-contained bounded context | Module API, event schemas, tests | Design -> Build -> Test -> Release -> Maintain -> Deprecate | Cardiology module |
| Plugin | Hot-reloadable runtime extension | Stable API, sandbox, resource limits | Install -> Configure -> Activate -> Update -> Deactivate -> Remove | FHIR export plugin |
| Connector | External system adapter | Adapter interface, retry, circuit breaker | Register -> Configure -> Connect -> Monitor -> Disconnect | Device bridge |
| Country Pack | Country-specific rules/coding | Country schema, regulatory mapping | Research -> Configure -> Validate -> Deploy -> Update | Iraq country pack |
| Language Pack | i18n resources for locale | Complete translation coverage | Translate -> Review -> Validate -> Deploy | Arabic language pack |
| AI Skill | AI Fabric capability | Model registry, validation, monitoring | Train -> Validate -> Register -> Deploy -> Monitor -> Retire | Malaria detection |
| Workflow Pack | BPMN/DMN processes | Process model, decision tables | Design -> Model -> Test -> Deploy -> Monitor -> Optimize | Lab ordering workflow |

### 7.1 Extension Lifecycle

All extensions follow: `Register in Catalog -> Version Check -> Dependency Resolution -> Sandbox Validation -> Feature Flag Activation -> Runtime Monitoring -> Deprecation Notice -> Sunset Removal`

### 7.2 Extension Isolation

- Extensions run in isolated namespaces
- No extension may directly access the database
- Extension API is versioned and stable
- Resource limits enforced per extension
- Extension failure never crashes the core

---

## PART 8: Backward Compatibility Rules

### 8.1 API Compatibility

| Rule | Detail |
|------|--------|
| Support window | 2 previous MAJOR versions |
| Deprecation notice | Minimum 6 months via Sunset and Deprecation HTTP headers |
| Breaking change | Removing/modifying fields, changing required to optional, removing endpoints |
| Non-breaking changes | Adding fields (with defaults), adding endpoints, adding HTTP methods |
| Documentation | Breaking changes in CHANGELOG.md with migration guide |

### 8.2 Database Compatibility

| Rule | Detail |
|------|--------|
| Forward-only | Migrations never rolled back; roll forward with new migration |
| No destructive changes | Never drop columns/tables without dual-write period |
| Rolling upgrade | New code works with old schema during deployment |
| Dual-write period | Write to both old and new columns for one release cycle |
| Migration validation | `alembic downgrade -1 && alembic upgrade head` must succeed |

### 8.3 Event Compatibility

| Rule | Detail |
|------|--------|
| Schema registry | All events registered with version in schema registry |
| Add-only evolution | New fields must be optional with defaults |
| No field removal | Fields deprecated but never removed from schema |
| Consumer resilience | Consumers ignore unknown fields |

### 8.4 SDK & Plugin Compatibility

| Component | Support Window | Deprecation Notice |
|-----------|---------------|-------------------|
| SDK | 1 previous MAJOR version | 3 months minimum |
| Plugin API | Same MAJOR version guaranteed | New MAJOR with migration path |
| UI | Graceful degradation, progressive enhancement | Responsive design for all screens |

### 8.5 Deprecation Policy

```
Notification -> 6-month notice -> Sunset header -> 410 GONE -> Removal
ADR + API        Changelog        HTTP headers    Return 410   Delete code
decision         announcement    + monitoring    for 3 months
```

---

## PART 9: Security Constitution (Expanded)

### 9.1 Zero Trust Architecture

| Principle | Implementation | Verification |
|-----------|---------------|--------------|
| Never trust, always verify | Every request authenticated, authorized, encrypted | JWT validation on every request |
| Microsegmentation | Network policies restrict pod-to-pod communication | Network policy enforcement |
| Continuous verification | Session refresh, token rotation, anomaly detection | Redis token blacklist |
| Least privilege | JIT elevation, time-bound access | Break glass audit trail |

### 9.2 Least Privilege

- Users have minimum permissions for their role
- API tokens have scoped permissions
- Elevated access requires justification and time limit
- Privileged access is logged and audited
- Default-deny for all resources

### 9.3 Defense in Depth

| Layer | Controls |
|-------|----------|
| Network | WAF, DDoS protection, network segmentation, egress filtering |
| Application | Input validation, output encoding, CSRF protection, rate limiting |
| Data | Encryption at rest/in transit, tokenization |
| Endpoint | Device trust verification, OS hardening |
| Identity | MFA, biometric, risk-based authentication |

### 9.4 Secure Defaults

- Every configuration defaults to the most secure option
- Features requiring reduced security must opt in explicitly
- Debug features never enabled in production
- TLS 1.3 minimum, no weak ciphers

### 9.5 Immutable Audit

- Audit entries never modified or deleted
- Hash chain ensures tamper evidence
- Cryptographic verification of audit integrity
- Real-time alerting on audit anomalies

### 9.6 Cryptographic Agility

- All algorithms configurable
- Key rotation without data re-encryption
- Algorithm deprecation with 12-month notice
- Post-quantum cryptography readiness assessment

### 9.7 Supply Chain Security

- SBOM for every build
- Dependencies pinned with hash verification
- Automated vulnerability scanning
- No unverified third-party code in production

### 9.8 Runtime Security

- RASP (Runtime Application Self-Protection)
- File integrity monitoring
- Container runtime security
- Network anomaly detection

### 9.9 Incident Response

| Phase | Activities | Timeline |
|-------|-----------|----------|
| Preparation | Runbooks, playbooks, tabletop exercises | Continuous |
| Detection | Monitoring, alerting, anomaly detection | < 5 minutes |
| Containment | Kill switch, network isolation, credential rotation | < 15 minutes |
| Eradication | Patch, configuration change, key rotation | < 4 hours |
| Recovery | Restore from backup, verify integrity | < 4 hours |
| Post-mortem | Root cause analysis, improvements, report | < 1 week |

---

## PART 10: AI Constitution (Expanded)

### 10.1 Human Authority

| Rule | Detail | Violation |
|------|--------|-----------|
| AI never overrides clinical decisions | All AI outputs require human review before clinical action | CRITICAL |
| Human-in-the-loop for diagnosis | AI suggests, doctor confirms | CRITICAL |
| Human override always possible | AI workflow supports override at every decision point | BLOCKER |

### 10.2 Explainability

- Every AI output explains reasoning (confidence, contributing factors, alternatives)
- Black-box models prohibited for clinical decisions
- Explanation must be in plain language

### 10.3 Traceability

| Trace Element | Required Fields |
|---------------|-----------------|
| Model version | Model ID, version, training date |
| Prompt version | Prompt ID, version, content hash |
| Input context | All input data with provenance |
| Retrieval sources | Document IDs, relevance scores |

### 10.4 Auditability

Every AI interaction stored in `AIInteraction` model with: interaction_id, user_id, model_id, prompt_id, input_hash, output, confidence, human_approval, human_feedback, latency_ms, created_at.

### 10.5 Hallucination Prevention

- Factual consistency verification against trusted sources
- Source grounding for every claim
- Confidence scoring with uncertainty quantification
- Low-confidence outputs flagged for human review

### 10.6 Bias Prevention

| Test | Metric | Threshold | Action |
|------|--------|-----------|--------|
| Demographic parity | Selection rate ratio | 0.8 - 1.25 | Retrain/adjust |
| Equal opportunity | TPR parity | +/-5% | Retrain/adjust |
| Disparate impact | Adverse impact ratio | >= 0.8 | Retrain |
| Calibration | Score per group | +/-0.1 | Adjust thresholds |

### 10.7 AI Safety

- Guardrails on all AI outputs
- Prompt injection prevention
- Model resource isolation
- Kill switch per AI skill

### 10.8 Model Registry

Every model registered with: ID, version, source, training data provenance, validation results, known limitations, documentation.

### 10.9 Prompt Registry

Every prompt registered with: ID, version, content hash, intended use case, testing results, change history.

---

## PART 11: Healthcare Constitution

| Principle | Mandate | Violation |
|-----------|---------|-----------|
| Patient Safety First | No change may risk patient data loss or harm | CRITICAL |
| Clinical Validation | All CDS tools validated before deployment | BLOCKER |
| No Workflow Bypass | No automation of clinical steps without human approval | BLOCKER |
| Traceability | Every clinical action logged | BLOCKER |
| Informed Consent | Consent documented for every procedure | BLOCKER |
| Immutable Clinical Audit | Clinical audit trail never modified | CRITICAL |
| Evidence-Based | Platform supports evidence-based medicine | REQUIRED |
| CDS Advisory Only | Clinical decision support is advisory only | BLOCKER |
| Offline Data Integrity | No data lost during offline operation | CRITICAL |
| FHIR Mandate | All clinical exchange uses FHIR R4 | BLOCKER |
| Medical Coding | ICD, LOINC, SNOMED required | REQUIRED |

### 11.1 Clinical Safety Case

Every clinical feature must produce:
1. Hazard identification (FMEA/HFDA)
2. Risk assessment (severity x probability)
3. Mitigation measures
4. Verification of mitigations
5. Clinical sign-off before deployment

---

## PART 12: Government Constitution

| Principle | Mandate | Implementation |
|-----------|---------|---------------|
| Multi-Government | Support multiple governments simultaneously | Country-level tenant hierarchy |
| Multi-Legal System | Support civil, common, sharia, customary law | Configurable legal rules engine |
| Multi-Regulatory | Support FDA, EMA, SFDA, WHO, national regulators | Regulatory adapter pattern |
| Data Sovereignty | Patient data stays in country of origin | Geo-fenced storage |
| Cross-Border Controls | Data transfer requires explicit consent | Data flow policy engine |
| National Audit | Separate audit logs per jurisdiction | Partitioned audit tables |
| Key Ownership | Each country controls its own encryption keys | Per-country KMS |
| Government Gateways | Country-specific API gateways | Gateway per deployment |
| Regulatory Reporting | Templates per jurisdiction | Reporting module |

### 12.1 Country Pack Structure

```
country-packs/
├── IQ/                    # Iraq
│   ├── regulations.yaml   # Iraqi MoH regulations
│   ├── codes/             # ICD-10-AM, Iraqi coding
│   ├── forms/             # Iraqi laboratory forms
│   ├── reporting/         # MoH report templates
│   └── locale/            # Arabic (ar-IQ) locale
├── SA/                    # Saudi Arabia
├── AE/                    # UAE
├── JO/                    # Jordan
├── EG/                    # Egypt
└── __template__/          # Country pack template
```

---

## PART 13: Internationalization Constitution

| Principle | Mandate | Implementation |
|-----------|---------|---------------|
| Unlimited Languages | Every UI supports all Unicode languages | ICU4X, gettext PO files |
| RTL/LTR Support | Automatic detection and switching | CSS dir=auto, logical properties |
| Country-Specific Rules | Lab coding, clinical guidelines per country | Country pack overrides |
| Multiple Calendars | Gregorian, Hijri, others | babel calendar support |
| Multiple Currencies | IQD, USD, SAR, etc. | Currency conversion service |
| Measurement Systems | Metric, imperial, US customary | UCUM unit conversion |
| Cultural Sensitivity | UI, content, guidelines respect local culture | Design review per locale |
| Locale Formatting | Numbers, dates, addresses per locale | CLDR data, ICU formatting |
| Health Terminology | Per-country medical terminology | Terminology mapping service |

### 13.1 Locale Data Model

```python
class Locale:
    language: str           # ar, en, ku, fr
    script: str             # Arab, Latn
    region: str             # IQ, SA, US
    calendar: str           # gregorian, islamic
    number_format: str      # ### ### ###
    date_format: str        # YYYY-MM-DD
    time_format: str        # 24h, 12h
    week_start: int         # 0=Sunday, 1=Monday
    measurement_system: str # metric, imperial, US
    currency: str           # IQD, USD, SAR
    direction: str          # ltr, rtl
```

---

## PART 14: Platform Sustainability

| Principle | Mandate | Implementation |
|-----------|---------|---------------|
| 30+ Year Design | Architecture supports decades of operation | Modular, upgradable components |
| Tech Debt Management | 20% of sprint to debt reduction | Technical debt register |
| No Vendor Lock-in | Open source, open standards, portable infra | Multi-cloud support |
| Sovereign Deployment | On-premises, government cloud, air-gapped | Terraform per environment |
| Power Resilience | Grid, diesel, solar, battery | Edge agent handles outages |
| Network Resilience | Offline-first, satellite backup | Store-and-forward pattern |
| Personnel Resilience | Documentation, knowledge transfer | Comprehensive runbooks |
| Financial Sustainability | Open core + enterprise features | Subscription model |
| Technology Sustainability | Proven stacks, avoid fads | Technology radar process |
| Code Sustainability | Clean code, minimal deps | Architecture guardian |

### 14.1 Technology Radar

| Ring | Technologies | Evaluation Cycle |
|------|-------------|-----------------|
| Adopt | PostgreSQL, Redis, FastAPI, Python, FHIR R4, Docker | Proven, default choice |
| Trial | Rust (performance-critical), WebAssembly (plugins) | Evaluate in staging |
| Assess | Quantum-safe crypto, WebGPU for imaging | Research phase |
| Hold | Blockchain (for most uses), NoSQL for patient data | Not recommended |

### 14.2 Longevity Checklist

Every major technology decision evaluated against:
- Will this technology exist in 10 years?
- Is it open source (or has open standard)?
- Can it be replaced without rewriting the platform?
- Is there a migration path to a successor?
- Does the community have critical mass?

---

## PART 15: Governance Documents Registry

| Document | Authority | Scope | Relationship |
|----------|-----------|-------|-------------|
| ENGINEERING_CONSTITUTION.md | Perm. Architecture Review Board | Engineering governance | THIS DOCUMENT |
| PLATFORM-CONSTITUTION.md | Supreme Engineering Authority | Architecture, Quality, Security, AI, Ops, Dev, Release | Supreme authority |
| docs/architecture/ | Architecture Board | Architecture decisions, diagrams | Supplements Article I |
| docs/security/ | Security Team | Security standards, procedures | Supplements Article IV |
| docs/ai/ | AI Ethics Board | AI governance, model safety | Supplements Article V |
| docs/sovereign/ | National Trust Board | Sovereignty, compliance | Supplements Article II |
| docs/trust/ | Trust Framework Authority | Privacy, consent, signatures | Supplements Article II |
| docs/factory/ | Engineering Automation | Automation, code generation | Supplements Article VII |
| docs/adr/ | Architecture Board | All ADRs (26 active) | Decision records |
| CLAUDE.md | Engineering Lead | Operational handbook | Day-to-day guidance |

---

## ADDENDUM A: Architecture Decision Records Index

| ADR | Title | Article Supported |
|-----|-------|------------------|
| ADR-001 | Engineering Constitution | Part 1, Part 2 |
| ADR-002 | Monolith-first Strategy | Part 3 |
| ADR-003 | Multi-Tenant Isolation | Part 3, Part 12 |
| ADR-004 | Skill Platform | Part 7 |
| ADR-005 | PostgreSQL + Redis Stack | Part 3, Part 14 |
| ADR-006 | Clinical AI Integration | Part 10, Part 11 |
| ADR-007 | Device Bridge (ASTM/HL7) | Part 7 |
| ADR-008 | Patient Card System | Part 11 |
| ADR-009 | Self-Healing Infrastructure | Part 14 |
| ADR-010 | SNDHS Government Integration | Part 12 |
| ADR-011 | Notification Platform | Part 7 |
| ADR-012 | Engineering Automation / Identity | Part 15 |
| ADR-013 | Production Platform | Part 3 |
| ADR-014 | Observability Stack | Part 2 (Trace) |
| ADR-015 | Disaster Recovery | Part 14 |
| ADR-016 | National EHR | Part 12 |
| ADR-017 | National Data Platform | Part 12 |
| ADR-018 | National Operations | Part 12 |
| ADR-019 | National Ecosystem | Part 12 |
| ADR-020 | Citizen Super App | Part 13 |
| ADR-021 | National Intelligence | Part 10 |
| ADR-022 | Doctor Workspace | Part 4 |
| ADR-023 | Laboratory Desktop | Part 4 |
| ADR-024 | Platform Constitution | Supersedes all prior |

---

## ADDENDUM B: Amendment Process

### B.1 Standard Amendment

```
1. RFC Proposal -> 2. Architecture Review -> 3. Comment Period (14 days)
                                             4. Vote (7/10 majority)
                                             5. ADR documentation
                                             6. Implementation
```

### B.2 Emergency Amendment

For security or regulatory emergencies:
1. Engineering Lead approves (immediate)
2. ADR documented within 24 hours
3. Architecture Board ratifies within 7 days

### B.3 Amendment Types

| Type | Approval | Notice Period | Version Bump |
|------|----------|---------------|-------------|
| Editorial | Engineering Lead | None | PATCH |
| Substantive | Architecture Board (7/10) | 14 days | MINOR |
| Structural | Architecture Board (9/10) | 30 days | MAJOR |

---

## ADDENDUM C: Signatories

This Engineering Constitution is adopted by the Permanent Architecture Review Board:

| Role | Representative |
|------|---------------|
| Enterprise Architect | TBD |
| Government Architect | TBD |
| Healthcare Architect | TBD |
| Cybersecurity Architect | TBD |
| Cloud Architect | TBD |
| Clinical Safety Expert | TBD |
| AI Researcher | TBD |
| Platform Engineer | TBD |
| Data Architect | TBD |
| Legal & Compliance Advisor | TBD |

**Adopted:** 2026-07-17
**Version:** 1.0.0
**Status:** FROZEN

---

*This ENGINEERING CONSTITUTION complements PLATFORM-CONSTITUTION.md. Where conflicts exist, PLATFORM-CONSTITUTION.md takes precedence. This document provides detailed implementation rules and governance processes.*

*End of Document*
