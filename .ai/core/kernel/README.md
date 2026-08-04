---
id: KER-AI-KERNEL-000001
type: kernel
title: "GULA AI Kernel — Execution Layer"
version: "1.0.0"
created: "2026-08-05"
status: active
confidence: 95%
tags: [kernel, execution, scheduler, safety, simulation, gula-kernel-001]
---

# AI Kernel — Execution Layer

## Purpose

The AI Kernel is the permanent execution layer of the GULA AI Operating
System. Every AI Engine executes inside it: it governs execution,
coordination, resource/state management, security, communication, knowledge
access, checkpointing, and recovery.

The Kernel **executes**. The Governor **governs** (never develops features,
protects the platform). Both are mandatory; the Kernel is the execution layer
that every engine depends on.

## Authority

The Kernel enforces the same immutable authority chain as the Governor
(Constitution → Governor → Architect → Orchestrator → Reviewer → Builder →
Deployer → Learner → Optimizer). The Kernel's maximum autonomous level is L5;
actions in the `ALWAYS_APPROVE` set always require human approval.

## Implementation

| Phase | Mechanism | Module |
|---|---|---|
| 0 | Foundation audit | `scripts/kernel/audit.py` |
| 1 | Execution state | `scripts/kernel/state.py` |
| 2 | Autonomy engine | `scripts/kernel/autonomy.py` |
| 3 | Engine contract | `scripts/kernel/contract.py` |
| 4 | Mission scheduler | `scripts/kernel/scheduler.py` |
| 5 | Resource manager | `scripts/kernel/resource.py` |
| 6 | Lock manager | `scripts/kernel/locks.py` |
| 7 | Context engine | `scripts/kernel/context.py` |
| 8 | Decision engine | `scripts/kernel/decisions.py` |
| 9 | Knowledge engine | `scripts/kernel/knowledge.py` |
| 10 | Safety engine | `scripts/kernel/safety.py` |
| 11 | Simulation engine | `scripts/kernel/simulation.py` |
| 12 | Quality engine | `scripts/kernel/quality.py` |
| 13 | Observability engine | `scripts/kernel/observability.py` |
| 14 | Failure recovery | `scripts/kernel/recovery.py` |
| 15 | Technical debt engine | `scripts/kernel/debt.py` |
| 16 | Engine registry | `scripts/kernel/registry.py` |
| 17 | Self diagnostics | `scripts/kernel/diagnostics.py` |
| 18 | Enterprise report | `scripts/kernel/report.py` |
| CLI | Entry point | `scripts/kernel.py` |

## CLI

```bash
python scripts/kernel.py check       # self-check (exit 1 on failure)
python scripts/kernel.py audit       # Phase 0 → KERNEL_AUDIT_REPORT.md
python scripts/kernel.py simulate    # Phase 11 simulation pass
python scripts/kernel.py report      # Phase 18 → enterprise reports
```

## Mandatory Rules Enforced

- No duplication: Kernel reuses Governor policy modules (`scripts/governor.*`)
  rather than re-implementing them.
- No execution without a simulation pass.
- No execution without checkpoints.
- 5-minute / 50-file micro phases.
- Everything versioned, auditable, recoverable, searchable, observable,
  reversible, measurable.

## Related

- `.ai/core/governor/README.md` — Governance layer (superset authority)
- `KERNEL_AUDIT_REPORT.md` — Phase 0 foundation audit
- `KERNEL_IMPLEMENTATION_REPORT.md` — Phase 18 implementation report
- `ENTERPRISE_READINESS_SCORE.md` — readiness 100.0/100 (grade A)
- `AI_OPERATING_STATUS.md` — operating status
- `docs/kernel/` — execution-layer documentation
