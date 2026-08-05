---
id: HEALTH-INDEX
type: health
title: "Health Engine"
version: "1.0.0"
created: "2026-08-05"
status: verified
confidence: 95%
tags: [health, risk, readiness, scoring, gula-kernel-ext-001]
---

# Health Engine

> Mission: GULA-KERNEL-EXT-001 — Phase 10
> Implementation: `scripts/kernel/ext/health.py`
> Report: `health_report.json`

Platform-wide **HEALTH / RISK / READINESS** scoring over every Kernel
extension. Composes the Kernel readiness components
(`scripts/kernel/report.py`) and diagnostics; each extension contributes
weighted component health.

## Model

| Concept | Definition |
|---|---|
| ComponentHealth | name, status (pass/fail), weight, critical, detail |
| HealthReport | health (0–100), risk (0–100), readiness (0–100), components |
| Scoring | weighted sum of passing/failing weights |

## Scores

- **HEALTH_SCORE** — percentage of passing weight.
- **RISK_SCORE** — percentage of failing weight.
- **READINESS_SCORE** — HEALTH, halved if any **critical** component
  fails (severity-aware per constitution).

## Live Components

| Component | Critical | Check |
|---|---|---|
| plugin_sdk | yes | all engines registered as plugins |
| policy_engine | yes | canonical policies registered |
| compatibility | yes | no breaking contract records |
| migration | yes | demo plan executes |
| event_bus | yes | zero failed deliveries |
| workflow | yes | demo workflow completes |
| marketplace | no | item installs |
| evolution | no | signals detected above threshold |
| memory | no | working entry promotes |

## CLI

```bash
python scripts/kernel.py ext-health   # score + save report
python scripts/kernel.py ext-check    # exits 1 if readiness < 90
```

## Reuse

Composes `scripts/kernel/report.py` (`readiness_components`) and
`scripts/kernel/diagnostics.py` — scoring extends, never duplicates,
Kernel health logic.

## Related

- `health_report.json` — machine-readable health report
- `ENTERPRISE_READINESS_SCORE.md` — kernel readiness (Phase 18)
- `scripts/kernel/diagnostics.py` — component diagnostics
