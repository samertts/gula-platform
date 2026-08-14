"""Converge the current device migration heads.

This revision contains no schema operation. It records the explicit convergence
of the previously published device/interop heads without rewriting or deleting
any migration history.
"""
from __future__ import annotations

revision: str = "20260815_0014"
down_revision: tuple[str, str] = ("20260815_0003", "20260815_0013")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Converge existing migration branches without changing the schema."""


def downgrade() -> None:
    """No-op downgrade marker; parent migrations retain their own rollback."""
