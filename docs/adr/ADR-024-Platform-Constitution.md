# ADR-024: Platform Constitution & National Trust Framework

**Status:** Accepted (Frozen)
**Date:** 2026-07-16
**Deciders:** GULA Engineering Leadership

---

## Context

The GULA platform has grown to encompass:
- 47+ route modules
- 19 ORM models
- 31+ business services
- 16 core infrastructure modules
- 12 national platform modules
- 43 database migrations
- 52 test modules
- 8 microservices
- 4 frontend applications
- 2,400+ test cases

As the platform scales toward national deployment, a permanent constitution
is required to ensure architectural integrity, security posture, privacy
compliance, data sovereignty, and engineering quality are maintained across
all future development.

Three separate but related missions converge:
1. **M037 (NPCE)** — Platform constitution and engineering standards
2. **M038** — National trust, compliance, privacy and sovereignty
3. **M039 (APFE)** — Autonomous platform factory and engineering automation

## Decision

### 1. Platform Constitution (M037)

Adopt a comprehensive Platform Constitution (`docs/constitution/PLATFORM-CONSTITUTION.md`)
as the supreme engineering authority. The constitution covers:

- **Architecture Constitution**: Clean Architecture, DDD, CQRS, Event-Driven,
  Hexagonal, Modular Monolith, Microservice Rules, Offline First, FHIR First,
  API First, Security/Privacy/Accessibility/Observability/AI By Design
- **Engineering Constitution**: Coding/naming/API/database/migration/testing/logging/
  telemetry/documentation/versioning standards
- **Quality Constitution**: Mandatory gates (coverage >=95%, zero critical bugs,
  zero high vulnerabilities, zero architecture violations, zero circular deps,
  zero dead code, zero unused deps, zero hardcoded secrets, zero broken docs)
- **Security Constitution**: Zero Trust, RBAC, ABAC, mTLS, Encryption, Secrets
  Rotation, SBOM, Supply Chain Security, Dependency/Architecture/Runtime/AI Guardians
- **AI Constitution**: Human Approval, Explainability, Prompt/Model Registry,
  Model Validation/Monitoring, Hallucination/Bias Detection, AI Audit Trail, AI Safety
- **Developer Constitution**: Automatic code/tests/docs/API catalog/SDK/architecture
  validation/security review/release notes generation
- **Operations Constitution**: Monitoring, Tracing, Metrics, Health Checks,
  Backups, Recovery, Chaos Engineering, Capacity Planning, Business Continuity, DR
- **Release Constitution**: Stable/LTS/Beta/RC/Nightly channels, Rollback, Migration
  Validation, Compatibility Validation, Feature Flags
- **Continuous Evolution**: Self-assessment, Tech Debt/Architecture Drift Detection,
  Automatic Refactoring/Performance/Security/Dependency Improvement Suggestions

### 2. National Trust Platform (M038)

Adopt the National Trust Platform (`docs/trust/NATIONAL-TRUST-PLATFORM.md`) as the
supreme authority for:

- Privacy: Consent management, purpose of use, minimum necessary access,
  sensitive record protection, minor/guardian policies, data masking/anonymization/
  pseudonymization, retention policies
- Digital Sovereignty: National data ownership, data residency, cross-border
  transfer prohibition, key ownership, national encryption/backup policies
- Compliance: Configurable framework, evidence collection, compliance dashboards,
  corrective actions, continuous compliance
- Trust Services: Digital signature, timestamping, evidence preservation,
  certificate lifecycle, identity verification, document integrity
- AI Trust: Transparency, explainability, human approval, model/prompt audit,
  bias monitoring, safety validation
- National Audit: Immutable audit, forensic logs, chain of custody, evidence
  export, integrity verification
- Long-Term Preservation: Medical record/archive/migration policies, checksum
  validation, integrity monitoring
- Citizen Trust: Privacy/consent dashboard, access history, notification center

### 3. Engineering Factory (M039)

Adopt the Engineering Factory (`docs/factory/ENGINEERING-FACTORY.md`) as the
supreme authority for automation:

- Repository Intelligence: Dependency/Module/Architecture/Event/API/Data Flow/
  Technical Debt/Ownership graphs
- Autonomous Code Factory: Automatic CRUD/Repository/DTO/Command/Query/Event/
  Service/REST/GraphQL/SDK/CLI/Doc/Test generation
- Autonomous Architecture: Drift detection, circular deps, duplicate logic,
  unused/dead code, performance/scalability/security hotspot detection
- Autonomous DevSecOps: Build, test, security scan, dependency upgrade, SBOM,
  release notes/changelog/versioning/packaging/deployment automation
- Autonomous Quality: Ruff/MyPy/Pytest/Coverage/Bandit/Semgrep/Trivy/pip-audit/
  Safety/OpenAPI/FHIR/Architecture/Performance/Accessibility enforcement
- Autonomous Documentation: Architecture/API/SDK/Operations/Security/Developer/
  User/Training/Migration documentation generation
- Autonomous Operations: Monitor/Trace/Scale/Recover/Rollback/Backup/Restore/
  Rotate secrets/certificates/Optimize resources
- Engineering Knowledge Graph
- Engineering AI Assistants
- Continuous Evolution with RFC/ADR/Implementation/Migration/Risk analysis generation

### 4. Execution Program

Adopt Execution Program 001 (`docs/execution/EXECUTION-PROGRAM-001.md`) as the
active implementation roadmap.

## Consequences

### Positive

- Single authoritative source for all engineering decisions
- No architecture drift permitted
- Automated compliance checking
- Clear upgrade and security policies
- Zero hardcoded secrets policy
- Self-documenting platform
- Self-testing platform
- Production-ready quality gates

### Negative

- Initial compliance burden for existing code
- Migration effort to meet strict standards
- Learning curve for new contributors

### Neutral

- ADR-024 supersedes and extends prior ADRs
- Existing architecture remains frozen
- All new development follows this constitution

## Alternatives Considered

1. **Incremental adoption** — Rejected: would leave gaps and ambiguities
2. **External framework adoption** — Rejected: no single framework covers all requirements
3. **Platform-specific minimal set** — Rejected: national scale requires comprehensive governance

## References

- ADR-001: Platform Architecture
- ADR-002: Monolith-first Strategy
- ADR-009: Self-healing Architecture
- ADR-010: SNDHS Government Integration
- `docs/constitution/PLATFORM-CONSTITUTION.md`
- `docs/trust/NATIONAL-TRUST-PLATFORM.md`
- `docs/factory/ENGINEERING-FACTORY.md`
- `docs/execution/EXECUTION-PROGRAM-001.md`
