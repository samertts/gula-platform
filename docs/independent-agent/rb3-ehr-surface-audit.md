# RB-3 — end-to-end audit of the served `/ehr` surface

Independent lane (`claude/independent-audit-1`), worktree `/home/user/gula-audit`.
Scope: RB-3 only. RB-5, RB-4 and RB-6 were not started.

**Evidence database:** `gula_agent2`, the RB-1 proven head — Alembic head
`20260916_0001`, 423 physical tables. Verified unchanged at the end of this phase
(423 tables, same head, zero rows added). No migration was authored, no
PostgreSQL table was created, no ORM model was deleted, IA-004's migration was
not touched, and migration transaction semantics were not changed.

---

## 1. Surface inventory

| measure | value |
|---|---|
| served `/ehr` paths in the OpenAPI schema | **54** |
| served `/ehr` operations (verb × path) | **86** |
| route functions in `backend/app/routes/ehr.py` | **86** (1:1 with operations) |
| sub-routers under `/ehr` | none — one `APIRouter(prefix="/ehr")` at `ehr.py:31` |
| write operations (POST/PUT/DELETE) | 51 |
| write operations carrying `@audit_log` | **51 / 51** (NR-082, this lane) |
| feature-flag gate on registration | **none** — `ehr` is in `feature_routes` in `factory.py:559` and is included unconditionally |

The surface is served unconditionally in every deployment. It is not behind
`SNDHS_ENABLE_*`, `ENABLE_FINANCIAL_ENGINE`, or any other toggle.

## 2. Classification of all 54 paths

Required six-way classification, one class per path:

| class | paths | share |
|---|---|---|
| REAL | **0** | 0 % |
| PARTIAL | **1** | 1.9 % |
| BROKEN | **53** | 98.1 % |
| STUB | 0 | 0 % |
| UNIMPLEMENTED | 0 | 0 % |
| INTENTIONALLY_EXTERNAL | 0 | 0 % |

Nothing is classified REAL. Runtime verification was feasible and was performed,
and no `/ehr` operation returned clinical data from the proven head database.

Nothing is STUB or UNIMPLEMENTED: every one of the 86 operations resolves to a
real service function and a real ORM model (§5). None returns a fabricated
literal, and none returns an empty success in place of work.

Nothing is INTENTIONALLY_EXTERNAL: the router is registered unconditionally, no
path proxies to another service, and no path is documented as externally served.

## 3. Runtime evidence against the proven head database

Probe: `TestClient` over `app.main:app` with `get_db` overridden onto
`gula_agent2`, a real `labs`/`lab_users` tenant (ids `1`,`1`), and a token minted
by `create_token({"user_id": 1, "lab_id": 1, "role": "admin"})`. Every operation
was executed; bodies were synthesised from the served OpenAPI schema.

| observed status | operations |
|---|---|
| `500` — `psycopg2.errors.UndefinedTable` | **85 / 86** |
| `403` — `Clinical EHR access is not permitted` | **1 / 86** |
| `2xx` | **0 / 86** |

Distinct root relations named in the 85 failures: `national_patients` (33),
then `ehr_care_plans`, `ehr_clinical_notes`, `ehr_allergies`,
`ehr_clinical_attachments`, `ehr_conditions`, `ehr_diagnoses`,
`ehr_family_history`, `ehr_immunizations`, `ehr_medication_administrations`,
`ehr_medication_dispenses`, `ehr_medication_requests`,
`ehr_medication_statements`, `ehr_problem_list_items`, `ehr_risk_factors`,
`ehr_social_history`, `ehr_care_plan_activities`, `ehr_care_plan_goals`.

The probe was first run against the RB-1 proof checkout
(`/home/user/gula-p02-proof`, `ce097a0c`), which does **not** carry this lane's
NR-082 work. It was re-run against `/home/user/gula-audit` (`89d107b0`, 51
`@audit_log` decorators present). Both runs produced 85 × `500` + 1 × `403`. The
figures reported here are from the audited lane.

