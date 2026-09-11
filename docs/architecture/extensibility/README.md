# Extensibility

**PROGRAM-EXT-001.** How GULA adds a capability without destabilising the Core.

Read in this order:

1. [core-boundary.md](core-boundary.md) — what is Core, what is a capability,
   what is a domain, and where the boundary currently leaks.
2. [capability-contract.md](capability-contract.md) — the metadata a capability
   must declare, and why each field cannot be derived from the code.
3. [domain-contract.md](domain-contract.md) — what a domain owes the platform,
   and the one rule that matters most.
4. [event-contract.md](event-contract.md) — the canonical envelope, versioning,
   and the rules for publishers and consumers.
5. [api-versioning.md](api-versioning.md) — compatible vs breaking, and the
   deprecation lifecycle.
6. [module-lifecycle.md](module-lifecycle.md) — the ten maturity states, the
   evidence each requires, and feature-flag classes.
7. [reusable-capabilities.md](reusable-capabilities.md) — what already exists.
   **Read this before building anything.**
8. [extension-template.md](extension-template.md) — the six files a new
   capability ships with.
9. [global-intelligence-registry.md](global-intelligence-registry.md) — the
   structure PROGRAM-GLOBAL-001 will fill.

Enforced by `backend/tests/test_extensibility_guards.py`, which runs in CI as
part of the Backend Tests job. Contract types live in
`backend/app/kernel/types.py`; validation in
`backend/app/kernel/extensibility.py`.

## What this programme did not do

No new registry was created — GULA already has one that loads at boot, and a
second would be the exact failure this exists to prevent. No capability was
consolidated, no dead code was resurrected, no domain was refactored and no
migration was written. Two findings (NR-050, NR-051) are recorded as decisions
for their owners rather than guessed at.
