# 13 — AI and Automation Governance — GULA-NATIONAL-COMPLETION-013

## Scope

Local AI/tool discovery, self-diagnostics, and guardrails against autonomous clinical decision-making.

## Methodology

Tool discovery only. No source code, secrets, PHI, identifiers, or private repository data were sent to external providers.

## Environment

Ollama service running with local models:
- `llama3:latest` (`365c0bd3c000`, 4.7 GB)
- `nomic-embed-text:latest` (`0a109f422b47`, 274 MB)

Available open-source engineering tools: Ruff, MyPy, pytest, Bandit, pip-audit, Semgrep, Trivy, Ollama, PostgreSQL, Redis.

## Commands and exit codes

```bash
ollama list                 # exit 0
command -v ruff mypy bandit semgrep trivy pip-audit   # exit 0
```

## Evidence paths

- `evidence/implementation_log.md`
- `00_EXECUTIVE_BASELINE.md`

## Findings

- AI-01 — INFO — Local inference is available and preferred; no commercial AI API used.
- AI-02 — HIGH — Runtime self-diagnostics and health classification are not independently verified; `NOT VERIFIED`.
- AI-03 — HIGH — Autonomous self-repair is constrained: no live clinical thresholds, diagnoses, identity ownership, or irreversible medical-data operation is permitted.

## Verification state

`RECONCILED` for tool discovery; `NOT VERIFIED` for runtime self-diagnostics.

## Limitations

- Local model quality was not benchmarked for clinical use.
- AI-generated output, if used, remains untrusted until independently tested.

## Residual risks

- Uncontrolled automation could become a clinical decision-maker; prohibited by program rules.

## Required actions

Keep all AI use in engineering assistance; do not activate clinical decision rules without qualified approval.
