# GULA AI Kernel — Phase Design

> GULA-KERNEL-001 — detailed phase-by-phase design of the AI Execution Kernel.
> The Kernel is the permanent execution layer: every AI Engine runs inside it.
> It governs execution, coordination, resource/state management, security,
> communication, knowledge access, checkpointing, and recovery.

## Phase 0 — Foundation Audit

Audits the entire execution foundation: Governor, existing Kernel concepts,
knowledge, registry, constitution, brain, debt automation, monitoring, and
architecture compliance. Produces `KERNEL_AUDIT_REPORT.md` (5 findings).

Implementation: `scripts/kernel/audit.py`.

## Phase 1 — Execution State

Tracks the canonical mission execution state in
`.ai/core/kernel/state/execution_state.json`: mission, phase, status, tasks,
checkpoints, and history. Provides a machine-readable, resumable state record.

Implementation: `scripts/kernel/state.py`.

## Phase 2 — Autonomy Engine

Defines autonomy levels L0 (read-only) → L8 (dangerous). Computes the maximum
autonomous level a mission may take given its actions; a fixed `ALWAYS_APPROVE`
set (delete functionality, drop database, deploy to production, dangerous
operations) always requires human approval. Reference autonomy = L5.

Implementation: `scripts/kernel/autonomy.py`.

## Phase 3 — Engine Contract

Every engine MUST expose a 16-field contract: inputs, outputs, events, errors,
artifacts, ownership, dependencies, health, progress, checkpoint, capabilities,
resources, timeout, retry, version, status. No undocumented engine behavior.

Implementation: `scripts/kernel/contract.py`. See `docs/kernel/CONTRACT.md`.

## Phase 4 — Mission Scheduler

Priority-queue mission scheduler with execution layers, DAG dependency ordering,
critical-path detection, fair scheduling, and cycle detection. Ensures missions
run in dependency order with priority escalation.

Implementation: `scripts/kernel/scheduler.py`.

## Phase 5 — Resource Manager

Monitors system load (CPU/memory), splits work into 5-minute/50-file micro
phases, and creates/resumes checkpoints using the Governor resource governor.

Implementation: `scripts/kernel/resource.py`.

## Phase 6 — Lock Manager

Six lock types with deadlock detection via wait-for graphs, TTL-based auto
unlock, and conflict resolution. Prevents concurrent engines corrupting state.

Implementation: `scripts/kernel/locks.py`.

## Phase 7 — Context Engine

Lazy LRU cache, context compression, and semantic-lite search reusing the
Governor context manager. Keeps context within limits while preserving meaning.

Implementation: `scripts/kernel/context.py`.

## Phase 8 — Decision Engine

Confidence/risk scoring, simulation and adverse-case review before decisions,
full decision tracing, and save/load of `decision_history.json`. Reuses the
Governor decision governance for conflicts and escalation.

Implementation: `scripts/kernel/decisions.py`.

## Phase 9 — Knowledge Engine

Knowledge search, dependency graph, health check, validation, archiving, and
merge. Reuses Governor knowledge governance + `KNOWLEDGE_LIFECYCLE`. Prevents
duplicate knowledge and enforces the lifecycle.

Implementation: `scripts/kernel/knowledge.py`.

## Phase 10 — Safety Engine

Denied commands plus checks for loops, mass modification, secrets, unsafe
deploy, knowledge changes, and architecture changes. Reuses Governor safety +
loop protection. Any violation blocks execution.

Implementation: `scripts/kernel/safety.py`.

## Phase 11 — Simulation Engine

Virtual repo, virtual DB, virtual deploy, virtual infra, virtual knowledge, and
rollback simulation. Simulation stops on the first failure; a failed simulation
raises and prevents real execution.

Implementation: `scripts/kernel/simulation.py`.

## Phase 12 — Quality Engine

Nine quality gates: architecture, security, testing, knowledge, deployment,
performance, documentation, governance, constitution (Governor's 8 + governance).

Implementation: `scripts/kernel/quality.py`.

## Phase 13 — Observability Engine

Metrics registry, tracer, audit log, timeline, and five dependency graphs
(engine, knowledge, decision, dependency, execution). Everything is measurable
and auditable.

Implementation: `scripts/kernel/observability.py`.

## Phase 14 — Failure Recovery

Classifies failures, plans bounded recovery (max retries), records incidents,
and resumes from Governor checkpoints. No unbounded retry loops.

Implementation: `scripts/kernel/recovery.py`.

## Phase 15 — Technical Debt Engine

Detects large modules, TODOs, secrets, nested loops, duplicate blocks, dead
code, and drift (knowledge, dependency, configuration, architecture).

Implementation: `scripts/kernel/debt.py`.

## Phase 16 — Engine Registry

Registry of the seven engines (Architect, Orchestrator, Reviewer, Builder,
Deployer, Learner, Optimizer) with seven matrices (ownership, autonomy,
contract, capabilities, dependencies, accountability, health).

Implementation: `scripts/kernel/registry.py`.

## Phase 17 — Self Diagnostics

Runs the Kernel's own diagnostics and generates improvement proposals reusing
Governor self governance. The Kernel audits itself.

Implementation: `scripts/kernel/diagnostics.py`.

## Phase 18 — Enterprise Report

Generates `KERNEL_IMPLEMENTATION_REPORT.md`, `ENTERPRISE_READINESS_SCORE.md`
(readiness 100.0/100, grade A from measurable signals), and
`AI_OPERATING_STATUS.md`.

Implementation: `scripts/kernel/report.py`.
