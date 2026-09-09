# P0-2 M3 — Sales / Substitution whole-entity reconciliation

**Status:** PARTIALLY VERIFIED (Group B is an explicit M4 dependency, by design).
**Physical authority:** migration-built PostgreSQL 16, `alembic upgrade head`, 104 revisions.
**Sequencing:** Option 2 from the M3-0 decision — whole-entity reconciliation, not an
isolated Group A column conversion.

---

## 1. What was wrong

`pharmacy_sales`, `pharmacy_sale_lines`, `pharmacy_drug_substitution_rules` and
`pharmacy_drug_substitution_requests` were the last Generation B entities in the
P0-2 scope. Three separate defects, one root cause:

1. **A `String(26)` `_ulid()` primary key.** Every other physical Pharmacy table
   keys on `INTEGER`. These four were the only ones that did not.
2. **Two ORM-only columns.** `fhir_id` and `fhir_resource_type` came from the
   Generation B base and were never in any migration for these tables, so every
   ORM `INSERT` failed with `UndefinedColumn` **before a row was created**. The
   tables were unwritable through the application.
3. **Six `VARCHAR(26)` references onto integer-keyed tables** with no foreign key
   — P0-2-SUBBLOCKER-A. PostgreSQL cannot create a `varchar` foreign key onto an
   `integer` primary key, so the constraint was simply left out and the columns
   accepted arbitrary strings.

## 2. Canonical identity (M3-2)

Derived from the identity model already frozen in `CANONICAL_DRUG_CONTRACT.md`
and already applied by M1 and M2 — no new taxonomy was invented.

| Entity | Internal key | Public identity | Business code | External IDs |
| --- | --- | --- | --- | --- |
| `pharmacy_sales` | `id` `INTEGER` | `sale_id` `UUID4` | `sale_number` | none |
| `pharmacy_sale_lines` | `id` `INTEGER` | `sale_line_id` `UUID4` | — | none |
| `pharmacy_drug_substitution_rules` | `id` `INTEGER` | `substitution_rule_id` `UUID4` | — | none |
| `pharmacy_drug_substitution_requests` | `id` `INTEGER` | `substitution_request_id` `UUID4` | — | none |

Two questions had to be settled from repository evidence rather than preference:

**Why not keep `String(26)`?** Eleven domain bases across the platform declare the
same `_ulid()` `String(26)` key, `app/national/base.py` (Blood Bank) included, so
it looks like a convention. It is not one: it is the same copy-pasted Generation B
base, and in Blood Bank's case its foreign keys are declared `String(100)` onto a
`String(26)` key. The only *reconciled* identity model in the repository is
`pharmacy_drug_catalog`: `id INTEGER` internal, `drug_id UUID` public.

**Why a separate public UUID, rather than publishing the Integer key?** Contract
§3: the internal key "must never be exposed as the canonical public identity".
Publishing it would also change every one of these identifiers on the wire from a
string to an integer. The naming follows the platform's existing public
identifiers — `drug_id`, `provider_id`, `campaign_id`, `interaction_id` are all
`<noun>_id` UUID columns.

## 3. Group A — resolved

The three catalog references are now `INTEGER` with enforced foreign keys onto
`pharmacy_drug_catalog.id`:

| Column | Was | Now |
| --- | --- | --- |
| `pharmacy_sale_lines.drug_catalog_id` | `varchar(26)`, no FK | `integer`, `fk_pharmacy_sale_lines_drug_catalog` → `pharmacy_drug_catalog(id)` `ON DELETE RESTRICT` |
| `..._requests.original_drug_catalog_id` | `varchar(26)`, no FK | `integer`, `fk_pharmacy_substitution_request_original_drug` |
| `..._requests.alternative_drug_catalog_id` | `varchar(26)`, no FK | `integer`, `fk_pharmacy_substitution_request_alternative_drug` |

The four `String(26)` foreign keys *between* these four tables (`sale_lines.sale_id`,
`requests.rule_id`, `requests.consumed_sale_id`) moved to `INTEGER` with their
constraints intact.

## 4. Group B — still M4, deliberately

| Column | Physical target | Why it is not resolved here |
| --- | --- | --- |
| `pharmacy_sale_lines.batch_id` | `pharmacy_drug_batches.id` (`integer`) | `DrugBatch` is still Generation B: its ORM maps `drug_catalog_id`, a column the physical table does not have (it has `drug_id integer`). No canonical batch identity exists in the application to point at. |
| `pharmacy_sale_lines.prescription_id` | `pharmacy_prescriptions.id` (`integer`) | `Prescription` is still Generation B. |
| `..._requests.prescription_id` | `pharmacy_prescriptions.id` (`integer`) | As above. |

These three stay `VARCHAR(26)`. What M3 *did* fix is that the ORM no longer
declares foreign keys onto them: it previously named constraints PostgreSQL could
not create and the database never had. A regression test asserts these columns
are still unconstrained `VARCHAR(26)`, so a later change cannot quietly convert
them without M4 establishing the canonical target.

**M4 prerequisite, exactly:** a canonical `DrugBatch` and `Prescription` whose ORM
matches the physical integer-keyed tables. Once those exist, the three columns
convert the same way Group A did.

## 5. FHIR fields (M3-6) — category C, obsolete

