---
name: gula-source-verification
description: Verifies technical claims, framework behaviour, APIs, dependencies, standards, and external implementation guidance against authoritative sources before GULA adopts them.
---

# GULA Source Verification

## Purpose

Prevent implementation decisions based on outdated, hallucinated, ambiguous,
or unsupported technical claims.

## Source Priority

Prefer:

1. Official standard
2. Official vendor documentation
3. Official project documentation
4. Official source repository
5. Official release notes
6. Authoritative security advisory
7. High-quality secondary source
8. Community discussion

Community content must not override authoritative documentation without
strong evidence.

## Version Awareness

For every version-sensitive claim establish:

- package/project;
- version;
- relevant API;
- source;
- date when relevant.

Never assume that behaviour from another version remains valid.

## Required Evidence

For important technical decisions record:

- claim;
- source;
- evidence;
- version;
- limitations;
- decision.

## Healthcare Standards

For FHIR, HL7, laboratory standards, security standards, or regulatory
requirements, prefer the authoritative standard or issuing organization.

## Conflict

When sources disagree:

1. identify the conflict;
2. determine version/date;
3. identify authoritative source;
4. document the resolution;
5. do not silently choose an answer.

## Prohibited

Do not present:

- model memory;
- guesses;
- undocumented behaviour;
- unverified repository claims

as established facts.
