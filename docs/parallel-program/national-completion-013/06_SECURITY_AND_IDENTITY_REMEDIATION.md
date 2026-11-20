# 06 — Security and Identity Remediation — GULA-NATIONAL-COMPLETION-013

## Scope

Security and identity defects within this program's implementable scope: NIAM persons authentication, NID/MPI fail-closed behavior, and gRPC fail-closed behavior. Broader security findings are tracked in `04_UNIFIED_FINDINGS_REGISTER.md`.

## Methodology

Reproduce from source, implement minimal real fixes on the isolated branch, add regression tests, and verify with pytest. No clinical authority or government identity registry is simulated as authoritative.

## Environment

Isolated clone, Python 3.10/3.12, synthetic data only.

## Commands and exit codes

Implementation commands and exact pytest invocations will be appended to `evidence/implementation_log.md` after each fix.

## Evidence paths

- `evidence/critical_defect_research.md`
- `evidence/implementation_log.md`
- `07_TENANT_ISOLATION_EVIDENCE.md`

## Findings

- NC013-C02: unauthenticated NIAM person create/read endpoints — `PARTIALLY FIXED` at baseline due PR #261 patch source only.
- NC013-C03: gRPC false success — `NOT FIXED` at baseline.
- NC013-C04: unverified NID identity bridge — `NOT FIXED` at baseline.
- NC013-H05/H06/H07: broader authorization/break-glass findings — `NOT VERIFIED`.

## Verification state

`HUMAN APPROVAL REQUIRED` for release; `NOT VERIFIED` until implementation evidence is recorded.

## Limitations

- No real Iraqi civil identity registry access exists or is claimed.
- No production secrets, PHI, or NIDs are used.

## Residual risks

- Fixing route authentication does not by itself establish authorization policy or tenant scope.
- MPI fails closed only for the paths changed; other identity routes remain to be audited.

## Required actions

1. Apply mount-level and handler-level NIAM authentication; return 404 on unknown person UUID.
2. Make gRPC unavailable state explicit and remove payload echo.
3. Stop NID-based identity disclosure and auto-matching when `nid_verified` is false.
4. Add independent review before accepting any fix.
