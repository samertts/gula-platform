"""Merge the dated application chain with the performance-index branch.

Revision ID: 20260819_0001
Revises: 20260815_0023, 507ea11c820a
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "20260819_0001"
down_revision: tuple[str, str] = ("20260815_0023", "507ea11c820a")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Converge both already-applied branches; neither branch needs new DDL."""
    return


def downgrade() -> None:
    """A merge revision owns no schema objects to remove."""
    return
