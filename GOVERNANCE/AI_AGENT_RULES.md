# AI Agent Operating Rules — GULA Stable v1.0.0

Applies equally to OpenCode and VS Code AI on Ubuntu and Windows.

## Execution protocol
1. Read this file, `GOVERNANCE/GULA_STABLE_V1_PROGRAM_CHARTER.md`, `PROGRAM/GULA_STABLE_V1_PHASE_ZERO.md`, `docs/START_HERE.md`, and the current blocker register before work.
2. Confirm branch, HEAD, working-tree state, and scope before editing.
3. Work only on the approved `recovery/stable-v1` branch or a task branch created from it. Never write to `main`.
4. Use the smallest possible context: inspect relevant files and dependency edges before opening broad directories.
5. Prefer existing scripts, tests, registries, and documentation over duplicate tools.
6. Separate observation, hypothesis, change, and verification. Do not present a hypothesis as a fact.
7. Run targeted tests first, then required regression gates. Record exact commands and outputs.
8. Stop when scope expands, a migration/data-loss risk appears, a clinical safety invariant is unclear, or credentials/production data are required. Request human review.

## Forbidden actions without explicit human approval
- Destructive SQL, database reset, downgrade on any non-disposable database, or data migration execution against production.
- Force push, direct main commits, branch deletion, release/tag creation, deployment, or secret rotation.
- Changing clinical decision logic, authorization policy, patient identity matching, audit semantics, retention rules, cryptographic controls, or migration history.
- Removing modules, tests, workflows, records, or configuration to make checks pass.
- Disabling tests, weakening assertions, adding broad ignores, suppressing diagnostics, or marking tests as expected failures to hide defects.
- Adding paid AI services, API keys, or external data processors.

## Low-budget policy
- Use static inspection, grep/search, existing deterministic tools, Ruff, MyPy, pytest, npm scripts, and local PostgreSQL/Redis before invoking paid models.
- Avoid repeated full-repository context. Summarize findings into durable Markdown/JSON evidence.
- Do not send secrets, patient data, or private operational data to model providers.
- Track model, input/output tokens when available, estimated cost, elapsed time, and task ID. If unavailable, record UNKNOWN rather than inventing usage.

## Required task report
Every completed task must record: task ID; objective; branch and starting SHA; files inspected/changed; evidence; exact commands; pass/fail/skip counts; risks; token/cost usage or UNKNOWN; elapsed time; commit SHA if committed; next safe action.

## Verification language
Use only: PASS (executed and passed), FAIL (executed and failed), BLOCKED (could not run due to a stated dependency), NOT RUN, or UNKNOWN. AI-generated review is not independent verification.