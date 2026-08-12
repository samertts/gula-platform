# Phase 18-01 — Governance Architecture

## Scope

This phase introduces a **configurable governance-policy framework** at the
documentation and configuration level. No new heavyweight policy engine is
introduced; instead, existing modules (`backend/app/core/feature_flags.py`,
`backend/app/core/sndhs_flags.py`, `backend/app/core/policy_engine.py`,
`backend/app/security/rbac.py`) are organized under one governance contract.

## Architectural Layers

```
+-------------------------------------------------------------+
|  Sovereign Governance Layer (this phase)                    |
|  - Retention policies                                       |
|  - Legal-hold registry                                      |
|  - Role-separation matrix                                   |
|  - AI capability registry                                   |
|  - Audit / compliance contract                              |
+-------------------------------------------------------------+
|  Tenant Governance Layer (existing)                         |
|  - feature_flags.py (per-tenant)                            |
|  - sndhs_flags.py (deployment-wide)                         |
|  - subscription tier matrix                                 |
+-------------------------------------------------------------+
|  Code-Enforced Controls (existing)                          |
|  - RBAC (rbac.py)                                           |
|  - tenant filter (database.py contextvars + route guards)   |
|  - audit chain (audit/)                                     |
|  - clinical safety (optimistic lock, state machine)         |
+-------------------------------------------------------------+
```

The **sovereign governance layer is policy + documentation**; the **tenant
governance layer maps policy to tenant-specific knobs**; the **code layer
enforces**.

A policy that has no code-enforcement counterpart is **documented-only**.
Documented-only policies are tracked in the audit-integrity state matrix
[`04-audit-integrity.md`](./04-audit-integrity.md) so that the gap is
visible.

## Policy Categories

1. **Retention policies** — how long data is retained, by data class.
2. **Legal-hold policies** — when retention is suspended for hold.
3. **Access policies** — who may access what, under what circumstances
   (regulator access, emergency access, audit-only access).
4. **Role-separation policies** — which roles cannot be unioned.
5. **AI policies** — what AI capabilities exist, what authority they have.
6. **Audit policies** — what is logged, what is signed, what is replicated.
7. **Compliance policies** — which standards apply per deployment context.

## Configuration Surfaces

For each category, the configuration surface today is:

| Category | Today's surface | Recommended evolution |
|----------|-----------------|-----------------------|
| Retention | Hardcoded per data class | Per-tenant `retention_policy` table; reviewed annually |
| Legal hold | None | New `legal_holds` table with subject + reason + reviewer |
| Access | RBAC + middleware | New `access_policy` table for break-glass + warrant flows |
| Role separation | `rbac.py` constants | Augment with explicit "incompatible roles" matrix |
| AI | Per-capability flags | New AI capability registry (Phase 21) |
| Audit | `audit/` module | Hash chain + signed daily-roll-up |
| Compliance | Documentation | Standards-mapping matrix kept fresh per release |

The recommendations are **future-phase** work. Phase 18 documents them.

## Configuration Authority

| Category | Set by | Review cadence |
|----------|--------|----------------|
| Retention | Regulator + program owner | Annually |
| Legal hold | Legal counsel + program owner | Per-event |
| Access | Security officer | Quarterly |
| Role separation | Security officer | Annually |
| AI | IRB-AI (Phase 21) | Per-capability |
| Audit | Security officer | Quarterly |
| Compliance | Regulator liaison | Annually + per regulation change |

## Non-Negotiables (Phase 18)

- Retention floor MUST NOT drop below the regulatory minimum.
- A legal hold MUST suspend retention. Retention purges MUST consult the
  legal-hold registry **before** acting.
- Break-glass / emergency access MUST itself be audited and reviewed within
  N business days (N is jurisdiction-defined; default 5).
- A regulator's read access MUST be scoped and time-boxed; no "regulator =
  superuser".
- AI capability changes MUST go through IRB-AI (Phase 21).
