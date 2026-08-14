"""Converge legacy device/interop and monitoring migration heads.

Revision ID: 20260815_0015
Revises: 20260815_0003, 20260815_0014
"""
from __future__ import annotations

revision = "20260815_0015"
down_revision = ("20260815_0003", "20260815_0014")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Converge migration histories without changing application tables."""


def downgrade() -> None:
    """Keep parent branches available for explicit rollback only."""
