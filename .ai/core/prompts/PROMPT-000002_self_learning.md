---
id: PROMPT-000002
type: prompt
title: "Self-Learning Evaluation Prompt"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [prompt, self-learning, evaluation, ai]
---

# PROMPT-000002: Self-Learning Evaluation Prompt

## Usage
Run this evaluation after completing every task.

## Template

```
POST-TASK EVALUATION:

1. WHAT WAS LEARNED?
   - New problem encountered: [description]
   - Root cause: [cause]
   - Solution: [solution]

2. SHOULD A SKILL BE CREATED?
   - Is this problem likely to recur? [yes/no]
   - Would a future AI benefit from this knowledge? [yes/no]
   - If yes: Create SKILL-NNNNNN in .ai/core/skills/

3. SHOULD MEMORY BE UPDATED?
   - Did architecture change? [yes/no]
   - Did technology stack change? [yes/no]
   - Did security decisions change? [yes/no]
   - If yes: Update .ai/core/memory/PROJECT_MEMORY.md

4. SHOULD A PLAYBOOK BE CREATED?
   - Is this an operational procedure? [yes/no]
   - Would this help in incident response? [yes/no]
   - If yes: Create PLAYBOOK-NNNNNN in .ai/core/playbooks/

5. SHOULD DOCUMENTATION CHANGE?
   - Did API contracts change? [yes/no]
   - Did deployment process change? [yes/no]
   - If yes: Update relevant docs/

6. KNOWLEDGE MERGE?
   - Does this duplicate existing knowledge? [yes/no]
   - Should existing skill be improved? [yes/no]
   - If merge: Update existing artifact, increment version
```

## Related
- `.ai/core/registry/REGISTRY.md` — Knowledge registry
- `.ai/core/index/INDEX.md` — Master index
