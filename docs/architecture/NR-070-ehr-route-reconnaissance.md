# NR-070 — reconnaissance of the 115 EHR routes

**Status:** RECONNAISSANCE COMPLETE. No authorization was changed.
**Measured:** 2026-09-26, by AST over `app/routes/ehr.py` (86 routes) and
`app/routes/ehr_fhir.py` (29 routes).
**Why no change:** the authorization question needs a per-resource decision, and
bulk-assigning one permission across 115 clinical routes is explicitly the wrong
move. What this pass does is make that decision cheap to take.

---

## 1. The effective authorization path, not the decorator count

| | value |
|---|---|
| routes | **115** (55 write, 60 read) |
| routes with an authentication dependency | **115 of 115** |
| routes with `require_permission` | **0 of 115** |
| distinct dependency expressions across all 115 | **2** — `get_current_user` (115), `get_db` (114) |
| router-level `dependencies=[...]` | none on either router |
| mount-level guard | none — `app.include_router(r.router)` with no arguments |

So the framing matters: these routes are **authenticated but not authorized**.
Every one of them admits any logged-in user of any role. "Unauthenticated" would
be wrong, and so would "unprotected" — the tenant boundary is largely present
(§3). What is absent is any role or permission check, on reads and writes alike.

Checked, not assumed: `factory.py:570` mounts both routers inside a bare
`include_router` loop, and neither `APIRouter(...)` carries `dependencies`.

## 2. Two things this scan got wrong first, and why they are recorded

Both are the reason the brief says to verify the effective path rather than grep
for a pattern.

* **Audit is decorator-provided on three routes.** A regex for `log_action`
  reported 0 of 55 writes audited. Three of them carry `@audit_log(action=...)`,
  which writes the row from a wrapper. Corrected count in §4.
* **Those same three routes have no `db.commit()` in their body, and that is
  correct.** The `@audit_log` decorator commits after writing the audit row, so
  the clinical mutation and its audit row land in one transaction — and if the
  audit write fails, the dependency rolls the mutation back. `app/audit/__init__.py`
  says so in a comment: *"Audit integrity takes precedence over mutation
  availability."* Reported as a missing-commit defect on first reading; it is not
  one, and this note exists so the next reader does not repeat the mistake.

## 3. Tenant boundary

| | reads | writes |
|---|---|---|
| calls `_get_patient(db, patient_id, current_user.lab_id)` | — | — |
| **combined: 85 of 115 routes** | | |
| routes not calling it | **30** | |

`_get_patient` delegates to `ehr_service.get_national_patient_or_404(db,
patient_id, lab_id)` — a 404-on-wrong-tenant helper, which is the right shape.

The 30 that do not call it are **not therefore unscoped.** Verified by reading:
`fhir_population_summary` filters `LabOrder.lab_id == current_user.lab_id`
directly and returns aggregates only, with a docstring saying so. Absence of the
helper is not absence of tenancy, and each of the 30 needs reading individually
before any claim. Mostly they are FHIR reads (`fhir_read_patient`,
`fhir_read_condition`, `fhir_search_*`, `fhir_search_provenance`) and
`GET /encounters/{id}/clinical-notes`.

**Not claimed:** that the 85 are correctly isolated, or that the 30 are not.
Tenant-field presence is not tenant isolation.

## 4. Audit — the most serious thing found, and it is not the authorization gap

Counting the decorator properly:

| | writes (55) | reads (60) |
|---|---|---|
| `@audit_log` decorator | **3** | 0 |
| inline `log_action` / `audit_service` | 0 | 0 |
| **neither** | **52** | 60 |

**52 of 55 clinical write routes write no audit row by any mechanism.** CLAUDE.md
Security Invariant #2 is *"All mutations MUST write to the audit log (`AuditLog`
model + hash chain)."*

The 52 cover: clinical notes, allergies, medication statements, medication
requests, medication dispenses, **medication administrations**, care plans, care
plan goals and activities, problem list, conditions, diagnoses, family history,
social history, risk factors, immunizations and attachments — create, update and
soft-delete for each. Plus `POST /fhir` (`fhir_batch`), the batch/transaction
endpoint.

