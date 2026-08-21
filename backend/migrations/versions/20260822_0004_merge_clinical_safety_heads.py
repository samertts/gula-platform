"""Converge the clinical-safety and canonical-domain migration branches.

Revision ID: 20260822_0004
Revises: 20260820_0005, 20260822_0003
"""
from __future__ import annotations

revision = "20260822_0004"
down_revision = ("20260820_0005", "20260822_0003")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge both already-applied additive branches without schema changes."""


def downgrade() -> None:
    """Keep the merge reversible as a graph-only operation."""