Evidence, not inference:

* the migrations that created these four tables never added the columns;
* seven other Pharmacy tables (`pharmacy_drug_catalog`, `_drug_batches`,
  `_prescriptions`, `_dispense_records`, `_recalls`, `_drug_monitoring`,
  `_clinical_guidelines`) **do** have them physically, so the author added them
  deliberately where FHIR exposure was intended;
* no service, route or test reads or writes them for these four entities.

They are Generation B base inheritance, not a domain requirement. Removing them
needed no FHIR architecture decision — M1 and M2 already established the rule
that these columns are declared per entity, only where the physical table has
them, and both `DrugCatalog` and `DrugMonitoring` declare them explicitly.

## 6. Data safety

`backend/migrations/versions/20260910_0001_pharmacy_m3_sales_substitution_identity.py`
refuses to run in **either direction** unless all four tables are empty, and
reports the exact per-table counts instead of casting anything. A `VARCHAR(26)`
ULID has no deterministic integer meaning, so no identifier data is ever
converted, truncated or dropped.

Proven, not asserted — with a realistic legacy ULID row present
(`01JLEGACYULIDVALUE00000000`):

* upgrade refused, `alembic_version` stayed `20260909_0001`, the row intact;
* downgrade refused from head, `pharmacy_sales.id` stayed `integer`, the row intact.

Emptiness is a realistic precondition rather than an assumption: while the
ORM-only `fhir_id` columns were mapped, every application `INSERT` failed before
a row could be created.

## 7. API compatibility

Wire shape is unchanged: every identifier that was a string is still a string.
What changed is which value it carries — the public identifier instead of the
retired Generation B key.

| Surface | Field | Now carries |
| --- | --- | --- |
| `POSSaleResponse` | `id` | `sale_id` (UUID4) |
| `POSSaleLineResponse` | `id` | `sale_line_id` (UUID4) |
| `POSSaleLineResponse` | `drug_catalog_id` | the drug's public `drug_id` (contract §8) |
| `POSSaleLineResponse` | `batch_id` | unchanged Generation B batch key (M4) |
| `POSSaleLineCreate` | `drug_catalog_id` | the drug's public `drug_id` |
| `POSSaleLineCreate` | `substitution_request_id` | `substitution_request_id` (UUID4) |
| `SubstitutionRequestCreate` | `rule_id` | `substitution_rule_id` (UUID4) |
| `GET /pharmacy/pos/sales/{sale_id}` | path | `sale_id` (UUID4) |
| `POST /pharmacy/substitutions/requests/{request_id}/…` | path | `substitution_request_id` (UUID4) |
| `GET /pharmacy/substitutions/candidates` | `original_drug_id` | the drug's public `drug_id`; `max_length` 26 → 36 |

Two response paths changed shape rather than only value:

* the three substitution endpoints returned `request.to_dict()`, publishing every
  column verbatim. After M3 those columns are internal Integer keys, so a
  passthrough would both leak them and change the wire types. They now return an
  explicit `SubstitutionRequestResponse` carrying public identifiers.
* `POSSaleResponse` / `POSSaleLineResponse` are built explicitly instead of by
  `model_validate`, because `drug_catalog_id` now has to resolve through the
  foreign key to the drug's public identity.

No consumer can have observed the old values: the endpoints could not create a
row (§1.2), so no sale or substitution identifier has ever been issued.

## 8. Verification

| Evidence | Result |
| --- | --- |
| Clean PostgreSQL `alembic upgrade head` | pass, 104 revisions, single head `20260910_0001` |
| `downgrade -1` → `upgrade head` round trip | pass |
| Fail-closed upgrade with a legacy ULID row | refused; nothing changed |
| Fail-closed downgrade with a row present | refused; nothing changed |
| ORM ↔ physical parity, four M3 tables | exact, both directions |
| Group A foreign keys enforced | 3/3 |
| `GULA-SCHEMA-002` on the M3 tables | 8 findings → **0** |
| `GULA-SCHEMA-002` elsewhere | 235 findings, an identical set before and after |
| `tests/test_pharmacy_sales_identity_postgres.py` | 32 passed |
| `tests/test_pharmacy_pos.py` (end-to-end POS + substitution) | 3 passed |
| All `-k pharmacy` tests | 81 passed |
| Tenant isolation / ABAC / clinical safety / stability | 145 passed |
| Intelligent Core `GULA-MIG-001/002`, `SCHEMA-001`, `STATE-001` | VERIFIED, 0 findings |
| Intelligent Core `GULA-ARCH-001` | 1 finding, `national_facilities` (NR-006 / P2-1), unchanged |

## 9. What M3 did not do

* did not invent a `DrugBatch` or `Prescription` identity (Group B, M4);
* did not convert Group B columns to make types match;
* did not touch the other seventeen Generation B Pharmacy models;
* did not modify any existing migration;
* did not change `pharmacy_drug_substitution_rules`' catalog foreign keys, which
  were already canonical from the NR-003 correction.

`StockLevel.drug_catalog_id` and `StockLevel.batch_id` carry the same impossible
ORM foreign keys these four tables had. They belong to the inventory entities and
are M4's to reconcile; they are recorded here so they are not rediscovered as new.
