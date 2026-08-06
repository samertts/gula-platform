# ADR-026: Dormancy Registry

**Status:** Accepted
**Date:** 2026-08-06
**Deciders:** Engineering Lead, Platform Architect, CTO

---

## Context

The GULA Constitution mandates that dormant enterprise modules are strategic
assets and must never be removed:

> "Never remove dormant enterprise modules. Dormant modules are strategic
> assets. Improve them without activating unfinished functionality."

The platform accumulated a large set of modules in different maturity states —
active production services, dormant bounded contexts, and the consolidated
monorepo roots (`ai/`, `nhop-platform/`, `edge_agent/`, `platform/`). During
the migration program (Commit 0.0 baseline → national releases) the following
risks emerged:

1. **Accidental deletion** — A migration or refactor commit could silently
   delete a dormant module that is a future strategic asset.
2. **Undeclared lifecycle state** — Without an explicit registry, every module
   is implicitly "active", so nothing distinguishes a frozen asset from live
   code, and the archive policy cannot be enforced.
3. **Archived-asset coupling** — An active Domain could come to depend on a
   module scheduled for archival, breaking the release plan.
4. **Non-deterministic archive policy** — The C1.4 archive set was described in
   prose; it must be machine-readable so CI can enforce it.

## Decision

Introduce a **Dormancy Registry** (`backend/app/domain_platform/dormancy.py`)
that gives every source module an explicit, immutable lifecycle state:

| State | Meaning |
|---|---|
| `active_development` | Live module; migration work may touch it |
| `dormant` | Frozen strategic asset; preserved, not developed |
| `archived` | Moved out of the active tree; preserved, never deleted |
| `retired` | Fully superseded; preserved for audit/history |

### Abstraction layer

The registry is **not** a hard-coded single source of truth. It is an
abstraction over a `DormancySource` interface (`typing.Protocol`):

- The **certification engine depends only on the `DormancySource` interface**
  and never on a concrete source implementation.
- The canonical data lives in a committed configuration file
  (`backend/app/domain_platform/config/dormancy.json`) loaded through
  `JsonDormancySource`.
- `build_dormancy_source(kind, ...)` is the single implementation seam. It
  currently resolves `canonical` (JSON config, default), `inmemory`, and
  `json`; the `database` and `governance` kinds are registered as documented
  future providers and fail loudly until implemented.
- Replacing the data source (configuration file → database metadata →
  governance service) is a one-line change inside the factory; the
  certification engine, the check, and its tests are untouched.

### Canonical declarations

- **Archive set (C1.4)** — `ai/`, `nhop-platform/`, `edge_agent/` are declared
  `archived`. They are preserved and must never be removed.
- **Deferred, not archived** — `platform/` is declared `active_development`.
  It is deferred from the active release sequence but is never a candidate for
  archival.
- **Dormant contexts** — `backend/app/national_data/` (warehouse star-schema
  modules) is declared `dormant` and protected.

The declarations are data (the JSON file), not code: the same policy can be
served later by any store without changing the framework.

### Protection invariant

A module in a protected state (`dormant`, `archived`, `retired`) cannot be
removed: `DormancyRegistry.assert_not_removed()` raises on any migration or
refactor commit that would delete a protected path. Declarations are immutable
— a state cannot silently change once recorded.

### Certification integration (10th check)

The Domain Certification engine (`certification.py`) now runs a 10th check,
`dormancy_policy`:

- no active Domain may own an `archived`/`retired` module (fail, severity
  `critical`);
- no active Domain may own a `dormant` module (fail, severity `major`) — a
  frozen strategic asset must not be coupled to live Domain code;
- modules without an explicit declaration are implicitly
  `active_development` (the platform is actively developed) and reported as
  advisory — the registry only *fails* a Domain for protected-asset coupling,
  so the real 11 canonical Domains still certify at 100% while the archive
  set stays protected.

## Consequences

**Positive:**

- The "never remove dormant modules" constitution rule becomes enforceable by
  CI and by Domain certification.
- The archive policy is machine-readable, versioned, and **data-driven** —
  the certification engine is decoupled from any concrete source.
- Certification jumps from 9 to 10 checks; all 11 canonical Domains still
  certify at 100% (backward compatible — no existing Domain behavior changes).
- Migration commits now have a deterministic guard against deleting strategic
  assets.

**Negative / trade-offs:**

- Modules that should be frozen must be explicitly registered as `dormant`
  or `archived`; anything unregistered is treated as `active_development`.
- `DORMANT_MODULES` currently lists only the known dormant context; additional
  dormant modules must be registered as discovered (each registration is
  additive and backwards compatible).

## Alternatives considered

- **Prose-only policy** (previous state): unenforceable; rejected.
- **Git-only history as the registry**: deletion is only discoverable after it
  happened; rejected because we need a forward-looking gate.
- **Auto-detection by last-commit date**: non-deterministic and silent; rejected
  in favour of explicit, auditable declarations.
