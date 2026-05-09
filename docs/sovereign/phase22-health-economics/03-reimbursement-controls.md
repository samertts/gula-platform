# Phase 22-03 — Reimbursement-Governance Controls

## Control Inventory

| Control | Description | State |
|---------|-------------|-------|
| Claim validation | Code mapping, coverage, completeness | Process today; coded validator deferred |
| Two-person approval over threshold | Two distinct operators must approve large batches | Process today |
| Idempotency on claim submission | Per-claim idempotency key prevents duplicate submission | Coded surface in adapter |
| Compensating reversal | Reversals create new rows; never UPDATE | Required by design |
| Audit chain participation | Every claim event hashes into chain | Required |
| Role separation | Submitter ≠ approver ≠ auditor | Required |
| Manual override prohibition | No "force approve" path without audit | Required |
| Rate limiting | Per-tenant adapter call rate cap | Existing pattern |
| Concurrency cap | Per-adapter bulkhead | Existing pattern |
| Replay protection | nonce + jti on adapter inbound | Existing pattern |

## Specific Constraints

- No autonomous reimbursement execution path. AI may flag; humans approve.
- No silent re-submission. A claim that fails returns to a queue; an
  operator decides to re-submit.
- No partial-amount mutation in place; partials are new rows.

## Adjudication Flow

Adjudication (whether a claim is accepted by the insurer) occurs at the
insurer side. Our role:

- record the insurer's decision verbatim
- never "interpret" an ambiguous response into a status
- escalate ambiguous responses to operator

## Recoupment

When an insurer recoups a previously-paid claim:

- the platform records a `fin_recoupment` row referencing the original
- audit chain includes the recoupment event
- the operator reconciles internally (notification to lab finance)

## Settlement

Settlement events come from the treasury adapter:

- `fin_settlement` row created on inbound notification
- linked to one or more claims
- audit-chained

If an inbound settlement does not match any expected claim, it is parked
in an exception queue for human reconciliation.

## Pre-Authorisation Discipline

- A pre-auth is requested for procedures that require it, before service
  delivery.
- Pre-auth records persist with their decision.
- Failed pre-auth does not block clinical care; the financial implication
  is communicated to the patient/operator per policy.

## Fraud / Waste / Abuse (FWA) Flagging

- FWA flags are advisory; they create a `fin_fraud_flag` row and require
  operator review.
- A flag does NOT auto-block any claim, payment, or operator action.
- A reviewer can confirm, dismiss, or escalate (e.g., to internal audit).

## Audit & Regulator Surface

- Quarterly: aggregate FWA flag rate; review by program owner.
- Annually: claim-cycle review for selected tenants; regulator may request
  any data from the audit chain on warrant.
- Continuously: claim-rejection rate monitored; spikes alert operations.

## Pricing & Fee Schedules

- Fee schedules are configurable, not hard-coded.
- Schedule changes are audited.
- Historical schedules are preserved for re-pricing on dispute.
