# NR-006 — `national_facilities` has one ORM owner

**Status:** RESOLVED 2026-09-26 (was OPEN — DECISION REQUIRED since the finding was raised)
**Decided by:** physical evidence, as part of NR-086's shared-`MetaData` change
**Owner of the table:** `app.models.clinical_scope.NationalFacility` (declarative base `Base`)
**Retired:** `app.national.domain.facility.Facility` (declarative base `NationalBase`)

## Why this was open, and why it is now decided

NR-006 recorded that two ORM classes on two declarative bases mapped the one
physical table `national_facilities`, and left it open because choosing an owner
looked like an ownership *preference* — its own `minimal_safe_fix` field reads
"NOT ATTEMPTED — requires an ownership decision; changing either mapping risks
silent behaviour change across authorization paths."

Two things changed that.

**First, the collision stopped being harmless.** While the two classes lived in
separate `MetaData` objects they never met. NR-086 puts eleven bases in one
shared namespace so that 374 cross-base foreign keys can resolve, and in one
namespace two declarations of one table name do meet. The retired class carried
`__table_args__ = (..., {"extend_existing": True})`, so it did not raise — it
silently unioned itself into the other owner's `Table`. Measured after the merge
and before the retirement:

    shared MetaData national_facilities: 30 columns
    columns not present in the physical table: 24
      address_line, city, code, created_by, deleted_at, directorate_id,
      district, email, facility_type, fhir_id, fhir_resource_type, governorate,
      is_active, is_deleted, is_emergency_available, latitude, longitude,
      name_ar, operating_hours, organization_id, parent_facility_id, phone,
      updated_by, version

That is a working owner being broken by a non-working one. Leaving both mapped
was no longer an option.

**Second, the evidence names the owner unambiguously.**

| | `clinical_scope.NationalFacility` | `national.domain.facility.Facility` |
|---|---|---|
| declarative base | `Base` | `NationalBase` |
| columns declared | 6 | 28 |
| columns absent from the physical table | **0** | **24** |
| `SELECT` through it | succeeds | `UndefinedColumn: column national_facilities.facility_type does not exist` |
| migration that creates its shape | `20260813_0004_clinical_ehr_scope_bridge.py` | none, on any revision of this branch |
| modules importing it | in live use | **none** — one re-export in `app/national/domain/__init__.py`, no consumers |

Every live `Facility` reference in the codebase — `app/services/order_service.py`,
`patient_service.py`, `app/identity/services/clinical_authorization_context_service.py`,
`app/radiology/clinical_read_gate.py`, `app/clinical_gateway/context.py`,
`app/platform/organization.py` — resolves to `app.models.organization.Facility`,
a third class on table `facilities`. None of them reached the retired one.

## The semantic point, which matters more than the column count

`app/models/clinical_scope.py` states the boundary directly, above
`NationalFacility`:

> منشأة EHR الوطنية مورد منفصل عن مورد المنشأة التشغيلي في NIAM؛ يُعاد استخدام
> حالات المراجعة نفسها، لكن لا يُسمح باستنتاج أي علاقة من تشابه المعرّفات.

*The national EHR facility is a resource separate from NIAM's operational
facility resource; the same review states are reused, but no relationship may be
inferred from a similarity of identifiers.*

There are three facility concepts in this platform, and they are not
interchangeable:

1. **NIAM operational facility** — `app.models.organization.Facility`, table
   `facilities`, integer id. Authorization scopes against this. In live use.
2. **National EHR scope facility** — `app.models.clinical_scope.NationalFacility`,
   table `national_facilities`, ULID id, six columns. Bridged to (1) through
   `clinical_ehr_facility_bindings`, deliberately and reviewably, never by
   identifier similarity.
3. **The retired class** — modelled concept (1)'s attributes (type,
   organization, directorate, address, geo, operating hours) but pointed at
   concept (2)'s table. That mismatch is why it never worked, and it is why the
   fix is retirement rather than a migration: the platform does not need a
   fourth facility model, it already has the operational one.

## What was deliberately not done

* **The 24 columns were not added to `national_facilities`.** That is a schema
  change, and under CLAUDE.md it needs human approval. It would also be the
  wrong change: it would make the EHR scope resource into a second operational
  facility, which the note above forbids.
* **The class was not re-pointed at `facilities`.** `app.models.organization.Facility`
  already owns that table; a second mapping would recreate NR-006 one table over.
* **The file was not deleted.** It is retired in place, with a `__getattr__` that
  raises a message naming which of the three concepts the caller probably wants,
  so a latent consumer fails loudly instead of silently binding to the EHR scope
  resource.

## The retired declaration, preserved verbatim

Kept so the intent it recorded stays traceable, and so that if the operational
shape is ever wanted on a national table, the proposal starts from what was
actually written rather than from memory.

```python
from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SAEnum

from app.national.base import AuditEntity
from app.national.enums import FacilityType


class Facility(AuditEntity):
    __tablename__ = "national_facilities"

    facility_type = Column(SAEnum(FacilityType), nullable=False)
    name = Column(String(200), nullable=False)
    name_ar = Column(String(200), nullable=True)
    code = Column(String(20), nullable=True, unique=True, index=True)

    organization_id = Column(String(26), ForeignKey("national_organizations.id", ondelete="RESTRICT"), nullable=True, index=True)
    directorate_id = Column(String(26), ForeignKey("national_directorates.id", ondelete="RESTRICT"), nullable=True, index=True)
    parent_facility_id = Column(String(26), nullable=True, index=True)

    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)

    address_line = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True)
    governorate = Column(String(100), nullable=True)
    district = Column(String(100), nullable=True)

    latitude = Column(String(20), nullable=True)
    longitude = Column(String(20), nullable=True)

    is_active = Column(Boolean, default=True)
    is_emergency_available = Column(Boolean, default=False)
    operating_hours = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_national_facilities_type", "facility_type"),
        Index("ix_national_facilities_org", "organization_id"),
        Index("ix_national_facilities_directorate", "directorate_id"),
        {"extend_existing": True},
    )
```

## Why the 17 dependent foreign keys still resolve

Sixteen `app/national/domain/*` modules declare 17 foreign keys naming
`national_facilities.id`. Before NR-086 those could only resolve inside
`NationalBase`'s own `MetaData`, which is the reason the retired class had to
exist at all. Under the shared namespace they find
`clinical_scope.NationalFacility`'s table directly, so the retirement needed no
replacement anchor. This is what made NR-006 resolvable only *together with*
NR-086, and it is why the two land in one change.

## Contradiction C-06, closed

The register recorded three sources that could not all be true: NR-006 said
OPEN — DECISION REQUIRED, the task log said "retire the duplicate
national_facilities ORM owner — completed", and the running process still loaded
both owners. The third was the accurate one; the task record was premature. It
is accurate now, and the guard below is what keeps it accurate.

## Verification

* `backend/tests/verification/test_cross_base_fk_topology.py` re-measures the
  topology and asserts no table name is declared by more than one mapped class
  in the shared namespace — so a reintroduction fails a test rather than
  silently unioning.
* `backend/tests/verification/test_schema_drift_guard.py::test_only_the_known_table_is_mapped_by_more_than_one_class`
  was the pin that held this finding open; it is expected to change meaning now
  that the known exception is gone.
