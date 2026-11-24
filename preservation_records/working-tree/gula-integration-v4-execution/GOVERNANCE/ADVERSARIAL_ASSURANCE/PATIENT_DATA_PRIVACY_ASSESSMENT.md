# Team A Independent Adversarial Patient-Data Privacy Assessment — GULA Integration

**Program:** GULA Extreme Adversarial Audit & Remediation Program  
**Team:** Team A (independent adversarial auditor)  
**Lane:** HEALTHCARE PATIENT DATA PRIVACY  
**Date:** 2026-11-18  
**Repository:** `gula-integration`  
**Branch:** `integration/gula-unification-v1`  
**HEAD reviewed:** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Sibling repository:** `gula-platform` @ `f478676b6fc375338648dde46fbf076c015a3f91` (read-only; no files changed)

---

## 0. Authority and constraints observed

- Read-only assessment: no source/config/git/database/network changes; no exploitation.
- No real patient data was accessed or created.
- No owner-gated decision was modified: **HOLD**, **MPI REJECT**, **MP-001**, **ODR-001**, **ODR-002**, **ODR-003**, **ODR-004**, **D-020**, **D-021**, **ADR-A** through **ADR-J**, **AUD-02**, **AUD-07**, **AUD-16** remain as recorded.
- No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded. Team C owns promotion.
- Findings use the required lifecycle state `DISCOVERED`; control statements use only the permitted vocabulary.
- The disclosed **NR-011 FK test co-collection failure** is not re-reported.

---

## 1. Executive privacy verdict

**Privacy verdict: NOT CERTIFIED. Release decision: HOLD preserved.**

Five privacy findings are recorded: **4 HIGH**, **1 MEDIUM**, **0 CRITICAL**, **0 LOW**. The most material privacy finding is:

- **AUD-PRV-001** — cross-facility PHI disclosure through the national-ID duplicate-detection response on patient creation.

Other material gaps: consent enforcement is present on only one citizen-read endpoint while break-glass is a client header; `force_create` is an unauthenticated-by-policy duplicate bypass; raw PII is written into the tamper-evident audit log; and minor/guardian linkage is optional rather than enforced.

---

## 2. PHI data-flow reviewed (static)

1. `POST /patients` (`backend/app/routes/patients.py:178-207`) accepts full name, phone, birth date, gender, email, national ID, family ID, `force_create`, and `guardian_id`.
2. `create_patient()` (`backend/app/services/patient_service.py:128-204`) hashes national/family IDs, optionally checks duplicates, optionally validates a guardian, writes a `Patient` row, resolves MPI identity, and writes an audit row.
3. `patient_to_dict()` (`backend/app/services/patient_service.py:53-68`) serializes full name, phone, birth date, gender, email, health ID, minor flag, guardian ID, and creation time.
4. Duplicate detection (`backend/app/services/patient_service.py:324-345`) queries by `national_id_hash` without a lab filter and returns `patient_to_dict(existing)` inside a 409 error body.
5. Consent enforcement (`backend/app/security/consent_dep.py:74-195`) exists, but a read-only usage scan found only one production use: `backend/app/services/mpi/api.py:568-572`.
6. Audit details are serialized verbatim into `AuditLog.details` (`backend/app/services/audit_service.py:184-212`).

---

## 3. Observed privacy-control status (not a certification)

| Privacy control | Observed status | Basis |
|---|---|---|
| National ID / family ID hashed at rest | `IMPLEMENTED` | `patient_service.py:145-147`; `models/patient.py:29,32` |
| Lab-scoped patient reads | `IMPLEMENTED` for `get/list` paths | `patient_service.py:71-125` |
| Cross-lab duplicate lookup isolation | `BLOCKED` | AUD-PRV-001 |
| Consent-gated PHI access | `INTEGRATED` on one route only | `mpi/api.py:568-572` |
| Break-glass justification / approval | `NOT IMPLEMENTED` | `consent_dep.py:68-71,121-153` |
| Duplicate-create control | `BLOCKED` | AUD-PRV-003 |
| PII minimization in audit details | `BLOCKED` | AUD-PRV-004 |
| Minor/guardian enforcement | `NOT IMPLEMENTED` | AUD-PRV-005 |

