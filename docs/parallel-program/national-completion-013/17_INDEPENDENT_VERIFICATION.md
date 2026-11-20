# 17 — Independent Verification — GULA-NATIONAL-COMPLETION-013

## Scope

Rules and current status for independent adversarial verification of implemented fixes.

## Methodology

A fix is not accepted on the implementer's assertion. Verification must:
1. Reproduce the original defect against the pre-fix commit.
2. Re-run the same reproduction against the fixed commit.
3. Attempt negative proof by perturbing or disabling the fix where practical.
4. Record exact command, environment, output, exit code, commit SHA, and limitations.

No agent may approve its own work as sole acceptance authority.

## Environment

Independent review agents may run in separate child sessions with fresh context. They receive read-only or explicitly assigned scopes.

## Commands and exit codes

No independent verification has been executed yet for this program. `NOT VERIFIED`.

## Evidence paths

- `evidence/implementation_log.md`
- `19_HUMAN_APPROVAL_REGISTER.md`

## Findings

- IND-01 — HIGH — No independent acceptance has occurred for this program's fixes yet.
- IND-02 — MEDIUM — Prior program's independent verification files are unavailable; they cannot be reused as primary evidence.

## Verification state

`NOT VERIFIED`.

## Limitations

- Time/resource constraints may limit depth; any unverified area remains open.

## Residual risks

- Self-verification bias and undetected regressions.

## Required actions

Launch independent verification after implementation commits; do not mark release-ready without it.
