# Architecture Diff & Updated Master Architecture — PROGRAM-STABLE-002

> Generated: 2026-08-02

## What changed (this certification cycle)

| Aspect | Before | After | Impact |
|---|---|---|---|
| Hardcoded health-exchange API key | `LAB_PLATFORM_SECRET` in source | env/key-file + constant-time verify, deny-by-default | Security (P5) |
| Mobile app-info path (frontend) | `/auth/mobile/app-info` (404) | `/mobile/app-info` | Parity (P6) |
| Error surfacing (frontend) | English `detail` only | Arabic-first `detail_ar` | Parity (P6) |
| FK index coverage | partial | migration `20260802_0002` + policy tests | Performance/Reliability (P3/P4) |
| Ruff SIM102 | 1 violation | 0 | Code quality |

No architecture change, no API contract break, no domain boundary change, no feature removal.

## Architecture invariants (re-verified)

1. Backend = single source of truth; frontend = operational representation (0 drift).
2. Shared Core unique for cross-cutting concerns.
3. Domains sovereign; only Shared Core / public APIs / FHIR / HL7 / event bus / approved contracts cross boundaries.
4. Multi-tenancy (lab_id scoping on every query) + RBAC/ABAC + immutable audit preserved.
5. Dormant national modules preserved (constitution) — not activated, not removed.
6. Country-agnostic national identity architecture preserved (NIAM, GPID, canonical patient).

## Architecture debt (advisory, tracked)

- Layer architecture score 21.4/100 (L1: 32 violations, L3: 75, L4: 375; L2 circular: 0).
  No behavior impact; roadmap item for national release.
- 1 flagged cross-domain write (nursing→EHR medication administration) — approved contract,
  risk-registered, single-directional.
- Duplicate-empty `__init__.py` files (3) — harmless, cleanup-listed.

## Updated master architecture (delta only)

All components as documented in `docs/architecture/CANONICAL_ARCHITECTURE.md`,
`docs/architecture/enterprise_architecture.md`, with the above deltas incorporated.
No superseding changes.

## Verdict

**Architecture remains backward compatible and certified.**
