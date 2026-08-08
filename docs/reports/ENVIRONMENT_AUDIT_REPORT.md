# ENVIRONMENT AUDIT REPORT

**Date:** 2026-08-04
**User:** samertts
**OS:** Ubuntu 22.04.5 LTS (WSL2)
**Shell:** /bin/bash

---

## 1. PATH ANALYSIS

### Total entries: 47 (recommended: ~20)

### Duplicated entries (× occurrence count)

| Entry | Count | Status |
|---|---|---|
| `~/.local/bin` | **5×** | DUPLICATE |
| `~/.opencode/bin` | **4×** | DUPLICATE |
| `~/.bun/bin` | **2×** | DEAD (empty dir) |
| `~/.grok/bin` | **2×** | DUPLICATE |
| `~/.npm-global/bin` | **2×** | DUPLICATE |

### Dead paths

| Path | Reason |
|---|---|
| `~/.bun/bin` | Directory exists but is empty — bun is installed via npm-global, not standalone |
| `/mnt/c/Program Files/...` (multiple) | WSL interop paths with spaces cause word-splitting issues during dead-path detection. These are valid Windows paths but irrelevant to Linux development |

### WSL Windows paths (22 entries)

All `/mnt/c/...` and `/mnt/c/Windows/...` entries are inherited from Windows PATH via WSL interop. These are **non-functional** in WSL2 native context and add 22 entries of noise.

**Verdict:** Remove Windows interop paths from Linux shell PATH. Windows tools should be invoked explicitly via `/mnt/c/...` when needed.

---

## 2. SHELL CONFIGURATION

### Files

| File | Lines | Status |
|---|---|---|
| `~/.bashrc` | 53 | ACTIVE — has issues |
| `~/.profile` | 15 | ACTIVE — sources .bashrc + adds PATH |
| `~/.bash_profile` | — | NOT FOUND (good) |

### `.bashrc` Issues