## 4. Physical schema evidence

The `/ehr` surface depends on 19 tables. **None is present in the proven head
database**, and `ehr_*` tables number zero:

| table | in head DB | created by any migration in the chain |
|---|---|---|
| `ehr_allergies` | no | **no** |
| `ehr_care_plan_activities` | no | **no** |
| `ehr_care_plan_goals` | no | **no** |
| `ehr_care_plans` | no | **no** |
| `ehr_clinical_attachments` | no | **no** |
| `ehr_clinical_notes` | no | **no** |
| `ehr_conditions` | no | **no** |
| `ehr_diagnoses` | no | **no** |
| `ehr_family_history` | no | **no** |
| `ehr_immunizations` | no | **no** |
| `ehr_medication_administrations` | no | **no** |
| `ehr_medication_dispenses` | no | **no** |
| `ehr_medication_requests` | no | **no** |
| `ehr_medication_statements` | no | **no** |
| `ehr_patient_timeline` | no | **no** |
| `ehr_problem_list_items` | no | **no** |
| `ehr_risk_factors` | no | **no** |
| `ehr_social_history` | no | **no** |
| `national_patients` | no | **no** — see below |

`national_patients` is named exactly once in `migrations/versions/`, at
`20260811_0002_citizen_relationship_foundation.py:72`, and only as a **foreign-key
target** inside the loop guarded by `if _has_table(target_table):`. No migration
creates it. A grep for `ehr_` across `migrations/` returns only the unrelated
`clinical_ehr_*` scope-bridge tables, which do exist.

**Root cause of RB-3 (single, unambiguous):** the EHR domain and the national
patient spine it is keyed on were never given migrations. This is not a migration
that failed, was skipped, or was reverted — it was never authored. The 86 served
operations sit over 19 relations that no deployment has ever had.

This is also exactly what IA-004 silently swallows: the FK to `national_patients`
is skipped without a trace because the target table does not exist. RB-3 confirms
IA-004's evidence independently. **IA-004 remains OPEN/P1 and was not fixed here.**

## 5. Route → service → model → table trace

All 86 operations were traced by AST from `routes/ehr.py` through
`services/ehr_service.py` (1 339 lines, ~100 functions) to the ORM classes in
`app/ehr/models/` and their `__tablename__`.

* operations resolving to at least one table: **86 / 86**
* operations resolving to no table (a stub signature): **0 / 86**
* operations touching at least one absent table: **86 / 86**

The service layer is a complete implementation, not a skeleton. Called directly
against a schema where the tables exist, `create_clinical_note` returns a
persisted ULID and `list_allergies_by_patient` / `list_clinical_notes_by_patient`
return result sets. The implementation is real; the schema under it is not.

## 6. Per-path matrix

`head-DB` is authoritative PostgreSQL evidence. `code-path` is the indicative
SQLite result from §7 and is **not** a PostgreSQL claim.

