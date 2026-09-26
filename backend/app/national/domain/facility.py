"""NR-006 — retired. ``national_facilities`` has one ORM owner, and it is not here.

This module used to declare ``Facility(AuditEntity)`` against
``__tablename__ = "national_facilities"`` on ``NationalBase``, while
``app.models.clinical_scope.NationalFacility`` declared the same table name on
``Base``. NR-006 recorded that collision as "OPEN — DECISION REQUIRED" for as
long as the two lived in separate ``MetaData`` objects, where nothing forced a
choice. NR-086's shared namespace forces it, and the evidence decides it:

* The physical table has exactly six columns -- ``id``, ``facility_code``,
  ``name``, ``status``, ``created_at``, ``updated_at`` -- and
  ``clinical_scope.NationalFacility`` declares exactly those six.
* The class that used to be here declared 28 columns, **24 of which the table
  does not have**. It could not read: ``SELECT`` through it raised
  ``UndefinedColumn: column national_facilities.facility_type does not exist``.
* Its ``__table_args__`` carried ``{"extend_existing": True}``, so under one
  shared namespace it did not collide loudly -- it silently unioned itself into
  the other owner's ``Table``, producing a 30-column object with 24 phantom
  columns and breaking the owner that had been correct. That is measured, not
  inferred.
* The only migration on this branch that touches ``national_facilities`` is
  ``20260813_0004_clinical_ehr_scope_bridge.py``. No migration anywhere on this
  branch creates the shape this module described.
* Nothing imported it. ``app/national/domain/__init__.py`` re-exported the name
  and no other module used it; every live ``Facility`` reference in the codebase
  resolves to ``app.models.organization.Facility`` instead.

**The operational facility concept is not lost, and is not this table.** The
platform already models an operational facility: ``app.models.organization``'s
``Facility``, on table ``facilities``, which is what every live call site uses
and what NIAM scopes authorization against. ``app.models.clinical_scope``
states the boundary directly, in Arabic, above ``NationalFacility``: the
national EHR facility is a resource *separate* from NIAM's operational facility
resource, and no relationship may be inferred from a similarity of identifiers.
This module was a third modelling of the operational concept aimed at the EHR
scope table, which is why it never worked.

**What is deliberately NOT done here.** The 24 columns are not added to
``national_facilities``, and the class is not re-pointed at ``facilities``.
Either would be a schema or semantic decision this retirement has no authority
to make -- the first is a migration, the second would conflate the two
resources that comment forbids conflating. The retired declaration is preserved
verbatim in ``docs/architecture/NR-006-national-facilities-ownership.md`` so the
intent it recorded stays traceable.

The 17 ``app/national/domain`` foreign keys that name ``national_facilities.id``
still resolve: under NR-086's shared ``MetaData`` they find
``clinical_scope.NationalFacility``'s table directly, which is the reason this
class could be retired rather than replaced by an anchor.
"""

from __future__ import annotations

_RETIRED = (
    "app.national.domain.facility.Facility is retired (NR-006). The single ORM "
    "owner of the national_facilities table is "
    "app.models.clinical_scope.NationalFacility -- a six-column EHR scope "
    "resource. If you want the OPERATIONAL facility (type, organization, "
    "directorate, address, hours), that is app.models.organization.Facility on "
    "table `facilities`, and it is a different resource: see the Arabic note "
    "above NationalFacility in app/models/clinical_scope.py. Read this module's "
    "docstring and docs/architecture/NR-006-national-facilities-ownership.md "
    "before reintroducing either."
)


def __getattr__(name: str):
    """Fail loudly for anything still reaching for the retired mapping.

    A silent ``ImportError`` would send a caller looking for a typo. A caller
    that wants ``Facility`` from here has picked the wrong one of three
    facility concepts, and the message says which one it probably wants.
    """
    if name == "Facility":
        raise AttributeError(_RETIRED)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
