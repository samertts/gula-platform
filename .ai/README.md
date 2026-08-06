# .ai/ — GULA Platform AI Knowledge System

**Mission:** PROGRAM-KNOWLEDGE-001 / GAIOS-001
**Created:** 2026-08-04
**Status:** Active

---

## Purpose

This directory is the permanent, repository-owned knowledge system for the
GULA Platform. It allows every AI session to:

1. **Search** existing knowledge before solving problems
2. **Reuse** previous solutions instead of reinventing
3. **Learn** from every completed task
4. **Improve** continuously

## Structure

```
.ai/
├── core/
│   ├── index/INDEX.md          # Master index — START HERE
│   ├── memory/                 # Persistent project memory
│   │   ├── PROJECT_MEMORY.md   # Architecture, stack, decisions
│   │   └── KNOW-*.md           # Knowledge records
│   ├── skills/                 # Reusable problem-solution pairs
│   │   └── SKILL-*.md          # Skill documents
│   ├── playbooks/              # Executable operational procedures
│   │   └── PLAYBOOK-*.md       # Playbook documents
│   ├── runbooks/               # Step-by-step operational guides
│   │   └── RUNBOOK-*.md        # Runbook documents
│   ├── templates/              # Document templates
│   │   ├── SKILL_TEMPLATE.md
│   │   ├── PLAYBOOK_TEMPLATE.md
│   │   └── RUNBOOK_TEMPLATE.md
│   ├── constitution/           # Reference to docs/constitution/
│   ├── architecture/           # Reference to docs/architecture/
│   ├── security/               # Security knowledge
│   ├── testing/                # Testing knowledge
│   ├── performance/            # Performance knowledge
│   ├── devops/                 # DevOps knowledge
│   ├── database/               # Database knowledge
│   ├── backend/                # Backend knowledge
│   ├── frontend/               # Frontend knowledge
│   ├── mobile/                 # Mobile knowledge
│   ├── infrastructure/         # Infrastructure knowledge
│   ├── research/               # Research findings
│   ├── incidents/              # Incident records
│   ├── lessons/                # Lessons learned
│   ├── reviews/                # Review records
│   ├── reports/                # Generated reports
│   ├── checkpoints/            # Task checkpoints
│   ├── automation/             # Automation scripts
│   ├── quality/                # Quality metrics
│   ├── registry/               # Knowledge registry
│   ├── graph/                  # Knowledge graph
│   ├── roadmap/                # Project roadmap
│   └── prompts/                # AI prompts
```

## Rules

1. **Audit first** — never modify without understanding
2. **Never overwrite** existing documentation
3. **Merge intelligently** — avoid duplicates
4. **Version-controlled** — everything in git
5. **Human-readable** — Markdown only
6. **No secrets** — never store tokens, passwords, or PII
7. **Metadata required** — every file has YAML frontmatter
8. **Reversible** — every change has a rollback

## Execution Policy

Before ANY task:
1. Search `.ai/core/skills/`
2. Search `.ai/core/memory/`
3. Search `.ai/core/playbooks/`
4. Search `docs/adr/`
5. Search `docs/decisions/`
6. Only then investigate externally

## Knowledge Lifecycle

```
Draft → Verified → Approved → [Deprecated → Archived]
```

Every knowledge artifact starts as Draft, must be Verified with evidence,
then Approved for use.

## Self-Learning

After EVERY completed task:
1. What was learned?
2. Should a skill be created?
3. Should an existing skill be improved?
4. Should memory be updated?
5. Should a playbook be created?
6. Should documentation change?
