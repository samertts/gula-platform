---
id: COMPAT-000000
type: compatibility
title: "Compatibility Framework"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [compatibility, semver, contracts, gula-kernel-ext-001]
---

# Compatibility Framework

> Mission: GULA-KERNEL-EXT-001 — Phase 3
> Implementation: `scripts/kernel/ext/compatibility.py`
> Machine-readable matrix: `compatibility.json` (per-domain, generated)

Detects breaking changes for **contracts, plugins, policies, schemas, and
configs** before they ship, and records a versioned, searchable matrix.
Enforces `docs/constitution/23_BACKWARD_COMPATIBILITY.md`.

## Model

| Concept | Definition |
|---|---|
| Semantic version | Strict `X.Y.Z` (`parse_version`, `compare_versions`) |
| Breaking change | Major-version bump (`is_breaking_change`) |
| Contract check | Missing `KERNEL_CONTRACT_FIELDS` detection (`check_contract`) |
| CompatibilityRecord | One row: kind, name, from → to, compatible, notes, checked_at |
| CompatibilityMatrix | Versioned, searchable, persistable (JSON), markdown-renderable |

## Kinds

`contract`, `plugin`, `policy`, `schema`, `config`

## Engine Contracts

Every engine in `ENGINE_REGISTRY` must be contract-conformant. The matrix
(`engine_matrix`) verifies all 16 `KERNEL_CONTRACT_FIELDS` for each of the
7 engines:

- architect, orchestrator, reviewer, builder, deployer, learner, optimizer

## CLI

```bash
python scripts/kernel.py ext-compat           # render + save matrix
python scripts/kernel.py ext-compat-check     # CI gate (exit 1 on break)
python scripts/kernel.py ext-check            # includes contract compat
```

## Rules

1. **Never** break a major version without a migration plan (Phase 4).
2. A breaking record in the matrix blocks the Kernel extension self-check.
3. Plugins must declare the SDK contract version they target; manifest
   validation (Phase 1 SDK) runs before any compatibility record is written.

## Reuse

Composes `scripts/kernel/contract.py` (contract definition) and
`scripts/kernel/core.py` (KERNEL_CONTRACT_FIELDS, ENGINE_REGISTRY). No
contract logic is duplicated.

## Related

- `compatibility.json` — machine-readable matrix
- `docs/constitution/23_BACKWARD_COMPATIBILITY.md` — constitutional basis
- `scripts/kernel/contract.py` — the Kernel engine contract
- Phase 4 Migration Framework — how breaking changes are executed safely
