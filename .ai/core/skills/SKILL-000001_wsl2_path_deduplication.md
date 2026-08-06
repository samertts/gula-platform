---
id: SKILL-000001
type: skill
title: WSL2 PATH Deduplication
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [path, wsl, shell, bash, environment, deduplication]
related_skills: []
related_adr: []
related_playbooks: [PLAYBOOK-000001]
---

# SKILL-000001: WSL2 PATH Deduplication

## Problem
WSL2 Ubuntu development environment accumulates duplicate PATH entries
over time as tools are installed. Each tool installer prepends its bin
directory without checking if it already exists. Windows interop adds
22 non-functional paths. Result: 47 PATH entries, 5+ duplicates,
performance degradation, and confusing tool resolution.

## Symptoms
- `which <tool>` returns unexpected path
- Tab completion is slow
- `hash -r` needed frequently
- `echo $PATH | tr ':' '\n' | wc -l` shows >30 entries
- Duplicate entries visible in `echo $PATH`

## Environment
- OS: Ubuntu 22.04.5 LTS (WSL2)
- Shell: bash
- Common offenders: ~/.local/bin, ~/.opencode/bin, ~/.npm-global/bin, ~/.bun/bin

## Investigation

### Commands Run
```bash
echo "$PATH" | tr ':' '\n'          # List all PATH entries
echo "$PATH" | tr ':' '\n' | sort | uniq -d  # Find duplicates
for p in $(echo "$PATH" | tr ':' '\n'); do [ -d "$p" ] || echo "DEAD: $p"; done  # Find dead paths
```

### Evidence
```
Duplicate: /home/samertts/.local/bin (5×)
Duplicate: /home/samertts/.opencode/bin (4×)
Duplicate: /home/samertts/.bun/bin (2×, dead)
Dead: /home/samertts/.bun/bin (empty directory)
Dead: Multiple /mnt/c/... Windows paths
```

## Root Cause
`.bashrc` accumulates PATH entries incrementally. Each new tool adds its
bin directory via `export PATH="...:$PATH"` without checking for existing
entries. `.profile` also adds `~/.local/bin`. Result: N additions = N
duplicates in final PATH.

## Solution

### Step 1: Audit current PATH
```bash
echo "$PATH" | tr ':' '\n' | sort | uniq -c | sort -rn
```

### Step 2: Rewrite .bashrc with clean PATH
Keep each directory exactly once. Remove dead entries. Use `$HOME` not
hardcoded paths. Group by category with comments.

### Step 3: Simplify .profile
Remove redundant PATH additions that are already in .bashrc.

### Step 4: Verify with clean shell
```bash
env -i HOME=$HOME SHELL=/bin/bash PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin bash --login -c 'echo "$PATH" | tr ":" "\n" | wc -l'
```

### Files Modified
- `~/.bashrc` — rewritten, deduplicated
- `~/.profile` — simplified

## Verification
```bash
# Should show ~13 entries and 0 duplicates
env -i HOME=$HOME SHELL=/bin/bash bash --login -c '
  echo "Entries: $(echo $PATH | tr ":" "\n" | wc -l)"
  echo "Duplicates: $(echo $PATH | tr ":" "\n" | sort | uniq -d | wc -l)"
'
```

## Rollback
```bash
cp ~/.backups/2026-08-04/.bashrc.bak ~/.bashrc
cp ~/.backups/2026-08-04/.profile.bak ~/.profile
```

## Lessons Learned
- Always check for existing PATH entries before adding
- Use `~/.local/bin` as the single user bin directory when possible
- Windows interop paths are non-functional in WSL2 native context
- Test with `env -i bash --login` for clean environment verification

## Related Playbooks
- PLAYBOOK-000001: Fix Duplicate PATH Entries

## References
- ENVIRONMENT_AUDIT_REPORT.md
- ENV-001 Phase 0 audit results

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation from ENV-001 |