---

## 4. Findings

### AUD-PRV-001 — Cross-facility PHI disclosure in national-ID duplicate response

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 8, Reproducibility 8, Exploitability 7, Affected users 7, Discoverability 6 → **7.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/services/patient_service.py:334-345` — when `nid_hash` is supplied, the query is `Patient.national_id_hash == nid_hash` with **no `Patient.lab_id == lab_id` filter**, and the error body includes `"existing_patient": patient_to_dict(existing)`.
- `backend/app/services/patient_service.py:324-331` — `_check_duplicates()` receives `lab_id`, but the national-ID branch does not use it.
- `backend/app/services/patient_service.py:53-68` — `patient_to_dict()` exposes full name, phone, birth date, gender, email, health ID, minor flag, and guardian ID.
- `backend/app/routes/patients.py:187-205` — the route passes the caller’s `lab_id` into `create_patient()` and returns the service error body to the client.
- `backend/app/models/patient.py:23` — the composite `(lab_id, national_id_hash)` index exists, showing lab-partitioned lookup was the intended model.

**Safe reproduction / falsification (static)**
1. Inspect `_check_duplicates()` at `patient_service.py:334-345`.
2. Observe the national-ID query lacks the tenant predicate that the phone query has at `:347-350`.
3. Observe the 409 response carries the full existing-patient DTO.
4. **Falsification:** show the national-ID query includes `Patient.lab_id == lab_id` and that cross-lab duplicates return only a non-identifying conflict marker (or that an approved MPI policy explicitly authorizes cross-lab disclosure).

**Root cause:** MPI-style global identity lookup was implemented inside a lab-scoped patient-creation path without tenant isolation or purpose limitation on the response.

**Impact:** A user at facility A who knows or discovers a patient’s national ID can receive identifying PHI from facility B, including name, phone, DOB, gender, email, health ID, and guardian link. This is a tenant-boundary PHI disclosure and a patient-linkage privacy harm.

**Remediation:** Scope the duplicate query by `lab_id` for local duplicates; route any national cross-facility match through the MPI consent/authorization layer; return only a conflict token such as `duplicate_reference` with no patient DTO; add a cross-facility negative test.

**Alternatives:** (a) Keep global duplicate detection but return only `exists: true`; (b) require an explicit, audited MPI disclosure permission and log purpose. Preferred: (a) for the create endpoint; (b) only in a dedicated MPI API.

---

### AUD-PRV-002 — Consent enforcement is effectively unwired, and break-glass is a client-supplied header

- **Severity:** HIGH
- **Likelihood:** HIGH
- **DREAD:** Damage 8, Reproducibility 9, Exploitability 8, Affected users 8, Discoverability 7 → **8.0**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/security/consent_dep.py:74-195` — `require_consent()` implements owner, emergency, and active-consent checks.
- `backend/app/security/consent_dep.py:68-71` — break-glass is triggered solely by `X-Emergency-Access: true`.
- `backend/app/security/consent_dep.py:121-153` — any caller with `role == "doctor"` who sets the header is allowed and only an audit row is written; no justification, duration, approval, or case linkage is required.
- `backend/app/security/consent_dep.py:53-65` — owner bypass depends on an attached `citizen_ulid` attribute that the docstring says is not directly exposed by `LabUser` and is populated only when the citizen portal surfaces it.
- `backend/app/services/mpi/api.py:560-572` — the only production use found: `GET /mpi/citizens/{citizen_ulid}/access`.
- Read-only usage scan found `require_consent` only in `consent_dep.py` (definition/docstring), `mpi/api.py:21,571`, and tests.
- `backend/app/routes/patients.py:159-286` — patient PHI routes do not use consent.

