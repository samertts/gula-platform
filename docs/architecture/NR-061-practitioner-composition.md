# NR-061 — the practitioner composition, proved column by column

**Status:** SPECIFIED. No table built, no reference re-pointed, no migration written.
**Method:** AST over `app/`, the committed `evidence-created-tables.json`, and the
NR-022 classification evidence. No repository-wide rescan.

## 1. What the decision asked

> Canonical practitioner identity must compose from the canonical Person/Identity
> model. Do not create a second registry of natural persons. Target:
> Person → Practitioner Profile → Credentials/Licensure/Specialty →
> Organization/Facility Assignment. Retire unbuilt rival practitioner identities
> only after dependency and compatibility proof. Do not blindly point every
> practitioner FK directly at Person.

Three things therefore have to be proved rather than asserted: that the
composition covers what the rival table holds, that nothing depends on the rival
today, and that a Practitioner Profile layer is required by something reachable.

## 2. There is no rival inside Identity

`niam_practitioners` has no ORM class and no migration. The Identity Platform
never modelled a practitioner as an entity; it models the parts:

| Table | Built | Holds |
| --- | --- | --- |
| `niam_persons` | yes | the natural person |
| `niam_licenses` | yes | licence number, authority, expiry, board certification, degree |
| `niam_employments` | yes | person → organization, position, dates, supervisor |
| `niam_assignments` | yes | posting: facility, department, unit, role, delegation |
| `niam_role_assignments` | yes | what the person may do |

84 of 87 NIAM tables are built. The composition is real, not aspirational.

## 3. Compatibility proof — all 21 columns of `national_practitioners`

Mapped by hand, not by name similarity: `date_of_birth` lives as `birth_date`,
`qualification` as `degree_name`, `role` as an assignment's `role_id`. A
name-matching heuristic would have called those gaps and this coverage, and both
errors change the decision.

**Covered — 15 of 21**

| Rival column | Composition home |
| --- | --- |
| `full_name`, `full_name_ar` | `niam_persons.given_name` / `family_name` / `full_name_ar` |
| `date_of_birth` | `niam_persons.birth_date` |
| `gender`, `nationality`, `phone`, `email`, `is_active` | `niam_persons.*` |
| `national_id_hash` | `niam_persons.national_id_hash` |
| `license_number` | `niam_licenses.license_number` |
| `qualification` | `niam_licenses.degree_name` (+ `degree_type`, `degree_institution`) |
| `is_verified` | `niam_licenses.verified` |
| `organization_id` | `niam_employments.organization_id` |
| `facility_id` | `niam_assignments.facility_id` |
| `role` | `niam_assignments.role_id` |

**Genuine gaps — 6 of 21**, every one of them additive to a table that already
exists. None needs a registry of natural persons, which is the whole point.

| Gap | Belongs on |
| --- | --- |
| `specialty`, `sub_specialty` | `niam_licenses` — clinical scope of practice is a property of the licence |
| `health_profession_number` | `niam_licenses` — a profession-registry identifier |
| `signature_url` | with the licence it signs under |
| `available_for_telehealth` | a practice attribute; needed only once a practitioner-facing feature is reachable |
| `photo_url` | person-scoped, not practitioner-scoped |

Held by `test_practitioner_canonical_identity.py`: a new rival column must map or
be declared, and every mapping must still name a column that exists.

## 4. Dependency proof — the surface is entirely latent

This is the result that decides the unit. Of the 263 subject references NR-022
classified, **261 live in tables that no migration builds**, including **all 57
practitioner references**. The complete live surface is two columns:

```
niam_citizen_relationships.citizen_id  -> national_citizens
niam_citizen_relationships.patient_id  -> national_patients
```

So no re-pointing is owed, and none is possible: there is nothing to re-point
from. Building a Practitioner Profile now would be schema created to satisfy an
unreachable reference list — the NR-059 failure mode with a different subject.

Held by `test_subject_reference_semantics.py::test_the_subject_transition_stays_latent`.

## 5. Is a Practitioner Profile table required?

**Not yet, and the evidence says so rather than taste.** The layer earns a table
when either of these becomes true:

1. A built table needs to reference "a person acting in a licensed capacity" —
   at which point the FK needs a target that structurally implies licensure, and
   `niam_persons.id` does not.
2. Practitioner-scoped state accumulates beyond what §3 shows. Today that state
   is two columns (`signature_url`, `available_for_telehealth`), and both have a
   defensible home on the licence.

Until then the composition answers every question the rival table answers, and
the cheapest correct action is to add the four licence-level columns when a
consumer needs them — not to create an entity.

## 6. What was deliberately not done

- `national_practitioners` was not built. Guarded.
- No FK was re-pointed. There is no live reference to re-point.
- No migration was written. The six gaps are additive columns on built tables
  and belong in the commit that gives them a consumer.

## 7. Status

**SPECIFIED.** The composition is proved complete to within six declared,
additive gaps, and proved to have no live dependants. The next practitioner
decision is triggered by a consumer, not by a reference count.
