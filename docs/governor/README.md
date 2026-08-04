# GULA Governor — Governance Layer Documentation

> Mission: GULA-GOVERNOR-001
> Purpose: Enterprise AI Governance, Coordination, Safety and Stability Framework

## Documents

| Document | Purpose |
|---|---|
| `docs/governor/README.md` | This index |
| `docs/governor/PHASES.md` | Detailed phase-by-phase design |
| `docs/governor/ENGINE_CONTRACT.md` | Phase 10 engine communication contract |

The Governor is implemented in `scripts/governor/` and invoked via
`scripts/governor.py`. Root artifacts: `GOVERNOR_AUDIT_REPORT.md`,
`AUTHORITY_MAP.md`, `AI_HEALTH_DASHBOARD.md`, `GOVERNOR_IMPLEMENTATION_REPORT.md`.

## Authority

See `AUTHORITY_MAP.md` at the repository root for the immutable chain of
authority and ownership rules.

## Command Reference

```bash
python scripts/governor.py check      # Governor self-check (CI gate)
python scripts/governor.py audit      # Phase 0 audit report
python scripts/governor.py authority  # Phase 1 authority map
python scripts/governor.py health     # Phase 12 health dashboard
python scripts/governor.py report     # Phase 13 implementation report
```

## Integration

- `make governor-check` — run the Governor self-check.
- `make governor-report` — regenerate all Governor artifacts.
- CI: the `ai-governance.yml` workflow runs `make governor-check`.
