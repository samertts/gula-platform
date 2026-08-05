# Learner Engine (GULA-LEARNER-001)

Transforms every completed mission into permanent, versioned, searchable
engineering knowledge. It never develops features and never deploys software —
it continuously extracts lessons, generates skills/playbooks/runbooks, records
memory, improves the knowledge base, and publishes learning reports. Knowledge
enters the engine from verified missions (Reviewer → Orchestrator).

## Pipeline

audit → extract → skill → playbook → runbook → memory → pattern → improve →
quality → search → report

## Phases

| Phase | Module | Responsibility |
|---|---|---|
| 0 | `audit.py` | Knowledge surface audit -> `LEARNER_AUDIT_REPORT.md` |
| 1 | `extract.py` | Deterministic knowledge extraction from missions/artifacts |
| 2 | `skills.py` | Versioned, id-sequenced skill generation (`SKILL-000008`) |
| 3 | `playbooks.py` | Template-complete playbooks (`PLAYBOOK-000005`) |
| 4 | `runbooks.py` | Template-complete runbooks (`RUNBOOK-000006`) |
| 5 | `memory.py` | Permanent memory records (`KNOW-000002`) |
| 6 | `patterns.py` | Thresholded pattern discovery + proposals (`PRO-000001..6`) |
| 7 | `improve.py` | Improvement proposals, deterministic IDs |
| 8 | `quality.py` | 7-check knowledge quality gate (health 90/100) |
| 9 | `search.py` | Search index + relevance scoring |
| 10 | `report.py` | `LEARNER_IMPLEMENTATION_REPORT.md` + learning report |

## Commands

All commands are reachable through `python scripts/kernel.py learner-<cmd>`
and `python scripts/learner.py <cmd>`:

- `learner-audit`, `learner-extract`, `learner-skill`, `learner-playbook`,
  `learner-runbook`, `learner-memory`, `learner-patterns`, `learner-improve`,
  `learner-quality`, `learner-search`, `learner-report`, `learner-learn`,
  `learner-check`.

The success criterion runs end-to-end idempotently without manual intervention:

```
python scripts/kernel.py learner-learn
```

## Principles

- Every mission produces permanent, versioned, searchable knowledge.
- Extraction is deterministic; regeneration reuses existing items — never
  duplicates skills/playbooks/runbooks/memory.
- Every artifact references only existing knowledge; quality gate fails on
  broken references.
- Knowledge health is bounded and monitored (7/7 checks, health 90/100).
- Improvement proposals are thresholded, deterministic, and actionable.
- Deterministic, auditable, continuously improving learning coordination.
