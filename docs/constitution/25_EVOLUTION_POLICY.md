# GULA Evolution Policy

## Evolution Philosophy

GULA is never finished. The platform continuously evolves through incremental improvements that preserve stability, maintainability, and backward compatibility. Evolution is measured, deliberate, and aligned with the long-term vision.

## Evolution Principles

1. **Incremental over revolutionary.** Every change is small enough to be understood, tested, and rolled back independently.

2. **Value-driven.** Every change must provide measurable value to at least one stakeholder group: clinicians, patients, laboratory staff, administrators, public health authorities, or developers.

3. **Architecture-preserving.** Changes work within the existing architecture. New capabilities extend the architecture rather than replacing it.

4. **Learning-informed.** Changes may be inspired by world-class platforms, but are implemented as native GULA capabilities.

## What Can Evolve

| Component | Evolution Approach |
|-----------|-------------------|
| **Business logic** | Refactor for clarity, add new capabilities, improve performance |
| **API contracts** | Add new endpoints, extend schemas. Deprecate old endpoints. |
| **Database schema** | Add new tables and columns. Never remove or alter existing structures. |
| **Frontend UI** | Improve existing screens, add new screens, adopt new component patterns |
| **Authentication/Authorization** | Add new methods, extend permission model, harden security |
| **Integration** | Add new adapters, extend FHIR capabilities, adopt new IHE profiles |
| **AI capabilities** | Add new models, improve existing models, extend clinical decision support |
| **Testing** | Add new tests, improve coverage, adopt new testing patterns |
| **Documentation** | Add new documents, update existing, improve clarity |
| **DevOps/CI/CD** | Improve automation, add new quality gates, reduce cycle time |

## What Must Not Evolve

| Component | Rationale |
|-----------|-----------|
| **Core data models** (patient, order, result) | Breaking changes would require data migration for every deployment |
| **Authentication flows** | Breaking auth would lock users out of the system |
| **Core API versioning strategy** | Breaking versioning would break all integrations |
| **Security architecture** | Security changes require zero-trust redesign, not incremental evolution |

## Evolution Process

5. **Idea** — Any team member proposes an evolution through a GitHub issue or ADR.

6. **Analysis** — The Architecture Board evaluates the proposal against the Constitution.

7. **Design** — A detailed design document is created, including implementation plan, test strategy, rollback plan, and migration impact.

8. **Implementation** — The change is implemented on a feature branch with tests.

9. **Review** — Architecture review, security review, clinical review (if applicable), and code review.

10. **Validation** — The change passes all quality gates in CI.

11. **Deployment** — The change is deployed following the release policy.

12. **Retrospective** — Post-implementation review captures lessons learned and measures actual value delivered.

## Evolution Horizons (aligned with Roadmap — Article 30)

Release cadence follows Article 22 (Release Policy). Horizons define strategic direction; implementation Waves within each horizon scope the tactical execution.

| Horizon | Name | Focus | Timeframe |
|---------|------|-------|-----------|
| **H1** | Foundation | Core platform, lab workflows, enterprise certification | 2025-2027 |
| **H2** | National Platform | Multi-tenant deployment, national identity, referrals | 2027-2029 |
| **H3** | Intelligent Platform | AI-native capabilities, prediction, automation | 2029-2032 |
| **H4** | Regional & Global | Cross-border interoperability, global certification | 2032-2035 |

Each Horizon contains multiple implementation Waves (Article 25.5-12).

## Rejection Criteria

A proposed evolution is rejected if:
- It duplicates existing functionality
- It breaks backward compatibility without strong justification
- It increases complexity without proportional value
- It conflicts with the Constitution
- It cannot be tested adequately
- It introduces unacceptable security or clinical risk
