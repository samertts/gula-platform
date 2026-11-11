"""Fix DigitalCertificate.issuer_ca_id FK target (was self-referential).

Revision ID: 20260908_0004
Revises: 20260908_0003

`niam_cert_certificates.issuer_ca_id` was declared (both in
`20260723_0002_niam_completion_tables.py`'s migration and in the ORM
model, `app/identity/certificates/models.py`) with a foreign key to
`niam_cert_certificates.id` (itself) instead of `niam_cert_authorities.id`
(the actual certificate authority table). Application code has always
treated the column as a CA reference (`generate_crl`'s
`DigitalCertificate.issuer_ca_id == ca.id` where `ca` is a
`CertificateAuthority`), so any attempt to actually populate it with a
real CA id crashed with a `ForeignKeyViolation` (proven in
docs/security/CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md) -- meaning
no real deployment of this migration could ever have successfully
written a non-null `issuer_ca_id`. Data-safety check (Phase 2 of the
P1 data-integrity closure workstream) against a real disposable
PostgreSQL confirmed zero existing rows and zero non-null
`issuer_ca_id` values, so this repair needs no data transformation --
only the constraint target changes. Column name, type
(`String(26)`), nullability, and `ondelete="SET NULL"` semantics are
all preserved exactly; this is not an API or ORM-field change.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260908_0004"
down_revision = "20260908_0003"
branch_labels = None
depends_on = None


_TABLE = "niam_cert_certificates"
_COLUMN = "issuer_ca_id"
_OLD_FK_NAME = "niam_cert_certificates_issuer_ca_id_fkey"
_NEW_FK_NAME = "fk_niam_cert_certificates_issuer_ca_id_authorities"


def _foreign_key_names(bind, table: str) -> set[str]:
    inspector = sa.inspect(bind)
    return {fk["name"] for fk in inspector.get_foreign_keys(table)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    # SQLite cannot drop/add named foreign-key constraints on an existing
    # table without a full table rebuild -- this repair is Postgres-only,
    # matching the existing convention in
    # 20260813_0003_clinical_assignment_scope.py for the same reason.
    if bind.dialect.name == "sqlite":
        return

    existing_fks = _foreign_key_names(bind, _TABLE)
    if _OLD_FK_NAME in existing_fks:
        op.drop_constraint(_OLD_FK_NAME, _TABLE, type_="foreignkey")
    if _NEW_FK_NAME not in _foreign_key_names(bind, _TABLE):
        op.create_foreign_key(
            _NEW_FK_NAME,
            _TABLE,
            "niam_cert_authorities",
            [_COLUMN],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _TABLE not in inspector.get_table_names():
        return

    if bind.dialect.name == "sqlite":
        return

    existing_fks = _foreign_key_names(bind, _TABLE)
    if _NEW_FK_NAME in existing_fks:
        op.drop_constraint(_NEW_FK_NAME, _TABLE, type_="foreignkey")
    if _OLD_FK_NAME not in _foreign_key_names(bind, _TABLE):
        op.create_foreign_key(
            _OLD_FK_NAME,
            _TABLE,
            _TABLE,
            [_COLUMN],
            ["id"],
            ondelete="SET NULL",
        )
