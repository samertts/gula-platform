---
id: LESSON-000002
type: lesson
title: "WSL2 PATH Interop Noise"
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [wsl, path, interop, windows, environment]
related_skills: [SKILL-000001]
---

# LESSON-000002: WSL2 PATH Interop Noise

## Problem
WSL2 automatically inherits Windows PATH entries via interop. These 22
entries (`/mnt/c/...`) are non-functional in Linux and cause:
- PATH bloat (47 entries)
- Word-splitting issues (paths with spaces)
- Tool resolution confusion

## Lesson
**Strip Windows interop paths from Linux shell PATH.**

In `.bashrc`, add after NVM init:
```bash
# Clean Windows interop paths from PATH
 cleaned_path=""
 IFS=':'
 for p in $PATH; do
     case "$p" in
         /mnt/c/*) ;;  # Skip Windows paths
         *) cleaned_path="${cleaned_path:+$cleaned_path:}$p" ;;
     esac
 done
 unset IFS
 export PATH="$cleaned_path"
```

## When to Apply
- Fresh WSL2 setup
- After Windows updates that modify PATH
- When debugging tool resolution issues

## Related Skills
- SKILL-000001: WSL2 PATH Deduplication

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial lesson |
