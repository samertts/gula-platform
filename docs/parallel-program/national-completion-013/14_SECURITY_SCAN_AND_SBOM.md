# 14 — Security Scan and SBOM — GULA-NATIONAL-COMPLETION-013

## Scope

Static analysis, secret scanning, dependency and vulnerability scanning, container/configuration scanning, and SBOM evidence.

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

`PARTIAL` — scanner-clean results for changed Python files, the Python dependency lock and CI secret/security checks; 490 infrastructure misconfigurations, an incomplete Trivy vulnerability-DB download and absent SBOM remain open.

## Limitations

- Network restrictions may block scanner databases; blockers will be documented precisely.
- A scanner detecting no findings is not proof of absence of vulnerabilities.

## Residual risks

- Exposed secrets or critical dependencies may remain undiscovered.

## Required actions

Run and preserve exact commands, exit codes and raw outputs; never label a failed/blocked scan successful.

## Execution update — 2026-11-20

| Scan                        | Command scope                                      | Exit | Result                                                                                          |
| --------------------------- | -------------------------------------------------- | ---: | ----------------------------------------------------------------------------------------------- |
| Ruff                        | changed `.py` files                                |    0 | All checks passed                                                                               |
| Bandit (`-ll`)              | changed backend app/migration files                |    0 | No medium/high findings                                                                         |
| Semgrep (`p/python`)        | changed backend app/migration files                |    0 | 0 results, 34 paths scanned, 1 WARN timeout on `backend/app/lims/routes.py` — partial coverage  |
| pip-audit (initial)         | `backend/requirements-lock.txt`                    |    1 | 55 vulnerabilities in 6 packages                                                                |
| pip-audit (final)           | upgraded lock file                                 |    0 | No known vulnerabilities                                                                        |
| Trivy vuln+secret+misconfig | repository filesystem                              |    1 | Vulnerability DB download timed out — **not completed**                                         |
| Trivy secret+misconfig      | repository filesystem                              |    0 | 0 secrets; 490 pre-existing misconfigurations (34 CRITICAL, 85 HIGH, 91 MEDIUM, 280 LOW)        |
| CI Secret Scan (initial)    | PR #307 docs commit `5079d67d`                     |    2 | Gitleaks `generic-api-key` false positive on "dependency/vulnerability"; no credential material |
| CI Secret Scan (re-run)     | PR #307 after targeted stopword + sentence rewrite |    0 | `no leaks detected`                                                                             |

Lock-file upgrades: `certifi 2026.10.18`, `dnspython 2.9.2`, `pillow 13.0.0`, `pyasn1 0.6.5`, `joserfc 1.7.6`, `urllib3 2.8.0`. A separate runtime dependency gap was closed by declaring `greenlet>=3.5.5` in `backend/requirements.txt`; greenlet is MIT-licensed, free/open source and was already pinned in the lock file. No commercial alternative was introduced.

Raw outputs: `evidence/test_logs/ruff_changed_nc013_driftclosed.log`, `bandit_changed_nc013_driftclosed.log`, `semgrep_changed_nc013_driftclosed.log`, `pip_audit_nc013.log`, `pip_audit_nc013_final.log`, `trivy_fs_nc013.log`, `trivy_secret_misconfig_nc013.log`. Earlier passes are preserved as `*_final.log` and `bandit_changed_nc013.log` / `semgrep_changed_nc013.log`. The final Ruff pass required targeted `# noqa: RUF001` annotations on two pre-existing medical unit strings (`×10³/µL`) to avoid changing clinical notation.

Verification state: **PARTIAL**. Scanner-clean results cover changed Python files and the Python dependency lock only. The container/IaaS misconfigurations remain open and no SBOM generation is claimed.