Reads being unaudited is a policy question, not an invariant breach. Writes are
an invariant breach.

This is registered separately as **NR-082**, because it is mechanical where the
authorization question is not: the platform already has the mechanism, uses it on
three routes in this very file, and it commits atomically with the mutation. One
decorator line per route, with a per-resource action name.

## 5. Consent and break-glass

| signal | reads | writes |
|---|---|---|
| consent consulted | **0 of 60** | **0 of 55** |
| break-glass / emergency access | **0 of 60** | **0 of 55** |
| clinical read gate | 1 of 60 | 0 of 55 |

Zero across the whole surface. The platform *has* these mechanisms — there is a
consent model, a break-glass table, and `ClinicalNursingTaskReadGate` in the
nursing domain — and the EHR, which is the most consent-sensitive surface it
has, uses none of them. Whether it should is the per-resource decision this
document is input to, not something to infer.

## 6. Deletes, against the PERMANENT DATA RULE

18 DELETE routes. **All 18 are soft deletes**, verified by reading:

* 17 call a `soft_delete_*` service helper;
* `fhir_delete_resource` sets `is_deleted`, `deleted_at` and `deleted_by`
  directly via `hasattr` checks — which a `soft_delete_` regex misses, and which
  is why it was read rather than counted.

So the rule *"GULA does not operationally delete data or business entities"* is
honoured on this surface. Recorded because `DELETE /medication-administrations/{id}`
looks like a hard delete and is not.

## 7. The classification the decision needs

Per resource family rather than per route, because the routes come in
create/update/soft-delete triples over one resource:

| resource family | routes | tenant via helper | audit | consent | the decision |
|---|---|---|---|---|---|
| clinical notes | 3W + reads | yes | **no** | no | who may write a note; are notes consent-gated |
| allergies | 3W | yes | **no** | no | safety-critical read for everyone; write for whom |
| medication statements / requests / dispenses / **administrations** | 12W | yes | **no** | no | prescriber vs dispenser vs administrator are different roles; BCMA's five rights (ADR-005) implies the administration route is nurse-scoped |
| care plans + goals + activities | 9W | yes | **no** | no | who authors a plan vs records against it |
| problem list / conditions / diagnoses | 9W | yes | **no** | no | diagnosis is a physician act in most regimes |
| family / social history / risk factors | 9W | yes | **no** | no | intake data; plausibly broader write scope |
| immunizations | 3W | yes | **no** | no | national programme overlap (care_continuum has its own) |
| attachments | 3W | yes | **no** | no | document upload; scanning and size limits are separate |
| FHIR generic create/update/delete | 3W | yes | **yes** | no | one endpoint spanning every resource type — a single permission here would be the coarsest possible grant |
| FHIR batch/transaction | 1W | — | **no** | no | executes many writes in one call; permission and audit must be per entry |
| FHIR reads / searches | ~26R | 30 lack the helper | no | no | read scope, and whether aggregate endpoints are exempt |

**Explicitly not done, and not to be done as a batch:** assigning one permission
across 115 routes. `POST /diagnoses` and `POST /social-history` are not the same
authorization question, and `POST /fhir/{resource_type}` is every question at
once.

## 8. What should happen next, in order

1. **NR-082 first** (audit on the 52). Mechanical, precedented in this same file,
   commits atomically, and it is a stated invariant rather than a judgement call.
   It also makes every later authorization decision observable.
2. **Then the resource-family permission matrix** in §7, one row at a time, with
   ADR-005's role separation (prescriber / dispenser / administrator) as the
   input for the medication families.
3. **Then consent and break-glass**, which is an architectural question about the
   dormant National ABAC layer and not a route-level fix.

`ADR-009` is the recorded input for step 2; the generic FHIR endpoints should be
decided last, because a permission on `POST /fhir/{resource_type}` constrains
every resource family at once.
