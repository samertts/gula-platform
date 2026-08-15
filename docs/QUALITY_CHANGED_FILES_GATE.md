# Changed-Files Ruff/MyPy Quality Gate

## Purpose

`python scripts/quality_changed_files_gate.py` enforces non-regression instead of pretending that the repository-wide Ruff/MyPy debt is already zero. It compares the base and head revisions per Python file and also compares the configured critical scopes.

The gate fails when a file has more Ruff or MyPy diagnostics at head than at base. It also fails when a diagnostic increases in any critical scope, even if the affected file was not listed as a changed Python file. Existing debt is reported and preserved; it is not hidden, reset, or converted into a pass claim.

## Local usage

From a checkout with the base ref available:

```bash
python scripts/quality_changed_files_gate.py \
  --base-ref origin/main \
  --head-ref HEAD \
  --report quality-gate-report.json
```

A documentation-only change is allowed and produces a PASS with zero changed Python files. Use `--require-python-change` only for a workflow that intentionally requires Python changes.

Critical scopes default to:

```text
backend/app/security
backend/app/identity
backend/app/clinical_gateway
backend/app/audit
backend/app/authorization
```

A workflow may override them by repeating `--critical-scope`.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | No diagnostic increase and no tool execution error |
| 1 | Ruff/MyPy diagnostic regression or explicit policy failure |
| 2 | Gate execution/configuration error, such as an unresolved Git ref or invalid tool output |

## CI behavior

`.github/workflows/quality-changed-files.yml` runs on pull requests targeting `main`, fetches full history, installs the backend runtime dependencies plus pinned `ruff==0.16.2` and `mypy==2.3.0`, runs the gate against `origin/${GITHUB_BASE_REF}` and the pull request head SHA, and uploads the JSON report as an artifact.

The workflow does not require repository-wide zero debt. It prevents new debt while the existing debt is addressed in scoped batches. It must not be weakened with global `noqa`, `type: ignore`, disabled MyPy checks, or altered Ruff configuration. Exceptions require a separate, explicit governance record that names the scope, owner, expiry and anti-regression condition.

## Review expectations

Every remediation PR should include the gate report, the before/after diagnostic counts, affected tests, and a statement that authorization, audit, tenant isolation and clinical fail-closed behavior were not bypassed. A green gate does not by itself close P4; database, runtime, production flag, Railway, rollback, performance and human-review evidence remain separate requirements.
