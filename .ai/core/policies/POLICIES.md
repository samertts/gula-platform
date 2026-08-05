# Policy Catalogue

> Mission: GULA-KERNEL-EXT-001 — Phase 2
> Machine-readable source of truth: `policies.json` (generated from
> `scripts/kernel/ext/policy.py::default_policies()`)

This is the human-readable catalogue of the canonical policy set. The
executable source (`default_policies()`) and `policies.json` are the
single source of truth — this document describes them.

| ID | Category | Action | Rule | Operator / Operand |
|---|---|---|---|---|
| POLICY-000001 | security | deny | No secrets in knowledge artifacts | `content contains "secret"` |
| POLICY-000002 | deployment | deny | Production deploys require Reviewer approval | `deployment_approval eq "auto"` |
| POLICY-000003 | autonomy | deny | Max autonomy is L5 (pull request) | `autonomy_level gt "L5"` |
| POLICY-000004 | resource | deny | Micro phases ≤ 50 files | `phase_files gt 50` |
| POLICY-000005 | resource | deny | Micro phases ≤ 5 minutes | `phase_seconds gt 300` |
| POLICY-000006 | knowledge | deny | Unverified knowledge must not be approved | `knowledge_verified eq false` |
| POLICY-000007 | testing | deny | Missions must not bypass quality gates | `bypass_quality eq true` |
| POLICY-000008 | rollback | deny | Rollback plans required for production deploys | `has_rollback eq false` |
| POLICY-000009 | cost | deny | No paid services without documented exception | `uses_paid_service eq true` |
| POLICY-000010 | approval | deny | Constitution changes require explicit user approval | `constitution_change eq "auto"` |
| POLICY-000011 | architecture | deny | No architecture changes without Architect approval | `architecture_change eq "auto"` |
| POLICY-000012 | compliance | deny | National platform capabilities must not be removed | `removes_national_feature eq true` |
| POLICY-000013 | performance | warn | No optimization without benchmarks | `has_benchmark eq false` |
| POLICY-000014 | documentation | warn | Public features require documentation | `has_docs eq false` |
| POLICY-000015 | context | warn | Context budget limits are enforced | `context_tokens gt 60000` |
| POLICY-000016 | risk | deny | High-risk missions require simulation | `simulated eq false` |

## Extending the Catalogue

To add a policy:

1. Add a `Policy` entry in `default_policies()` (the executable source).
2. Regenerate `policies.json`.
3. Add a regression test in `test_kernel_ext_policy.py`.
4. Update this catalogue.

A policy is replaceable at runtime by registering the same id at a higher
version — the replacement is audited in the engine history and the old
version is deprecated (never deleted).
