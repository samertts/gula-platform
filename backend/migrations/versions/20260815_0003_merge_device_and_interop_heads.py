"""Merge the device-integration and interop migration branches.

This revision has no schema operation. It only records the convergence of the
existing migration histories so fresh deployments and upgrades have one
canonical Alembic head without rewriting already-published revisions.
"""
from __future__ import annotations

revision: str = "20260815_0003"
down_revision: tuple[str, str] = ("20260814_0011", "20260815_0002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Converge existing migration branches without changing the schema."""


def downgrade() -> None:
    """Leave branch-specific schema rollback to their parent revisions."""
