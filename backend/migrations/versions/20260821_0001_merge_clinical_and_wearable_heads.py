"""Merge the canonical clinical and wearable migration heads.

Revision ID: 20260821_0001
Revises: 20260818_0005, 20260819_0004
"""
from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260821_0001"
down_revision: tuple[str, str] = ("20260818_0005", "20260819_0004")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converge both already-applied branches; this revision owns no DDL."""
    return


def downgrade() -> None:
    """A merge revision owns no schema objects to remove."""
    return
