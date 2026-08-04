---
id: GOV-GOVERNOR-000001
type: governor
title: "GULA Governor — Governance Layer"
version: "1.0.0"
created: "2026-08-04"
status: active
confidence: 95%
tags: [governor, governance, coordination, gula-governor-001]
---

# Governor — Governance Layer

## Purpose

The Governor is the supreme coordination, policy, validation,
conflict-resolution, resource-management, knowledge-governance, and
execution-control framework for the GULA AI Operating System.

The Governor **never develops features**. It protects the platform.

## Authority

```
Constitution
   ↓
Governor
   ↓
Architect
   ↓
Orchestrator
   ↓
Reviewer
   ↓
Builder
   ↓
Deployer
   ↓
Learner
   ↓
Optimizer
```

Every decision has exactly one owner. No engine may override a higher authority.

## Implementation

| Phase | Mechanism | Module |
|---|---|---|
| 0 | Full system audit | `scripts/governor/audit.py` |
| 1 | Chain of authority | `scripts/governor/authority.py` |
| 2 | Mission router | `scripts/governor/mission_router.py` |
| 3 | Decision governance | `scripts/governor/decision_governance.py` |
| 4 | Knowledge governance | `scripts/governor/knowledge_governance.py` |
| 5 | Context manager | `scripts/governor/context_manager.py` |
| 6 | Loop protection | `scripts/governor/loop_protection.py` |
| 7 | Resource governor | `scripts/governor/resource_governor.py` |
| 8 | Quality gates | `scripts/governor/quality_gates.py` |
| 9 | AI safety | `scripts/governor/safety.py` |
| 10 | Engine communication | `scripts/governor/engine_contract.py` |
| 11 | Self governance | `scripts/governor/self_governance.py` |
| 12 | Health dashboard | `scripts/governor/health_dashboard.py` |
| 13 | Enterprise report | `scripts/governor/report.py` |
| CLI | Entry point | `scripts/governor.py` |

## CLI

```bash
python scripts/governor.py audit      # Phase 0 → GOVERNOR_AUDIT_REPORT.md
python scripts/governor.py authority  # Phase 1 → AUTHORITY_MAP.md
python scripts/governor.py health     # Phase 12 → AI_HEALTH_DASHBOARD.md
python scripts/governor.py report     # Phase 13 → GOVERNOR_IMPLEMENTATION_REPORT.md
python scripts/governor.py check      # self-check (exit 1 on failure)
```

## Mandatory Rules Enforced

- No duplicated knowledge, reports, authority, ownership, or decisions.
- No hidden modifications.
- No automatic breaking changes.
- No architecture modifications without Architect approval.
- No deployment without Reviewer approval.
- No optimization without benchmarks.
- No learning without verification.
- No execution without checkpoints.
- No phase longer than 5 minutes or 50 files.

## Related

- `AI_OPERATING_CONSTITUTION.md` — supreme authority
- `AUTHORITY_MAP.md` — chain of authority
- `GOVERNOR_AUDIT_REPORT.md` — Phase 0 audit
- `GOVERNOR_IMPLEMENTATION_REPORT.md` — Phase 13 report
- `docs/governor/` — governance documentation
