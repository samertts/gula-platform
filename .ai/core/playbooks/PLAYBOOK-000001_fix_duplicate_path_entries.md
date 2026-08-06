---
id: PLAYBOOK-000001
type: playbook
title: Fix Duplicate PATH Entries
version: "1.0"
created: "2026-08-04"
status: verified
confidence: 100%
tags: [path, shell, bash, environment, wsl, deduplication]
related_skills: [SKILL-000001]
related_runbooks: []
estimated_duration: "10 minutes"
---

# PLAYBOOK-000001: Fix Duplicate PATH Entries

## Objective
Clean duplicated, dead, and non-functional entries from the shell PATH
on WSL2 Ubuntu systems.

## Prerequisites
- [ ] Backup existing shell configs (`~/.bashrc`, `~/.profile`)
- [ ] Knowledge of which tools are actually installed
- [ ] Access to shell config files

## Scope
- **In scope:** `.bashrc`, `.profile`, PATH entries
- **Out of scope:** Windows-side PATH, system-wide `/etc/environment`

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking tool resolution | Medium | High | Test each tool after modification |
| Losing NVM functionality | Low | High | Preserve NVM init block exactly |
| Losing Cargo/Rust | Low | Medium | Preserve cargo/env sourcing |

## Procedure

### Phase 1: Audit (2 min)
1. List all PATH entries:
   ```bash
   echo "$PATH" | tr ':' '\n'
   ```
2. Find duplicates:
   ```bash
   echo "$PATH" | tr ':' '\n' | sort | uniq -d
   ```
3. Find dead paths:
   ```bash
   for p in $(echo "$PATH" | tr ':' '\n'); do [ -d "$p" ] || echo "DEAD: $p"; done
   ```

### Phase 2: Backup (1 min)
```bash
mkdir -p ~/.backups/$(date +%Y-%m-%d)
cp ~/.bashrc ~/.backups/$(date +%Y-%m-%d)/.bashrc.bak
cp ~/.profile ~/.backups/$(date +%Y-%m-%d)/.profile.bak
```

### Phase 3: Rewrite .bashrc (5 min)
1. Remove all `export PATH=` lines
2. Add each directory exactly once with clear comments:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   export PATH="$HOME/.opencode/bin:$PATH"
   export PATH="$HOME/.npm-global/bin:$PATH"
   ```
3. Preserve NVM, Cargo, and other tool initializations
4. Use `$HOME` not hardcoded paths
5. Remove dead entries (empty directories)

### Phase 4: Simplify .profile (1 min)
Remove redundant PATH additions. Keep only `.bashrc` sourcing.

### Phase 5: Verify (2 min)
```bash
env -i HOME=$HOME SHELL=/bin/bash PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin \
  bash --login -c 'echo "$PATH" | tr ":" "\n" | wc -l'
```
Expected: ~13-15 entries, 0 duplicates.

### Phase 6: Test tools (2 min)
```bash
node --version && npm --version && python3 --version && \
git --version && docker --version && ollama --version
```

## Verification
- [ ] `echo $PATH | tr ':' '\n' | sort | uniq -d` returns empty
- [ ] All installed tools are accessible
- [ ] New terminal session works correctly

## Rollback
```bash
cp ~/.backups/YYYY-MM-DD/.bashrc.bak ~/.bashrc
cp ~/.backups/YYYY-MM-DD/.profile.bak ~/.profile
source ~/.bashrc
```

## Related Skills
- SKILL-000001: WSL2 PATH Deduplication

## References
- `ENVIRONMENT_AUDIT_REPORT.md`
- `ENVIRONMENT_AUDIT_REPORT.md.bak` in backups

## Changelog
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-08-04 | GAIOS | Initial creation from ENV-001 |
