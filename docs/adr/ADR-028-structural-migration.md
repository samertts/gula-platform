# ADR-028: Structural Migration Rules

**Status:** Accepted
**Date:** 2026-08-07
**Deciders:** Engineering Lead, Platform Architect, CTO

---

## Context

The Architecture Policy Engine (ADR-027) and the Architecture Constitution Gate
(Commit 0.2) are now certified. The platform holds 57 acknowledged Shared Core
reimplementation findings plus 2 country-hardening findings in
`.ai/core/architecture/constitution_baseline.json` — known debt awaiting
migration to the canonical Shared Core providers (`SHARED_CORE_CATALOG` in
`backend/app/domain_platform/shared_core.py`).

The project now enters the **structural migration phase**: reduce technical debt
without changing production behavior. This phase must not weaken any of the
constitution guarantees (behavior preservation, security, authorization, audit,
database integrity, multi-tenancy, FHIR/HL7/ISO conformance, offline-first).

Because structural migrations are risk-bearing, a deterministic rule set
governs every commit. These rules are the migration constitution.

## Decision

Adopt the following seven rules for the structural migration phase. Every
commit from Commit 1.1 onward SHALL satisfy all of them.

### Rule 1 — Behavior preservation is mandatory

Every migration MUST preserve:

- runtime behavior
- API behavior
- business rules
- security behavior
- authorization
- audit behavior
- database behavior

Structural improvements MUST never change functional behavior.

### Rule 2 — Every deletion must be evidence-based

Nothing may be archived, removed, or replaced unless there is objective
evidence that it is:

- unused,
- superseded,
- duplicated,
- or intentionally deprecated.

Every deletion MUST be justified in the verification report (see Rule 4).

### Rule 3 — Backend remains the authoritative source of truth

The frontend MUST always adapt to backend changes; never the reverse. After
every migration verify:

- OpenAPI compatibility
- frontend consumers
- generated client types
- permissions
- request/response models
- route compatibility

### Rule 4 — Introduce a Migration Impact Report

For every commit include:

- files removed
- files moved
- files replaced
- duplicate code eliminated
- LOC reduction
- dependency changes
- API impact
- frontend impact
- rollback procedure

### Rule 5 — Prefer moving before deleting

Archive first. Delete only after verification. The repository has an
established `archive/` convention for superseded code.

### Rule 6 — Every migration must remain independently reversible

A single `git revert` of the migration commit MUST restore the previous state.
Migrations must therefore be atomic and self-contained.

### Rule 7 — One commit at a time

Execute one commit at a time. After each commit run the complete verification
cycle, produce the Migration Impact Report, and stop for explicit approval
before beginning the next commit.

## Consequences

- Every structural migration commit is self-contained, evidenced, and
  independently reversible.
- The acknowledged-findings baseline shrinks monotonically; it never grows.
- Each commit carries a Migration Impact Report (`docs/baselines/`) and a
  verification report with hard gates (backend suite, policy, architecture
  gate, ruff baseline, OpenAPI byte-compatibility, frontend contract).
- Deleting dead code is permitted only with evidence (Rule 2) and always
  archive-first (Rule 5) when the code is part of a live import graph.
