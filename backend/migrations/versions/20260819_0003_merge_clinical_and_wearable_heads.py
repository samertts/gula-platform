"""Merge the canonical clinical and wearable migration heads.

Revision ID: 20260819_0003
Revises: 20260818_0005, 20260819_0002
"""
from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260819_0003"
down_revision: tuple[str, str] = ("20260818_0005", "20260819_0002")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converge both already-applied branches; this revision owns no DDL."""
    return None


def downgrade() -> None:
    """A merge revision owns no schema objects to remove."""
    return None
