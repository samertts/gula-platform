# Next Safe Action — GULA Stable v1.0.0

## Current gate
Phase 0 is active. Governance files and the working branch exist. Application code has not been changed.

## Next action
Run the read-only baseline locally on Ubuntu first, then reproduce the environment checks on Windows. Do not start remediation.

### Ubuntu
1. Clone or fetch the private repository and checkout `recovery/stable-v1`.
2. Confirm `git status --short` is empty and record `git rev-parse HEAD`.
3. Read the program charter, AI agent rules, Phase 0 plan, START_HERE, existing negative register and intelligent platform core docs.
4. Run repository inventory and existing deterministic inventory tools without writing generated files over maintained evidence.
5. Run the minimal baseline commands in isolation: Python syntax/lint, migration graph static test, selected focused tests, frontend lockfile/install/build checks only if dependencies are already available.
6. Do not run migrations against any persistent or real database. Use disposable local PostgreSQL only after inspecting the migration configuration and confirming the target database is disposable.
7. Save exact output, environment versions, timestamps, exit codes, and skipped tests under `EVIDENCE/BASELINE/`.

### Windows
Repeat repository/branch/worktree checks, inventory, Python/Node toolchain checks and supported tests. Mark Linux-only or unavailable toolchains NOT RUN/BLOCKED; do not infer parity.

## Stop conditions
Stop and request review before any database write, migration modification, secrets handling, production connection, clinical workflow change, authorization change, or broad refactor.

## Required review
Submit `BASELINE_REPORT.md`, machine-readable inventories, exact test logs and updated blocker register for human approval. Phase 1 remains unauthorized until that review is complete.