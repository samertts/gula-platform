"""Guard the corrected historical migration chain against deployed schema drift.

This revision is intentionally conservative. It may recreate one unambiguous
performance index when the owning table exists, but it never casts live data or
creates an inferred Hospital schema. Suspected drift fails the migration with
an actionable error so a separately reviewed data/DDL repair can be prepared.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

revision: str = "20260827_0012"
down_revision: str | None = "20260827_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _inspector():
    return inspect(op.get_bind())


def _table_exists(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _index_exists(inspector, index_name: str) -> bool:
    for table_name in inspector.get_table_names():
        if any(index["name"] == index_name for index in inspector.get_indexes(table_name)):
            return True
    return False


def _is_integer_type(column_type) -> bool:
    visit_name = getattr(column_type, "__visit_name__", "").lower()
    rendered = str(column_type).lower()
    return visit_name in {"integer", "big_integer", "small_integer"} or rendered in {
        "integer",
        "bigint",
        "smallint",
    }


def _assert_integer_foreign_key_columns(inspector) -> None:
    table_name = "pharmacy_drug_substitution_rules"
    if not _table_exists(inspector, table_name):
        return

    columns = {column["name"]: column["type"] for column in inspector.get_columns(table_name)}
    expected = ("original_drug_catalog_id", "alternative_drug_catalog_id")
    missing = [name for name in expected if name not in columns]
    if missing:
        raise RuntimeError(
            f"{table_name} is missing {', '.join(missing)}; stop and review the deployed schema"
        )
    non_integer = [name for name in expected if not _is_integer_type(columns[name])]
    if non_integer:
        raise RuntimeError(
            f"{table_name}.{', '.join(non_integer)} has non-integer type; "
            "manual data audit and an approved USING cast are required"
        )

    foreign_keys = inspector.get_foreign_keys(table_name)
    for column_name in expected:
        matching = [
            foreign_key
            for foreign_key in foreign_keys
            if foreign_key.get("constrained_columns") == [column_name]
        ]
        if not any(foreign_key.get("referred_table") == "pharmacy_drug_catalog" for foreign_key in matching):
            raise RuntimeError(
                f"{table_name}.{column_name} is missing its pharmacy_drug_catalog FK; "
                "review and repair the deployed schema explicitly"
            )


def _assert_hospital_dependencies(inspector) -> None:
    checklist = "hospital_surgical_safety_checklists"
    if not _table_exists(inspector, checklist):
        return

    required = ("hospitals", "hospital_departments", "hospital_operation_theaters")
    missing = [table_name for table_name in required if not _table_exists(inspector, table_name)]
    if missing:
        raise RuntimeError(
            f"{checklist} depends on missing {', '.join(missing)}; "
            "do not infer or create a production Hospital schema in this guard"
        )

    foreign_keys = inspector.get_foreign_keys(checklist)
    if not any(
        foreign_key.get("constrained_columns") == ["operation_theater_id"]
        and foreign_key.get("referred_table") == "hospital_operation_theaters"
        for foreign_key in foreign_keys
    ):
        raise RuntimeError(
            f"{checklist}.operation_theater_id is missing its Hospital FK; "
            "review and repair the deployed schema explicitly"
        )


def upgrade() -> None:
    inspector = _inspector()

    # The index name is shared with the historical owner migration. Create it
    # only if the table exists and the relation is genuinely absent.
    if _table_exists(inspector, "lab_orders") and not _index_exists(
        inspector, "ix_lab_orders_lab_status_created"
    ):
        op.create_index(
            "ix_lab_orders_lab_status_created",
            "lab_orders",
            ["lab_id", "status", "created_at"],
            unique=False,
        )

    _assert_integer_foreign_key_columns(inspector)
    _assert_hospital_dependencies(inspector)


def downgrade() -> None:
    # This guard never owns an index exclusively: the same index name belongs
    # to the historical lab-orders migration. Keeping it on downgrade avoids
    # destructive deletion of a pre-existing performance relation.
    pass
