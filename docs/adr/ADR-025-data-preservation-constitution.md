# ADR-025: Data Preservation Constitution

**Status:** Accepted
**Date:** 2026-07-22
**Deciders:** Engineering Lead, Platform Architect, CTO

---

## Context

The GULA Platform serves Iraqi medical laboratories where patient data integrity and preservation are critical for patient safety and regulatory compliance. The platform has experienced rapid growth across multiple repositories that were consolidated into a monorepo. During this evolution, several risks emerged:

1. **Migration drift** — Multiple Alembic migrations in the codebase lack consistent safety guards
2. **Data loss risk** — No automated gate prevents destructive schema changes from reaching production
3. **Inconsistent policies** — Data preservation rules are spread across `CLAUDE.md`, `13_DATA_CONSTITUTION.md`, `15_DATABASE_CONSTITUTION.md`, and ad-hoc scripts
4. **AI agent safety** — Future AI-assisted development (Claude Code, Codex, etc.) may introduce changes that violate data preservation rules
5. **No rollback enforcement** — Migrations are not consistently required to include downgrade paths

**Requirements:**
- Permanent, non-negotiable rules for data preservation
- Automated enforcement in CI/CD pipeline
- Protection for all existing production data categories
- Backward compatibility assurance for schema evolution
- Enforceable by automated quality gates

## Decision

Adopt a **Data Preservation Constitution** with 17 permanent rules, enforced through:

### 1. Constitution Document (`docs/constitution/31_DATA_PRESERVATION_CONSTITUTION.md`)

17 rules covering:
- Zero data loss (Rule 1)
- Expand-only schema evolution (Rule 2)
- Backward compatibility (Rule 3)
- Prohibition of drop migrations (Rule 4)
- Safe migration sequence (Rule 5)
- Immutable audit (Rule 6)
- Pre-migration backup (Rule 7)
- Mandatory rollback (Rule 8)
- Post-migration validation (Rule 9)
- Soft delete only (Rule 10)
- Versioned models (Rule 11)
- API stability (Rule 12)
- Test data safety (Rule 13)
- Data integrity gate (Rule 14)
- Protected tables registry (Rule 15)
- CI enforcement (Rule 16)
- Future proof (Rule 17)

### 2. Automated Quality Gate (`scripts/data_preservation_gate.py`)

- Scans migration files for prohibited patterns (DROP, TRUNCATE, DELETE)
- Validates downgrade() existence
- Cross-references changes against Protected Tables Registry
- Verifies backup strategy compliance
- CI-friendly JSON output mode

### 3. CI Enforcement (`.github/workflows/ci.yml`)

- New `data-preservation-gate` job added to CI pipeline
- Runs after `syntax-gate`, before `migration-check`
- Blocks PR merge on violation

### 4. Supporting Documents

- Migration Safety Policy
- Protected Tables Registry
- Backup Strategy
- Restore Strategy
- Disaster Recovery Guide
- Certification Report

## Alternatives Considered

### 1. Trust-Based (No Automated Gate)

**Pros:** Lowest implementation effort.

**Cons:**
- Human error is the leading cause of data loss
- AI agents may be instructed to "optimize" or "clean up" schemas
- No audit trail of policy compliance
- **Rejected because:** Data integrity cannot rely on trust alone.

### 2. Database-Level Protection Only (Event Triggers / Rules)

**Pros:** Enforced at database level, cannot be bypassed by application.

**Cons:**
- Does not catch issues in migration scripts before deployment
- Hard to customize per-environment
- Cannot enforce business-level rules (e.g., soft delete)
- **Rejected because:** Prevention must happen before the database is reached.

### 3. Third-Party Schema Migration Tool

**Pros:** Potential built-in safety features.

**Cons:**
- Vendor lock-in
- Does not understand GULA-specific protected tables and business rules
- Migration from Alembic would be disruptive
- **Rejected because:** Alembic with custom enforcement is more flexible and maintainable.

## Consequences

### Positive
- Zero data loss guarantee for all production data categories
- Automated enforcement catches violations before they reach production
- Clear, documented rules for all developers and AI agents
- Rollback path guaranteed for every migration
- Protected tables have explicit governance

### Negative
- Additional CI job adds ~2 minutes to pipeline runtime
- Developers must learn and follow the safe migration sequence
- Architecture Board must review protected table changes (potential bottleneck)
- Migration files have more boilerplate (guards, comments, downgrade)

### Risks
- **False positives** — Gate may flag legitimate changes. Mitigated by: bypass mechanism requiring Architecture Board approval.
- **Policy fatigue** — Developers may try to bypass the gate. Mitigated by: build failure is final.
- **Migration complexity** — Safe sequence (add → copy → validate → switch) adds steps. Mitigated by: documented examples and templates.

## Implementation Plan

1. **Phase 1 (This ADR):** Create constitution documents, quality gate script, CI job, supporting documents
2. **Phase 2 (Next Sprint):** Backfill existing migrations with downgrade() where missing
3. **Phase 3 (Ongoing):** Quarterly audit of compliance, update protected tables registry

## References

- `docs/constitution/31_DATA_PRESERVATION_CONSTITUTION.md` — The Constitution
- `docs/constitution/data_preservation/migration_safety_policy.md` — Migration Safety Policy
- `docs/constitution/data_preservation/protected_tables_registry.md` — Protected Tables Registry
- `docs/constitution/data_preservation/backup_strategy.md` — Backup Strategy
- `docs/constitution/data_preservation/restore_strategy.md` — Restore Strategy
- `docs/constitution/data_preservation/disaster_recovery_guide.md` — Disaster Recovery Guide
- `scripts/data_preservation_gate.py` — Quality Gate script
- ADR-005: PostgreSQL Redis Stack
- ADR-015: Disaster Recovery Strategy
- `docs/constitution/13_DATA_CONSTITUTION.md` — Data Constitution
- `docs/constitution/15_DATABASE_CONSTITUTION.md` — Database Constitution
