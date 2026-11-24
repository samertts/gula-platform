# NATIONAL INTEGRATION ROADMAP — patient-centred, evidence-scored

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` · **HEAD:** `2827c1ff`
**Date:** 2026-11-17
**Inputs:** `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` + `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md`
**Release status:** `GOVERNANCE/FINAL_DECISION.md` = **HOLD** (unchanged)

> **This is a plan, not an authorisation.** No wave may start until its listed
> entry gate is signed off. Nothing here was implemented, migrated, committed or deployed.

---

## 1. Scoring model (deterministic, reproducible)

Each service is scored 1–5 on six axes. Higher is better on benefit/readiness axes;
higher is **worse** on risk axes (and is inverted in the formula).

| Axis | 1 | 5 | Evidence used |
|---|---|---|---|
| **M** — MoH relevance | niche | national mandate | service purpose vs national platform scope |
| **P** — Patient benefit | indirect | direct life/health impact | clinical pathway position |
| **R** — Implementation readiness | not built | stable contract | contracts §6 status + migrations + tests |
| **C** — Clinical risk if left broken | low | safety-critical | audit gaps, transfusion/maternal/emergency exposure |
| **D** — Architecture dependency (blocking others) | leaf | substrate | dependency map, inventory §11 |
| **T** — Testability today | untestable | contract-testable now | existing tests + schema availability |

**Priority = (M + P + R + C + D + T)**, tie-broken by **C then D**.
`Blocked-by` records the ADR(s) that must be approved first — a blocked service cannot
start even with a high score.

---

## 2. Service priority table

| Rank | Service | M | P | R | C | D | T | **Score** | Wave | Blocked by |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | **Substrate: migrations + audit for `cc_*` / `ehr_*`** | 5 | 5 | 4 | 5 | 5 | 3 | **27** | W1 | ADR-A, ADR-C, ADR-D |
| 2 | Referral & continuity of care | 5 | 5 | 4 | 4 | 4 | 3 | **25** | W2 | ADR-A, ADR-C |
| 3 | Blood bank (audit + auth) | 4 | 5 | 4 | 5 | 3 | 3 | **24** | W2 | ADR-D |
| 4 | Maternal & child health | 5 | 5 | 3 | 5 | 3 | 2 | **23** | W2 | ADR-A, ADR-C |
| 5 | Primary healthcare | 5 | 5 | 3 | 4 | 5 | 2 | **24** | W2 | ADR-A, ADR-C |
| 6 | Laboratory (contract hardening) | 4 | 4 | 5 | 3 | 5 | 5 | **26** | W2 | — (typed schemas only) |
| 7 | Pharmacy (authz + dispense events) | 4 | 4 | 5 | 4 | 3 | 4 | **24** | W2 | — |
| 8 | Immunization | 5 | 5 | 3 | 4 | 3 | 2 | **22** | W3 | ADR-A, ADR-C |
| 9 | Hospital (schema + audit) | 4 | 4 | 2 | 4 | 4 | 2 | **20** | W3 | ADR-A, ADR-D |
| 10 | Emergency & ambulance | 4 | 4 | 4 | 4 | 3 | 3 | **22** | W3 | — (typed schemas) |
| 11 | Radiology | 4 | 3 | 4 | 3 | 3 | 3 | **20** | W3 | — (1 table) |
| 12 | Chronic disease mgmt | 5 | 4 | 2 | 4 | 2 | 2 | **19** | W4 | ADR-A, ADR-C |
| 13 | Home healthcare | 4 | 4 | 2 | 3 | 2 | 2 | **17** | W4 | ADR-A, ADR-C |
| 14 | Public health & surveillance | 5 | 3 | 3 | 3 | 4 | 3 | **21** | W4 | ADR-D (admin gate), audit |
| 15 | Medical equipment | 3 | 2 | 4 | 3 | 3 | 4 | **19** | W5 | ADR-D |
| 16 | Insurance & claims | 4 | 3 | 1 | 2 | 2 | 2 | **14** | W6 | ADR-G, ADR-I |
| 17 | Mental health | 4 | 3 | 1 | 3 | 1 | 1 | **13** | W7 | ADR + funding |
| 18 | Dental | 3 | 3 | 1 | 2 | 1 | 1 | **11** | W7 | ADR + funding |
| 19 | Rehabilitation / physiotherapy | 3 | 3 | 1 | 2 | 1 | 1 | **11** | W7 | ADR + funding |

> Note: the exact rank order between adjacent scores is deliberately **not** treated as
> authoritative — only the **wave** assignment is. The score exists to make the ordering
> auditable and to prevent "most exciting feature first" sequencing.

---

## 3. Waves, entry gates and exit evidence

### W0 — Contract gate (current position)

* **Entry:** inventory + contracts documents exist.
* **Exit:** Program Director accepts `NATIONAL_SERVICE_CONTRACTS.md` §8 rules (R-UNI-1…8).
* **Deliverables:** both documents; no code change.

### W1 — Clinical substrate (highest structural risk)

**Scope:** migrations for `cc_*` (45) and `ehr_*` (18); immutable audit for the
care-continuum writes; ADR-A/B/C/D decisions recorded.
**Why first:** every journey J1–J7 depends on it; 63 tables behind live endpoints
currently cannot be provisioned on a freshly migrated database.
**Entry gate:** ADR-A, ADR-C, ADR-D approved.
**Exit evidence:**
1. `alembic upgrade head` on a **disposable clone** creates all 63 tables;
2. before/after revision + table-count + schema diff recorded;
3. row-count/checksum reconciliation on a supported prior snapshot (MIG-EXISTING);
4. `care_continuum` write endpoints emit immutable audit events (new regression tests);
5. full backend suite green against the migrated clone (not `create_all`);
6. OpenAPI unchanged.
**Rollback:** single revert + drop/reload clone; no operational DB touched.

### W2 — High-readiness clinical spine

**Scope:** Referral/continuity (18 ops, already complete) → contract tests for J7;
Blood bank audit + re-permissioning; Maternal & child; Primary care; Laboratory typed
schemas; Pharmacy explicit authz + dispense events.
**Journeys unlocked:** J7 first, then J1 (partial), J6.
**Entry gate:** W1 accepted for the shared substrate; ADR-D for re-permissioning.
**Exit evidence per service:** typed OpenAPI schemas added additively; audit tests;
journey hop tests with synthetic patients; no path rename.

### W3 — Hospital depth + diagnostics

**Scope:** hospital hierarchy migrations (12 tables) + audit; Emergency typed schemas;
Radiology 1 remaining table + critical-finding event.
**Journeys:** J2.
**Entry gate:** ADR-A disposition of the 12 hospital tables; ADR-D audit model.
**Exit evidence:** 12/12 hospital tables migrated on clone; hospital + critical-care
audit writes proven; EMS→hospital consumer test.

### W4 — Continuity and population health

**Scope:** Chronic disease; Home healthcare; Public health (replace blanket
`system:admin` with surveillance roles, add audit).
**Journeys:** J4, J5 (surveillance half).
**Exit evidence:** `cc_*` chronic/home tables migrated; notifiable-disease flow tested;
audit on surveillance writes.

### W5 — Equipment

**Scope:** biomedical audit for maintenance/calibration; keep device gateway as is.
**Exit evidence:** audit events on work-order/calibration transitions.

### W6 — Insurance (decision-first)

**Scope:** ADR-G (schema provisioning) + ADR-I (unserved 84-endpoint package).
**Entry gate:** both ADRs approved; **no code before that**.
**Exit evidence:** one claims implementation only; `ins_*` migrated on clone; J-financial
contract tests.

### W7 — Genuinely new services

**Scope:** Dental; Rehabilitation; Mental health.
**Entry gate:** explicit product/funding decision + ADR; these are **new builds**, not
integration work, and are explicitly excluded from every earlier wave.

---

## 4. Patient journeys mapped to waves (certification targets)

| Journey | Hops | Wave complete | Contract tests required |
|---|---|---|---|
| **J7** Referral → facility → feedback | care-continuum referral → accept → transition → handover | **W2** | origin, accept/reject, tenant isolation, audit, idempotent retry |
| **J6** Blood request → compatibility → transfusion | blood bank crossmatch → issue → hospital record | **W2–W3** | ABO/Rh compatibility, audit trail, no cross-tenant read |
| **J1** Primary → Lab → Pharmacy → Follow-up | care-continuum → orders → samples → critical result → dispense → follow-up | **W2** | critical-result propagation, idempotency, tenant scope |
| **J3** Maternal → Lab → Pharmacy → Referral | pregnancy → antenatal → lab → dispense → referral | **W2** | maternal record integrity, audit, referral handoff |
| **J2** Emergency → Hospital → Radiology → Lab → Discharge | ems → admission → exam → results → discharge | **W3** | pre-arrival event, admission/discharge, audit |
| **J4** Chronic → Primary → Lab → Medication → Follow-up | registry → encounter → result → dispense → plan | **W4** | NCD plan adherence, audit, no duplicate patient |
| **J5** Immunization → Record → Surveillance | vaccination → EHR → public-health case/surveillance | **W4** | event propagation, FHIR mapper test, anonymised reporting |

All journey tests use **synthetic anonymised patients only**.

---

## 5. Parallel remediation track (does not wait for waves)

These are release conditions, not service work; they run in parallel and gate the
release, not the waves.

| Order | Item | Gate |
|---:|---|---|
| 1 | MIG-EXISTING rehearsal on disposable clone (Phase C) | release criteria 5 |
| 2 | MyPy 71 errors (32 domain_platform, 35 communication, 4 workflows) | quality gate |
| 3 | API contract drift — 101 unresolved calls, 28 verb mismatches | release criterion 8 |
| 4 | Pilot readiness `lab_id` | release criteria |
| 5 | Four-service contracts (`admin`/`test_result`/`lab`/`sample`) | release criterion 9 |
| 6 | R-01…R-11 residuals | release criterion 10 |
| 7 | Architecture gate 7.1/100, 737 findings (pre-existing) | quality gate |
| 8 | Change manifest + Git readiness report | release process |

---

## 6. What is explicitly out of scope for this roadmap

* Implementing Dental / Rehabilitation / Mental-health services (W7 only, funding-gated).
* Any Platform-Core or `gula-platform` modification (out of authorisation).
* Renaming any existing API path or table.
* Any migration against an operational database.
* Declaring Production Ready / Clinical Safety Certified from tests alone.

**`FINAL_DECISION.md` remains HOLD until all 14 release conditions are independently proven.**
