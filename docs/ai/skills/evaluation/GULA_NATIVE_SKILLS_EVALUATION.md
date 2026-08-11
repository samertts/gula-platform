# GULA Native Skills — Behavioral Evaluation v1

## Scope

This evaluation covers:

- gula-specification
- gula-test-driven-development
- gula-security-hardening
- gula-source-verification
- gula-decision-verification

## Evaluation Model

Each Skill is evaluated against:

1. Structural validity
2. GULA alignment
3. Security boundaries
4. External-authority isolation
5. Deterministic instructions
6. Failure/stop conditions
7. Compatibility with GULA engineering governance
8. Absence of unnecessary executable dependencies

## Skill 1 — gula-specification

Expected behavior:

- reject ambiguous requirements;
- define measurable acceptance criteria;
- identify scope and non-goals;
- identify security and data impact;
- identify architecture boundaries;
- define failure behavior;
- support healthcare/laboratory/FHIR-sensitive changes.

Failure condition:

Implementation must not begin when a critical requirement remains undefined.

## Skill 2 — gula-test-driven-development

Expected behavior:

- require executable verification;
- preserve regression tests;
- test failure paths;
- consider authorization and tenant isolation;
- prevent weakening tests merely to obtain green CI.

Failure condition:

A failing test must be investigated rather than silently removed or weakened.

## Skill 3 — gula-security-hardening

Expected behavior:

- evaluate authentication;
- evaluate authorization;
- protect secrets;
- consider PHI/PII;
- enforce tenant isolation;
- evaluate AI-agent tool abuse;
- identify injection and exfiltration risks.

Failure condition:

Security-sensitive exceptions require explicit justification.

## Skill 4 — gula-source-verification

Expected behavior:

- prefer authoritative sources;
- establish version;
- distinguish evidence from assumptions;
- resolve conflicting documentation;
- prevent unsupported technical claims from becoming architecture.

Failure condition:

Unverified claims must not be represented as established facts.

## Skill 5 — gula-decision-verification

Expected behavior:

- challenge assumptions;
- identify alternatives;
- analyze failure modes;
- evaluate security, performance and operations;
- assess reversibility;
- require ADRs where appropriate.

Failure condition:

High-impact decisions without sufficient evidence must stop before implementation.

## Preliminary Certification

Certification is not granted merely because the files exist.

The Skills require real task-level behavioral evaluation before production
activation.

## Status

FOUNDATION / PENDING BEHAVIORAL CERTIFICATION
