# Phase 22-05 — Regulated-Payment Governance Framework

## Roles

| Role | Permissions |
|------|------------|
| Lab finance operator | Prepare claim batches; submit for approval |
| Lab finance approver | Approve prepared batches; cannot also prepare |
| Treasury operator | Receive and acknowledge settlements; cannot prepare claims |
| Insurer adapter | Submit + receive claim status (machine principal) |
| Treasury adapter | Receive settlement notifications (machine principal) |
| Internal audit | Read-only across financial events |
| Regulator | Read-only on warrant |

PB-5: an account MUST NOT hold both "lab finance operator" and "lab finance
approver".

## Approval Thresholds

Configurable per tenant per claim type. Defaults illustrative:

| Tier | Threshold (single claim) | Approvers required |
|------|-------------------------:|:------------------:|
| 1 | up to T1 | 1 |
| 2 | T1..T2 | 2 |
| 3 | above T2 | 2 + program owner notification |

Threshold changes are audit-chained.

## Settlement Posting

- Inbound settlement notifications acknowledged with idempotency key.
- Posting writes a `fin_settlement` row.
- Linked claims update status (paid / partial / reversed).
- Mismatch goes to exception queue.

## Reconciliation

Daily:

- Sum of acknowledged settlements vs. expected = 0
- Pending claims with no insurer status > N days → flagged
- Mismatches in exception queue > N days → escalated

## Audit Surface

| Event | Audit row content |
|-------|-------------------|
| Claim prepared | who, when, batch id, totals |
| Claim approved | who, when, batch id |
| Claim submitted | who/adapter, when, idempotency key |
| Insurer status received | adapter, status, claim ids |
| Settlement received | adapter, amount, claim ids |
| Recoupment received | adapter, amount, claim id |

All hashed into the audit chain.

## Patient Communication

When a financial event affects the patient (denial, partial coverage,
appeal opportunity), notification flows through the existing notification
service. No silent decision against the patient's interest.

## Cross-Border Payments

If a settlement crosses borders:

- additional regulator pre-approval required
- adapter manifest declares the cross-border capability explicitly
- treasury adapter records the cross-border flag in the settlement row

## Anti-Money-Laundering Stance

This phase does not introduce AML controls. Where AML obligations apply
(e.g., large cash settlements), the deployment integrates the obligated
party's AML system via an adapter — out of scope here.

## Disabled by Default

Until Phase B+ implementation:

- `ENABLE_FINANCIAL_ENGINE=false` (default)
- `ENABLE_ADS=false` (default)

These flags remain off in production deployments until governance approves.
