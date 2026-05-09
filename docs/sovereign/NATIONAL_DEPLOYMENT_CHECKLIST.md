# National Deployment Preparation Checklist

This is the pre-go-live checklist for sovereign national deployment. It is
**not** the per-tenant onboarding checklist (that lives in
`docs/DEPLOYMENT.md`). It is the program-level readiness gate.

A "ready" answer requires **evidence** — a runbook, a passing test, a signed
governance document, or a configured artifact. A verbal "yes" is insufficient.

---

## A. Architectural Readiness

- [ ] Tenant-isolation regression suite passes on the deployment release tag.
- [ ] Audit-chain integrity verifier runs green over a 30-day production window.
- [ ] Migration round-trip (`alembic upgrade head` → `downgrade -1` → `upgrade head`) green on a fresh DB.
- [ ] CI `migration-check` job green for the release SHA.
- [ ] All sovereign invariants (`SOVEREIGN_INVARIANTS.md`) reviewed and acknowledged in writing by the program owner.
- [ ] Adapter framework (`backend/app/interoperability/`) reviewed by security; **no adapter wired in `main.py` without explicit approval**.

## B. Interoperability Readiness (Phase 16)

- [ ] Trust-domain manifest reviewed and signed for each institutional integration.
- [ ] FHIR / HL7 / DHIS2 adapter mappings reviewed against the canonical terminology table.
- [ ] Inbound integrations have been load-tested at expected national-scale volume (≥ 5× peak).
- [ ] Failure-isolation policy verified: a failing institutional adapter does not cascade to clinical writes.
- [ ] Interop audit-event schema validated end-to-end.

## C. Operational Infrastructure (Phase 17)

- [ ] Primary + DR datacenter deployment topology approved.
- [ ] Backup restore drill executed within the last 90 days; documented RPO and RTO measured.
- [ ] On-call rotation, escalation matrix, and incident-response runbooks published.
- [ ] Operational dashboard reachable from SOC + NOC environments.
- [ ] Dependency register up to date (see `phase17.../07-dependency-register.md`).
- [ ] Blue/green or staged-rollout pipeline validated.

## D. Governance Readiness (Phase 18, 24)

- [ ] Retention policy ratified; aligned with national health-data law.
- [ ] Legal-hold mechanism tested (a held record cannot be purged by retention).
- [ ] Role-separation matrix signed by the regulator/oversight body.
- [ ] Audit-export procedure for regulators documented and rehearsed.
- [ ] AI explainability registry populated for every AI capability in production.
- [ ] Compliance traceability matrix complete (Standards Mapping Matrix has no 🔴 in scope).

## E. Health Data Fabric (Phase 19)

- [ ] MPI policy approved (auto-merge thresholds, escalation policy).
- [ ] Reconciliation audit format validated; immutable, hash-chained.
- [ ] Terminology-governance committee charter signed.
- [ ] Patient-merge UI/process exists with two-person rule for high-confidence merges.

## F. Public Health Intelligence (Phase 20)

- [ ] Anonymization pipeline reviewed; k-anonymity / l-diversity targets met for any export.
- [ ] No raw `national_id` / `phone` / DOB exits the analytical perimeter.
- [ ] Outbreak-detection threshold policy ratified by the public-health authority.

## G. Clinical AI Governance (Phase 21)

- [ ] AI capability registry published; each entry has scope, version, owner.
- [ ] Each clinical AI capability ships with explainability metadata.
- [ ] AI fails closed in degraded mode (verified by chaos test).
- [ ] Human-override path tested for every clinical AI.

## H. Health Economics (Phase 22)

- [ ] No autonomous reimbursement execution path exists in the release.
- [ ] Insurance-data tenant boundary verified.
- [ ] Fraud/waste detection runs read-only; flags require human review before action.

## I. Crisis & Continuity (Phase 23)

- [ ] Offline-edge synchronization conflict-resolution policy ratified.
- [ ] Paper-fallback workflow documented and tested.
- [ ] Emergency-access procedure exists, is auditable, and is reviewed monthly.
- [ ] Sovereign communication-fallback channels (e.g., SMS gateway) have warm contracts.

## J. Ecosystem Governance (Phase 25)

- [ ] Third-party integration lifecycle (request → certify → monitor → revoke) documented.
- [ ] Sandbox tenant exists for ecosystem partners.
- [ ] No unsigned plugin/extension can be loaded into production tenants.

---

## Final Sign-off

National deployment requires **all** of the following, recorded in the program
register:

1. Program owner sign-off (technical readiness)
2. Regulator / oversight-body sign-off (governance readiness)
3. Clinical-safety committee sign-off (patient-safety readiness)
4. Operations chief sign-off (operational readiness)
5. Security officer sign-off (security & privacy readiness)

Absence of any sign-off blocks deployment. There is no "exception path".
