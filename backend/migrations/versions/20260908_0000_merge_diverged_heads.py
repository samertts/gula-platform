"""Merge divergent migration heads (20260819_0004 + 20260820_0005).

Revision ID: 20260908_0000
Revises    : 20260819_0004, 20260820_0005
Create Date: 2026-09-08

Housekeeping revision — no schema change. Two independent lineages had
accumulated in the ``versions/`` directory:

  * ``20260819_0004_national_search_tenant_scope`` (head)
  * ``20260820_0005_icu_infusion_independent_verification`` (head)

Both descend from the pre-existing duplicate revision id ``20260819_0003``
(``clinical_command_receipts`` and ``research_entities`` were both authored
against ``20260819_0002``, and both claim ``20260819_0003``). Fixing the
duplicate revision id would rename an in-lineage revision and break other
in-flight branches, so this merge accepts the duplicate as-is and joins the
two head lineages into one so ``alembic upgrade head`` and CI's
``upgrade → downgrade -1 → upgrade`` round-trip both succeed again.

The merge itself performs no DDL — ``upgrade()`` and ``downgrade()`` are
no-ops. Alembic still writes the merge into ``alembic_version`` so future
migrations descend from a single head.
"""
from __future__ import annotations


revision      = "20260908_0000"
down_revision = ("20260819_0004", "20260820_0005")
branch_labels = None
depends_on    = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
