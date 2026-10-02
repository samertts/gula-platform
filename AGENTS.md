# AI Agent Guidance for GULA Platform

All AI agents (Claude Code, ChatGPT, Gemini, OpenCode, GitHub Copilot, and future agents)
working on this repository MUST automatically enforce the following rules.

## Permanent Platform Constitution — PROGRAM-CONSTITUTION-001

The following rules are ALWAYS in effect, even if not mentioned in the current prompt:

### Free First
Never recommend commercial software before evaluating free alternatives.
Document free alternatives considered.

### Open Source First
Prefer open source over proprietary. License priority: Apache > MIT > BSD > MPL > GPL.

### Self-Hosted First
Prefer self-hosted (PostgreSQL, Redis, MinIO, etc.) over SaaS.

### No Vendor Lock-In
Every component MUST be replaceable. Never introduce vendor-specific coupling.

### Zero Paid Dependency
Paid software requires documented exception with cost analysis.

### Reuse Before Build
Search existing codebase before implementing new functionality.

### Local AI First
Prefer self-hosted AI inference (Ollama) over commercial APIs.

### Free Security First
Use OpenSSL, Let's Encrypt, WireGuard before commercial security products.

## Enforcement

1. Stop and report if a violation is detected
2. Do not generate code that introduces vendor lock-in
3. Always justify external dependencies
4. Check `docs/constitution/COST_GOVERNANCE.md` for full policy
5. Check `docs/architecture/` for detailed policies

## Multi-Agent Change Control

When more than one AI agent works on this repository, agents MUST use the
provider-neutral coordination store under `tools/ai_coordination/` before
editing code. The store is for code-work metadata only; it must never contain
PHI, credentials, API keys, or clinical records.

Required sequence:

1. Register the agent with a unique provider/session identity on a non-protected
   branch: `python -m tools.ai_coordination.cli register --agent-id ... --provider ...`.
2. Create or claim a task before editing. Claims are leases and prevent two
   agents from owning the same task concurrently.
3. Declare the exact repository paths and base commit before writing. An active
   overlapping intent is rejected; use a separate worktree/branch or coordinate
   a handoff instead of overwriting another agent.
4. Send handoff/status messages with commit hashes and test evidence. Close the
   intent after commit or mark it `conflicted` when review is required.
5. Never write directly to `main`/`master`, force-push, or merge a different
   agent's work without an explicit review decision and passing gates.

The SQLite coordination database is local by default at `.gula/coordination.sqlite3`
and should be ignored by Git. For a shared team environment, point
`GULA_COORDINATION_DB` at a controlled shared path; do not put it in a public
repository or expose it over an unauthenticated network.
