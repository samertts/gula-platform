# Audit Actor Attribution — Full Census of `log_action` in `backend/app/`

**Generated:** 2026-09-24 · **Branch:** `claude/p0-2-pharmacy-reconciliation`
**Register findings:** NR-158 (LIMS, fixed), NR-159 (hospital, fixed), NR-160 (the
pattern), NR-161 (financial, blocked), NR-162 (role vocabularies)

This document records a complete, measured classification of every audit-writing
call site in the backend monolith. It is not a sample. Every one of the 188
reachable instances was inspected and given a verdict.

---

## 1. Why the actor's role is a security property, not metadata

An audit trail exists to answer one question after the fact: **was this action
within the actor's authority?** Identity alone cannot answer it. `user_id=101`
says who; only the role says what they were permitted to do at the moment they
did it.

This makes a *wrong* role strictly worse than a *missing* one. A NULL role is an
honest "unknown" and a reader knows to look elsewhere. A hard-coded literal is a
false statement that reads as fact — and in both cases found here it was false in
the direction that conceals a privilege problem, recording a privileged actor as
a routine one.

## 2. Method

An AST pass over every `.py` file under `backend/app/`, matching each `Call`
whose function name is `log_action`, and resolving the `user_role` argument from
either the keyword or positional index 5 (`log_action`'s sixth parameter).

Each site was then classified:

| Class | Meaning |
|-------|---------|
| `EXPR` | the role is derived from an expression — the correct shape |
| `LITERAL` | a hard-coded constant string |
| `OMITTED` | `user_role` not passed; `AuditLog.user_role` takes NULL |

The 33 `OMITTED` sites were classified a second time by whether a role is
*reachable* at the call site, by inspecting the innermost enclosing function's
parameters for `current_user`, an explicit role parameter, or only `user_id`.

## 3. Census

| Class | Before repair | After repair |
|-------|--------------:|-------------:|
| `EXPR` | 145 | **150** |
| `OMITTED` | 33 | 33 |
| `LITERAL` | 10 | **5** |
| **Total** | **188** | **188** |

Nine falsifying literals were repaired: four in `app/lims/services.py`
(`"lab_tech"`, NR-158) and five in `app/services/hospital_service.py`
(`'hospital_staff'`, NR-159).

## 4. The five remaining literals — all inspected, none falsifying

| Site | Value | Verdict |
|------|-------|---------|
| `routes/citizen_portal.py:194` | `'citizen'` | **Correct by construction.** Both lookup branches filter `User.role == "citizen"`, so any row reaching the audit line is a citizen. *P3 note:* on this failure branch no row may have matched at all, yet the row still asserts a role. Authentication logic — recorded, not altered (CLAUDE.md requires approval). |
| `routes/citizen_portal.py:221` | `'citizen'` | **Correct by construction**, same query constraint. |
| `routes/register.py:382` | `'citizen'` | **Correct by construction.** Self-registration; the subject was created moments earlier and `User.role` defaults to `citizen`. |
| `routes/register.py:652` | `'doctor'` | **Correct, duplicated.** The `User` row is created 12 lines above with `role="doctor"`. `user_role=doctor.role` would be self-evidently correct. P3 hygiene. |
| `services/patient_service.py:464` | `'system'` | **OPEN (P2).** An `mpi_resolve_failed` diagnostic that names a human `user_id` but overwrites that human's role with `'system'` — a value in neither role vocabulary. A genuine, minor misattribution on an exception path. |

## 5. The 33 omitted roles — classified by actor reachability

| Verdict | Count | Sites |
|---------|------:|-------|
| **Correct by construction** — no authenticated actor exists, so NULL is the true value | 4 | `routes/password_reset.py:53,76` (`user_id` is the *subject*, not the actor); `services/order_service.py:759,858` (public token-authenticated reads) |
| **BLOCKED — human approval required** | 4 | `financial/routes.py:313,368`; `financial/services.py:131,247` — see NR-161 |
| **OPEN coverage gap** — role must be threaded from the caller | 25 | see below |

### The 25 open sites

| Domain | Count | Notes |
|--------|------:|-------|
| `app/nursing/` | 15 | `coordination.py` ×8, `medication.py` ×3, `services.py` ×3 |
| `app/pharmacy/` | 4 | `inventory.py` ×3, `services.py` ×1 (two are `_audit()` helpers — the role must arrive from their callers) |
| `app/nhdw/services.py` | 3 | `complete_clinical_task`, `review_care_plan`, `resolve_alert` |
| `app/blood_bank/application/service.py` | 1 | `_audit()` helper |
| `app/governance/repositories/base.py` | 1 | `_write_audit()` |
| `app/audit/__init__.py` | 1 | a wrapper — inherits from its caller |
| `app/services/hospital_service.py:109` | 1 | `deactivate_hospital` |

**Nursing medication is the highest-value remaining cluster.**
`record_five_rights_attestation`, `record_administration` and
`electronic_signature` are exactly the records whose evidential value depends on
knowing the signer's authority.

## 6. The canonical source, and why it can be trusted

`current_user.role`.

`get_current_user` does **not** take the role from the token. It calls
`resolve_token_subject(db, payload)`, which loads the live subject row, and then
compares the token's `perm_ver` against the authoritative permission version,
refusing the request on a mismatch. The role is therefore a database column
belonging to the authenticated subject, re-read on every request, and a token
minted before a role change is rejected rather than honoured.

It is also the source `ClinicalCommandGuard` already used in both repaired
domains. Each repair made the service layer agree with the guard beside it
instead of keeping a second, divergent convention.

## 7. The control: keyword-only, no default

In both repairs `actor_role` is declared after `*` with **no default**, so a call
site that forgets it raises `TypeError` immediately.

This is not stylistic. Any default would reinstate the exact defect being fixed —
a plausible-looking role silently standing in for the real one. The control
proved itself on landing: it surfaced seven stale call sites in
`tests/test_emergency_surgery_workflow_p0.py` that no grep would have found.

## 8. Guards

| Guard | Covers |
|-------|--------|
| `backend/tests/test_lims_audit_actor_is_server_derived.py` (5 tests) | NR-158 |
| `backend/tests/test_hospital_audit_actor_is_server_derived.py` (6 tests) | NR-159, and pins NR-162's vocabulary claim |

Each guard carries a structural test (the parameter is keyword-only with no
default), a source ratchet that filters comment lines, a positive control (the
role the wrong constant happened to resemble is asserted, not assumed), and the
finding itself.

There is **no platform-wide ratchet yet**. One would have to allow-list the eight
correct-by-construction sites together with the reason each is correct;
otherwise it would either fail permanently or be weakened into vacuity.

## 9. Negative proof (NR-159)

Restoring `user_role='hospital_staff'` in `assign_bed` alone fails three of the
six tests — the source ratchet, the technician positive control, and the
administrator finding — while the structural and wiring tests correctly continue
to pass, because the signature and the routes are untouched and only the written
row is falsified. The file was then restored byte-identically (sha256 verified)
and all 10 tests across both hospital files pass.

## 10. Open items requiring a decision from an owner

1. **NR-161** — may audit-actor corrections be made under `app/financial/` during
   Phase A? Two of the four are one-line changes.
2. **NR-162** — which role vocabulary is canonical, and should writing a role
   outside it raise rather than fail silently closed?
3. **NR-160** — the 25 open sites, nursing medication first.
