# GULA Behavioral Test Result Contract

Each executed test must record:

## Identity

- Test ID
- Skill
- Execution timestamp
- Agent/model
- Environment

## Input

Exact scenario supplied to the Agent.

## Actual Response

Exact response produced by the Agent.

## Evaluation

For every expected behaviour:

- PASS
- FAIL
- PARTIAL
- NOT-OBSERVED

## Severity

If failure occurs:

- Critical
- High
- Medium
- Low

## Decision

One of:

- PASS
- FAIL
- CONDITIONAL

## Evidence

Explain exactly why the result was classified that way.

## Certification Rule

No Skill may be marked CERTIFIED without actual response evidence.

A missing response is NOT a PASS.
