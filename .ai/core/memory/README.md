---
id: MEM-INDEX
type: memory
title: "Enterprise AI Memory"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [memory, tiers, recall, archival, gula-kernel-ext-001]
---

# Enterprise AI Memory

> Mission: GULA-KERNEL-EXT-001 — Phase 9
> Implementation: `scripts/kernel/ext/memory.py`
> Store: `memory_store.json`

Multi-tier operational memory for AI agents: **long-term, working,
semantic, decision, failure** tiers, with recall, promotion, archival, and
access accounting.

## Tiers

| Tier | Purpose |
|---|---|
| working | transient, current mission context |
| long_term | promoted knowledge that earned retention |
| semantic | conceptual/derived meaning |
| decision | recorded decisions (ADR-style) |
| failure | incident/lesson records |

## Model

| Concept | Definition |
|---|---|
| MemoryEntry | id (MEM-XXXXXX), tier, content, tags, source, timestamps, access_count, archived |
| MemoryStore | remember, recall(query, tier, top_k), entries, touch, promote, archive, archive_unaccessed |

## Lifecycle

1. **Remember** — entries start in a tier.
2. **Access** — `touch()` increments the access count.
3. **Promote** — working entries with ≥ `PROMOTION_ACCESSES` (3) accesses
   move to long-term.
4. **Archive** — `archive()` or `archive_unaccessed()` moves never-accessed
   entries out of recall.

## Properties

1. **Tiered** — no single flat store; retention follows access value.
2. **Deterministic** — recall ordering is stable (score, then id).
3. **Access accounting** — every `touch` is timestamped and audited.
4. **Auto-archival** — unused entries are archived, never deleted.

## CLI

```bash
python scripts/kernel.py ext-memory   # write/recall across tiers
python scripts/kernel.py ext-check    # includes promotion gate
```

## Reuse

Composes the Kernel knowledge layer (`scripts/kernel/knowledge.py`
search/rank semantics) and decision records. Knowledge *artifacts* remain
in knowledge; this store holds operational memory records.

## Related

- `memory_store.json` — machine-readable memory store
- `scripts/kernel/knowledge.py` — artifact layer (long-term knowledge)
- `.ai/core/decisions/` — decision records
