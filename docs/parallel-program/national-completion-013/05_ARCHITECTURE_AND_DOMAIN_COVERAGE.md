# 05 — Architecture and Domain Coverage — GULA-NATIONAL-COMPLETION-013

## Scope

Map the 26 approved national-platform domains to code/configuration evidence on `main`, and record preservation constraints for `frontend-v3` and Platform-Core.

## Methodology

Read-only repository inspection on the isolated clone: directory listing, router/module discovery, migration inventory, and historical architecture reports. A module is counted as `PRESENT` only when executable code exists; `PRESENT` is not `VERIFIED`.

## Environment

Isolated clone at `2ee9e8bc…`; Python/Node toolchain as in `00_EXECUTIVE_BASELINE.md`.

## Commands and exit codes

```bash
find backend/app -maxdepth 2 -type d | sort
find backend/migrations/versions -maxdepth 1 -type f -name '*.py' | wc -l
find frontend-v3/src -maxdepth 2 -type d | sort | sed -n '1,120p'
```

All exit codes 0.

## Evidence paths

- `evidence/architecture_inventory.txt`
- `06_SECURITY_AND_IDENTITY_REMEDIATION.md`
- Historical: `ARCHITECTURE.md`, `MASTER_SYSTEM_ATLAS.md`, `docs/adr/` in the isolated clone.

## Findings

| # | Domain | Observed state | Notes |
|---:|---|---|---|
| 1 | National health identity | PRESENT / NOT VERIFIED | NIAM modules exist; C02/C04 open |
| 2 | Patient records & matching | PRESENT / NOT VERIFIED | MPI exists; NID trust defect open |
| 3 | Organizations/facilities | PRESENT / NOT VERIFIED | Migration/provenance concerns |
| 4 | Workforce | PRESENT / NOT VERIFIED | IAM branches open/unmerged |
| 5 | Hospitals/PHC | PARTIAL | Migration collision #261/#257 |
| 6 | Appointments/encounters | PRESENT / NOT VERIFIED | Ownership rules unverified |
| 7 | EMR | PRESENT / NOT VERIFIED | health_core guard not wired (H06) |
| 8 | LIMS | PRESENT / NOT VERIFIED | C01 open |
| 9 | Orders/specimens/results | PRESENT / NOT VERIFIED | Dual result stores |
| 10 | Imaging | PRESENT / NOT VERIFIED | Tenant checks unverified |
| 11 | Pharmacy | PRESENT / NOT VERIFIED | H01 migration mismatch |
| 12 | Blood bank | PRESENT / NOT VERIFIED | Prior 21 PG tests NOT VERIFIED |
| 13 | Emergency care | PRESENT / NOT VERIFIED | Scope documented in GRC-ERS |
| 14 | MNCH | PARTIAL | Domain coverage incomplete/unverified |
| 15 | Vaccination | PARTIAL | Coverage unverified |
| 16 | Chronic disease | PRESENT / NOT VERIFIED | Routing/deprecation PRs open |
| 17 | Referrals/care continuity | PRESENT / NOT VERIFIED | BOLA findings in checkpoint |
| 18 | Surveillance | PARTIAL | Public-health reporting unverified |
| 19 | Public-health reporting | PARTIAL | Statistics claims not accepted as evidence |
| 20 | Clinical notifications | PRESENT / NOT VERIFIED | Delivery policy not approved |
| 21 | Device/analyzer integration | PRESENT / NOT VERIFIED | C03 open; device bridge 3.10 issue |
| 22 | National exchange/interoperability | PRESENT / NOT VERIFIED | FHIR/terminology H12 open |
| 23 | Citizen services | PRESENT / NOT VERIFIED | Self-registration C04 open |
| 24 | Offline operations/sync | PRESENT / NOT VERIFIED | H08 open |
| 25 | Audit/governance/quality | PRESENT / NOT VERIFIED | H13 open |
| 26 | Reporting/analytics/decision support | PRESENT / NOT VERIFIED | No approval for clinical rules |

Preservation decision: `frontend-v3` remains the production web reference. No alternative design system was imported. Platform-Core was not restructured.

## Verification state

`NOT VERIFIED` for national completeness; `RECONCILED` for the decision to preserve `frontend-v3` and Platform-Core boundaries.

## Limitations

- Directory presence does not prove behavior, authorization, persistence, or clinical safety.
- No mobile/desktop build was executed in this phase.

## Residual risks

- Counting modules as present may overstate engineering completeness; the dashboard separates presence from verification.

## Required actions

Execute domain-specific verification in later phases; do not promote `PRESENT` to `IMPLEMENTED` without tests and evidence.