**Safe reproduction / falsification (static)**
1. Scan production imports/calls of `require_consent`.
2. Confirm only `mpi/api.py:571` applies it.
3. Inspect `consent_dep.py:68-71,121-153` and confirm emergency access is header-only with no server-side justification/approval.
4. **Falsification:** show consent dependencies applied to all PHI reads, with break-glass requiring a server-issued emergency case ID, justification, expiry, and post-hoc approval workflow.

**Root cause:** The consent engine was built as a reusable dependency but not adopted by the primary PHI surfaces; break-glass was modeled as a request flag rather than a governed clinical process.

**Impact:** Most PHI access is not consent-gated. Where consent is used, a doctor can self-authorize emergency access by setting a header, producing an audit record but no preventive control. Owner-bypass may fail closed for citizens because `citizen_ulid` is not reliably attached.

**Remediation:** Apply `require_consent(scope=...)` to every cross-lab/citizen PHI read; replace the raw header with a server-issued, short-lived break-glass grant tied to a case/patient, justification, and approver; require post-use review; add tests for denied, consented, owner, and emergency paths.

**Alternatives:** (a) Move break-glass into the clinical gateway policy engine with purpose-of-use context; (b) keep header but require signed emergency token + mandatory review queue. Preferred: (a); (b) as a minimal hotfix.

---

### AUD-PRV-003 — Client-controlled `force_create` bypasses duplicate detection without authorization

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 7, Reproducibility 8, Exploitability 7, Affected users 8, Discoverability 6 → **7.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/routes/patients.py:39` — `force_create: bool = False  # skip duplicate check` is a client-supplied request field.
- `backend/app/routes/patients.py:199` — the value is passed directly into `create_patient()`.
- `backend/app/services/patient_service.py:149-155` — duplicate detection is skipped entirely when `force_create` is true.
- `backend/app/models/patient.py:29` — `national_id_hash` is indexed but not unique; `patient.py:23` has only a composite `(lab_id, national_id_hash)` index.
- `backend/app/services/patient_service.py:182-185` — MPI resolution still runs after the bypass, so duplicate records can be created with the same identity material.

**Safe reproduction / falsification (static)**
1. Trace `force_create` from `routes/patients.py:39,199` into `patient_service.py:149-155`.
2. Confirm no role/permission check gates the flag.
3. Confirm no database uniqueness constraint prevents duplicate national-ID hashes.
4. **Falsification:** show the flag is authorized (e.g. `master_admin` plus audited override reason) and that a uniqueness/constraint or MPI merge path prevents duplicate clinical records.

**Root cause:** A safety override was exposed as an ordinary request parameter without authority, justification, or compensation.

**Impact:** Any caller able to create patients can fragment a patient’s record across duplicate rows, weakening MPI linkage, duplicating results/orders, and increasing risk of wrong-patient clinical decisions.

**Remediation:** Remove the public flag; implement a server-side override permission with mandatory reason and audit; add a partial unique constraint on `(lab_id, national_id_hash)` where not null (or application-level transaction-safe lock); require duplicate-resolution review before creating a second record.

**Alternatives:** (a) Keep override only in an admin-only endpoint; (b) automatically route duplicates to MPI review instead of creating a row. Preferred: (b), with (a) as a controlled break-glass path.

---

### AUD-PRV-004 — Raw PII is written into the tamper-evident audit log

