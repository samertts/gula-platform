# Integration & Survivability Risk Analysis

This document enumerates the cross-institutional integration risks introduced
by sovereign-grade interoperability and the survivability risks that follow
from national-scale deployment. Each risk is assessed against the platform's
existing controls and tagged with the residual exposure after mitigations.

Severity is rated **S1 (catastrophic) → S5 (negligible)**. Likelihood is
**L1 (frequent) → L5 (rare)**. Residual = severity × likelihood **after**
listed mitigations.

---

## R-01 — Cross-tenant identity bleed via national reconciliation

| Field | Value |
|-------|-------|
| Domain | Phase 16 + Phase 19 |
| Severity (untreated) | S1 |
| Likelihood (untreated) | L2 |
| Mitigations | TI-3, TI-5; reconciliation audit chain; immutable merge log; two-person rule for high-confidence merges |
| Residual | S2 / L4 |
| Owner | Health Data Fabric architect |
| Open actions | Implement reconciliation simulation harness; enforce mandatory escalation for cross-province matches |

## R-02 — Adapter privilege drift

| Field | Value |
|-------|-------|
| Domain | Phase 16 |
| Severity | S2 |
| Likelihood | L2 |
| Mitigations | PB-1 (bounded trust domain), adapter manifest review, no inheritance of user privileges |
| Residual | S3 / L3 |
| Owner | Interop security lead |
| Open actions | Quarterly adapter re-review; static check that no adapter file imports `routes/` modules |

## R-03 — Ministry/insurer integration cascade failure

| Field | Value |
|-------|-------|
| Domain | Phase 16 + Phase 17 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Failure isolation (per-adapter circuit breakers), CS-1 clinical-write exemption from concurrency shedding |
| Residual | S3 / L4 |
| Owner | Operational survivability lead |
| Open actions | Add dedicated integration outbox + retry; add chaos test "downstream ministry 503" |

## R-04 — Audit chain corruption during DR failover

| Field | Value |
|-------|-------|
| Domain | Phase 17 + Phase 23 |
| Severity | S1 |
| Likelihood | L4 |
| Mitigations | AI-2 (chain continuity), OS-1 (DR preserves chain), append-only writes, hash chain verifier |
| Residual | S2 / L5 |
| Owner | Audit integrity owner |
| Open actions | Document and rehearse chain-merge protocol on DR cutover |

## R-05 — National outbreak data leakage to operators

| Field | Value |
|-------|-------|
| Domain | Phase 20 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Anonymization pipeline; k-anonymity floor; no raw PII exits analytical perimeter |
| Residual | S3 / L4 |
| Owner | Privacy officer |
| Open actions | Privacy review of every published epidemiology dashboard pre-release |

## R-06 — Silent AI clinical-state mutation

| Field | Value |
|-------|-------|
| Domain | Phase 21 |
| Severity | S1 |
| Likelihood | L4 |
| Mitigations | AG-1 (no clinical authority), AG-3 (fail closed), AG-5 (advisory only), CS-4 (critical results unaffected) |
| Residual | S2 / L5 |
| Owner | Clinical AI owner |
| Open actions | Static enforcement that AI modules cannot write to `LabResult`, `LabOrder`, `Sample` tables |

## R-07 — Autonomous reimbursement / fraud-flag execution

| Field | Value |
|-------|-------|
| Domain | Phase 22 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Read-only fraud detection; mandatory human review; ENABLE_FINANCIAL_ENGINE off by default |
| Residual | S3 / L4 |
| Owner | Health economics lead |
| Open actions | Add explicit role separation between "flagger" and "executor"; never the same account |

## R-08 — Crisis-mode reconciliation duplication

| Field | Value |
|-------|-------|
| Domain | Phase 23 + Phase 19 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | OS-4 (conflict-detectable sync), AI-5 (chained replay), no auto-merge in degraded mode |
| Residual | S3 / L4 |
| Owner | Crisis continuity lead |
| Open actions | Document degraded-mode reconciliation protocol; rehearse twice yearly |

## R-09 — Regulator over-broad query authority

| Field | Value |
|-------|-------|
| Domain | Phase 18 + Phase 24 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | PB-4 (regulator role separation); PB-5 (no role unions clinical+audit modify); export audit log of regulator activity |
| Residual | S3 / L4 |
| Owner | Governance lead |
| Open actions | Define minimum-necessary fields per regulator role; enforce in RBAC tests |

## R-10 — Ecosystem plugin sandbox escape

| Field | Value |
|-------|-------|
| Domain | Phase 25 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | No code-loading plugins in v1; ecosystem extensions are external services, communicating via the same adapter pattern |
| Residual | S3 / L5 |
| Owner | Ecosystem governance owner |
| Open actions | Document explicit decision: "no in-process plugin loader is shipped"; if reversed, full sandbox design required |

## R-11 — Catastrophic regional connectivity loss

| Field | Value |
|-------|-------|
| Domain | Phase 23 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Offline-first edge survivability; paper fallback; sovereign comms fallback (SMS); regional isolation |
| Residual | S3 / L3 |
| Owner | Crisis continuity lead |
| Open actions | Edge agent must accept signed result emissions for ≥ 72h offline; rehearsed quarterly |

## R-12 — Migration drift on a national fleet

| Field | Value |
|-------|-------|
| Domain | Phase 17 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Idempotent migrations; CI migration-gate; staged rollout |
| Residual | S3 / L4 |
| Owner | Platform engineering |
| Open actions | National-fleet migration dashboard (per-tenant version + drift count) |

## R-13 — Telecommunications / payment-gateway compromise

| Field | Value |
|-------|-------|
| Domain | Phase 16 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Adapter-bounded trust; signed message exchange; payment idempotency keys; no shared secrets across institutions |
| Residual | S3 / L4 |
| Owner | Interop security lead |
| Open actions | Contractual security baselines per provider; rotating credentials per-adapter |

## R-14 — Long-term key custody (NID_HMAC_KEY, ENCRYPTION_KEY)

| Field | Value |
|-------|-------|
| Domain | Phase 17 + Phase 24 |
| Severity | S1 |
| Likelihood | L4 |
| Mitigations | Hard-fail on weak/missing secrets; documented rotation procedure; sovereign KMS preferred |
| Residual | S2 / L4 |
| Owner | Security officer |
| Open actions | Formal rotation calendar + rehearsed re-encryption procedure |

## R-15 — Provincial directorate over-reliance on central platform

| Field | Value |
|-------|-------|
| Domain | Phase 17 + Phase 23 |
| Severity | S2 |
| Likelihood | L3 |
| Mitigations | Edge-agent at province level; partial-offline operation; degraded-mode workflows |
| Residual | S3 / L4 |
| Owner | Operational survivability lead |
| Open actions | Province-level capacity model; test "central down, province up" flow quarterly |

---

See `REMAINING_NATIONAL_RISKS.md` for the **ranked residual register** that
this analysis feeds into.
