"""Build the attestation and health columns `MachineIdentity` already declares.

NR-083 / NR-084.

`niam_machine_identities` is mapped by `app/identity/models/machine_identity.py`,
which declares ten columns the table does not have. Every statement against it
therefore fails -- executed against PostgreSQL 16 at head:

    SELECT ... FROM niam_machine_identities LIMIT 1
    UndefinedColumn: column niam_machine_identities.iot_device_type does not exist

Three endpoints are registered over it (`POST /devices/register`,
`/devices/{uuid}/trust`, `/devices/{uuid}/revoke`), and
`app/identity/services/device_service.py` writes seven of the ten missing
columns: `attest_device` sets `device_attestation`, `attested_at` and
`health_status`; `report_health` sets `health_status` and `last_health_check`;
`mark_compromised` sets `health_status = "compromised"` and `risk_score = 100`.

So the identity platform's device-compromise path could not record that a
machine identity was compromised, because the column it writes did not exist.

**This is the unambiguous ADD case, and it was checked rather than assumed.**
The table has *zero* columns the mapper does not declare, so there is no
physical column any of these ten could be a rename of -- the disposition cannot
be RENAME, and nothing is being displaced. All ten are additive, nullable and
carry no foreign key. `health_status` is `nullable=False` in the mapper with a
Python default of ``"unknown"``; it is added nullable with a matching
``server_default`` so existing rows satisfy the mapper without the application
default being bypassed for new writes.

Guarded on ``_has_table``/``_has_column``: idempotent, and a database that
already carries a column is left alone.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260915_0002"
down_revision: str | None = "20260915_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "niam_machine_identities"

#: (column, type, server_default) -- exactly the ten the mapper declares and the
#: table lacks, measured against a database at head.
_COLUMNS: tuple[tuple[str, object, object], ...] = (
    ("iot_device_type", sa.String(length=100), None),
    ("robot_type", sa.String(length=100), None),
    ("ai_agent_id", sa.String(length=100), None),
    ("analyzer_type", sa.String(length=100), None),
    ("device_attestation", sa.Text(), None),
    ("attested_at", sa.DateTime(timezone=True), None),
    ("health_status", sa.String(length=20), sa.text("'unknown'")),
    ("last_health_check", sa.DateTime(timezone=True), None),
    ("firmware_version", sa.String(length=50), None),
    ("risk_score", sa.Integer(), None),
)


def _has_table(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _has_column(table: str, column: str) -> bool:
    return column in {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    if not _has_table(_TABLE):
        return
    for name, type_, server_default in _COLUMNS:
        if _has_column(_TABLE, name):
            continue
        op.add_column(
            _TABLE, sa.Column(name, type_, nullable=True, server_default=server_default),
        )


def downgrade() -> None:
    if not _has_table(_TABLE):
        return
    for name, _type, _default in _COLUMNS:
        if _has_column(_TABLE, name):
            op.drop_column(_TABLE, name)
