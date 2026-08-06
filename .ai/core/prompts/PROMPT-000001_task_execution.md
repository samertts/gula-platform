---
id: PROMPT-000001
type: prompt
title: "AI Task Execution Prompt"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [prompt, execution, workflow, ai]
---

# PROMPT-000001: AI Task Execution Prompt

## Usage
Use this prompt template before starting any implementation task.

## Template

```
TASK: [Brief description]

BEFORE IMPLEMENTING:
1. Search .ai/core/skills/ for existing solutions
2. Search .ai/core/memory/ for project context
3. Search .ai/core/playbooks/ for procedures
4. Search docs/adr/ for architecture decisions
5. Search git log for previous attempts

EXECUTION:
1. Audit current state
2. Create backup if modifying files
3. Implement in small steps
4. Verify after each step
5. Run quality gates (lint, typecheck, tests)

AFTER COMPLETING:
1. Run tests
2. Update knowledge if new skill learned
3. Update memory if architecture changed
4. Create checkpoint if long task
5. Commit with conventional commit message
```

## Related
- `.ai/core/checklists/CHECKLIST-000002_pre_commit.md`
- `.ai/core/checklists/CHECKLIST-000001_code_review.md`
