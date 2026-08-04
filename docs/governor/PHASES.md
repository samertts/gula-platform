# GULA Governor — Phase Design

> GULA-GOVERNOR-001 — detailed phase-by-phase design of the Governor layer.

## Phase 0 — Full System Audit

Audits every AI subsystem: Builder, Reviewer, Architect, Orchestrator,
Learner, Optimizer, Deployer, Knowledge, Registry, Constitution, AI
Bootstrap, Engineering Memory. Produces `GOVERNOR_AUDIT_REPORT.md` listing
weaknesses, conflicts, risks, missing policies, ownership, and authority.

Implementation: `scripts/governor/audit.py`.

## Phase 1 — Chain of Authority

One immutable hierarchy: Constitution → Governor → Architect → Orchestrator
→ Reviewer → Builder → Deployer → Learner → Optimizer. Every decision has
exactly one owner; no engine may override a higher authority.

Implementation: `scripts/governor/authority.py`. Artifact: `AUTHORITY_MAP.md`.

## Phase 2 — Mission Router

Classifies every mission by type, size, risk, and complexity, then selects
the minimum required engine pipeline. Never executes unnecessary engines.

| Mission | Pipeline |
|---|---|
| Tiny bug | Builder → Reviewer |
| Infrastructure change | Architect → Builder → Reviewer → Deployer |
| Large feature | Architect → Orchestrator → Builder → Reviewer → Learner → Optimizer |
| Security change | Architect → Builder → Reviewer → Deployer |

Implementation: `scripts/governor/mission_router.py`.

## Phase 3 — Decision Governance

Decision registry with priority, single ownership, conflict resolution
(majority voting, quorum 2, threshold 0.6), escalation rules (always up the
authority chain), and rollback rules. Only the Architect may approve
architectural decisions; only the Reviewer may approve deployments.

Implementation: `scripts/governor/decision_governance.py`.

## Phase 4 — Knowledge Governance

Prevents duplicate skills/playbooks/runbooks/ADRs via title + content
similarity. Implements merge, ranking, confidence, archive, retirement, and
the lifecycle Draft → Verified → Approved → Deprecated → Archived.

Implementation: `scripts/governor/knowledge_governance.py`.

## Phase 5 — Context Manager

Prevents context overflow with max files (50), tokens (60,000), reports
(10), and docs (25). Semantic-lite retrieval ranks knowledge by token
overlap; only required knowledge is loaded.

Implementation: `scripts/governor/context_manager.py`.

## Phase 6 — Loop Protection

Prevents infinite reviews/optimization/learning/planning with maximum
retries (3), review cycles (3), optimization cycles (3), learning cycles
(3), and planning cycles (5). Escalates to a human when limits are reached.

Implementation: `scripts/governor/loop_protection.py`.

## Phase 7 — Resource Governor

Monitors execution time and file writes; enforces 5-minute / 50-file micro
phases; creates automatic checkpoints and supports resume.

Implementation: `scripts/governor/resource_governor.py`.

## Phase 8 — Quality Gates

Eight mandatory gates: architecture, security, testing, performance,
documentation, knowledge, deployment, constitution. Missions failing any
mandatory gate are rejected.

Implementation: `scripts/governor/quality_gates.py`.

## Phase 9 — AI Safety

Blocks unsafe refactoring, mass file modification (>50 files), silent
architecture changes, breaking API changes, unsafe dependency updates,
unauthorized knowledge changes, unauthorized deployment, and secret access.
Requires approval when needed (Architect for architecture, Reviewer for
deployment).

Implementation: `scripts/governor/safety.py`.

## Phase 10 — Engine Communication

Standardized contract every engine must expose: inputs, outputs, status,
events, progress, health, errors, artifacts, dependencies, completion. No
direct undocumented communication.

Implementation: `scripts/governor/engine_contract.py`.

## Phase 11 — Self Governance

Continuously audits engines, knowledge, constitution compliance, and
technical debt; generates improvement proposals. Never modifies engines
automatically.

Implementation: `scripts/governor/self_governance.py`.

## Phase 12 — Health Dashboard

Generates `AI_HEALTH_DASHBOARD.md` with engine, knowledge, architecture,
deployment, documentation, performance, technical debt, risk, coverage, and
readiness health.

Implementation: `scripts/governor/health_dashboard.py`.

## Phase 13 — Enterprise Report

Generates `GOVERNOR_IMPLEMENTATION_REPORT.md` covering architecture,
governance, authority, knowledge, safety, performance, quality, conflict
resolution, resource management, and future recommendations.

Implementation: `scripts/governor/report.py`.