| # | path | verbs | class | head-DB (PostgreSQL, authoritative) | code-path (SQLite, indicative) | IA-005 ops | audited ops | owned table(s) |
|---|------|-------|-------|--------------------------------------|--------------------------------|-----------|-------------|----------------|
| 1 | `/ehr/allergies` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_allergies` |
| 2 | `/ehr/allergies/{allergy_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_allergies` |
| 3 | `/ehr/attachments` | POST | **BROKEN** | 500 | 200 | 0/1 | 1/1 | `ehr_clinical_attachments` |
| 4 | `/ehr/attachments/{attachment_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 200, 404 | 0/3 | 2/3 | `ehr_clinical_attachments` |
| 5 | `/ehr/care-plan-activities/{activity_id}` | DELETE, PUT | **BROKEN** | 500 | 404 | 1/2 | 2/2 | `ehr_care_plan_activities`, `ehr_care_plans` |
| 6 | `/ehr/care-plan-goals/{goal_id}` | DELETE, PUT | **BROKEN** | 500 | 404 | 1/2 | 2/2 | `ehr_care_plan_goals`, `ehr_care_plans` |
| 7 | `/ehr/care-plans` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_care_plans` |
| 8 | `/ehr/care-plans/{plan_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_care_plans` |
| 9 | `/ehr/care-plans/{plan_id}/activities` | POST | **BROKEN** | 500 | 404 | 1/1 | 1/1 | `ehr_care_plan_activities`, `ehr_care_plans` |
| 10 | `/ehr/care-plans/{plan_id}/goals` | POST | **BROKEN** | 500 | 404 | 1/1 | 1/1 | `ehr_care_plan_goals`, `ehr_care_plans` |
| 11 | `/ehr/clinical-notes` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_clinical_notes` |
| 12 | `/ehr/clinical-notes/{note_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_clinical_notes` |
| 13 | `/ehr/clinical/facilities/{national_facility_id}/notes/{note_id}` | GET | **PARTIAL** | 403 | RAISED | 0/1 | 0/1 | `ehr_clinical_notes` |
| 14 | `/ehr/conditions` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_conditions` |
| 15 | `/ehr/conditions/{condition_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_conditions` |
| 16 | `/ehr/diagnoses` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_diagnoses` |
| 17 | `/ehr/diagnoses/{diagnosis_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_diagnoses` |
| 18 | `/ehr/encounters/{encounter_id}/clinical-notes` | GET | **BROKEN** | 500 | 200 | 1/1 | 0/1 | `ehr_clinical_notes` |
| 19 | `/ehr/family-history` | POST | **BROKEN** | 500 | 200 | 0/1 | 1/1 | `ehr_family_history` |
| 20 | `/ehr/family-history/{record_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 0/3 | 2/3 | `ehr_family_history` |
| 21 | `/ehr/immunizations` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_immunizations` |
| 22 | `/ehr/immunizations/{record_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_immunizations` |
| 23 | `/ehr/medication-administrations` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_medication_administrations` |
| 24 | `/ehr/medication-administrations/{admin_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_medication_administrations` |
| 25 | `/ehr/medication-dispenses` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_medication_dispenses` |
| 26 | `/ehr/medication-dispenses/{dispense_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_medication_dispenses` |
| 27 | `/ehr/medication-requests` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_medication_requests` |
| 28 | `/ehr/medication-requests/{request_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_medication_requests` |
| 29 | `/ehr/medication-statements` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_medication_statements` |
| 30 | `/ehr/medication-statements/{statement_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_medication_statements` |
| 31 | `/ehr/patient/{patient_id}` | GET | **BROKEN** | 500 | 200 | 0/1 | 0/1 | `ehr_allergies`, `ehr_care_plans`, `ehr_clinical_notes`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements` |
| 32 | `/ehr/patient/{patient_id}/summary` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_allergies`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements` |
| 33 | `/ehr/patients/{patient_id}/allergies` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_allergies` |
| 34 | `/ehr/patients/{patient_id}/attachments` | GET | **BROKEN** | 500 | 200 | 0/1 | 0/1 | `ehr_clinical_attachments` |
| 35 | `/ehr/patients/{patient_id}/care-plans` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_care_plans` |
| 36 | `/ehr/patients/{patient_id}/clinical-notes` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_clinical_notes` |
| 37 | `/ehr/patients/{patient_id}/conditions` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_conditions` |
| 38 | `/ehr/patients/{patient_id}/diagnoses` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_diagnoses` |
| 39 | `/ehr/patients/{patient_id}/family-history` | GET | **BROKEN** | 500 | 200 | 0/1 | 0/1 | `ehr_family_history` |
| 40 | `/ehr/patients/{patient_id}/immunizations` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_immunizations` |
| 41 | `/ehr/patients/{patient_id}/medication-administrations` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_medication_administrations` |
| 42 | `/ehr/patients/{patient_id}/medication-dispenses` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_medication_dispenses` |
| 43 | `/ehr/patients/{patient_id}/medication-requests` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_medication_requests` |
| 44 | `/ehr/patients/{patient_id}/medication-statements` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_medication_statements` |
| 45 | `/ehr/patients/{patient_id}/problem-list` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_problem_list_items` |
| 46 | `/ehr/patients/{patient_id}/risk-factors` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_risk_factors` |
| 47 | `/ehr/patients/{patient_id}/social-history` | GET | **BROKEN** | 500 | RAISED | 1/1 | 0/1 | `ehr_social_history` |
| 48 | `/ehr/patients/{patient_id}/timeline` | GET | **BROKEN** | 500 | 200 | 1/1 | 0/1 | `ehr_allergies`, `ehr_care_plans`, `ehr_clinical_notes`, `ehr_conditions`, `ehr_diagnoses`, `ehr_immunizations`, `ehr_medication_statements`, `ehr_patient_timeline` |
| 49 | `/ehr/problem-list` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_problem_list_items` |
| 50 | `/ehr/problem-list/{item_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_problem_list_items` |
| 51 | `/ehr/risk-factors` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_risk_factors` |
| 52 | `/ehr/risk-factors/{record_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_risk_factors` |
| 53 | `/ehr/social-history` | POST | **BROKEN** | 500 | RAISED | 1/1 | 1/1 | `ehr_social_history` |
| 54 | `/ehr/social-history/{record_id}` | DELETE, GET, PUT | **BROKEN** | 500 | 404 | 2/3 | 2/3 | `ehr_social_history` |

## 7. Does the schema alone explain it? — the second, latent defect (IA-005)

The head-DB evidence proves the surface cannot serve. It cannot by itself
distinguish *"correct code over a missing schema"* from *"code that is also
defective"*. That distinction decides whether one migration unblocks 86
operations or not, so it was measured.

**Method.** The 19 tables plus `labs`/`lab_users`/`audit_logs` were created from
ORM metadata in a throwaway **SQLite file** inside the session scratchpad, a
patient was seeded, and all 86 operations were re-executed. No PostgreSQL table
was created and no migration was written. **SQLite is weakly typed and masks type
mismatches PostgreSQL rejects, so a pass here is a code-path pass only and is not
evidence of PostgreSQL correctness.**

With the schema present:

| outcome | operations |
|---|---|
| `200` | 8 |
| `404` (record absent — the not-found branch, correct) | 50 |
| `RecursionError` (stack exhausted) | 27 |
| `OperationalError` (probe limitation: NIAM tables not created) | 1 |

So the schema is **not** the only defect. 27 operations still fail.

### IA-005 — `to_dict()` returns SQLAlchemy's `MetaData` for any column named `metadata`

`shared/models/base.py:36` serialises by column name:

```python
def to_dict(self) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for col in self.__table__.columns:
        val = getattr(self, col.name)      # <-- col.name, not the mapped attribute
```

16 of the 18 EHR tables have a column literally named `metadata`, whose mapped
Python attribute is `metadata_`. For those, `getattr(self, "metadata")` does not
read the column — it returns the declarative base's **`MetaData` registry object**
(564 tables). FastAPI's `jsonable_encoder` then walks it and the stack dies.

Measured directly, not inferred:

* `A.__table__.columns` contains `metadata`; the mapped attribute is `metadata_`.
* `type(AllergyIntolerance.metadata).__name__` is `MetaData`, and it **is**
  `SHARED_METADATA`, holding 564 tables.
* Encoding one real record field-by-field: the only key that recurses is
  `metadata`, `type=MetaData`, `repr=MetaData()`.
* Traceback frame census on `POST /ehr/allergies`: 1 052 frames, of which 486 +
  484 are `fastapi/encoders.py:307` and `:356` in `jsonable_encoder`.

**Causation is not NR-086 (this lane's shared-MetaData change).**
`jsonable_encoder(MetaData())` on an **empty** registry encodes fine, but a
registry holding **one** table already recurses. The defect therefore exists for
any non-empty `MetaData`. NR-086 enlarged the object being walked; it did not
create the defect.

**Exposure, measured statically over all 86 operations** (an operation is exposed
when it serialises via `to_dict()`/`_to_dict()` without a field allowlist and its
own model has a `metadata` column):

| | operations |
|---|---|
| serialise via `to_dict()` | 67 |
| use the field allowlist (`_clinical_note_read_response`) | 1 |
| **exposed to IA-005** | **59 / 86** |
| not exposed | 27 |

The 27 unexposed ones are the 13 `DELETE`s (which return no record), the
`family-history` and `attachments` families (their two tables are the only EHR
tables with no `metadata` column), `GET /ehr/patient/{patient_id}`, and the one
allowlisted clinical read.

**The static model was validated against runtime in both directions**, with
records seeded so the success path is actually reached:

| operation | predicted | observed |
|---|---|---|
| `GET /ehr/allergies/{id}` | exposed | `RecursionError` |
| `GET /ehr/patients/{pid}/allergies` | exposed | `RecursionError` |
| `GET /ehr/family-history/{id}` | not exposed | `200` |
| `GET /ehr/patients/{pid}/family-history` | not exposed | `200` |

4/4, including two negatives — the model discriminates and is not vacuous.

### Blast radius beyond `/ehr`

`metadata` is a column name on **124 tables** in `SHARED_METADATA`. Every route
anywhere in the platform that returns `to_dict()` on one of those models carries
the same defect. Named examples outside EHR: `ai_conversations`,
`ai_agent_executions`, `ai_embeddings`, and the whole `cc_*` care-continuum
cluster (`cc_care_journeys`, `cc_clinical_handovers`, `cc_delivery_records`,
`cc_antenatal_care_visits`, …). **RB-3 measured the `/ehr` exposure only; the
platform-wide route exposure is UNKNOWN and is not claimed here.**

IA-005 is registered as a new finding. It is **not fixed in this lane** — the fix
touches `shared/models/base.py`, which is shared surface used by the primary lane,
and changing a serialiser used by 124 tables is an API-response-shape change
requiring approval under `CLAUDE.md`.

## 8. The one PARTIAL path

`GET /ehr/clinical/facilities/{national_facility_id}/notes/{note_id}` is the only
path that is not wholly broken, and it is the only one that returned something
other than `500`.

**Its authorization layer is real and executes correctly against the head
database.** All ten tables `ClinicalEhrReadGate` traverses are physically present:
`niam_legacy_account_links`, `niam_accounts`, `niam_identities`,
`clinical_lab_facility_bindings`, `clinical_ehr_facility_bindings`, `facilities`,
`organizations`, `tenants`, `niam_assignments`, `niam_policies`.

Executed against the real head DB it denied deny-by-default with reason
`legacy_identity_unresolved` — correct, since the probe actor has no canonical
identity link. It is **not** a constant denial: driven down different code paths
it emits different reasons (`national_facility_id=""` or `None` →
`ehr_facility_scope_unavailable`), two distinct reasons across three inputs. The
physical schema also enforces the identity spine — seeding a link with a
non-existent `canonical_account_id` is rejected by
`niam_legacy_account_links_canonical_account_id_fkey`.

**Its data layer is broken:** past the gate it reads `ehr_clinical_notes`, which
is absent. Hence PARTIAL, not REAL and not BROKEN.

Its read response is also the only one in the file behind a field allowlist
(`_clinical_note_read_response`), which is why it is the one serialising path not
exposed to IA-005.

**Not proven:** that the gate can ever reach `ALLOWED`. Doing so needs a full
identity spine (account → identity → person → assignment → policy → facility →
organization → tenant → both scope bindings). That traversal was not performed.
The allow path is **UNKNOWN**. Only the deny paths are VERIFIED.

## 9. Audit coverage of the surface

All 51 write operations carry `@audit_log` (NR-082, this lane, commit `7ac18fae`).
That is structural coverage; it was **not** exercised end-to-end against the head
database, because no write can reach its table there.

In the SQLite code-path run 16 audit rows were written, confirming the decorator
fires and commits on paths that complete. One consequence is recorded for
whoever creates the schema: `AuditLog.resource_id` is `INTEGER` while EHR ids are
`String(26)` ULIDs. The decorator routes non-numeric ids to
`details["record_id"]` via `_numeric_or_none()`, so no ULID is handed to that
column — but **SQLite would have accepted one silently and PostgreSQL would
not**, so this is called out rather than left to a future integration.

## 10. Infrastructure instability — recorded separately from application defects

Per instruction, infrastructure events are kept out of the defect counts.

| event | detail |
|---|---|
| PostgreSQL restart | once, at the start of this phase (`pg_postmaster_start_time` = 07:09:15 UTC); uptime 24 m at the close |
| PostgreSQL loss **during** a probe | **none** — `pg_isready` passed in every execution context |
| runs voided by infrastructure | **none in RB-3** |

Two probe-harness artifacts, which are **not** application defects:

1. In-memory SQLite (`:memory:`) is per-connection, so a `sessionmaker` opening a
   second connection saw `no such table: lab_users`. Fixed by using a file-backed
   SQLite database. Any earlier reading of that run is void.
2. In the SQLite code-path run the clinical-gate path raised
   `OperationalError: no such table: niam_legacy_account_links`, because the NIAM
   tables were not created in the scratch database. That path's real evidence is
   §8, taken against PostgreSQL.

One method error of my own, corrected: the first probe ran against
`/home/user/gula-p02-proof` (`ce097a0c`) rather than the audited lane. Re-run
against `/home/user/gula-audit`; both give 85 × `500` + 1 × `403`.

## 11. Claim ledger

| claim | state |
|---|---|
| 54 paths / 86 operations served under `/ehr`, unconditionally | **VERIFIED** |
| 0 of 86 operations return clinical data from the proven head DB | **VERIFIED** |
| 85 of 86 fail with `UndefinedTable`; 1 returns `403` | **VERIFIED** |
| all 19 required tables absent from the head DB | **VERIFIED** |
| no migration in the chain creates any of the 19 | **VERIFIED** |
| `national_patients` appears in migrations only as a guarded FK target | **VERIFIED** |
| every operation resolves to a real service + model (no stubs) | **VERIFIED** |
| the service layer works when the schema exists | **VERIFIED (SQLite only)** |
| IA-005: `to_dict()` returns `MetaData` for a `metadata` column | **VERIFIED** |
| IA-005 exposes 59 of 86 `/ehr` operations | **VERIFIED (static, runtime-validated 4/4)** |
| IA-005 predates NR-086 | **VERIFIED** (a one-table `MetaData` already recurses) |
| IA-005 blast radius = 124 tables carry a `metadata` column | **VERIFIED** |
| how many non-`/ehr` **routes** IA-005 breaks | **UNKNOWN** — not measured |
| the clinical read gate's authorization layer executes and discriminates | **VERIFIED** |
| the clinical read gate can reach `ALLOWED` | **UNKNOWN** — allow path not traversed |
| 51/51 write operations carry `@audit_log` | **VERIFIED** (structural) |
| audit rows land for `/ehr` writes on PostgreSQL | **UNKNOWN** — unreachable |
| the `/ehr` code is PostgreSQL-correct once migrated | **UNKNOWN** — SQLite cannot establish it |

## 12. What RB-3 does not prove

* Not that creating the 19 tables makes the surface work. IA-005 alone keeps 59
  of 86 operations failing, and PostgreSQL type strictness is untested.
* Not that the remaining 27 operations are correct — 50 of them were observed only
  on their `404` not-found branch, and 3 of the 8 `200`s were empty result sets
  (`/ehr/encounters/{id}/clinical-notes`, `/ehr/patients/{id}/timeline`), which is
  a vacuous pass, not a success-path proof.
* Nothing about tenant isolation on these paths. `_get_patient` filters
  `national_patients` by `lab_id`, but with the table absent the filter has never
  executed against real data. Tenant-isolation correctness here is **UNKNOWN**.
* Nothing about the other 317 absent ORM tables from RB-2 outside this surface.

## 13. Findings raised

| id | severity | statement | state |
|---|---|---|---|
| **IA-005** | **P0** | `shared/models/base.py::to_dict()` reads `getattr(self, col.name)`, so for any column named `metadata` it returns the declarative `MetaData` registry instead of the column value; FastAPI then recurses until the stack is exhausted. 59 of 86 `/ehr` operations exposed; 124 tables platform-wide carry the column. | OPEN — not fixed in this lane (shared surface + response-shape change) |
| **IA-006** | **P1** | The `/ehr` domain (18 tables) and `national_patients` have no migration anywhere in the chain, yet 86 operations are served over them unconditionally, with no feature flag. Every one fails closed with `500`. | OPEN — remediation requires the schema decision that RB-2 escalated |
| IA-004 | P1 | `20260811_0002` skips four FKs whenever the target table is absent, silently. RB-3 confirms the `national_patients` arm independently. | OPEN — unchanged, **not fixed here as instructed** |

## 14. Remediation options — presented, not taken

RB-3 is an audit. No remediation was applied. Three options, for the owner:

1. **Migrate the domain.** Author migrations for `national_patients` + the 18 EHR
   tables, then fix IA-005, then re-run this probe against PostgreSQL. This is the
   only option that makes the surface work. It is a schema change on the scale
   RB-2 escalated and needs explicit approval; it also overlaps the 4 Category-G
   orphans and the 369 dormant tables still awaiting an owner statement.
2. **Fail honestly at the boundary.** Leave the schema absent but stop serving 86
   operations that can only 500 — gate the router behind an explicit flag,
   defaulting off, so a fresh deployment does not advertise a clinical API it
   cannot serve. Smaller, reversible, and it removes the false capability signal
   without touching clinical semantics. It does **not** deliver the capability.
3. **Fix IA-005 alone.** Worth doing on its own merits for the other 123 tables,
   but it changes nothing for `/ehr` while the tables are absent.

Option 1 and option 2 are mutually exclusive as a first step. Option 3 is
independent of both and is the one with value outside this surface.

**Recommendation:** fix IA-005 first, as its own change with its own proof, since
it is a live defect on 124 tables and independent of the schema decision. Then
decide 1 vs 2 for `/ehr` as an ownership question, not an engineering one.

Not proposed, and not to be inferred: creating the 19 tables to make the count
look closed, deleting the ORM models, or weakening any test or gate.

### A guard, specified but deliberately not committed

IA-005 wants a regression test, but the only honest form of it fails today, and
committing a failing test changes what the quality gate reports. The assertion is
therefore specified here so it can land **with** the fix rather than before it:

```python
# for every mapped class whose table has a column named "metadata"
row = model.to_dict()
assert not isinstance(row["metadata"], MetaData), (
    f"{model.__name__}.to_dict() returned the ORM schema registry, not the column value"
)
# and the encoder must terminate
jsonable_encoder(row)
```

Parametrised over the 124 tables carrying the column, this fails now and passes
once `to_dict()` resolves through the mapped attribute instead of `col.name`. No
test was weakened, skipped or disabled to produce this report.

---

*RB-3 complete. RB-5, RB-4 and RB-6 not started.*
