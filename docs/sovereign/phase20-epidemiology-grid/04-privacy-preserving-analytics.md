# Phase 20-04 — Privacy-Preserving Analytics

## Goal

Allow useful national analytics — surveillance, capacity, utilisation —
without exposing individuals.

## Techniques in Scope

- Bucketisation + suppression (Phase 20-03)
- k-anonymity / l-diversity
- Differential privacy (future, where statistical noise is acceptable)
- Federated analytics (regional aggregation before central collection)
- Secure multi-party computation (only if a future use case justifies the
  complexity)

## Differential Privacy (planned, not enabled)

Where applicable (e.g., national rate estimates), DP can be added with:

- a privacy budget per consumer per period
- noise calibration documented and reviewed
- a "honest accountant" tracking budget consumption

DP is not introduced in this phase. It is documented as a future option.

## Federated Analytics

For deployments where central aggregation is itself a privacy concern:

- Each region runs its own analytical perimeter.
- Outputs are aggregates of aggregates.
- Central authority sees only post-aggregation results.
- The architecture is otherwise identical.

## Consumer Discipline

Every consumer of analytical outputs:

- has a stated purpose (e.g., "weekly outbreak detection in Anbar")
- has bounded data classes
- has a TTL on access
- is reviewed at the same cadence as the rest of the governance program

A consumer that asks for finer resolution gets it only with proportionally
stronger justification.

## Cross-Border Transfers

Analytical exports leaving the sovereign jurisdiction:

- pre-approved by the regulator
- one-way, signed
- recorded in the analytical audit lineage

If cross-border transfer is forbidden by jurisdiction, federated analytics
or international DHIS2 reporting via aggregated only is the fallback.

## AI in Analytics

AI / ML over analytical outputs:

- Models trained on bucketised, suppressed data only.
- No model receives raw identifiers.
- Models reviewed under Phase 21's IRB-AI.
- Predictive outputs themselves treated as analytical data and protected
  accordingly.

## Anti-Patterns Forbidden

- Raw clinical SQL access "just to look around" — every analytical query
  goes through the perimeter.
- One-off Excel exports of individual records for "analysis" — never.
- Combining low-suppression aggregates from different exports to triangulate
  identities — surface in incident review.
