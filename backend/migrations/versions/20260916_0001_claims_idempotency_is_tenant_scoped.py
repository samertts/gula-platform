"""Scope the claims idempotency key to its lab, as every comparable table already does.

NR-094.

`claims` carries `lab_id`, and every application path that reads the key is
already lab-scoped -- `services/claims_service.py::create_claim` and
`insurance/api/claims.py::create_claim` both filter `lab_id` alongside
`idempotency_key`. The *database* was not: the column was declared
`unique=True`, producing a global `claims_idempotency_key_key`.

The consequence is cross-tenant interference, executed against PostgreSQL 16
at head 20260915_0003:

    lab 901 creates a claim with key 'INV-2026-001'        -> OK
    lab 902's lab-scoped idempotency lookup finds          -> 0, so it proceeds
    lab 902's INSERT                                       -> REFUSED
        duplicate key value violates unique constraint "claims_idempotency_key_key"

So one lab's choice of idempotency key makes that key permanently unusable for
every other lab. Keys that clients actually pick -- invoice numbers, counters,
dates -- collide across tenants by construction. Nothing is disclosed; the
lookups are correctly scoped. What breaks is the other tenant's ability to
write, which is a tenant-isolation failure in the availability dimension.

This is the platform's own established convention, applied to the one table
that was missing it. The nine comparable tables already scope the key:

    uq_billing_invoice_lab_idempotency      (lab_id, idempotency_key)
    uq_pharmacy_sale_lab_idempotency        (lab_id, idempotency_key)
    uq_device_outbox_lab_idempotency        (lab_id, idempotency_key)
    uq_clinical_command_actor_key           (lab_id, actor_user_id, operation, idempotency_key)
    uq_integration_inbox_tenant_idempotency_key  (tenant_id, idempotency_key)
    uq_pay_intent_idempotency               (institution_id, idempotency_key)
    uq_pay_control_institution_idempotency  (institution_id, idempotency_key)
    uq_pay_sub_usage_event_idempotency      (subscription_id, metric_code, idempotency_key)

**Why this migration can never fail on existing data.** Widening a unique key
is not a narrowing: any row set that satisfies `UNIQUE(idempotency_key)`
necessarily satisfies `UNIQUE(lab_id, idempotency_key)`, because two rows
sharing `(lab_id, idempotency_key)` would have to share `idempotency_key` and
would already have been refused. So the new index is always creatable, no row
is rejected, and nothing is deleted or rewritten. The column stays nullable and
PostgreSQL keeps treating NULLs as distinct, so the rows with no key -- claims
created without one -- are unaffected in both directions.

The downgrade is the narrowing direction and therefore *can* legitimately fail,
once two labs have used the same key. It is written to say so rather than to
destroy data: it restores the global constraint if and only if the data still
permits it, and raises otherwise. Deleting a tenant's claim to make a downgrade
succeed would be exactly the trade this codebase refuses.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260916_0001"
down_revision = "20260915_0003"
branch_labels = None
depends_on = None

_TABLE = "claims"
_OLD = "claims_idempotency_key_key"
_NEW = "uq_claims_lab_idempotency"


def _inspector():
    return sa.inspect(op.get_bind())


def _table_exists(table: str) -> bool:
    return _inspector().has_table(table)


def _constraint_names(table: str) -> set[str]:
    insp = _inspector()
    names = {c["name"] for c in insp.get_unique_constraints(table) if c.get("name")}
    names |= {i["name"] for i in insp.get_indexes(table) if i.get("name")}
    return names


def upgrade() -> None:
    if not _table_exists(_TABLE):
        return
    existing = _constraint_names(_TABLE)

    if _NEW not in existing:
        op.create_index(
            _NEW, _TABLE, ["lab_id", "idempotency_key"], unique=True,
        )

    # Drop the global constraint only after the scoped one exists, so the table
    # is never briefly unprotected.
    if _OLD in existing:
        op.drop_constraint(_OLD, _TABLE, type_="unique")


def downgrade() -> None:
    if not _table_exists(_TABLE):
        return
    existing = _constraint_names(_TABLE)

    if _OLD not in existing:
        clashes = op.get_bind().execute(
            sa.text(
                """
                SELECT count(*) FROM (
                    SELECT idempotency_key
                    FROM claims
                    WHERE idempotency_key IS NOT NULL
                    GROUP BY idempotency_key
                    HAVING count(*) > 1
                ) AS d
                """,
            ),
        ).scalar()
        if clashes:
            raise RuntimeError(
                f"cannot restore the global unique constraint on {_TABLE}."
                f"idempotency_key: {clashes} key(s) are now used by more than one "
                "lab, which is precisely what this migration made legal. "
                "Restoring it would require deleting another tenant's claims. "
                "Resolve the intended ownership of those keys first.",
            )
        op.create_unique_constraint(_OLD, _TABLE, ["idempotency_key"])

    if _NEW in existing:
        op.drop_index(_NEW, table_name=_TABLE)
