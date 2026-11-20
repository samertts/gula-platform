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
| NC013-C01 | CRITICAL | Critical-result ID contract | INDEPENDENTLY VERIFIED AT CODE LEVEL | RELEASE BLOCKED BY GOVERNANCE |
| NC013-C02 | CRITICAL | NIAM persons endpoints | INDEPENDENTLY VERIFIED AT CODE LEVEL | RELEASE BLOCKED BY GOVERNANCE |
| NC013-C03 | CRITICAL | gRPC gateway | INDEPENDENTLY VERIFIED AT CODE LEVEL | RELEASE BLOCKED BY GOVERNANCE |
| NC013-C04 | CRITICAL | NID self-registration / MPI | INDEPENDENTLY VERIFIED AT CODE LEVEL | RELEASE BLOCKED BY GOVERNANCE |
| NC013-C05 | CRITICAL | Transfusion verification → in-progress transition | NOT FIXED — PRE-EXISTING | HUMAN APPROVAL REQUIRED — OUT OF NC013 SCOPE |
| NC013-H01 | HIGH | Drug substitution migration FK | FIXED — LOCAL TESTS PASS | REMEDIATED — AWAITING INDEPENDENT VERIFICATION |
| NC013-H02 | HIGH | Python 3.10 UTC compatibility | FIXED — LOCAL TESTS PASS | REMEDIATED — AWAITING INDEPENDENT VERIFICATION |
| NC013-H14 | HIGH | Missing hospital core migration | FIXED — LOCAL TESTS PASS | REMEDIATED — AWAITING INDEPENDENT VERIFICATION |
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

`HUMAN APPROVAL REQUIRED` for release; individual states are per-finding in the JSON register. C01–C04, H01, and H14 are `INDEPENDENTLY VERIFIED AT CODE LEVEL — RELEASE BLOCKED BY GOVERNANCE` after two adversarial passes. H02 remains `PARTIALLY VERIFIED — SCOPE LIMITATIONS DOCUMENTED` (three Python 3.12-only syntax sites and 13 further direct `UTC` imports are outside the claim). See `17_INDEPENDENT_VERIFICATION.md`.

## Limitations

- The previous verification-010 report files are unavailable; those entries rely on the conversation checkpoint and are explicitly labelled.
- Historical governance findings were not re-executed in this workspace.
- The register is a living artifact; implementation phases will update `state`, `regression_test`, and `verification_evidence`.

## Residual risks

- Four CRITICAL findings have engineering fixes, local regression evidence, and two independent verification passes; they are still not release-accepted because all human approvals are `BLOCKED`.
- Historical HIGH findings remain open despite documented engineering attempts in untracked work; dependency vulnerabilities in the Python lock file were remediated and re-audited clean.
- Pre-existing infrastructure misconfigurations found by Trivy remain outside this code change and unresolved.
- No live `RESULT_CRITICAL` subscriber is wired: `process_critical_result_from_event()` is tested and fails closed, but notification activation is intentionally withheld while `AUD-CLIN-001` is `BLOCKED`.
- Three Python 3.12-only syntax sites and 13 further app modules importing `UTC` directly remain outside the Python 3.10 compatibility claim.
- NC013-C05 is a newly discovered, pre-existing safety-critical transfusion transition failure reproduced on the untouched baseline; it is deliberately not changed without a clinical workflow owner decision.

## Required actions

1. Implement fixes for C01–C04 and H01–H02 on the isolated branch.
2. Regenerate executable evidence for each affected finding.
3. Route clinical, identity, database-history, and release decisions to the human approval register.
