# POLICY CERTIFICATION

**Mission:** GULA-KERNEL-EXT-001 — Phase 11 (Final Certification)
**Certifier:** Kernel Extension Certification (deterministic engine checks)
**Date:** 2026-08-05
**Verdict:** **CERTIFIED**

---

## Scope

Certification of the Policy Engine (Phase 2): 16 canonical policies
encoding the constitution as machine-readable rules.

## Results

- **Policies:** 16 (`POLICY-000001` … `POLICY-000016`)
- **Categories:** 16 (security, architecture, deployment, knowledge,
  testing, performance, documentation, cost, autonomy, rollback, resource,
  context, retry, approval, risk, compliance)
- **Operators:** 10 (eq, neq, lt, lte, gt, gte, in, not_in, contains, matches)
- **Validation:** 100% of policies pass `validate_policy`
- **Unique ids:** 16/16
- **Versioned replacement audit:** verified (deprecation + history)

## Rule Coverage (sample)

| ID | Category | Rule | Action |
|---|---|---|---|
| POLICY-000001 | security | no secrets in knowledge artifacts | deny |
| POLICY-000002 | deployment | production deploys require Reviewer approval | deny |
| POLICY-000003 | autonomy | max autonomy is L5 (pull request) | deny |
| POLICY-000004 | resource | micro phases ≤ 50 files | deny |
| POLICY-000006 | knowledge | unverified knowledge must not be approved | deny |
| POLICY-000009 | cost | no paid services without documented exception | deny |
| POLICY-000012 | compliance | national platform capabilities must not be removed | deny |
| POLICY-000013 | performance | no optimization without benchmarks | warn |
| POLICY-000016 | risk | high-risk missions require simulation | deny |

## Machine-Readable Parity

`policies.json` is generated directly from `default_policies()` — zero
drift between executable source and catalog.

## Checks Performed

- `validate_policy` — id/category/action/operator/statement
- `ext-policy` — registry snapshot (16 registered)
- `ext-policy-evaluate` — sample context (2 DENY + 1 WARN expected)
- `ext-check` — policy registration gate
- `policies.json` — regenerated from source of truth

## Evidence

- `backend/tests/unit/test_kernel_ext_policy.py` — 36 tests passing
- `.ai/core/policies/README.md`, `POLICIES.md`, `policies.json`
- `python scripts/kernel.py ext-policy` — 16 policies active

---

**Verdict: PASS** — the Policy Engine is enterprise-certified.
