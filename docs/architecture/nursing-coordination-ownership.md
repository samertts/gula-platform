# Nursing Coordination Endpoints — Ownership (NR-033)

**Batch:** BATCH-3.1 · **Finding:** NR-033 (P2) · **Status:** VERIFIED (trace and
classification); execution deferred.
**No table was created. No migration was written.**

---

## 1. What these endpoints do today

All eight `/nursing/coordination/*` routes call a `CareCoordinatorService` method
that builds a dictionary, writes one audit entry, and returns the dictionary.
No domain state is created. Every response carries a **status the platform has no
way to advance**: `sent`, `pending`, `ordered`, `created`, `planned`,
`handed_over`.

That is the defect, and it is worse than "does not persist": a nurse who raises a
referral receives `200` and a status of `created`, and nothing exists for anyone
to act on. Until BATCH-3 these endpoints additionally raised on every call — their
`log_action` arguments were miscalled, so psycopg2 was handed a dict for `lab_id`.
They execute as designed now, which is what makes the design question live.

Zero frontend consumers were found in `frontend-v3`, `mobile`, `mobile-expo` or
`client`.

## 2. Classification

Canonical owners were checked against the physical schema, not against names.

| # | Endpoint | Represents | Canonical owner (exists today) | Classification |
|---|---|---|---|---|
| 1 | `/coordination/physician-message` | clinician-to-clinician message | **`nhdw_hospital_messages`** — sender_id, recipient_id, subject, body, priority, is_read, requires_acknowledgment, acknowledged_by; lab-scoped INTEGER; ORM `app/nhdw/models.py:290` | **MOVE TO EXISTING DOMAIN** |
| 2 | `/coordination/lab-request` | request for specimen collection | **`lab_orders`** — the platform's core LIMS order | **MOVE TO EXISTING DOMAIN** |
| 3 | `/coordination/radiology-request` | request for an imaging exam | **`radiology_orders`** — ORM `app/radiology/models.py:41` | **MOVE TO EXISTING DOMAIN** |
| 4 | `/coordination/pharmacy-request` | request for a medication | **`pharmacy_prescriptions` + `pharmacy_prescription_items`** (see NR-032) | **MOVE TO EXISTING DOMAIN** |
| 5 | `/coordination/discharge-plan` | prospective discharge planning | `nhdw_discharges` — admission_id, patient_id, discharge_date, discharge_summary, follow_up_* | **MOVE — PARTIALLY VERIFIED** (see §3) |
| 6 | `/coordination/referral` | referral to another specialty | **none** | **BLOCKED** |
| 7 | `/coordination/family-communication` | record of talking to a family member | **none** | **PERSIST IN NURSING** |
| 8 | `/coordination/home-care-handover` | handover to a home-care provider | **none** (`nursing_shift_handovers` is shift-to-shift, not discharge-to-home) | **BLOCKED** |

**None is KEEP AS STATELESS.** Every one of the eight asserts a status, and a
status with no owner is a claim the platform cannot honour.

## 3. Why discharge-plan is only partially verified

`nhdw_discharges` records a discharge that **happened** (`discharge_date`,
`discharge_summary`, `discharged_by`). `plan_discharge` describes one that is
**intended** (`expected_date`, `discharge_needs`, status `planned`). Those are
different clinical objects, and conflating them would let a plan be read as an
event. Either `nhdw_discharges` gains an explicit planned/actual distinction, or
discharge planning is a separate table. **That is a clinical-owner decision, not
an engineering one** — recorded, not decided.

## 4. Why referral and home-care handover are BLOCKED, not "create a table"

Both cross an organisational boundary — a referral goes to another specialty or
facility, a home-care handover to an external provider. Modelling either requires
the Organization/Facility ownership question (NR-006) and the provider-directory
question to be settled first. Creating a Nursing-local `nursing_referrals` table
would make Nursing the owner of a cross-organisation clinical object, which
contradicts the ownership matrix. **Do not create these tables in Nursing.**

`family-communication` is different: it is a note about a conversation at the
bedside, made by a nurse, scoped to one laboratory's episode of care. That is
genuinely Nursing's, and it is the one of the eight that could be persisted
inside the domain without an ownership question — most cheaply as a
`nursing_notes` row with a dedicated `note_type`, since that table already exists,
is reconciled, and carries `patient_id`, `content`, `written_by` and `written_at`.

## 5. Intersections recorded (not implemented)

**Visit / Encounter** — all eight take a `patient_id` and none takes an encounter
or visit. If the coordination objects move to their canonical owners, four of
those owners (`lab_orders`, `radiology_orders`, `pharmacy_prescriptions`,
`nhdw_discharges`) are episode-scoped in the Visit design. This is another domain
waiting on the Visit decision. No second Visit model was created.

**Organization / Facility** — referral and home-care handover depend on NR-006.

**State machines** — the six fabricated statuses (`sent`, `pending`, `ordered`,
`created`, `planned`, `handed_over`) are **SYNTHETIC**: emitted by code, held by
no table, advanced by nothing. They are carried to the state-ownership batch and
should be attributed to the receiving domain's own vocabulary when each endpoint
moves — not re-created in Nursing. The global state registry was not modified.

## 6. Tenancy and authorization

All eight require `get_current_user` and pass `current_user.lab_id` into the
audit entry. There is no data to isolate, so tenant filtering is not yet
applicable; when each endpoint moves, it inherits the receiving domain's existing
lab scoping. **No new authorization mechanism is proposed.** Audit attribution is
correct as of BATCH-3 (`user_id` and `lab_id` now reach their own columns).

## 7. Recommended sequence

**COORD-001** (needs approval, one domain at a time, in this order):
1. `physician-message` → `nhdw_hospital_messages`. Lowest risk: the target table
   matches the payload field for field.
2. `lab-request` → `lab_orders`, `radiology-request` → `radiology_orders`.
3. `pharmacy-request` → Pharmacy, after MED-001 settles NR-032.
4. `family-communication` → a `nursing_notes` row with a dedicated `note_type`.
5. `discharge-plan`, `referral`, `home-care-handover` → hold. They need the
   clinical owner (plan vs event) and NR-006 (organisation boundary) first.

Until an endpoint moves, its response should not assert a workflow status it
cannot honour. Changing those responses is an API contract change and is left to
COORD-001 rather than applied here.
