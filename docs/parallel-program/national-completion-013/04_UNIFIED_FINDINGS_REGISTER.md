# 04 — Unified Findings Register — GULA-NATIONAL-COMPLETION-013

## Scope

One register merging findings from the 2026-11-20 critical-defect research, GitHub inventory, historical governance evidence, and the preserved conversation checkpoint. Duplicate findings are merged only where root causes are demonstrably identical; all original references are retained.

Machine-readable companion: `evidence/unified_findings_register.json`.

## Methodology

- Deduplicated by root cause and affected module.
- Preserved original source IDs and file paths in the JSON `source`/`github_refs` fields.
- Used only the allowed verification states: `FIXED`, `PARTIALLY FIXED`, `NOT FIXED`, `NOT VERIFIED`, `RECONCILED`, `HUMAN APPROVAL REQUIRED`.
- No finding was removed because its wording changed.

## Environment

Isolated workspace at `main` @ `2ee9e8bc…`. Findings inherited from historical evidence are marked as such and are not claimed to have been re-executed in this workspace.

## Commands and exit codes

```bash
jq -e . docs/parallel-program/national-completion-013/evidence/unified_findings_register.json >/dev/null
# exit 0 after generation; revalidated below in implementation evidence
```

## Evidence paths

- `evidence/unified_findings_register.json`
- `evidence/critical_defect_research.md`
- `evidence/github_inventory_summary.json`
- Historical source paths quoted in individual JSON entries.

## Findings summary

| ID | Severity | Module | State | Disposition |
|---|---|---|---|---|
| NC013-C01 | CRITICAL | Critical-result ID contract | NOT FIXED | OPEN |
| NC013-C02 | CRITICAL | NIAM persons endpoints | PARTIALLY FIXED | OPEN |
| NC013-C03 | CRITICAL | gRPC gateway | NOT FIXED | OPEN |
| NC013-C04 | CRITICAL | NID self-registration / MPI | NOT FIXED | OPEN |
| NC013-H01 | HIGH | Drug substitution migration FK | PARTIALLY FIXED | OPEN |
| NC013-H02 | HIGH | Python 3.10 UTC compatibility | NOT FIXED | OPEN |
| NC013-H03 | HIGH | GitHub protection / CI | NOT FIXED | OPEN |
| NC013-H04 | HIGH | Provenance / untracked evidence | NOT FIXED | OPEN |
| NC013-H05 | HIGH | Patient route authorization | NOT VERIFIED | OPEN |
| NC013-H06 | HIGH | health_core guard not wired | NOT VERIFIED | OPEN |
| NC013-H07 | HIGH | Break-glass header | NOT FIXED | OPEN |
| NC013-H08 | HIGH | Offline LAST_WRITE_WINS | NOT VERIFIED | OPEN |
| NC013-H09 | HIGH | Restore script swallows failure | NOT FIXED | OPEN |
| NC013-H10 | HIGH | No restore/PITR/RPO/RTO drill | NOT VERIFIED | OPEN |
| NC013-H11 | HIGH | Unpinned container dependencies | NOT FIXED | OPEN |
| NC013-H12 | HIGH | FHIR terminology validation | NOT VERIFIED | OPEN |
| NC013-H13 | HIGH | PHI in audit/duplicate responses | NOT VERIFIED | OPEN |
| NC013-M01 | MEDIUM | Missing numbered predecessor artifacts | RECONCILED | ACCEPTED WITH LIMITATION |
| NC013-M02 | MEDIUM | Missing previous isolated workspace | RECONCILED | ACCEPTED WITH LIMITATION |

## Verification state

`HUMAN APPROVAL REQUIRED` for release; individual states are per-finding in the JSON register.

## Limitations

- The previous verification-010 report files are unavailable; those entries rely on the conversation checkpoint and are explicitly labelled.
- Historical governance findings were not re-executed in this workspace.
- The register is a living artifact; implementation phases will update `state`, `regression_test`, and `verification_evidence`.

## Residual risks

- Four CRITICAL findings remain capable of wrong-patient or unauthorized access until fixed and independently verified.
- Historical HIGH findings remain open despite documented engineering attempts in untracked work.

## Required actions

1. Implement fixes for C01–C04 and H01–H02 on the isolated branch.
2. Regenerate executable evidence for each affected finding.
3. Route clinical, identity, database-history, and release decisions to the human approval register.
