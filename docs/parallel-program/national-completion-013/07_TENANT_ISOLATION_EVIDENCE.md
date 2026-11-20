# 07 — Tenant Isolation Evidence — GULA-NATIONAL-COMPLETION-013

## Scope

Cross-tenant authorization evidence for application domains. The previous verification checkpoint recorded 312 BOLA cases with 7 failures; that raw evidence is unavailable because the prior isolated workspace no longer exists.

## Methodology

At baseline: source inventory plus inherited checkpoint. A later phase must execute synthetic multi-tenant tests against the isolated branch and record exact commands/output.

## Environment

Isolated clone; synthetic tenants only.

## Commands and exit codes

No new tenant-isolation test execution yet in this workspace. Inherited record from checkpoint: 312 cases, 305 pass, 7 fail; not re-executable here.

## Evidence paths

- `evidence/unified_findings_register.json` (NC013-H05/H06)
- `evidence/implementation_log.md` (to be appended)
- `04_UNIFIED_FINDINGS_REGISTER.md`

## Findings

- **TEN-01 — CRITICAL — Inherited BOLA failures.** Seven previously reproduced failures cannot be re-opened from raw logs; they remain open by root cause.
- **TEN-02 — HIGH — Patients routes lack per-action authorization** (AUD-SEC-005).
- **TEN-03 — HIGH — health_core guard not wired** (AUD-SEC-008).

## Verification state

`NOT VERIFIED`.

## Limitations

- No raw verification-010 evidence file is available.
- Source search alone is not accepted as isolation proof.

## Residual risks

- Cross-tenant patient-data exposure remains plausible until negative tests are executed on the final head.

## Required actions

Build at least three synthetic tenants and test read/write/update/delete/export/indirect-reference paths across the domains listed in the mandate. Do not mark FIXED without negative proof.
