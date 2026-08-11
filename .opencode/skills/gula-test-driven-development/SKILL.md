---
name: gula-test-driven-development
description: Applies GULA test-driven development and verification rules to implementation changes. Use when creating or modifying production code, APIs, business rules, integrations, security controls, or critical workflows.
---

# GULA Test-Driven Development

## Purpose

Ensure that implementation is supported by executable verification rather
than assumptions.

## Core Cycle

RED
→ GREEN
→ REFACTOR
→ VERIFY

## Before Implementation

Identify:

- expected behaviour;
- invalid behaviour;
- boundary conditions;
- failure modes;
- security constraints;
- compatibility requirements.

## Tests

Tests should cover, where applicable:

1. Unit behaviour
2. Integration behaviour
3. API contracts
4. Persistence
5. Authorization
6. Multi-tenancy isolation
7. Error handling
8. Event behaviour
9. Offline/synchronization behaviour
10. Regression cases

## Healthcare-critical behaviour

For clinical or laboratory workflows:

- never weaken a test to make implementation pass;
- never delete a failing regression test without documented justification;
- test invalid clinical states;
- test authorization boundaries;
- test audit requirements;
- test data integrity.

## Quality Gate

Implementation is not complete merely because tests pass.

Also verify:

- architecture compliance;
- security;
- type checking;
- linting;
- relevant integration tests;
- regression tests.

## Failure Rule

A failing test must be investigated.

Do not:

- skip it;
- delete it;
- weaken assertions;
- mock away the behaviour under test;
- change expected behaviour without specification/decision evidence.
