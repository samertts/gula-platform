---
id: EVO-INDEX
type: evolution
title: "Continuous Evolution System"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [evolution, rfc, proposals, self-improvement, gula-kernel-ext-001]
---

# Continuous Evolution System

> Mission: GULA-KERNEL-EXT-001 — Phase 8
> Implementation: `scripts/kernel/ext/evolution.py`
> State: `evolution_state.json`

Detects repeated fixes, bugs, and decisions, then opens improvement
proposals — **only** through the RFC-before-KUP workflow
(`.ai/core/kup/RFC_WORKFLOW.md`). No proposal is ever applied directly:
the RFC gate is constitutional.

## Model

| Concept | Definition |
|---|---|
| EvolutionSignal | id (EVO-XXXXXX), kind, area, evidence, count, severity |
| Signal kinds | repeated_fix, repeated_bug, repeated_decision, stagnation |
| RfcProposal | id (RFC-XXXXXX), signal ref, title, rationale, status |
| Proposal states | open → accepted \| rejected → archived |

## Process (RFC Workflow)

1. **Record** observations (`record(kind, area, evidence)`).
2. **Detect** signals whose count meets the threshold (`detect()`).
3. **Propose** an RFC with evidence (`propose()`).
4. **Decide** accepted/rejected (`decide()`) — never self-apply.

## Properties

1. **RFC-before-KUP** — evolution proposals are review artifacts, not
   code changes.
2. **Evidence-based** — signals carry the observations that triggered them.
3. **Thresholded** — repeated patterns only, not single events.
4. **Severity escalation** — more repetitions raise severity.
5. **Audited** — every observation, proposal, and verdict is recorded.

## CLI

```bash
python scripts/kernel.py ext-evolution   # detect signals + open RFC
python scripts/kernel.py ext-check       # includes signal detection gate
```

## Reuse

Composes self-governance review semantics (`scripts/governor/
self_governance.py`) and the RFC workflow convention. No review or
approval logic is duplicated.

## Related

- `evolution_state.json` — machine-readable signal/proposal state
- `.ai/core/kup/RFC_WORKFLOW.md` — RFC-before-KUP gate
- `docs/ai/MASTER_ROADMAP.md` — where accepted proposals land
