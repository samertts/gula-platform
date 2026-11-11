# ADR-026: Rule 10 soft-delete rollout and release gating

- **Status:** Proposed — Architecture Board approval required for schema changes
- **Date:** 2026-08-22
- **Owners:** Platform Architect, Security Lead, Privacy/DPO, Clinical Safety Lead
- **Scope:** Data Preservation Constitution Rule 10 and model inventory enforcement

## Context

The original Rule 10 check used a file-level text heuristic. That approach could
misclassify a file containing multiple models, miss inherited mixins, and treat
append-only audit/event tables and expiring authentication stores as ordinary
business entities. At the same time, several legacy business models, including
`patients`, `lab_orders`, and `lab_results`, genuinely lack soft-delete columns
and default filtering.

The shared model primitives provide `SoftDeleteMixin` and `BaseEntityMixin`, but
legacy models still inherit the plain SQLAlchemy `Base`. `SessionLocal` does not
install a global soft-delete criterion. Therefore, adding columns alone would
not satisfy Rule 10 and could change relationship, reporting, and restore
semantics without adequate verification.

## Decision

1. The gate now builds an AST class/table inventory and records direct fields,
   inherited soft-delete support, lifecycle category, and a default-filter
   evidence flag. It does not import application modules or require a database.
2. All currently discovered model tables are explicitly included in the
   protected-table registry. Unregistered business tables remain warnings in
   rollout mode and become blocking findings in `--strict` release mode.
3. `audit_logs`, `outbox_events`, `authorization_audit`,
   `clinical_command_receipts`, and `edge_events` are classified as append-only
   history. `mfa_sessions` and `oauth2_tokens` are classified as expiring or
   revocable operational stores. These classifications are not deletion
   permissions; they require retention, integrity, and access controls.
4. `break_glass_sessions`, clinical scope bridges, health preferences, and all
   other business models remain protected business data unless the Board records
   a different lifecycle policy.
5. No protected-table schema migration is included in this change. A future
   migration must have an Architecture Board decision, ADR linkage, pre-
   migration backup, checksum and clone restore validation, expand/copy/validate/
   switch sequencing, tenant and relationship tests, and a rollback plan.
6. The default gate remains advisory for legacy remediation (`exit 1`).
   `python scripts/data_preservation_gate.py --ci --strict` is the release-
   blocking Rule 10 check (`exit 2`) until all in-scope business models have
   approved lifecycle controls and runtime default-filter evidence.

## Required follow-up before clinical production

The Board must approve a table-by-table lifecycle matrix. For each business
table, the implementation must add the agreed metadata, replace hard deletes
with an audited idempotent service operation, enforce optimistic version checks,
and make active-only queries the default while preserving explicit authorized
restore/admin paths. The implementation must be piloted on anonymized data and
validated on PostgreSQL before any production backfill.

The release packet must include migration and restore evidence, tenant-isolation
negative tests, audit-chain integrity checks, security scan results, clinical
workflow UAT, incident/rollback runbooks, and sign-off from Architecture,
Security, Privacy, QA/Validation, Operations, and Clinical Safety.

## Consequences

The repository now has a truthful inventory and an explicit production gate.
The current default scan will still report a warning because the legacy schema
has not been changed. This is intentional: the warning is actionable evidence,
not a suppressed failure. A production release that includes these business
models must not bypass strict mode or use an unapproved exception.
