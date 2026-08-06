# Constitution Bridge — `.ai/core/constitution/`

## Purpose
This directory bridges the repository constitution to the GULA Platform
knowledge system. It provides the AI with the authoritative rules for
engineering decisions.

## Structure
```
constitution/
├── README.md                    # This file
├── CONSTITUTION_REGISTRY.md     # Constitution registry (CONST-000001)
└── (future ADRs referenced here)
```

## Supremacy

The supreme constitution is:
```
AI_OPERATING_CONSTITUTION.md  (root of repository)
```

This file is NOT duplicated here. The bridge files reference it.

## Usage

When working on this repository:
1. Read `AI_OPERATING_CONSTITUTION.md` first
2. Check `CONSTITUTION_REGISTRY.md` for registered constitutions
3. Follow the precedence rules in Section 1.4

## Rules (from constitution)

### Platform Constitution (PROGRAM-CONSTITUTION-001)
- **Free First:** Never recommend commercial before free
- **Open Source First:** Apache > MIT > BSD > MPL > GPL
- **Self-Hosted First:** PostgreSQL, Redis, MinIO before SaaS
- **No Vendor Lock-In:** Every component replaceable
- **Zero Paid Dependency:** Paid requires exception
- **Reuse Before Build:** Search before implementing
- **Local AI First:** Ollama before commercial AI
- **Free Security First:** OpenSSL, Let's Encrypt, WireGuard

### Knowledge System
- Every knowledge artifact gets immutable ID
- Never overwrite existing knowledge
- Never delete without user approval
- Verify before accepting
- Backup before modification

## References
- `AI_OPERATING_CONSTITUTION.md` — Supreme authority
- `AGENTS.md` — Detailed engineering rules
- `CLAUDE.md` — Full AI operating manual
- `docs/constitution/01-32` — Domain constitutions
- `.ai/core/registry/REGISTRY.md` — Knowledge registry
