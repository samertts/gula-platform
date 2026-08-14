"""Finalize the linear device adapter migration chain.

Revision ID: 20260815_0013
Revises: 20260815_0012
"""
from __future__ import annotations

revision = "20260815_0013"
down_revision = "20260815_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No-op finalization; all schema DDL is contained in the parent revisions."""


def downgrade() -> None:
    """No-op downgrade marker for the final adapter revision."""
