# Phase 22-02 — Insurance Governance Preparation

## Insurance-Side Boundaries

- An insurer adapter is a Phase 16 adapter.
- Its trust domain is `single_tenant_proxy` mapped to the insurer's lab
  contract space.
- It receives **prepared** claims; it does NOT trigger claim creation.
- It returns claim status; it never asserts "this claim is paid" without a
  treasury-side confirmation.

## Insurance Lifecycle Events

| Event | Source | Effect |
|-------|--------|--------|
| Coverage inquiry | Lab user | Read-only adapter call; no DB write |
| Pre-authorisation | Lab user | Adapter request; persisted; awaits insurer response |
| Claim submission | Lab finance (approved batch) | Persisted as `fin_claim`; sent via adapter |
| Claim status update | Insurer adapter (inbound) | Persisted on existing `fin_claim` |
| Settlement notification | Treasury adapter (inbound) | Persisted as `fin_settlement` |
| Recoupment / reversal | Insurer or treasury (inbound) | Compensating row; original preserved |

Every event is audit-chained.

## Approval Workflow (illustrative)

For claim submission:

1. Operator selects batch.
2. System runs validation (codes mapped, prior auth present, coverage
   active).
3. System produces a manifest of claims with totals.
4. Operator approves; second approver required if batch > threshold.
5. Adapter sends; per-claim audit row written.
6. Insurer responses arrive asynchronously; auto-applied to status.

No single operator can submit, approve, and settle a claim. Role separation
(PB-5) prevents the union.

## Coverage Verification

- Coverage check is performed before order creation when configured.
- A negative coverage result is informational, not blocking — clinical
  workflow proceeds; the patient is informed; the financial treatment is
  decided per policy.

## Insurance AI

AI used for insurance:

- coverage prediction (advisory, tenant)
- fraud likelihood (advisory, tenant or aggregate)
- network selection (advisory, tenant)

All are advisory; humans act.

## Insurer Adapter Manifest Notes

Insurer manifests carry strict capabilities:

- `insurance.coverage.read`
- `insurance.preauth.write`
- `insurance.claim.write_prepared`
- `insurance.claim.status.read`

No insurer adapter ever has `clinical.write` or `patient.read.full`.

## Patient Privacy

Insurer-bound payloads carry the minimum necessary:

- patient identifier as the insurer's policy id, not national_id (where
  the insurer system uses its own id space)
- diagnosis / procedure codes (ICD / LOINC)
- amounts, period, provider id
- never free-text PHI

## Tenant-Safety Discipline

- A claim row carries `lab_id`.
- Insurer adapter responses MUST resolve back to the original `lab_id`;
  responses cannot be auto-routed to a different tenant.
- Cross-tenant claim aggregation is regulator-only and runs over the
  analytical perimeter.
