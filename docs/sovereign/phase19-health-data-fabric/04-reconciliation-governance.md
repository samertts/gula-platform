# Phase 19-04 — Reconciliation Governance

## Position

Reconciliation is the process by which the platform decides "this person
record in tenant A is the same person as this record in tenant B (or NHOP,
or MOH)". It is the single most patient-safety-critical workflow at
national scale, because a wrong link can:

- mix patient data across patients
- expose a patient's records to the wrong institution
- corrupt longitudinal record continuity
- create a hidden audit-chain anomaly

For these reasons, reconciliation is governed, not automated-by-default.

## Governance Principles

1. **No silent reconciliation.** Every link is an audit event with an
   identifiable approver (human or automatic-rule).
2. **No unsafe auto-merge.** Auto-link is only allowed under
   `deterministic_high` (national_id match + secondary attributes
   confirmed) and only within scope rules below.
3. **Two-person rule** for cross-province probabilistic merges and any
   merge involving a flagged record (legal hold, VIP, juvenile, deceased).
4. **Reversible.** Every link can be unlinked; an unlink is itself audited.
5. **Privacy-preserving.** Reviewers see redacted identifiers; full data
   appears only on confirmed link.
6. **Tenant-safe.** A reconciliation review NEVER reveals data from one
   tenant to another tenant's user. Reviewers are scoped: regulator
   reviewers see redacted national-level views; lab reviewers see only
   their tenant's side.

## Auto-Link Scope Rules

Auto-link is permitted **only** when **all** the following are true:

- Match mode is `deterministic_high`.
- Both records share the same national_id (HMAC-equal).
- Both records share DOB and at least 3 first chars of family name.
- No legal-hold flag on either record.
- Score above the policy threshold.

Otherwise, the candidate enters the human-review queue.

## Human Review Queue

- Items are tenant-scoped (lab reviewers see their tenant's side only).
- Cross-tenant items are routed to a regulator-scoped reviewer pool.
- Each item has a target SLA (e.g., 24 hours for routine, 1 hour for
  flagged).
- Reviewers see:
  - both candidates' redacted attributes
  - score and contributing features
  - audit lineage of each constituent
  - notes from previous attempts (if any)

## Disposition Outcomes

| Disposition | Effect |
|-------------|--------|
| `link` | A reconciliation event is written; canonical id assigned/updated; query layer follows the canonical id from now |
| `reject` | A reconciliation event is written with disposition `rejected`; future automatic match against the same pair is suppressed for the suppression window |
| `defer` | Item parked with note; SLA paused; revisited within window |

A `reject` is itself a useful long-lived signal: if the same candidate is
re-proposed, the prior rejection is shown to the new reviewer.

## Reversal (Unlink)

A confirmed link can be reversed. Trigger reasons:

- Reviewer error
- New evidence
- Legal direction (court / regulator)

An unlink:

- writes a new reconciliation event with disposition `unlinked`
- does NOT delete the prior link event
- restores the constituent records to their pre-link canonical ids (or to
  fresh canonical ids if the prior canonical was synthetic)
- triggers a downstream audit on any clinical, billing, or analytics
  outputs that depended on the prior link

## Conflict Detection

Edge / offline scenarios can produce simultaneous reconciliation events on
the same constituent across two locations. Conflict detection:

- compares incoming events on reconnect
- conflicts with disposition `link` from one location and `reject` from
  another go to a special "conflict review" queue
- conflicts are NEVER auto-resolved

## Audit Chain Integration

Reconciliation events are part of the platform's audit chain (AI-2). Their
hash format and chain participation are identical to other audit events.
A regulator can replay the chain and reproduce the canonical-id history at
any point in time.

## Standards Touchpoints

- FHIR `Patient.link` represents a logical merge in FHIR space (Phase 16).
- HL7 v2 ADT^A40 / ADT^A41 (merge / unmerge) supported on inbound;
  treated as proposals.
- DHIS2 receives only post-canonicalised aggregated data.

## Open Items (Phase 19 deferred coding)

- `reconciliation_events` table
- Reviewer queue and UI
- Auto-link rule engine
- Cross-walk dashboard for monitoring SLAs
- Regulator export of reconciliation history
