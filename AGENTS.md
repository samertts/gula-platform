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
