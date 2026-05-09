# Phase 17-03 — Incident Response Framework

## Severity Definitions

| Severity | Definition | Examples |
|----------|------------|----------|
| **SEV-1** | National-scale clinical impact or audit integrity loss | Audit chain mismatch, mass tenant unavailability, multi-region outage |
| **SEV-2** | Single-tenant clinical impact, or platform partial outage | Single-tenant 500s on result write, regional latency spike |
| **SEV-3** | Operational degradation, no clinical impact | Adapter down, dashboard outage, monitoring gap |
| **SEV-4** | Cosmetic / latent | Log noise, non-clinical UI bug |

## Roles

- **Incident Commander (IC)** — owns the response; rotates per on-call.
- **Communications Lead** — internal + external comms; pulls from prepared
  templates.
- **Clinical Liaison** — represents clinical-safety committee for any SEV-1
  or SEV-2 with patient-data implications.
- **Audit Recorder** — a non-incident-active engineer who timestamps every
  decision and command into the incident log.
- **Regulator Liaison** — engaged for SEV-1 within an SLA defined by the
  regulator agreement.

## Decision Authority Matrix

| Action | SEV-3/4 | SEV-2 | SEV-1 |
|--------|---------|-------|-------|
| Restart backend container | Engineer | Engineer | IC |
| Scale replicas | Engineer | Engineer | IC |
| Rollback deployment | IC | IC | IC + ops chief |
| Tier-1 → Tier-2 cutover | n/a | n/a | IC + ops chief |
| Kill switch (`make kill-switch-on`) | n/a | IC | IC + ops chief |
| Regulator notification | n/a | n/a | IC + comms lead |
| Public communication | n/a | comms lead | comms lead + ops chief |

## Response Sequence

1. **Page** — alerting webhook fires; on-call acknowledges within 5 minutes
   for SEV-1, 15 for SEV-2.
2. **Triage** — IC opens an incident channel; classifies severity; engages
   roles per matrix.
3. **Stabilize** — apply the appropriate runbook from `02-runbooks.md`.
4. **Communicate** — internal status updates every 15 minutes for SEV-1,
   30 for SEV-2.
5. **Recover** — restore service; verify with `make health-deep` GREEN for
   ≥ 30 minutes.
6. **Close** — IC marks resolved; audit recorder finalises the log.
7. **Post-mortem** — within 5 working days for SEV-1 / 2; blameless; outputs
   tracked actions.

## Audit / Forensic Requirements

For every SEV-1:

- Immutable incident log preserved.
- All affected `request_id`s captured.
- Snapshot of audit chain at start + end of incident.
- Chain hash integrity reverified before closing.

For every SEV-2:

- Incident log preserved.
- Affected tenant list + impact window recorded.

## Communication Templates

(Stored in `runbooks/templates/`. Two examples illustrative only.)

**SEV-1 internal opening:**
> SEV-1 declared at <time>. Symptom: <one-line>. Affected: <scope>.
> IC: <name>. Channel: <link>. Status update in 15 minutes.

**SEV-1 regulator pre-notification:**
> A potential national-scale incident is in progress. Class: <symptom>.
> Tenant scope: <list>. Patient-data implication: <yes/no>. We will provide
> a follow-up within <SLA>. Contact: <name, role, phone>.

## Tabletop Exercises

Quarterly tabletop drills of:

- SEV-1 audit chain mismatch (RB-05)
- SEV-1 Tier-1 → Tier-2 cutover (RB-09)
- SEV-2 single-tenant breach (RB-04)
- SEV-2 critical-result delay (RB-08)

Exercises are recorded; gaps feed the dependency register and the deployment
checklist.

## Linkage

- The incident-response framework is referenced from the
  [`NATIONAL_DEPLOYMENT_CHECKLIST.md`](../NATIONAL_DEPLOYMENT_CHECKLIST.md)
  as a deployment gate.
- It is referenced from
  [`phase24-legal-governance/03-digital-health-governance.md`](../phase24-legal-governance/03-digital-health-governance.md)
  for legal accountability.
