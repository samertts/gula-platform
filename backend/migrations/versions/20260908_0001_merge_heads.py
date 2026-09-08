"""Merge the three independent migration branches into one head.

Revision ID: 20260908_0001
Revises: 20260819_0004, 20260820_0005, 20260908_0002

The national-search, ICU-infusion and Blood Bank branches all forked from the
shared 20260814 lineage and never rejoined, so "alembic upgrade head" could not
choose a target.  This is a pure merge: it carries no schema operations of its
own and loses nothing from any branch.
"""
from __future__ import annotations


revision = "20260908_0001"
down_revision = ("20260819_0004", "20260820_0005", "20260908_0002")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """No schema change; this revision only rejoins the branches."""


def downgrade() -> None:
    """No schema change; this revision only rejoins the branches."""
