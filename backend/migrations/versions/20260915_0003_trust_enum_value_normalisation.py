"""Normalise trust enum columns to the value spelling the schema already declares.

NR-085.

Nine columns across five `trust_*` tables are `character varying` in PostgreSQL,
and every migration that created them wrote its `server_default` as the Python
enum's **value** -- ``'pending'``, ``'pending_review'``, ``'national_only'``.
The models declared a bare ``Enum(SomeEnum)``, which persists the member's
**name** -- ``'PENDING'`` -- because that is SQLAlchemy's default and none of them
passed `values_callable`. The two halves of one intent disagreed, so the
database's own default value was unreadable by the model that owns the column.

The models are corrected in the same change (`app/trust/models.py::_enum`), which
makes them read and write the value. This migration brings any row already
written in the *name* spelling across to match, so that correction cannot orphan
existing data.

**Corrective, not destructive.** Each `UPDATE` rewrites one string to the
documented equivalent of the same member -- no row is deleted, no column is
dropped, no value is truncated, and nothing is cast. Every statement is bounded
by an explicit `IN` list of exactly the enum names, so:

* a value already in the value spelling is not touched;
* a value that is neither a name nor a value -- something a future integration or
  a hand-written insert put there -- is **left exactly as it is**, not coerced and
  not discarded. It will then be reported by
  ``test_mapped_tables_are_readable.py`` rather than silently rewritten. Guessing
  at an unrecognised clinical or consent value is not this migration's business.

**Reversible.** `downgrade` performs the inverse mapping, bounded the same way,
so a database that predates this change can be restored to the name spelling the
old models expected.

Idempotent: re-running changes nothing, because after the first pass no row
matches the name list any more. Guarded on `_has_table` so a database missing the
trust platform is skipped.

These tables are served by thirteen registered routes under
``/api/v1/trust/*``, including consent creation and withdrawal, so the columns
are reachable rather than theoretical.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260915_0003"
down_revision: str | None = "20260915_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: (table, column, enum class import path) -> resolved to {NAME: value} below.
#: Written out literally rather than imported from ``app.trust.enums`` so that
#: this migration keeps describing the schema at *this* revision even if the
#: enums gain or lose members later. A migration that follows the application's
#: current definitions is not a record of what happened.
_COMPLIANCE_STATUS = {
    "COMPLIANT": "compliant",
    "NON_COMPLIANT": "non_compliant",
    "PENDING_REVIEW": "pending_review",
    "EXEMPTED": "exempted",
    "NOT_APPLICABLE": "not_applicable",
}
_CONSENT_PURPOSE = {
    "TREATMENT": "treatment",
    "PAYMENT": "payment",
    "OPERATIONS": "operations",
    "PUBLIC_HEALTH": "public_health",
    "RESEARCH": "research",
    "NATIONAL_REPORTING": "national_reporting",
    "EMERGENCY": "emergency",
}
_CONSENT_STATUS = {
    "PENDING": "pending",
    "GRANTED": "granted",
    "DENIED": "denied",
    "WITHDRAWN": "withdrawn",
    "EXPIRED": "expired",
}
_DATA_CATEGORY = {
    "CLINICAL": "clinical",
    "LABORATORY": "laboratory",
    "GENETIC": "genetic",
    "MENTAL_HEALTH": "mental_health",
    "REPRODUCTIVE": "reproductive",
    "HIV_STATUS": "hiv_status",
    "DEMOGRAPHIC": "demographic",
    "FINANCIAL": "financial",
    "AUDIT": "audit",
}
_RETENTION_POLICY = {
    "CLINICAL_25_YEARS": "clinical_25_years",
    "LAB_RESULTS_10_YEARS": "lab_results_10_years",
    "AUDIT_LOGS_7_YEARS": "audit_logs_7_years",
    "CONSENT_DURATION_PLUS_2": "consent_duration_plus_2",
    "SESSION_24_HOURS": "session_24_hours",
    "BACKUP_30_DAYS": "backup_30_days",
    "BACKUP_1_YEAR": "backup_1_year",
}
_SOVEREIGNTY_LEVEL = {
    "NATIONAL_ONLY": "national_only",
    "NATIONAL_PRIMARY": "national_primary",
    "REGIONAL": "regional",
    "INTERNATIONAL": "international",
}
_TRUST_SERVICE_TYPE = {
    "DIGITAL_SIGNATURE": "digital_signature",
    "TIMESTAMPING": "timestamping",
    "EVIDENCE_PRESERVATION": "evidence_preservation",
    "CERTIFICATE_MANAGEMENT": "certificate_management",
    "IDENTITY_VERIFICATION": "identity_verification",
    "DOCUMENT_INTEGRITY": "document_integrity",
}

#: (table, column, {name: value}) for each of the nine.
_COLUMNS: tuple[tuple[str, str, dict[str, str]], ...] = (
    ("trust_compliance_checks", "result", _COMPLIANCE_STATUS),
    ("trust_compliance_evidence", "status", _COMPLIANCE_STATUS),
    ("trust_consent_records", "purpose", _CONSENT_PURPOSE),
    ("trust_consent_records", "status", _CONSENT_STATUS),
    ("trust_retention_policies", "data_category", _DATA_CATEGORY),
    ("trust_retention_policies", "retention_period", _RETENTION_POLICY),
    ("trust_service_logs", "service_type", _TRUST_SERVICE_TYPE),
    ("trust_sovereignty_rules", "data_category", _DATA_CATEGORY),
    ("trust_sovereignty_rules", "sovereignty_level", _SOVEREIGNTY_LEVEL),
)


def _has_table(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _remap(table: str, column: str, mapping: dict[str, str]) -> None:
    """Rewrite only the exact keys of `mapping`; leave every other value alone."""
    bind = op.get_bind()
    for source, target in mapping.items():
        if source == target:
            continue
        bind.execute(
            sa.text(
                f"UPDATE {table} SET {column} = :target "  # identifiers are module literals
                f"WHERE {column} = :source",
            ),
            {"target": target, "source": source},
        )


def upgrade() -> None:
    for table, column, mapping in _COLUMNS:
        if not _has_table(table):
            continue
        _remap(table, column, mapping)


def downgrade() -> None:
    for table, column, mapping in _COLUMNS:
        if not _has_table(table):
            continue
        _remap(table, column, {value: name for name, value in mapping.items()})
