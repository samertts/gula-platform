---
id: POLICY-INDEX
type: policies
title: "Policy Engine — Catalog"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [policy, governance, gula-kernel-ext-001]
---

# Policy Catalog

> Mission: GULA-KERNEL-EXT-001 — Phase 2
> Implementation: `scripts/kernel/ext/policy.py`
> Machine-readable defaults: `policies.json`

Every rule in the GULA AI Kernel is a versioned, auditable, composable,
replaceable, searchable, machine-readable policy. Policies are declarative
conditions (`field`, `operator`, `value`) — **changing a policy never
requires changing code**.

## Categories

| Category | Governs | Constitution source |
|---|---|---|
| security | secrets, sandbox, access | 08_SECURITY |
| architecture | clean architecture, ADR | 05_ARCHITECTURE, 11_AI |
| deployment | deploy approvals, rollback | 22_RELEASE |
| knowledge | verification, lifecycle | 08_KNOWLEDGE |
| testing | quality gates, regression | 20_TESTING |
| performance | benchmarks, budgets | 24_WORLD_BENCHMARK |
| documentation | public features | 21_DOCUMENTATION |
| cost | paid dependencies, exceptions | COST_GOVERNANCE |
| autonomy | autonomy levels L0-L8 | 32_AI_EXECUTION |
| rollback | rollback plans | 23_BACKWARD_COMPATIBILITY |
| resource | 5-min/50-file phases | 32_AI_EXECUTION |
| context | context budget | 32_AI_EXECUTION |
| retry | bounded retries | 32_AI_EXECUTION |
| approval | who must approve | 27_ARCHITECTURE_DECISION |
| risk | simulation requirement | 32_AI_EXECUTION |
| compliance | national platform invariants | 06_DOMAIN, 26_NATIONAL |

## Operators

`eq`, `neq`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`, `contains`, `matches`

## Composition

- Multiple policies apply with **AND** semantics (any `deny` blocks).
- `warn` reports without blocking.
- Replacement: registering the same policy id at a higher version
  deprecates the old version and writes an audit-history entry.

## Default Policy Set

16 canonical policies (`POLICY-000001` … `POLICY-000016`) encode the
constitution as machine-readable conditions. See `POLICIES.md` for the
human-readable catalogue, or `scripts/kernel/ext/policy.py::default_policies()`
for the executable source.

## CLI

```bash
python scripts/kernel.py ext-policy           # registry snapshot
python scripts/kernel.py ext-policy-evaluate  # evaluate sample context (CI gate)
python scripts/kernel.py ext-check            # includes policy registration check
```

## Reuse

The Policy Engine reuses Governor authority (ownership), quality gates, and
safety logic; it encodes rules as data instead of re-implementing them.

## Related

- `POLICIES.md` — human-readable policy catalogue
- `policies.json` — machine-readable policy set
- `AI_OPERATING_CONSTITUTION.md` — supreme authority
