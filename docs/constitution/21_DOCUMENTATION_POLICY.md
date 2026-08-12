# GULA Documentation Constitution

## Documentation Principles

1. **Documentation is a first-class deliverable.** Features are not complete until their documentation is written and reviewed.

2. **Documentation serves its readers.** Know your audience: developer, operator, clinician, citizen, or integrator. Write for them.

3. **Documentation is maintained with the code.** Outdated documentation is worse than no documentation. Docs are updated in the same PR as the code change.

4. **Documentation is discoverable.** Clear structure, consistent naming, and cross-references ensure readers find what they need.

## Documentation Types

| Type | Location | Audience | Purpose |
|------|----------|----------|---------|
| **Architecture** | `docs/architecture/` | Developers, Architects | System design, decisions, patterns |
| **Constitution** | `docs/constitution/` | Everyone | Governing principles and rules |
| **API** | Auto-generated from OpenAPI | Integrators | Endpoint reference |
| **Operations** | `docs/operations/` | Operators, SRE | Deployment, monitoring, DR |
| **Clinical** | `docs/clinical/` | Clinicians | Workflow guides, reference guides |
| **User Guides** | `docs/user-guides/` | End users | How-to guides, FAQs |
| **Development** | CLAUDE.md, README.md, CONTRIBUTING.md | Developers | Setup, conventions, contributing |
| **Release Notes** | `CHANGELOG.md` | Everyone | What changed in each release |

## Documentation Standards

5. **Markdown** is the primary format. Diagrams use Mermaid for in-doc diagrams and draw.io for complex architecture diagrams.

6. **Arabic documentation** is provided for user-facing and clinical documentation. English is the primary language for technical documentation.

7. **Every document has:** title, purpose, audience, and last-updated date.

8. **Code examples** in documentation are tested. Inline examples that cannot be tested are marked as illustrative.

## Documentation Review

9. **Documentation is reviewed** as part of the PR review process.

10. **Documentation reviews** verify: accuracy, completeness, clarity, and consistency with the codebase.

11. **Outdated documentation** is flagged by automated freshness checks. Documents older than 6 months are reviewed for relevance.

## API Documentation

12. **OpenAPI specification** is the authoritative API reference. It is generated from code and published.

13. **Every endpoint** has: summary, description, request/response examples, error codes, and permission requirements.

14. **API changelog** documents breaking and non-breaking changes per version.
