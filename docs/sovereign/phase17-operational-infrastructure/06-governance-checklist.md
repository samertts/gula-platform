# Phase 17-06 — Production Governance Checklist

This is the operational governance gate that runs **per release** in the
national-deployment context. The deployment-wide gate is in
[`../NATIONAL_DEPLOYMENT_CHECKLIST.md`](../NATIONAL_DEPLOYMENT_CHECKLIST.md).

## Per-Release

- [ ] CI green for the release SHA (`syntax-gate`, `migration-check`,
      `smoke-test`, `backend-test`, `security-scan`).
- [ ] `make ci` green locally.
- [ ] No new SEV-1 issues open for ≥ 7 days.
- [ ] Audit-chain verifier green for the last 24h on staging.
- [ ] Migration round-trip green on a fresh DB.
- [ ] Per-tenant migration dashboard shows zero laggards.
- [ ] Adapter manifest hashes unchanged unless a corresponding governance
      change record exists.
- [ ] Sovereign-KMS reachability check green from production network.
- [ ] Backup restore drill not older than 90 days.
- [ ] Tier-1 → Tier-2 cutover drill not older than 12 months.
- [ ] Edge offline-72h drill not older than 90 days.
- [ ] On-call rotation populated for the release window.
- [ ] No open SEV-2 incidents older than 30 days.
- [ ] Release notes reviewed for clinical-safety implications.

## Per-Quarter

- [ ] Review of the dependency register
      ([`07-dependency-register.md`](./07-dependency-register.md)).
- [ ] Review of the residual risk register
      ([`../REMAINING_NATIONAL_RISKS.md`](../REMAINING_NATIONAL_RISKS.md)).
- [ ] Tabletop SEV-1 exercise.
- [ ] Adapter manifest re-review for any adapter not exercised in production
      that quarter.
- [ ] Sovereign-KMS rotation cycle executed if calendar requires.
- [ ] Standards-mapping matrix re-checked against latest releases (FHIR R4
      → R5, HL7 v2 minor versions, ICD-10 → ICD-11 readiness).

## Per-Year

- [ ] Adapter recertification (Phase 16-04 §"Recertification").
- [ ] Tier-1 → Tier-2 cutover drill.
- [ ] Audit-chain replay across the full year.
- [ ] Regulator-readiness self-assessment vs. the standards mapping matrix.
- [ ] Clinical-safety incident review with the safety committee.
- [ ] Update of the
      [`NATIONAL_DEPLOYMENT_CHECKLIST.md`](../NATIONAL_DEPLOYMENT_CHECKLIST.md)
      against the prior year's incidents.

## Sign-off Roles

- **Platform release** — engineering on-call lead
- **Quarterly review** — operations chief + security officer
- **Annual review** — operations chief + security officer + clinical-safety
  committee chair + regulator liaison

A missed item is recorded with a remediation plan and a deadline. There is
no silent skipping.
