# GULA AI Governance — Final Risk Register

> PROGRAM-012, Deliverable 10 — consolidated governance-layer risk register
> Date: 2026-07-31
> Scope: risks specific to AI governance, execution layer, and autonomous engineering.
> For platform-wide risks see: `security/RISK_REGISTER.md`, `docs/reports/risk_register.md`, `reports/RISK_REGISTER.md`.

Methodology: Likelihood (Unlikely / Possible / Likely / Almost Certain) × Impact
(Minimal / Moderate / Significant / Severe) → Level (Low / Medium / High / Critical).

## Top Risks

| ID | Risk | Likelihood | Impact | Level | Mitigation | Owner |
|----|------|-----------|--------|-------|-----------|-------|
| GOV-01 | AI model introduces regression silently (bad refactor, dropped validation) | Likely | Significant | Critical | Baseline regression gate (`reports/validation/baseline.json`), hard gates in `make validate`, CI enforcement | Validation |
| GOV-02 | AI fabricates passing tests or skips verification | Possible | Severe | High | CI reruns tests independently; constitution R7; verification is a hard gate | QA |
| GOV-03 | Architecture drift from layer violations accumulating | Likely | Significant | Critical | Architecture guardian + compliance engine + ADR rule R8 | Architecture |
| GOV-04 | Knowledge goes stale (brain, docs, AGENTS.md) | Almost Certain | Moderate | High | `make brain` freshness gate (7-day), CI check, AGENTS.md anchored summary | Governance |
| GOV-05 | Vendor lock-in via AI-preferred dependency | Possible | Significant | High | Constitution engine Free/Open-Source/Self-Hosted First rules (R6) | Governance |
| GOV-06 | Unsafe destructive migration by automation | Unlikely | Severe | High | Data-preservation constitution 31, migration policy script, R5 | Database |
| GOV-07 | Commit without rollback path in production-critical change | Possible | Significant | High | Safe commit engine (purpose/risk/rollback), blue-green + auto-rollback CI | Release |
| GOV-08 | Multi-agent conflicting implementations merged | Unlikely | Significant | Medium | Constitution 32.6 consensus rule, never auto-merge conflicts | Governance |
| GOV-09 | Dormant modules damaged by over-zealous cleanup | Possible | Moderate | Medium | Constitution: dormant modules are strategic assets; R4 proof requirement | Architecture |
| GOV-10 | Validation engine itself regresses (false pass) | Unlikely | Significant | Medium | Engine unit tests, JSON reports auditable, baseline pinning | Validation |

## Acceptance Criteria

- CRITICAL risks: automated gate in place (GOV-01 ✓ regression gate, GOV-03 ✓ arch guardian).
- HIGH risks: process + tooling in place; reviewed quarterly.
- MEDIUM/LOW: tracked; reviewed annually.

## Escalation

Any CRITICAL-level finding blocks release until resolved. Escalation path:
Validation Engine → Architecture Board (`docs/governance/governance_framework.md`)
→ Executive Committee.
