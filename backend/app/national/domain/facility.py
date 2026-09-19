"""NR-006 / NR-086 — ``national_facilities`` has one definition, and it is not here.

``app.models.clinical_scope.NationalFacility`` maps this table, and migration
``20260813_0004_clinical_ehr_scope_bridge`` creates it with exactly that model's
six columns.

A second mapped class used to live here. It declared 28 columns, 24 of which the
migration never creates -- including ``facility_type`` NOT NULL -- while omitting
two that do exist (``facility_code``, ``status``). It had no consumer anywhere in
the repository, and the dangerous half was ``create_all``: three test modules
build this package's metadata directly, so the suite was creating a
``national_facilities`` that production cannot have.

NR-006 replaced it with a bare ``Table`` -- a foreign-key anchor, not an entity --
because seventeen models in this package carry ``ForeignKey("national_facilities.id")``
and SQLAlchemy resolves a foreign key inside the ``MetaData`` that owns the
*referring* table. ``NationalBase`` had its own ``MetaData``, so it needed its own
copy of the target.

**It no longer does.** NR-086 gave ``NationalBase`` and ``Base`` one shared
``MetaData`` (see ``app.orm_topology``), so those seventeen foreign keys resolve
against the canonical model directly. A second declaration under one namespace is
not merely redundant, it is illegal -- SQLAlchemy raises ``InvalidRequestError``
on the duplicate key -- so the anchor is gone and this module re-exports the one
remaining definition.

Do not re-add a mapped class or a ``Table`` here. Facilities are written through
``app.models.clinical_scope.NationalFacility``.
"""

from __future__ import annotations

from app.models.clinical_scope import NationalFacility

#: The canonical table object, re-exported so that importers of this module keep
#: working. There is exactly one, and `NationalFacility` owns it.
national_facilities = NationalFacility.__table__

__all__ = ["national_facilities"]
