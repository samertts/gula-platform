"""B5 regression guard — delegation model/migration schema drift.

Owner directive GULA-MASTER-AUTH-2026-11-19 §5/B5 (AUD-SEC-008).

On 2026-11-19 a real defect was found: ``NiamDelegation`` was not registered in
``app.identity.models``, so ``niam_delegations`` was absent from
``IdentityBase.metadata`` and ``alembic check`` reported a spurious
``remove_table`` (new schema drift). The composite index names in the migration
also differed from the ORM declarations. These tests lock both facts down so a
future regression fails fast without needing a database.

Source-text assertions are deliberate: a migration file cannot be introspected
at runtime, so parity is checked against the migration source itself.
"""

from __future__ import annotations

import re
from pathlib import Path

import app.identity.models as identity_models
from app.identity.base import IdentityBase
from app.identity.models.delegation import NiamDelegation
from sqlalchemy import CheckConstraint

_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "migrations"
    / "versions"
    / "20261119_0002_niam_delegations.py"
)
_COMPOSITE_COLUMNS = (
    frozenset({"delegate_account_id", "status"}),
    frozenset({"role_id", "status"}),
)


def _migration_source() -> str:
    return _MIGRATION.read_text(encoding="utf-8")


def test_delegation_table_registered_in_identity_metadata() -> None:
    """Regression: the ORM table must be visible to Alembic autogenerate."""
    assert "niam_delegations" in IdentityBase.metadata.tables
    assert IdentityBase.metadata.tables["niam_delegations"] is NiamDelegation.__table__


def test_delegation_model_exported_from_canonical_identity_models() -> None:
    """Regression: the model is importable from the package Alembic imports."""
    assert "NiamDelegation" in identity_models.__all__
    assert "DelegationStatus" in identity_models.__all__
    assert identity_models.NiamDelegation is NiamDelegation


def test_model_composite_index_names_match_migration() -> None:
    """Regression: composite index declarations and migration names agree."""
    source = _migration_source()
    composite_names = sorted(
        index.name
        for index in NiamDelegation.__table__.indexes
        if frozenset(index.columns.keys()) in _COMPOSITE_COLUMNS
    )
    assert composite_names == ["ix_niam_delegations_delegate", "ix_niam_delegations_role"]

    create_names = set(re.findall(r'op\.create_index\(\s*"([^"]+)"', source))
    drop_names = set(re.findall(r'op\.drop_index\("([^"]+)"', source))
    for name in composite_names:
        assert name in create_names, f"{name} missing from migration upgrade()"
        assert name in drop_names, f"{name} missing from migration downgrade()"


def test_depth_check_constraint_name_matches_migration() -> None:
    """Regression: the named depth CHECK is identical in ORM and migration."""
    source = _migration_source()
    model_checks = {
        constraint.name
        for constraint in NiamDelegation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }
    assert "ck_niam_delegations_depth" in model_checks
    assert 'name="ck_niam_delegations_depth"' in source
    assert "depth >= 1 AND depth <= 3" in source


def test_model_and_migration_column_sets_match() -> None:
    """Regression: no column exists in only one of the ORM or the migration."""
    source = _migration_source()
    migration_columns = set(re.findall(r'sa\.Column\("([^"]+)"', source))
    model_columns = set(NiamDelegation.__table__.columns.keys())
    assert model_columns == migration_columns
    assert len(model_columns) == 23


def test_migration_is_additive_and_reversible() -> None:
    """Regression: the migration creates/drops only its own table."""
    source = _migration_source()
    assert 'op.create_table(\n        "niam_delegations"' in source
    assert 'op.drop_table("niam_delegations")' in source
    assert "op.alter_column" not in source
    assert "op.add_column" not in source
    assert 'down_revision: str | None = "20261119_0001"' in source
