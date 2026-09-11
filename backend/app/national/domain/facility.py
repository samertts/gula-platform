"""NR-006 — ``national_facilities`` has one ORM owner, and it is not this module.

``app.models.clinical_scope.NationalFacility`` maps this table on
``app.database.Base``, and migration ``20260813_0004_clinical_ehr_scope_bridge``
creates it with exactly that model's six columns.

A second mapped class used to live here. It declared 28 columns, 24 of which the
migration never creates -- including ``facility_type`` NOT NULL -- while omitting
two that do exist (``facility_code``, ``status``). It had no consumer anywhere in
the repository: every ``Facility`` import resolves to
``app.models.organization.Facility``, which maps the unrelated ``facilities``
table. Any query issued through this one would have raised ``UndefinedColumn``.

The more dangerous half was ``create_all``: three test modules build
``NationalBase.metadata`` directly, so the suite was creating a
``national_facilities`` that production cannot have. Tests written against that
shape would have passed against a schema no migration produces.

What ``NationalBase``'s metadata genuinely needs from this module is the foreign
key target -- seventeen models in this package carry
``ForeignKey("national_facilities.id")`` and must resolve inside their own
MetaData. That is a table, not an entity. Declared as a bare ``Table`` it keeps
every one of those references resolvable, makes what ``create_all`` builds match
the migration, and leaves exactly one class in the codebase able to write a
facility row.

Do not re-add a mapped class here. Facilities are written through
``app.models.clinical_scope.NationalFacility``.
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Table, UniqueConstraint

from app.national.base import NationalBase

#: Foreign-key anchor only -- mirrors the physical table column for column.
national_facilities = Table(
    "national_facilities",
    NationalBase.metadata,
    Column("id", String(26), primary_key=True, nullable=False),
    Column("facility_code", String(100), nullable=True),
    Column("name", String(255), nullable=False),
    Column("status", String(20), nullable=False, server_default="active"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("facility_code", name="uq_national_facilities_facility_code"),
    extend_existing=True,
)

__all__ = ["national_facilities"]
