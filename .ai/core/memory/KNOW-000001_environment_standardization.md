---
id: KNOW-000001
type: memory
title: Environment Standardization
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [environment, path, shell, wsl]
---

# KNOW-000001: WSL2 Development Environment Standardization

## Summary
The GULA Platform development environment on WSL2 Ubuntu 22.04 had severe
PATH pollution: 47 entries with 5 duplicated local paths and 22 dead
Windows interop paths. Shell configs accumulated entries without deduplication.

## Findings
- `~/.local/bin` appeared 5× in PATH
- `~/.opencode/bin` appeared 4× in PATH
- 22 Windows `/mnt/c/...` paths were non-functional in WSL2
- `.bashrc` had no deduplication guard
- `BUN_INSTALL` env pointed to empty directory
- OpenCode had duplicate installations (native + npm wrapper)
- System `python3` was 3.10, project requires 3.12

## Resolution
Rewrote `.bashrc` and `.profile` with clean, deduplicated PATH.
Result: 13 entries, 0 duplicates.

## Verification
`env -i bash --login -c 'echo $PATH'` confirms 13 entries.

## Related
- PLAYBOOK-000001: Fix Duplicate PATH Entries
- SKILL-000001: WSL2 PATH Deduplication
