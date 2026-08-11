---
name: gula-specification
description: Defines and validates GULA engineering specifications before implementation. Use for new features, architectural changes, integrations, APIs, data models, security-sensitive changes, and cross-platform work.
---

# GULA Specification

## Purpose

Convert a requested change into an explicit, testable GULA specification
before implementation begins.

## Mandatory Principle

Do not implement ambiguous requirements.

If the requirement is incomplete, identify the missing information before
implementation.

## Required Specification

Every non-trivial change must define:

1. Objective
2. Scope
3. Non-goals
4. Actors
5. Inputs
6. Outputs
7. Preconditions
8. Postconditions
9. Business rules
10. Security requirements
11. Data requirements
12. Failure modes
13. Compatibility requirements
14. Testing requirements
15. Observability requirements
16. Rollback/recovery strategy

## GULA-specific domains

When applicable, explicitly identify impact on:

- patients
- laboratory workflows
- specimens
- test results
- FHIR
- identity
- authentication
- authorization
- multi-tenancy
- PHI/PII
- audit
- offline clinical mode
- analyzer integration
- event bus
- AI systems

## Architecture Constraint

Do not introduce a new subsystem when an existing GULA capability can
satisfy the requirement without compromising architecture.

## Completion Criteria

A specification is complete only when:

- acceptance criteria are measurable;
- failure behaviour is defined;
- security impact is understood;
- affected architecture boundaries are identified;
- tests can be written from the specification.

## Prohibited

Never treat an AI-generated implementation plan as the specification itself.

The specification is the source of truth for implementation.
