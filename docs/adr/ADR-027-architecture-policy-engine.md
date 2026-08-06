# ADR-027: Architecture Policy Engine

**Status:** Accepted
**Date:** 2026-08-06
**Deciders:** Engineering Lead, Platform Architect, CTO

---

## Context

Commit 0.1 introduced the Dormancy Registry (ADR-026) as a single-purpose
validation wired into Domain certification check 10. The platform, however,
accumulates governance rules faster than it can wire them individually:
Shared Core reimplementation scans, domain isolation, lifecycle state
machines, cross-domain contracts, API governance, security posture, and data
governance each need a deterministic, CI-enforced gate. Wiring each rule
directly into certification, the architecture gate, and CI would couple every
rule to every consumer and make governance impossible to reason about.

The platform needs a **single governance entry point**: one engine that runs
independent policy modules, aggregates deterministic results, supports
severity levels and acknowledged-debt baselines, and feeds CI/CD, the
Architecture Gate, and Domain Certification with identical machine-readable
outcomes.

## Decision

Introduce the **Architecture Policy Engine**
(`backend/app/domain_platform/policies/`), a generic framework where the
Dormancy Policy is simply the first implemented policy.

### The `Policy` contract

Every policy satisfies a common `typing.Protocol`:

| Member | Meaning |
|---|---|
| `name` | Stable identifier (e.g. `dormancy_policy`) |
| `description` | Human-readable scope of the rule |
| `enabled` | Whether the engine executes it |
| `evaluate(context) -> PolicyResult` | Deterministic evaluation |

Adding a future governance rule = adding one module that implements this
contract and registering it — **never an engine change**.

### Engine behavior

- `PolicyEngine.run(context)` executes every *enabled* policy in
  registration order (deterministic), then applies baseline waivers.
- Each `PolicyResult` carries `status` (`pass`/`warn`/`fail`/`skipped`/
  `error`), the worst `severity` (`info`/`minor`/`major`/`critical`),
  machine-readable `findings`, and a human-readable `summary`.
- `PolicyReport` renders both a JSON payload (for CI and tooling) and a
  Markdown report (for humans).
- Verdict aggregation: any `fail`/`error` → gate FAIL; any `warn` →
  gate WARN; otherwise PASS. Critical/major findings fail; minor findings
  warn; info findings pass.
- **Deterministic output.** Reports carry no timestamps or durations;
  status is derived from findings and findings are emitted in a stable
  order. Two runs over the same context produce byte-identical JSON and
  Markdown — required for CI diffing and reproducible governance.

### Waivers / baselines

`PolicyBaseline` loads acknowledged-debt waivers from a committed JSON file
(`.ai/core/policies/policy_baseline.json`). Waived findings are removed from
the gated result (the status is recomputed), so acknowledged debt never
blocks CI — and anything *not* acknowledged still fails. This mirrors the
Architecture Constitution baseline (PROGRAM-ALPHA) but is policy-generic.

### Policy catalog (10 policies)

`POLICY_CATALOG` is the authoritative list. The Dormancy Policy is the only
enabled policy; the other nine are registered **disabled** (no rule bodies,
no fake logic) so the manifest always documents the full catalog and enabling
them is configuration:

| Policy | Scope | State |
|---|---|---|
| `dormancy_policy` | Protected strategic assets (ADR-026) | **implemented** |
| `lifecycle_policy` | Domain lifecycle state machine | registered, disabled |
| `domain_ownership_policy` | No Domain owns another Domain | registered, disabled |
| `production_readiness_policy` | Health/observability/deployment/DR | registered, disabled |
| `shared_core_policy` | Shared Core usage 100% | registered, disabled |
| `dependency_policy` | Circular/skip-layer dependencies | registered, disabled |
| `cross_domain_communication_policy` | Contracts/gateway-only traffic | registered, disabled |
| `api_governance_policy` | Versioning/idempotency/OpenAPI | registered, disabled |
| `security_policy` | OWASP ASVS / API Top 10 posture | registered, disabled |
| `data_governance_policy` | Retention/classification/auditability | registered, disabled |

### Integration points (single governance entry point)

1. **Certification** — check 10 (`dormancy_policy`) now delegates to the
   shared `DormancyPolicy` module; the adapter maps the policy result onto
   the `CheckResult` shape. Certification, the gate, and CI therefore run
   the identical rule implementation (backward compatible: 10 checks,
   11/11 certification unchanged).
2. **Architecture Gate** — `run_all_gates()` now includes a `policies`
   section produced by the engine; the gate verdict depends on it.
3. **CI/CD** — `ai-governance.yml` runs `architecture-policy`; the
   `architecture-check` hard gate already includes the policy verdict.
4. **CLI / Kernel** — `architecture-policy`, `architecture-policy-json`,
   and `architecture-policy-baseline` are wired into the Architecture CLI
   and the Kernel.

## Consequences

**Positive:**

- Governance is one engine, many modules: enabling a future policy is a
  one-line registry change that automatically joins certification's
  consumers, the gate, and CI.
- Deterministic, severity-aware, machine-readable (JSON) *and*
  human-readable (Markdown) outcomes from a single source.
- Acknowledged debt is managed through policy-generic waivers without
  touching policy implementations.
- Each policy is independently testable (interface-level fakes + per-policy
  unit tests).
- Dormancy semantics are byte-for-byte preserved (all 47 Commit 0.1 tests
  and the 11/11 certification stay green).

**Negative / trade-offs:**

- Future policies are scaffolded but intentionally contain no rule bodies;
  each still needs a real implementation before it can be enabled.
- A shared baseline file adds one governance artifact to keep in sync.
- The engine evaluates enabled policies in one pass; very expensive future
  policies will need per-policy caching/selection (a future evolution, not a
  redesign).

## Alternatives considered

- **One policy per consumer** (wiring each rule into certification, gate,
  and CI separately): duplicated enforcement logic and divergent behavior;
  rejected.
- **A monolithic rules file**: every rule coupled to every other; cannot be
  independently tested or versioned; rejected.
- **Middleware-style hooks in certification**: hides governance behind the
  certification API and does not serve CI; rejected.
- **Over-engineered plugin framework** (dynamic loading, hot-reload, DSL):
  not needed yet; the static `Policy` Protocol + registry provides the same
  extension seam with far less machinery.
