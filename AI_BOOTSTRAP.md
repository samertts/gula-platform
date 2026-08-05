# AI_BOOTSTRAP.md

> **Version:** 1.0.0
> **Status:** Active
> **Purpose:** First document every AI assistant reads before any work
> **Authority:** References `AI_OPERATING_CONSTITUTION.md` (supreme)

---

## Purpose

This file is the **mandatory entry point** for every AI assistant working
on the GULA Platform repository. It establishes context, directs reading
order, and enforces governance before any implementation begins.

**Never skip this file.** Never start work without reading it first.

---

## Repository Overview

**GULA Platform** is a national healthcare Laboratory Information System
(LIS) for Iraq. It is a monolithic FastAPI application with React frontend,
designed for FHIR R4 interoperability, multi-tenancy, offline-first operation,
and Arabic-first user experience.

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Mobile | Flutter (Android/iOS) |
| Cache | Redis 7.x |
| Storage | MinIO (S3-compatible) |
| AI | Ollama (local inference) |
| Container | Docker |
| CI/CD | GitHub Actions |

---

## Reading Order

Every AI session MUST follow this order:

1. **AI_BOOTSTRAP.md** (this file) — context and rules
2. **AI_OPERATING_CONSTITUTION.md** — supreme authority
3. **CLAUDE.md** — full operating manual (commands, architecture, security)
4. **AGENTS.md** — engineering rules + workspace state
5. **docs/brain/PROJECT_BRAIN.md** — live knowledge index
6. **docs/constitution/** — domain-specific rules (01-32)
7. **docs/adr/** — architecture decisions
8. **.ai/core/skills/** — existing solutions
9. **.ai/core/playbooks/** — procedures
10. **.ai/core/runbooks/** — operational guides
11. **.ai/core/sdk/** — plugin SDK (GULA-KERNEL-EXT-001)
12. **.ai/core/policies/** — policy engine catalog
13. **.ai/core/compat/** — compatibility matrix
14. **.ai/core/migrations/** — migration plans
15. **.ai/core/events/** — event bus journal
16. **.ai/core/workflows/** — workflow state
17. **.ai/core/marketplace/** — AI marketplace catalog
18. **.ai/core/evolution/** — evolution signals/RFCs
19. **.ai/core/health/** — health reports

---

## Knowledge System

The GULA Platform has a structured AI knowledge system at `.ai/core/`:

| Directory | Purpose | Count |
|---|---|---|
| `skills/` | Problem solutions | 7 |
| `playbooks/` | Step-by-step procedures | 4 |
| `runbooks/` | Operational guides | 5 |
| `checklists/` | Verification lists | 3 |
| `capabilities/` | System capabilities | 1 |
| `decisions/` | Decision records | 1 |
| `failures/` | Failure database | 2 |
| `kup/` | Knowledge governance (KUP) | 8 |
| `quality/` | Quality & governance docs | 10 |
| `registry/` | Knowledge registry | 1 |
| `graph/` | Knowledge relationships | 1 |
| `memory/` | Persistent memory | 4 |
| `lessons/` | Learned lessons | 3 |
| `index/` | Master index + search | 3 |
| `sdk/` | Plugin SDK (GULA-KERNEL-EXT-001) | 6 |
| `policies/` | Policy Engine catalog | 3 |
| `compat/` | Compatibility matrix | 2 |
| `migrations/` | Migration plans | 2 |
| `events/` | Event bus journal | 2 |
| `workflows/` | Workflow state | 2 |
| `marketplace/` | AI Marketplace catalog | 2 |
| `evolution/` | Evolution signals/RFCs | 2 |
| `health/` | Health reports | 2 |

---

## Constitution

The **AI_OPERATING_CONSTITUTION.md** is the supreme authority.
All other files reference it. If any conflict exists, the constitution wins.

**Precedence hierarchy:**
1. AI_OPERATING_CONSTITUTION.md
2. Architecture Decision Records
3. Architecture Documentation
4. Project Standards
5. Skills, Playbooks, Runbooks, Checklists
6. Tool-specific instructions (AGENTS.md, CLAUDE.md, etc.)
7. Conversation instructions

---

## Architecture

| Pattern | Status |
|---|---|
| Monolith-first | ADR-002 |
| Clean Architecture | Active |
| SOLID | Enforced |
| DDD | Bounded contexts |
| CQRS | Where appropriate |
| Event-driven | Event Bus |

See `docs/architecture/CANONICAL_ARCHITECTURE.md` for full architecture.

---

## Engineering Principles

1. **Correctness** over speed
2. **Maintainability** over cleverness
3. **Scalability** over premature optimization
4. **Security** over convenience
5. **Reliability** over features
6. **Long-term architecture** over quick fixes

---

## Coding Standards

| Standard | Rule |
|---|---|
| Python | 3.12, snake_case, type hints mandatory |
| TypeScript | Strict mode, ESLint, Prettier |
| Linting | Ruff (Python), ESLint (TypeScript) |
| Testing | pytest (backend), Vitest (frontend) |
| Documentation | Google style docstrings |
| Commits | Conventional Commits |
| Max line | 88 chars (Python), 100 chars (TypeScript) |

---

## Execution Rules

### Before Every Task
1. Read this bootstrap file
2. Read the constitution
3. Search `.ai/core/skills/` for existing solutions
4. Search `.ai/core/memory/` for project context
5. Search `.ai/core/playbooks/` for procedures
6. Search `docs/adr/` for architecture decisions
7. Only then investigate externally

### After Every Task
1. Run tests
2. Run lint
3. Run type checking
4. Update knowledge if new skill learned
5. Update memory if architecture changed
6. Create checkpoint if long task
7. Commit with conventional commit message

---

## Audit First Policy

**Never modify without understanding.** Before any change:
- Read the affected files
- Check git history for previous attempts
- Search for existing patterns
- Verify no duplication
- Assess impact on other modules

---

## Long Task Policy

For tasks exceeding **5 minutes** or **50 files**:
1. Create a checkpoint before starting
2. Work in phases (max 5 min or 50 files each)
3. Save state after each phase
4. Resume from checkpoint if interrupted
5. Verify after each phase

---

## Checkpoint Policy

Create checkpoints when:
- Task will take more than 5 minutes
- Task modifies more than 50 files
- Task involves architecture changes
- Task involves database migrations
- Task involves security changes
- Before any destructive operation

---

## Approval Required

Stop and request approval before:
- Deleting important functionality
- Breaking API compatibility
- Dropping database data
- Changing licenses
- Adding paid services
- Exposing credentials
- Changing business requirements
- Modifying the constitution

---

## Quality Gates

Nothing is complete until ALL pass:
- [ ] Tests pass
- [ ] Lint passes
- [ ] Type checking passes
- [ ] No critical security vulnerabilities
- [ ] Documentation updated
- [ ] Knowledge updated (if applicable)
- [ ] Memory updated (if architecture changed)

---

## Tool Independence

This bootstrap works with ANY AI system:
- OpenCode
- Claude Code
- Codex
- Gemini
- Cursor
- GitHub Copilot
- Aider
- Roo Code
- Future agents

Never use vendor-specific rules unless isolated in vendor-specific files.

---

## Future Compatibility

This bootstrap must remain valid as:
- New AI systems emerge
- New team members join
- New features are added
- New technologies are adopted
- New deployment targets are added

---

## Self-Improvement

After every completed task, evaluate:
- What was learned?
- Should a skill be created?
- Should memory be updated?
- Should a playbook be created?
- Should a runbook be created?
- Should a decision be recorded?
- Should a failure record be created?
- Should documentation improve?

Generate recommendations. Never update knowledge automatically
without approval.

---

## References

| Document | Purpose |
|---|---|
| `AI_OPERATING_CONSTITUTION.md` | Supreme authority |
| `CLAUDE.md` | Full operating manual |
| `AGENTS.md` | Engineering rules + workspace state |
| `docs/brain/PROJECT_BRAIN.md` | Live knowledge index |
| `docs/constitution/` | Domain constitutions (01-32) |
| `docs/adr/` | Architecture decisions |
| `.ai/core/index/INDEX.md` | Knowledge system index |
| `.ai/core/registry/REGISTRY.md` | Knowledge registry |
| `.ai/core/graph/README.md` | Knowledge graph |

---

**Status:** ✅ ACTIVE
**Next Review:** 2026-11-04
