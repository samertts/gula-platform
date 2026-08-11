# Addy Osmani Agent Skills — GULA Assessment

Source:
https://github.com/addyosmani/agent-skills.git

Version:
0.6.2

Commit:
d187883b7d761265309cdcc0f202cc76b4b3fb06

## Decision

ACCEPTED AS EXTERNAL FOUNDATION.

These skills are engineering workflow references.
They are not GULA-native authority.

## Purpose

The selected workflows provide foundations for:

- specification
- planning
- implementation
- testing
- verification
- debugging
- security
- API design
- CI/CD
- code review
- documentation
- observability
- performance
- release management

## GULA-specific adaptation required

Generic skills do not define:

- clinical safety;
- PHI/PII handling;
- FHIR semantics;
- laboratory semantics;
- Iraqi regulatory requirements;
- national identity;
- multi-tenancy;
- GULA security boundaries;
- GULA AI governance.

These must remain GULA-native.

## Promotion Strategy

Examples:

test-driven-development
→ gula-test-driven-development

security-and-hardening
→ gula-security-hardening

source-driven-development
→ gula-source-driven-development

doubt-driven-development
→ gula-decision-verification

frontend-ui-engineering
→ gula-frontend-engineering

## Update Policy

No automatic upstream updates.

Every update requires source diff + security review + regression verification.
