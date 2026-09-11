# NR-047 — Organization ORM/schema reconciliation: discovery

Status: **discovery complete, implementation not started.**
Head: `42d58cb2` · branch `claude/p0-2-pharmacy-reconciliation` · PR #258.

No schema was changed, no migration was written, no ORM was edited. This
document is evidence.

## 1. The defect, restated from measurement

`app/models/organization.py::Organization` declares four columns the migrated
`organizations` table does not have:

| ORM declares | physical `organizations` | where it actually exists |
|---|---|---|
| `org_id` | — (`organization_id`) | `niam_organizations.org_id` |
| `org_type` | — (`organization_type`) | `niam_organizations.org_type` |
| `parent_org_id` | — | `niam_organizations.parent_org_id` |
| `updated_at` | — | `niam_organizations.updated_at` |

Any ORM query that selects the `Organization` *entity* emits all sixteen
declared columns and PostgreSQL answers `UndefinedColumn`.

**The four phantom columns are exactly `NIAMOrganization`'s vocabulary.** The
operational model was written in the NIAM model's names.

## 2. Physical schema (read from PostgreSQL, not from metadata)

`organizations`: integer `id` (serial PK), `organization_id` varchar(100)
UNIQUE, `name_en` NOT NULL, `name_ar`, `organization_type`, `is_active` NOT
NULL default true, `created_at`, `tenant_id` → `tenants.id` ON DELETE SET NULL,
`governorate_id`, `directorate_id`, `contact_email`, `contact_phone`,
`address`, `metadata` json.

**Four inbound foreign keys** — and the fourth is the decisive one:

* `facilities.organization_id`
* `users.organization_id`
* `role_assignments.organization_id`
* **`niam_assignments.clinical_organization_resource_id`**

NIAM's own assignment table points *into* `organizations`. That is not a
projection; it is the referenced authority for clinical organization identity.

## 3. Migration history — the four columns never existed

`organizations` is created exactly once, by
`20260722_0001_authorization_expansion.py`, **with** `organization_id` and
`organization_type` from birth. Across all 106 migrations, no statement ever
adds, renames or drops `organizations.org_id`, `.org_type`, `.parent_org_id`
or `.updated_at`. `org_id` appears in migrations in exactly one place:
`20260723_0001_niam_identity_platform_tables.py`, creating
`niam_organizations` — **the day after**.

So: no rename happened, nothing was removed. The ORM drifted toward a
neighbouring model's names.

## 4. Ownership

| | `organizations` | `niam_organizations` | `national_organizations` |
|---|---|---|---|
| physical table | **yes** | yes | **no** |
| ORM owners | **exactly 1** | 1 | 1 (unmigrated) |
| PK | integer serial | varchar(26) | — |
| rows | 0 | 0 | — |
| inbound FKs | 4 | — | — |

One ORM owner, one physical table, one creating migration. **No duplicate
authority exists**, so the "ambiguous ownership" stop condition does not apply.

## 5. Runtime dependency graph

Fourteen modules import `Organization`. They split cleanly in two:

**The authorization path — uses only `id`, `is_active`, `tenant_id`, all of
which exist physically.** `clinical_authorization_context_service.py` joins on
`Organization.id` and filters `Organization.is_active`;
`clinical_scope_bridge_service.py` does the same twice;
`authorization_service.py` filters `Organization.id`. None of them touches a
phantom column. The path fails *only* because `select(Facility, Organization,
Tenant)` selects whole entities.

**Bootstrap — the only consumer of the phantom columns**, in
`app/core/bootstrap/{ministry,organizations,directorates,facilities,laboratories,validation}.py`:
`Organization.org_id` (6 sites), `.org_type` (2), `.parent_org_id` (1).

## 6. Second blast radius: the national bootstrap has never run

`run_bootstrap` is called from `startup_guard.py::_run_national_bootstrap`,
wrapped in `try/except Exception` and logged as **"non-fatal"**. Executed
against the migrated schema (inside a rolled-back transaction), it fails at:

```
SELECT organizations.id, organizations.org_id, ... FROM organizations
WHERE organizations.org_id = 'org-iraq-moh'
```