| Line | Issue | Severity |
|---|---|---|
| 4 | `~/.opencode/bin` prepended to PATH | OK |
| 9 | `~/.npm-global/bin` prepended to PATH | OK |
| 14 | `~/.local/bin` prepended to PATH | OK |
| 26 | `~/.grok/bin` prepended to PATH | OK (2nd time) |
| 43-45 | NVM init — correct | OK |
| 49 | `BUN_INSTALL=$HOME/.bun` set but bun is NOT installed there (it's in npm-global) | **WRONG** |
| 50 | `$BUN_INSTALL/bin` prepended — points to empty dir | **DEAD** |
| 50 | `~/.local/bin` prepended AGAIN (3rd time) | DUPLICATE |
| 53 | Hardcoded `/home/samertts/.opencode/bin` instead of `$HOME` | **BAD PRACTICE** |

### `.profile` Issues

| Line | Issue | Severity |
|---|---|---|
| 9-10 | Adds `~/bin` if exists | OK (dir doesn't exist) |
| 12-14 | Adds `~/.local/bin` — duplicated in .bashrc | DUPLICATE |

### Duplicate sourcing chain

`.profile` → sources `.bashrc` → adds `~/.local/bin` → `.profile` adds `~/.local/bin` again → net: `~/.local/bin` appears twice minimum from config files alone.

---

## 3. TOOL INVENTORY

### Node.js Ecosystem

| Tool | Version | Location | Status |
|---|---|---|---|
| node | v24.18.0 | `~/.nvm/versions/node/v24.18.0/bin/` | ✅ PASS |
| npm | 11.16.0 | `~/.nvm/versions/node/v24.18.0/bin/` | ✅ PASS |
| npx | (bundled) | `~/.nvm/versions/node/v24.18.0/bin/` | ✅ PASS |
| nvm | 0.40.1 | `~/.nvm/nvm.sh` | ✅ PASS |
| corepack | 0.35.0 | `~/.nvm/.../bin/` | ✅ PASS |
| pnpm | 11.18.0 | `~/.local/bin/pnpm` | ✅ PASS |
| bun | 1.3.14 | `~/.npm-global/bin/bun.exe` | ⚠️ WARNING — installed via npm, not standalone. BUN_INSTALL env points to empty dir |

### Python Ecosystem

| Tool | Version | Location | Status |
|---|---|---|---|
| python3 | 3.10.12 | `/usr/bin/python3` | ⚠️ WARNING — system default is 3.10, project requires 3.12 |
| python3.12 | 3.12.13 | `/usr/bin/python3.12` | ✅ PASS (available) |
| uv | 0.11.26 | `~/.local/bin/uv` | ✅ PASS |
| pip | 26.1.2 | `~/.local/bin/pip` (python 3.10) | ⚠️ WARNING — targets 3.10 |
| pip3 | 25.0.1 | `~/.local/bin/pip3` (python 3.12) | ✅ PASS |

### Rust Ecosystem

| Tool | Version | Location | Status |
|---|---|---|---|
| cargo | 1.96.0 | `~/.cargo/bin/` | ✅ PASS |
| rustc | 1.96.0 | `~/.cargo/bin/` | ✅ PASS |

### DevOps / Infrastructure

| Tool | Version | Location | Status |
|---|---|---|---|
| git | 2.34.1 | `/usr/bin/git` | ⚠️ WARNING — 3+ years old (current: 2.47+) |
| docker | 29.1.3 | `/usr/bin/docker` | ✅ PASS |
| docker-compose | — | Windows path (broken) | ❌ FAIL — not available in WSL |
| ollama | 0.24.0 | `/usr/local/bin/ollama` | ✅ PASS (server running, 1 model loaded) |
| cloudflared | — | Not installed | ❌ FAIL — if needed |
| kubectl | — | `/usr/local/bin/` | ✅ PRESENT |
| trivy | — | `/usr/local/bin/` | ✅ PRESENT |

### AI / Editor Tools

| Tool | Version | Location | Status |
|---|---|---|---|
| opencode | 1.18.13 | `~/.opencode/bin/opencode` (180MB native) | ✅ PASS |
| opencode (npm) | — | `~/.npm-global/bin/opencode` (symlink to npm wrapper) | ⚠️ WARNING — duplicate, npm version is redundant |
| grok | — | `~/.grok/bin/grok` | ✅ PASS |

---

## 4. CRITICAL FINDINGS

### F1: PATH Pollution (SEVERITY: HIGH)
- **47 PATH entries** — 5 are duplicated local paths, 22 are non-functional Windows paths
- Each shell launch processes all 47 entries
- `hash -r` and tab completion are slower with bloated PATH
- **Impact:** Performance, maintainability, confusing tool resolution

### F2: `.bashrc` Accumulation Pattern (SEVERITY: HIGH)
- PATH entries appended incrementally without deduplication
- Same directories added 2-5 times
- No guard against re-adding existing entries
- **Impact:** Every new tool install duplicates existing entries

### F3: Bun Configuration Mismatch (SEVERITY: MEDIUM)
- `BUN_INSTALL=$HOME/.bun` set in `.bashrc:48` but bun is at `~/.npm-global/bin/bun.exe`
- `$BUN_INSTALL/bin` is an empty directory in PATH
- Bun was installed via npm (`npm install -g bun`), not standalone installer
- **Impact:** `BUN_INSTALL` env var is misleading, dead PATH entry

### F4: OpenCode Double Installation (SEVERITY: LOW)
- Native binary at `~/.opencode/bin/opencode` (180MB, working)
- npm wrapper at `~/.npm-global/bin/opencode` → `../lib/node_modules/opencode-ai/bin/opencode.exe`
- PATH resolves to native binary first (correct behavior)
- **Impact:** Wasted ~180MB npm-global storage, confusing which is "real"

### F5: Python Version Confusion (SEVERITY: MEDIUM)
- `python3` → 3.10.12 (system)
- `python3.12` → 3.12.13 (uv-managed)
- `pip` → targets 3.10
- `pip3` → targets 3.12
- Project AGENTS.md specifies Python 3.12 as target
- **Impact:** Accidental use of `python3` or `pip` runs wrong version

### F6: Hardcoded Paths (SEVERITY: LOW)
- `.bashrc:53` uses `/home/samertts/.opencode/bin` instead of `$HOME/.opencode/bin`
- **Impact:** Breaks if HOME changes, inconsistent with rest of file

### F7: Dead Alias (SEVERITY: LOW)
- `alias sgr="$HOME/workspace/runtime/sovereign-git-runtime.sh"` — file likely doesn't exist
- **Impact:** Confusing dead reference

### F8: WSL Docker Compose (SEVERITY: MEDIUM)
- `docker-compose` resolves to Windows Docker Desktop path (broken in WSL)
- Docker CLI works but compose subcommand doesn't
- **Impact:** `docker compose` (v2 plugin) should be used instead

---

## 5. RECOMMENDED CLEAN PATH (target state)

```
~/.local/bin
~/.opencode/bin
~/.nvm/versions/node/v24.18.0/bin
~/.cargo/bin
/usr/local/bin
/usr/local/sbin
/usr/bin
/usr/sbin
/bin
/sbin
/usr/games
/usr/local/games
/usr/lib/wsl/lib
/snap/bin
```

**Total: 14 entries** (down from 47)

Removed:
- `~/.bun/bin` (dead)
- `~/.grok/bin` (move grok binary to `~/.local/bin`)
- `~/.npm-global/bin` (move needed binaries to `~/.local/bin` or use nvm's npm)
- All 22 Windows interop paths
- All duplicate entries

---

## 6. RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Breaking tool resolution after PATH cleanup | Medium | High | Test each tool after modification |
| Losing nvm functionality | Low | High | Preserve NVM init block exactly |
| Cargo/Rust path breakage | Low | Medium | Preserve cargo/env sourcing |
| Ollama connectivity loss | Low | Low | Ollama uses /usr/local/bin, unaffected |
| WSL Windows tool access | Medium | Low | Invoke via explicit `/mnt/c/...` paths when needed |

---

## 7. PHASE READINESS

| Phase | Readiness | Dependencies |
|---|---|---|
| Phase 1 — Backup | ✅ READY | None |
| Phase 2 — Shell Reconstruction | ✅ READY | Phase 1 complete |
| Phase 3 — Node Standardization | ✅ READY | Phase 2 complete |
| Phase 4 — Tool Validation | ✅ READY | Phase 3 complete |
| Phase 5 — Documentation | ✅ READY | Phase 4 complete |
| Phase 6 — Health Check Script | ✅ READY | Phase 5 complete |

---

## 8. APPROVAL REQUIRED

**Phase 0 complete.** Awaiting approval to proceed with Phase 1 (Backup).

Planned modifications summary:
1. Rewrite `~/.bashrc` — deduplicate PATH, fix BUN_INSTALL, remove dead entries, use `$HOME`
2. Simplify `~/.profile` — remove redundant PATH additions
3. Remove npm-global opencode wrapper (keep native binary)
4. Verify grok binary can be moved to `~/.local/bin`

**No modifications have been made. This is audit-only.**
