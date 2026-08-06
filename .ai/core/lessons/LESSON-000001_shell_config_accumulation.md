---
id: LESSON-000001
type: lesson
title: "Shell Config Accumulation Pattern"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [shell, bash, path, environment, pattern]
related_skills: [SKILL-000001]
related_incidents: []
---

# LESSON-000001: Shell Config Accumulation Pattern

## Problem
Shell configuration files (`.bashrc`, `.profile`) accumulate PATH entries
over time without deduplication. Each new tool installer prepends its bin
directory blindly. Result: 47 PATH entries with 6 duplicates.

## Lesson
**Never add to PATH without checking for existing entries.**

Use a guard pattern:
```bash
# Add to PATH only if not already present
add_to_path() {
    case ":$PATH:" in
        *":$1:"*) ;;  # already present
        *) export PATH="$1:$PATH" ;;
    esac
}
add_to_path "$HOME/.local/bin"
```

## Pattern
This is a general accumulation anti-pattern. It applies to:
- PATH entries
- Environment variables
- Configuration arrays
- Import statements
- Dependency lists

## Prevention
- Audit before adding
- Use deduplication guards
- Periodic cleanup reviews
- Automated detection scripts

## Related Skills
- SKILL-000001: WSL2 PATH Deduplication

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial lesson |