So the platform boots, `system_ready` becomes True, and the ministry,
directorates, organizations, facilities and laboratories are silently never
seeded. **`organizations` having 0 rows is not "unused" — it is the symptom.**

## 7. Relationship to NR-022 — related in theme, separable in fact

NR-022 is about `national_practitioners`, `national_citizens`,
`national_patients`, `national_encounters` — tables that are *mapped but have
no physical table* — plus `national_facilities`, the one that acquired a second
owner.

NR-047 is a different shape: an existing, singly-owned, FK-referenced table
whose ORM drifted in column naming. `national_organizations` has no physical
table and no FK relationship to `organizations`, so it is not a competing
authority today.

**NR-047 does not require the National Core decision.** It is answer **A** —
an isolated Organization ORM/schema defect — with **E** as its mechanism: the
ORM adopted the wrong model's vocabulary.

## 8. Canonical owner decision

`organizations` **is canonical** for operational/clinical organization
identity, on the FK graph, the creating migration and the authorization path —
not on naming. `niam_organizations` is canonical for the NIAM administrative
hierarchy. They are two distinct entities, deliberately bridged by
`ClinicalLabFacilityBinding`. Nothing here argues for merging them.

## 9. Are the missing columns real requirements?

* `org_id`, `org_type` — **naming only.** `organization_id` and
  `organization_type` already carry those exact semantics. No migration needed.
* `parent_org_id` — **a real domain concept** (Iraq MoH → governorate
  directorates, seeded and asserted by `validation.py`), but note its semantics
  differ from NIAM's: `OrganizationDef.parent_org_id: str | None` is a *public
  identifier string*, whereas `NIAMOrganization.parent_org_id` is an integer
  self-FK. Borrowing the name did not borrow the meaning.
* `updated_at` — declared by the ORM and read by nothing.

## 10. Error handling: a schema fault wearing an authorization label

`clinical_gateway/context.py:164` converts **any** exception into
`ClinicalGatewayBlocked("invalid_context")`, which the route renders as 403.
An `UndefinedColumn` is therefore indistinguishable from a genuine policy
denial. By contrast `authorization_decision.py:200` maps failures to
`deny(internal_failure)` — correctly labelled. The gateway resolver is the one
that misclassifies. Documented, not changed in this batch.

## 11. Repair options

| | Option | Migration | Data risk | Fixes authz | Fixes bootstrap |
|---|---|---|---|---|---|
| **A** | ORM name correction: map `organization_id`/`organization_type` | none | none | partly | partly |
| **B** | Additive migration: `parent_org_id varchar(100)`, `updated_at timestamptz`, both nullable | 1, additive | none (0 rows, nullable) | — | yes |
| **C** | Query correction: select columns instead of entities | none | none | yes | no |
| **D** | Canonical owner reconciliation (merge with `niam_organizations`) | large | high | — | — |
| **E** | Defer into NR-022 | — | — | no | no |

**C** is rejected: it hides the drift at each call site instead of fixing it,
and leaves bootstrap broken. **D** is rejected: the FK graph shows two distinct
entities with a deliberate bridge; merging is unjustified. **E** is rejected on
§7 — NR-047 is separable and NR-022 would delay a bootstrap defect that is live
now.

### Recommended: **A + B**, as one small batch

Map the ORM attributes onto the real column names (`Column("organization_id",
...)` keeps the Python attribute stable so bootstrap needs no edit), then one
additive, nullable, idempotent migration for the two genuinely absent columns.
No rename, no drop, no type change, no data movement.

## 12. Proof required to close NR-047

Against migrated PostgreSQL: ORM/physical agreement with no phantom columns;
`select(Facility, Organization, Tenant)` executes; `run_bootstrap` completes
and seeds; the clinical allow path returns 200; invalid context still denied;
cross-tenant organization still denied; migration up/down round trip; a guard
that fails if ORM and table diverge again.

## 13. Impact

* **NR-044.1** — remains PARTIALLY VERIFIED. NR-047 is its ALLOW-path blocker.
* **AUTH-F5 / NR-043** — unchanged; blocked on NR-044.2, not on this.
* **NR-022** — unchanged. No evidence here alters it.

---

# Implementation and verification (recorded after the fact)

Status: **NR-047 VERIFIED.** Delivered with migration `20260913_0001`.

