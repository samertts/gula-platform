---
name: gula-decision-verification
description: Challenges high-impact GULA technical and architectural decisions before implementation using evidence, alternatives, failure analysis, reversibility, security, and operational risk.
---

# GULA Decision Verification

## Purpose

Prevent unsupported assumptions from becoming permanent architecture.

## Trigger

Use for decisions involving:

- architecture;
- databases;
- identity;
- security;
- infrastructure;
- AI models;
- external services;
- clinical workflows;
- FHIR;
- national-scale integrations;
- irreversible migrations;
- significant cost;
- production availability.

## Decision Process

CLAIM
→ EVIDENCE
→ ASSUMPTIONS
→ ALTERNATIVES
→ FAILURE MODES
→ SECURITY
→ PERFORMANCE
→ OPERATIONS
→ COST
→ REVERSIBILITY
→ DECISION

## Mandatory Questions

1. What exactly are we claiming?
2. What evidence supports it?
3. What assumptions are hidden?
4. What could make the decision wrong?
5. What are the alternatives?
6. What happens when the dependency fails?
7. What happens offline?
8. What happens under load?
9. What is the security impact?
10. What is the operational burden?
11. Can the decision be reversed?
12. What is the migration path?

## National-scale Considerations

For GULA national-scale decisions consider:

- availability;
- scalability;
- network instability;
- offline operation;
- data sovereignty;
- disaster recovery;
- operational simplicity;
- cost;
- vendor lock-in;
- interoperability.

## Stop Condition

If a high-impact decision lacks sufficient evidence:

STOP.

Do not silently convert an assumption into implementation.

## Output

For significant decisions produce or update an ADR when appropriate.

The ADR should capture:

- context;
- decision;
- alternatives;
- consequences;
- risks;
- rollback/reversal strategy.
