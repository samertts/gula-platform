# GULA AI Kernel — Execution Layer Documentation

> Mission: GULA-KERNEL-001
> Purpose: Enterprise AI Execution Kernel — the permanent execution layer every
> AI Engine depends on (governance, execution, coordination, resource/state
> management, security, communication, knowledge access, checkpointing,
> recovery).

## Documents

| Document | Purpose |
|---|---|
| `docs/kernel/README.md` | This index |
| `docs/kernel/PHASES.md` | Detailed phase-by-phase design (Phases 0–18) |
| `docs/kernel/CONTRACT.md` | Phase 3 engine contract + autonomy levels |

The Kernel is implemented in `scripts/kernel/` and invoked via
`scripts/kernel.py`. Root artifacts: `KERNEL_AUDIT_REPORT.md`,
`KERNEL_IMPLEMENTATION_REPORT.md`, `ENTERPRISE_READINESS_SCORE.md`,
`AI_OPERATING_STATUS.md`.

## Command Reference

```bash
python scripts/kernel.py check       # Kernel self-check (CI gate)
python scripts/kernel.py audit       # Phase 0 foundation audit
python scripts/kernel.py state       # Phase 1 execution state
python scripts/kernel.py autonomy    # Phase 2 autonomy levels
python scripts/kernel.py contract    # Phase 3 engine contract
python scripts/kernel.py schedule    # Phase 4 mission scheduler
python scripts/kernel.py resources   # Phase 5 resource manager
python scripts/kernel.py locks       # Phase 6 lock manager
python scripts/kernel.py context     # Phase 7 context engine
python scripts/kernel.py decisions   # Phase 8 decision engine
python scripts/kernel.py knowledge   # Phase 9 knowledge engine
python scripts/kernel.py safety      # Phase 10 safety engine
python scripts/kernel.py simulate    # Phase 11 simulation engine
python scripts/kernel.py quality     # Phase 12 quality engine
python scripts/kernel.py observe     # Phase 13 observability engine
python scripts/kernel.py recover     # Phase 14 failure recovery
python scripts/kernel.py debt        # Phase 15 technical debt engine
python scripts/kernel.py registry    # Phase 16 engine registry
python scripts/kernel.py diagnose    # Phase 17 self diagnostics
python scripts/kernel.py report      # Phase 18 enterprise report
```

## Integration

- `make kernel-check` — run the AI Kernel self-check.
- `make kernel-report` — regenerate all Kernel artifacts.
- `make kernel-test` — run Kernel unit tests.
- CI: the `ai-governance.yml` workflow runs `python3 scripts/kernel.py check`.

## Design Principles

1. **No duplication** — Kernel policy reuses Governor policy modules
   (`scripts/governor.*`) rather than re-implementing them.
2. **Simulate before execute** — no mission executes without a simulation pass.
3. **Checkpoint before execute** — no mission executes without checkpoints.
4. **Bounded work** — 5-minute / 50-file micro phases.
5. **Everything versioned, auditable, recoverable, searchable, observable,
   reversible, measurable.**

## Runtime State

Kernel runtime state lives under `.ai/core/kernel/state/` and is gitignored:
`execution_state.json`, `tasks.json`, `decision_history.json`,
`incidents.json`, and `checkpoints/`.
