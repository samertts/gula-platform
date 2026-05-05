# 15 — National-Scale War-Game Simulation

## 15.1 Purpose

Validate, on a recurring schedule, that the entire SNDHS continues to
satisfy H1–H5 under realistic national failure scenarios. War-games
exercise people, processes, and platform together. Pass/fail is
auditable.

War-games run on:

- A **shadow national environment** that mirrors production topology
  and signs all events but does not affect citizens.
- A subset run **in production** as targeted chaos with safety nets
  (kill switch, blast-radius controls).

## 15.2 Scenario library

### 15.2.1 Set A — clinical & emergency

| ID | Name | Summary |
|----|------|---------|
| A-01 | Cardiac arrest from rural call | 122 call → ambulance dispatch → ED arrival → cath-lab activation; full critical path under MCOM-1 |
| A-02 | Multi-region MCI | Bus crash crossing two regions; MCOM-3 declared; transfers across regions |
| A-03 | Stroke chain | Symptoms onset → ambulance + telestroke → tPA decision under stabilizer hysteresis |
| A-04 | Sepsis bundle compliance | Adult patient with positive sepsis screen; bundle ordered, completed within window |
| A-05 | Paediatric resuscitation | Weight-based dosing + bundle binding |
| A-06 | Mass food poisoning | Surge of moderate-acuity ED visits in one city; capacity routing |

### 15.2.2 Set B — infrastructure & platform

| ID | Name | Summary |
|----|------|---------|
| B-01 | Single RSN datacentre lost | Region-wide failover; DR-warm activation |
| B-02 | National uplink severed | All RSNs partitioned simultaneously for 4 h |
| B-03 | NFT failure | National federation tier offline for 2 h |
| B-04 | Time authority failure | National time desync; safe-mode activation |
| B-05 | Bus storm | NATS RAFT under pathological load; subject hot-spot |
| B-06 | DB corruption single shard | Recovery from WAL + base + event log |
| B-07 | Supply-chain image revoke | Forced redeploy under load |

### 15.2.3 Set C — security & integrity

| ID | Name | Summary |
|----|------|---------|
| C-01 | Phished clinician | Compromised credential used at unusual hour |
| C-02 | Insider data exfil attempt | Patterned "stranger" patient access |
| C-03 | Audit chain tamper attempt | Inserted record; verifier must catch |
| C-04 | Adversarial AI input | Crafted vitals injecting model bias under shadow |
| C-05 | Mass break-glass | Coordinated break-glass across many users |
| C-06 | Pivot from GULA | Attacker controls a GULA service, attempts SNDHS reach |
| C-07 | Rogue device | Tampered ambulance device telemetry |

### 15.2.4 Set D — governance & policy

| ID | Name | Summary |
|----|------|---------|
| D-01 | Bad bundle canary | Canary policy bundle introduces an over-permissive forbid; auto-rollback |
| D-02 | Conflicting bundle versions during partition | Two RSNs on different bundles for 24 h; reconcile |
| D-03 | Retention purge race | Legal hold flipped during purge cycle |
| D-04 | Time authority compromise | False time tokens; reject + recover |

### 15.2.5 Set E — catastrophic

| ID | Name | Summary |
|----|------|---------|
| E-01 | National emergency MCOM-4 | Country-wide declaration; freeze bundle; paper fallback |
| E-02 | Two RSNs lost concurrently | Adjacent regions; cross-region transfer capacity |
| E-03 | Earthquake split-brain + power loss | Several RSNs run on UPS for 4 h; sync after restoration |
| E-04 | Pandemic surge | 10× sustained load for 30 days; auto-degrade ladder; AI freeze |

## 15.3 Pass/fail criteria (per scenario)

Common gates (all must hold unless explicitly waived):

1. **Audit completeness**: 100% of state-changing actions audited;
   audit chain unbroken; cross-checkpoints verified.
2. **Time constraints**: H1 (P99 < 2 s) and H2 (< 2% time-violation
   rate) maintained for the relevant pathways during the scenario or
   degraded as expected per the scenario's ladder.
3. **Bypass rate**: H3 (< 3%) maintained; any spike has matching
   integrity-engine response.
4. **Offline survivability**: For partition scenarios, RSN remains
   functional for the scenario's duration up to 72 h.
5. **Safety**: No double-write; no lost write; no medication-safety
   violation in the synthetic stream.
6. **Recovery**: Heal achieves convergence within the scenario's RTO;
   manual queue returns to baseline within the scenario's window.

Scenario-specific gates:

- Set A: clinical bundle compliance ≥ 95%; correct triage acuity per
  ground-truth ≥ 95%; bundle timer adherence per protocol.
- Set B: RTO/RPO targets per scenario met; no orphaned events.
- Set C: detector firing rate matches injected attacks within
  ± tolerance; no PHI exfil; user restrictions trigger correctly.
- Set D: rollback within auto-rollback window; reconciliation
  consistent.
- Set E: MCOM transitions follow rules; paper backfill is auditable;
  data integrity preserved.

## 15.4 Execution platform

- A **scenario runner** drives synthetic actors (citizens, dispatch,
  ambulance, clinicians, lab devices) and **fault injectors** (pod
  kill, network partition, clock skew, packet loss, key revocation,
  bundle activation).
- Synthetic data is generated from a curated population model that
  preserves demographic and clinical realism without re-identifying
  any real citizen.
- All synthetic events are tagged `wargame:true` and routed via a
  dedicated bus subject namespace; production consumers ignore them.
- Scoring engine compares observed outcomes vs scenario gates and
  produces a signed report.

## 15.5 Cadence

- **Weekly** — 1 small scenario (mostly Set B/C low-blast).
- **Monthly** — 1 medium scenario (Set A/B).
- **Quarterly** — 1 large scenario (Set E or multi-set).
- **Annually** — full national-scale catastrophic exercise (E-01),
  with Ministry observation.

## 15.6 Production-targeted chaos

Selected drills run in production:

- Pod kills and pool exhaustion (low blast).
- Network jitter on selected services.
- Time skew injection (regional, bounded).
- Bundle canary rollouts (already part of governance).

These are bound by:

- Pre-approval by SRE lead + clinical safety officer.
- Time-of-day windows (low-traffic).
- Kill switch armed.
- Real-time SLO monitoring with auto-abort thresholds.

Production-targeted chaos NEVER includes synthetic patients in
production data stores. Any "synthetic" test in production exercises
infrastructure only.

## 15.7 Reporting

- After-action report within 14 days, signed by:
  - SRE lead,
  - CISO,
  - Clinical safety officer,
  - Ministry duty officer (for quarterly+).
- Findings tagged with severity; remediation tasks tracked in the
  governance backlog with owners and target dates.
- Repeat of failed scenarios mandatory within 90 days.

## 15.8 Continuous improvement loop

- Each war-game finding flows into:
  - Policy authority (rules tuned, transitions hardened),
  - Validation loop (additional adversarial seeds),
  - Integrity engine (detector tuning),
  - SDK / contracts (better invariants),
  - Performance gates (CI thresholds).
- The MSBC acceptance gates (`08-msbc.md` §8.7) are augmented with new
  scenarios that have caused regressions, so future deployments
  inherit the lesson.

## 15.9 Pass/fail summary metric

Per quarter, publish:

- War-games run: count, set distribution.
- Pass rate per scenario set.
- MTTR for findings.
- New gates introduced.
- Trend lines for H1–H5 measured during war-games.

The goal is a **non-decreasing** pass rate over time and a strictly
decreasing MTTR for high-severity findings.
