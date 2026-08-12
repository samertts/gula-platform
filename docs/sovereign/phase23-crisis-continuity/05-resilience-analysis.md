# Phase 23-05 — Sovereign Resilience Analysis

## Failure-Class × Function Matrix (does the function still operate?)

| Function ↓ / Failure → | Cyber | Connectivity | Power | Datacenter | Mass-displacement | Conflict |
|------------------------|:-----:|:-----:|:-----:|:----------:|:----------------:|:--------:|
| Order intake | partial | edge | edge | Tier-2 | edge | edge |
| Sample chain-of-custody | yes | edge | edge | Tier-2 | edge | edge |
| Result entry | yes | edge | edge | Tier-2 | edge | edge |
| Critical-result delivery | partial | SMS fallback | SMS / runner | Tier-2 | SMS | SMS / radio |
| Audit logging | yes | local chain | local chain | Tier-2 | local chain | local chain |
| Adapter calls (MOH/NHIS) | partial | queued | queued | Tier-2 | queued | queued |
| Analytics / surveillance | paused | paused | paused | reduced | paused | paused |
| Reimbursement | paused | paused | paused | Tier-2 | paused | paused |

"yes" = full; "partial" = degraded but available; "edge" = provincial
operation; "Tier-2" = via Tier-2 cutover; "queued" = adapter queue.

## Doctrinal Findings

1. Clinical core (intake → result → critical delivery → audit) survives
   every modeled failure class.
2. Adapter integrations gracefully queue; no clinical work depends on
   adapter responsiveness.
3. Audit chain continuity is maintained at whichever level the system
   operates at.
4. Analytics and reimbursement are non-essential during crisis; pausing
   them is acceptable.
5. Sovereign comms fallback (SMS/USSD) is essential for critical-result
   delivery in connectivity scenarios.

## Identified Stress Points

- **Sovereign comms fallback** depends on telco availability; war-zone
  scenarios may compromise this. Backup: pre-arranged voice + runner
  protocols.
- **Tier-2 capacity** must be sized for full Tier-1 load; capacity drift
  is a quarterly review item.
- **Edge readiness** depends on pre-positioning of supplies (paper, fuel,
  forms); slippage on supply review is a SEV-3.
- **Audit chain DR cutover** is the highest-stakes single procedure;
  rehearsal annually is mandatory.

## Recommendations

- Quarterly resilience review against this matrix.
- Drill cadence enforced via the deployment checklist.
- Pre-positioning audit logged.
- Capacity drift monitored via a "Tier-2 sizing dashboard".
- The matrix is reviewed any time the platform's architecture changes
  meaningfully (e.g., a new adapter enters the clinical-essential set).

## Open Questions (national-scale)

- What is the regulator's target RTO for full national outage?
- What is the patient-side tolerance for SMS delivery during conflict?
- What is the institution's policy for cross-border failover (which is
  generally forbidden)?
- What is the sovereign cloud's own DR posture?

These questions are not answered in this document; they are tracked in
the sovereign-deployment register.
