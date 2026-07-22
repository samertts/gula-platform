# GULA Governance Constitution

## Governance Model

GULA is governed by a structured decision-making process that balances engineering integrity, clinical safety, business value, and strategic alignment.

## Governance Bodies

| Body | Composition | Authority |
|------|-------------|-----------|
| **Architecture Board** | Chief Architect + Domain Architects | Architecture decisions, technology choices, standards compliance |
| **Clinical Safety Board** | Chief Medical Officer + Clinical Domain Experts | Clinical feature approval, patient safety review, CDS validation |
| **Security Board** | CISO + Security Engineers | Security policy, incident response, vulnerability management |
| **Product Council** | Product Managers + Stakeholders | Feature prioritization, roadmap, business value assessment |
| **Technical Review Board** | Senior Engineers | Code quality, testing standards, operational readiness |

## Decision Process

1. **Proposal** — Any team member can propose a change through a documented Architecture Decision Record (ADR). See Article 27 (Architecture Decision Process) for the full ADR lifecycle.

2. **Review** — The relevant governance body reviews the proposal against the Constitution.

3. **Impact Assessment** — Clinical, security, performance, and operational impacts are assessed.

4. **Decision** — Approve, approve with conditions, defer, or reject. All decisions are documented with rationale.

5. **Implementation** — Approved changes are implemented following the Constitution.

6. **Verification** — The implementation is verified against the approval conditions.

7. **Retrospective** — Post-implementation review captures lessons learned.

## Architecture Decision Records

8. **ADRs are stored in `docs/architecture/decisions/`** following the DATE-title.md naming convention.

9. **Every ADR includes:** title, status (proposed/accepted/deprecated/superseded), context, decision, consequences, and compliance.

10. **ADRs are immutable after acceptance.** Superseded ADRs reference their replacement.

## Compliance Verification

11. **Automated compliance checks** run in CI: lint, security scan, test coverage, migration idempotency, OpenAPI validation.

12. **Manual compliance reviews** are conducted for: architecture changes, security-sensitive changes, clinical features, and data model changes.

13. **Compliance exceptions** require written justification and approval from the Architecture Board. Exceptions have expiration dates.

## Release Governance

14. **Release criteria** are defined per release type (patch, minor, major).

15. **All releases** require: passing CI, completed security scan, clinical safety review (for clinical features), architecture board sign-off (for architectural changes), and documented release notes.

16. **Emergency releases** follow a fast-track process with post-release retrospective.