The discovery above recommended A+B. Implementation followed it, with one
refinement the evidence forced: the four phantom columns did **not** deserve the
same treatment.

| Column | Treatment | Why |
|---|---|---|
| `org_id` | **mapped** to `organization_id` | naming only; the semantics already existed |
| `org_type` | **mapped** to `organization_type` | naming only |
| `updated_at` | **removed from the ORM** | read, written and serialised by nothing — adding it would be drift in the other direction |
| `parent_org_id` | **added by migration** | the bootstrap genuinely seeds a ministry-to-directorate hierarchy through it |

Mapping rather than renaming means every caller in `app/core/bootstrap/` is
untouched: `Organization.org_id` still exists in Python, it simply resolves to
the real column now.

## `parent_org_id` — type taken from the contract, not from the name

`OrganizationDef.parent_org_id` is `str | None` and holds a *public* identifier
(`"org-iraq-moh"`), so the column is `VARCHAR(100)` against
`organizations.organization_id`. It is deliberately **not** the integer self-FK
`niam_organizations.parent_org_id` uses. The names coincide because of the same
drift that caused NR-047; the semantics never did.

No foreign key is declared. `organization_id` is UNIQUE so one would be
well-formed, but it would impose a seed-ordering constraint the bootstrap does
not need, and NR-047's remit was to make the model and the schema agree — not to
add referential rules nobody asked for. A deliberate omission, not an oversight.

## Proof

Against migrated PostgreSQL 16.13, never SQLite and never `create_all()`.

* **Schema** — declared-minus-physical and physical-minus-declared both empty.
* **Queries** — all six execute: `select(Organization)`; `Organization+Tenant`;
  `Facility+Organization+Tenant`; the exact
  `ClinicalAuthorizationContextService` query; the bootstrap lookup; the
  bootstrap `org_type`/`parent_org_id` reads.
* **Migration** — upgrade, downgrade, re-upgrade; one head; all four inbound
  foreign keys and the UNIQUE constraint preserved.
* **Bootstrap** — completes (ministry 1, directorates 19, permissions 92, roles
  19). The ministry sits at the root with `parent_org_id` NULL; every
  directorate's parent resolves to a real `organization_id`; no facility lacks
  an organization. A second pass adds **zero** organizations and **zero**
  facilities, with no duplicate `org_id`.
* **ALLOW** — `GET /api/v1/clinical/patients` returns **200**, and the resolver
  reports the full operational scope (lab, facility, tenant, workspace).
* **DENY** — eight boundaries broken one at a time *from that same
  otherwise-allowing context*, each yielding its own reason code and recovering
  when restored. That ordering matters: a universal 403 from a hidden database
  failure cannot produce it.
* **Audit** — exactly one `clinical_gateway` entry per read, with uuid,
  entry_hash and `decision=allow`; `verify()` returns VALID.
* **Negative proof** — reverting the ORM mapping fails 8 tests; reinstating
  `updated_at` fails 8; rolling the migration back fails 7. All restored.

## The four states of this request

A useful record of what each batch actually bought:

| | Response | Cause |
|---|---|---|
| before NR-044.1 | 500 | the async actor raised before reaching PostgreSQL |
| after NR-044.1 | 503 | the deny audit could not be written (NR-045) |
| after NR-045 | 403 `invalid_context` | the Organization ORM named columns the table lacks (NR-047) |
| **after NR-047** | **200** | — |

## Recorded, not fixed

* `lims_departments` gains 16 rows on a second bootstrap pass and is stable from
  the third. A pre-existing behaviour in a different seeder; organizations and
  facilities are fully idempotent.
* `clinical_gateway/context.py:164` still converts any exception into
  `invalid_context`. Left alone deliberately — what changed is that the repaired
  path no longer needs it, so `invalid_context` is again reserved for real
  context failures, as the denial ladder demonstrates.
* The startup guard still logs bootstrap failure as "non-fatal". Not weakened,
  and not strengthened: with the bootstrap working, nothing is being swallowed
  today, but the pattern would hide the next failure just as well.

## NR-022 boundary

No `national_*` table was created; `niam_organizations` was not touched; no
National Core ownership changed; no legacy identity migration was performed.
NR-022 remains a separate, open finding.
