# Phase 23-02 — Continuity of Operations (COOP)

## COOP Objectives

- Provide essential clinical functions during disruption.
- Maintain audit survivability.
- Enable orderly recovery.
- Communicate status to operators, regulators, and patients.

## Essential Functions (declared)

1. Order intake from a clinician
2. Sample chain-of-custody record
3. Result entry by lab personnel
4. Critical-result delivery to the ordering clinician
5. Audit logging of all of the above

These functions MUST persist in CRISIS and PAPER modes. Other functions
(reporting, analytics, financial workflows) may be paused.

## COOP Deployment Layers

| Layer | Operates in | Mode |
|-------|------------|------|
| Central platform | GREEN-RED | normal |
| Provincial gula-backend (edge) | All modes | edge-mode beyond RED |
| Lab-local LabLink-Core | All modes | local mode |
| Paper procedures | CRISIS, PAPER | manual |

## Edge Mode Operation

In edge mode:

- Provincial gula-backend serves the province's labs.
- Local PostgreSQL is authoritative for the province's data.
- Outbound to central is queued in the signed local outbox.
- Audit chain continues locally.
- Critical-result delivery is local (clinician within province).

On reconnect:

- Outbox replayed forward.
- Conflict-detectable sync runs.
- Reconciliation events governance-handled (Phase 19).

## Paper-Fallback Procedure

When even the edge is offline (power, hardware, severe damage):

1. Lab uses pre-printed forms.
2. Each form has a unique pre-issued id (printed in advance, supply
   maintained).
3. Each result is signed by the responsible technologist.
4. Critical results communicated by phone/runner.
5. On recovery, results are entered into the system with paper provenance:
   - paper id
   - technologist
   - phone-call recipient (for criticals)
   - timestamps
6. Each paper-derived row is audit-chained with a `paper_provenance` flag.

The paper procedure is rehearsed annually.

## Sovereign Comms Fallback

When notification channels are degraded:

- SMS/USSD via telco adapter is the fallback for critical results.
- Pre-arranged voice trees for clinician on-call.
- Status to operators via radio/voice if SMS also unavailable.

## Resource Pre-positioning

For each provincial site:

- 7-day battery / fuel stock (operations target)
- Pre-printed forms supply (one quarter's typical volume)
- Local KMS-cached keys with short TTL
- Local backup of recent reference data

Levels reviewed quarterly.

## Patient-Identity Continuity in Crisis

- Identity reconciliation is **not** automated in crisis mode.
- New patient registrations may use temporary local identifiers.
- Reconciliation occurs after recovery; canonical id assignment audited.

## COOP Plan Review

- Quarterly: pre-positioning levels.
- Quarterly: edge sync rehearsal.
- Annually: paper-fallback drill.
- Annually: COOP plan ratification by ops chief and clinical-safety
  committee.
