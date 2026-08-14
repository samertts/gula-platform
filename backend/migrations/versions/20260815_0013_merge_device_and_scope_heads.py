"""Merge the device adapter and scope-inbox migration heads.

Revision ID: 20260815_0013
Revises: 20260815_0012, 20260815_0002
"""
from __future__ import annotations

revision = "20260815_0013"
down_revision = ("20260815_0012", "20260815_0002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge-only revision; both parent branches already contain their DDL."""


def downgrade() -> None:
    """Merge-only revision; downgrade selects an explicit parent head."""
