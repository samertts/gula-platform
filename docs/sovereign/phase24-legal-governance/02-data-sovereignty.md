# Phase 24-02 — Healthcare-Data Sovereignty

## Principles

1. Patient data persists within the declared national jurisdiction unless
   a regulator-approved cross-border transfer is recorded.
2. Backups, archives, and analytical exports respect residency.
3. Cryptographic key custody respects residency (sovereign KMS preferred).
4. Logs and observability data respect residency.

## Residency Inventory

For each deployment:

| Data class | Residency |
|------------|-----------|
| Clinical records | Sovereign jurisdiction |
| Audit chain | Sovereign jurisdiction |
| Analytics outputs | Sovereign jurisdiction (or regulator-approved cross-border) |
| Backups | Sovereign jurisdiction |
| Cold archive | Sovereign jurisdiction |
| Application logs | Sovereign jurisdiction |
| Model snapshots | Sovereign jurisdiction |
| KMS keys | Sovereign jurisdiction (KMS provider can be in-jurisdiction) |

## Cross-Border Transfers

When a transfer crosses the sovereign border:

- pre-approved by the regulator (per data class)
- restricted to specific peer institutions (named in contract)
- minimised in scope (only essential fields)
- recorded in the audit chain with the transfer's authorisation reference
- end-to-end signed; integrity-checked

A transfer that lacks the authorisation reference is rejected by the
adapter (fail-closed).

## Backup Residency

- Tier-1 backups in jurisdiction A.
- Tier-2 replica in jurisdiction A (different region).
- Tier-3 cold archive in jurisdiction A.
- No tier crosses border in this deployment posture.

If a deployment requires cross-border DR (e.g., fragile sovereign cloud),
the regulator pre-authorises and the audit chain records the bound DR
relationship.

## KMS

- Sovereign KMS preferred.
- Local development uses local secrets; production must NOT.
- Key rotation calendar approved.

## Patient-Side Rights

The platform supports (or is prepared to support, depending on
jurisdiction):

- right of access (via the patient card and longitudinal-record API)
- right of correction (via patient-update workflow with audit)
- right of portability (FHIR bundle export)
- right of erasure (where applicable; restricted by clinical-records floor)

## Erasure Constraints

Where law mandates erasure but clinical retention floor demands keeping:

- the regulator's policy resolves the conflict
- a redaction approach (rather than physical delete) is preferred where
  permitted, because the audit chain MUST remain intact
- the redacted view is accessible only on warrant

## Verification

- Quarterly residency check (where do backups actually live?).
- Annual cross-border transfer review.
- Sovereign KMS reachability test.
