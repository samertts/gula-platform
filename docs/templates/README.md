# Markdown Templates — GULA Platform

Reusable templates for engineering documentation. Copy the appropriate template and fill in the fields.

## Available Templates

| Template | Purpose | File |
|----------|---------|------|
| Risk | Risk register entry | `RISK-TEMPLATE.md` |
| ADR | Architecture Decision Record | `ADR-TEMPLATE.md` |
| Assessment | Module assessment report | `ASSESSMENT-TEMPLATE.md` |
| Decision Log | Informal decision tracking | `DECISION-LOG-TEMPLATE.md` |
| Technical Debt | Debt item tracking | `TECHNICAL-DEBT-TEMPLATE.md` |
| Government Compliance | Regulatory compliance tracking | `GOVERNMENT-COMPLIANCE-TEMPLATE.md` |

## Usage

```bash
cp docs/templates/ADR-TEMPLATE.md docs/adr/ADR-NNN-my-title.md
# Edit the file with your content
# Update docs/adr/README.md index
```

## Template Guidelines

1. Fill all fields — empty fields indicate incomplete analysis
2. Keep language precise and factual
3. Reference code locations with file:line
4. Link related templates (e.g., risk → technical debt)
5. Update status as the item progresses
