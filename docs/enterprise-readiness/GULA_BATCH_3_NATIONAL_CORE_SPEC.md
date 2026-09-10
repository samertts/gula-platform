# BATCH-3 — National Core Specification

**Specification only. Not implemented. No migrations created.**
2026-09-10 · `production_ready: false`

Two independent analyses converged on this batch. BATCH-2 reached it from
foreign-key direction; the global capability discovery reached it from clinical
value. A third has now joined them: `alembic revision --autogenerate` cannot run
at all because of this same gap (NR-023).

## 1. Why this is first

Four of the five most-depended-on tables in the repository do not exist:

| Table | Inbound references | Physical |
|---|---|---|
| `national_practitioners` | 58 | no |
| `national_citizens` | 51 | no |
| `national_patients` | 51 | no |
| `national_encounters` | 42 | no |
| `national_facilities` | 44 | **yes — and mapped by two bases** |

`care_continuum` (45/45 tables), `ehr` (16/18), `nursing` and `national_data`
all declare foreign keys into this core. Nothing above it can be built, and
autogenerate cannot emit a migration for anything while it is missing.

## 2. Canonical ownership — decided

Per the authorising decision, and recorded in
`GULA_CANONICAL_ARCHITECTURE_DECISIONS.md`:

| Entity | Canonical owner | Consequence |
|---|---|---|
| **Patient** | **Core `patients`** (`app.models.base.Base`, physical, 22 inbound refs) | `national_patients` must **not** become a second transactional owner |
| **Facility** | **Core Facility** for operations | a national directory may exist as a registry/projection only |
| Practitioner | open — see §7 | `national_practitioners` has 58 references and no owner decision |
| Encounter | open — see §7 | `national_encounters` has 29 reachable operations |

A national read model is permitted and must be classified `PROJECTION`. A
projection may be read from and rebuilt; it may never be written to as a source
of truth, and no foreign key may point *at* it.

## 3. Entities in scope

Measured state, not aspiration:

| Entity | Table | Physical | Scope | Reachable ops | PK today |
|---|---|---|---|---|---|
| Citizen | `national_citizens` | no | GLOBAL | 10 | `VARCHAR` |
| Patient (national view) | `national_patients` | no | TENANT | 0 | `VARCHAR` |
| Practitioner | `national_practitioners` | no | FACILITY | 0 | `VARCHAR` |
| Encounter | `national_encounters` | no | TENANT | 29 | `VARCHAR` |
| Department | `national_departments` | no | FACILITY | 0 | `VARCHAR` |
| Facility | `national_facilities` | **yes** | GLOBAL | 0 | `VARCHAR` |
| Organization | `national_organizations` | no | GLOBAL | 0 | `VARCHAR` |

**Every one keys on `VARCHAR`** — the Generation-B shape Pharmacy was moved off
in P0-2. Building them as they stand would recreate the defect P0-2 spent four
milestones removing.

## 4. Identity model

Follow the settled Pharmacy contract exactly; it is the reference
implementation and is not reopened:

- internal `INTEGER` primary key, never exposed by an API;
- immutable public `UUID4` — the only identifier a response may carry;
- mutable business codes (facility code, licence number) that are never keys
  and never join targets;
- external identifiers from other domains stay `String(26)` and are not
  converted merely because this domain uses integer keys.

The national ID and health ID carry the existing SNDHS rules: encrypted at
rest, dual-read tolerant of `NULL`, never plaintext.

## 5. Tenancy

| Entity | Scope | Rule |
|---|---|---|
| Citizen, Facility, Organization | GLOBAL | national reference data — a tenant filter here would be **wrong** |
| Patient, Encounter | TENANT | every query filters `lab_id`; no exceptions |
| Practitioner, Department | FACILITY | scoped through facility, which is itself global |

NR-021 is the cautionary case: nine reachable methods on one service queried
without a tenant filter, on tables that all carried `lab_id`.

## 6. Audit, authorization, migration, API, clients

- **Audit** — every mutation writes to the SHA-256 hash-chained audit log. No
  new mechanism; the existing one is one of GULA's genuine strengths.
- **Authorization** — RBAC + ABAC as they stand. Do not introduce a parallel
  model. NR-021 was fixed by *reusing* the existing `_lab_id` helper.
- **Migration** — fail-closed, in the M3/M4 pattern: refuse in both directions
  unless the affected tables are empty, reporting per-table counts rather than
  casting. Every migration idempotent, every new column nullable or defaulted.
- **API** — public UUIDs only; explicit response builders so an internal integer
  key cannot leak, exactly as M4 did for Pharmacy.
- **Clients** — no existing client contract changes, because none of these
  endpoints can currently return a row. Web, Android, iOS and desktop are
  unaffected until the endpoints work; that is when versioning matters.

## 7. Blockers and open decisions

**Blocking, must be answered before implementation:**

1. **Is `national_patients` the same entity as core `patients`?** The
   authorising decision names Core Patient canonical. What remains is whether
   `national_patients` becomes a `PROJECTION` of it, or is retired outright.
   Its own evidence — 0 reachable operations, 51 inbound references — supports
   projection-or-retire, not independent existence.
2. **Practitioner.** 58 inbound references, no owner decision, and a core
   `lab_users` table already exists with 21. Same question as Patient, unanswered.
3. **`national_facilities` (NR-006).** Physical and mapped by two bases. Which
   base keeps it, and does the other become a projection?

**Blocking but already answered elsewhere:** NR-023 — autogenerate cannot run
until this core exists. That is not a reason to delay; it is a reason this batch
must be written by hand and verified against a clean database.

## 8. Acceptance criteria

1. Every entity in §3 exists physically with an `INTEGER` key and a public `UUID4`.
2. `GULA-SCHEMA-003` findings fall by at least the 5 core tables; `GULA-SCHEMA-004`
   falls materially as cross-base foreign keys resolve.
3. `alembic revision --autogenerate` runs to completion (NR-023 closes).
4. Tenant isolation tests pass for every TENANT-scoped entity, in both directions.
5. Migration refuses on non-empty tables, proven in both directions.
6. No API returns an internal integer key.
7. No entity in §3 has two owners.

## 9. Explicitly out of scope

EHR, clinical, care_continuum, nursing, governance, national_data — every one
of them waits. Building any of them inside this batch would reintroduce the
coupling this batch exists to remove.
