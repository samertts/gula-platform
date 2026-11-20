# 14 — Security Scan and SBOM — GULA-NATIONAL-COMPLETION-013

## Scope

Static analysis, secret scanning, dependency/vulnerability scanning, container/config scanning, and SBOM evidence.

## Methodology

Free/open-source scanners only. Tool availability was confirmed; execution results will be appended after implementation on the final combined head. Failed or blocked tools will be recorded as blocked, never as success.

## Environment

Ruff 0.15.21, MyPy 2.2.0, Bandit 1.9.4, pip-audit 2.10.1, Semgrep 1.168.0, Trivy 0.72.0. `gitleaks`, `osv-scanner`, and `gitleaks` binary availability was not confirmed in the earlier check; `trivy` covers secret/misconfig use cases where available.

## Commands and exit codes

```bash
ruff --version
mypy --version
bandit --version
pip-audit --version
semgrep --version
trivy --version
```

All exit 0.

## Evidence paths

- `evidence/implementation_log.md`
- `evidence/security_scan_results/` (to be generated)

## Findings

- SCAN-01 — HIGH — No scan result has been produced yet for this program; `NOT VERIFIED`.
- SCAN-02 — HIGH — Baseline GitHub Security Hardening failed at Gitleaks history scan and pinned-manifest audit.
- SCAN-03 — MEDIUM — PR #261 raw Semgrep attempts in prior program had rule parse errors; no successful scan accepted.

## Verification state

`NOT VERIFIED`.

## Limitations

- Network restrictions may block scanner databases; blockers will be documented precisely.
- A scanner detecting no findings is not proof of absence of vulnerabilities.

## Residual risks

- Exposed secrets or critical dependencies may remain undiscovered.

## Required actions

Run and preserve exact commands, exit codes and raw outputs; never label a failed/blocked scan successful.
