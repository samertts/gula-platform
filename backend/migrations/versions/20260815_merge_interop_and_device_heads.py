"""Merge interop and device migration heads.

Revision ID: 20260815_merge_heads
Revises: 20260815_0002, 20260815_0012
Create Date: 2026-08-15

The revision identifier is intentionally unique because the repository already
contains date-based revisions from parallel development lines.
"""

from __future__ import annotations

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "20260815_merge_heads"
down_revision: str | Sequence[str] | None = (
    "20260815_0002",
    "20260815_0012",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Merge the two existing migration branches without schema changes."""


def downgrade() -> None:
    """Re-open the two migration branches when rolling back the merge."""