- **Severity:** MEDIUM
- **Likelihood:** HIGH
- **DREAD:** Damage 5, Reproducibility 9, Exploitability 6, Affected users 7, Discoverability 6 → **6.6**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/services/patient_service.py:187-196` — audit `details` contains `f"Created patient {patient.full_name} (phone={phone})"`.
- `backend/app/services/audit_service.py:198-212` — `log_action()` serializes `details` and writes it verbatim to `AuditLog.details`.
- `backend/app/services/patient_service.py:53-68` — the normal response DTO already exposes these fields under access control; the audit copy is an additional, immutable PII store.
- `GOVERNANCE/SECURITY_COVERAGE_MATRIX.md:22` — audit immutability/hash-chain is an owner-listed control that must be preserved, raising the impact of log content errors.

**Safe reproduction / falsification (static)**
1. Read `patient_service.py:194` and `audit_service.py:198-212`.
2. Confirm full name and phone are embedded in a string stored in the audit table.
3. **Falsification:** show redaction/tokenization at the logging boundary and a test asserting no raw name/phone/national ID appears in `AuditLog.details`.

**Root cause:** Audit logging treats details as free-form human text rather than as a data-minimized structured field.

**Impact:** The append-only audit log becomes a secondary PHI repository with broader retention and different access controls. This violates minimization and complicates breach notification, retention, and role-based log review.

**Remediation:** Log `resource_id`, `health_id` reference, and field names only; never log raw names, phones, emails, national IDs, or family IDs. Add a redaction helper and a CI test scanning audit detail literals for PII patterns.

**Alternatives:** (a) Store a salted reference token for the patient; (b) encrypt details with a separate key and strict reviewer permission. Preferred: (a) plus minimization; encryption is defense in depth, not a substitute.

---

### AUD-PRV-005 — Minor/guardian linkage is optional and unenforced

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 8, Reproducibility 8, Exploitability 7, Affected users 6, Discoverability 6 → **7.0**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/routes/patients.py:124-126` — `guardian_id` is described as “Strongly recommended when birth_date indicates the patient is under 18,” not required.
- `backend/app/services/patient_service.py:157-163` — guardian is validated only **if** `guardian_id is not None`; no age-derived requirement exists.
- `backend/app/models/patient.py:54-59` — `is_minor` is computed from `birth_date`; `patient.py:33-36` defines the optional guardian FK.
- `backend/app/services/patient_service.py:304-321` — family/guardian views return all children linked by `guardian_id`; missing links silently reduce visibility.
- `backend/app/routes/patients.py:229-245` — children lookup is keyed only by `guardian_id` and lab.

**Safe reproduction / falsification (static)**
1. Compare `is_minor` derivation (`models/patient.py:54-59`) with create validation (`patient_service.py:157-163`).
2. Confirm a birth date indicating a minor can be submitted with `guardian_id=None`.
3. Confirm no service/route check rejects that state.
4. **Falsification:** show a validator that requires an adult guardian for any patient whose `birth_date` implies age < 18, plus tests for missing/invalid/cross-lab guardian IDs.

**Root cause:** Guardian linkage is treated as optional metadata rather than as a privacy/safety control for pediatric records.

**Impact:** Minor PHI can be created without a verifiable guardian, breaking consent/guardian authorization assumptions and family-view completeness. It also weakens auditability of who may act for the child.

**Remediation:** Derive age from `birth_date`; require a guardian ID for minors; verify the guardian is an adult patient in the same lab/facility scope; record the guardian relationship in audit details as IDs only; add tests for minor-without-guardian, adult-guardian, expired/deceased guardian, and cross-lab guardian cases.

**Alternatives:** (a) Block creation until guardian verification; (b) create a pending state with limited access until a guardian is linked. Preferred: (b) for emergency intake, (a) for routine registration.

---

## 5. Cross-lane dependencies

- AUD-PRV-001 and AUD-PRV-003 are worsened by AUD-SEC-005 (patient routes lack action-level authorization).
- AUD-PRV-002 depends on the same NIAM/authorization gaps described in AUD-SEC-001 and AUD-SEC-006.
- AUD-PRV-004 affects the audit control listed in `GOVERNANCE/SECURITY_COVERAGE_MATRIX.md:22` and `:53`.
- None of these findings changes the owner-gated **HOLD** decision.

---

## 6. Items excluded

- The synthetic FHIR evidence surface (`backend/app/interoperability/fhir_http/security.py`) was reviewed but not counted as a live PHI exposure because no factory mount was found.
- NR-011 is intentionally not re-reported.
- No claim is made about real production data, backups, or database contents; no database was accessed.

---

## 7. Handoff

All findings are `DISCOVERED` and require Team C independent verification. Privacy certification is not claimed. Release decision remains **HOLD**.
