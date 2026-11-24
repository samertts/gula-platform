# P-16 Post-Change Package Record (owner numbering = roadmap P-14 / AUD-F16 — MPI identity integrity)

Generated: 2026-11-20T18:17:44Z (UTC)

## Invariants
- branch: integration/gula-unification-v1
- HEAD: 2206654dc713ea2de8c564a3207dfe05fde23549
- protected sibling HEAD: f478676b6fc375338648dde46fbf076c015a3f91
- staged name-status MD5: 56c524d6ffe9872c3a3ac6eff8c8f203
- staged count: 20
- staged R100 count: 20
- unstaged count: 160
- untracked count: 647
- git diff --check exit: 0

## Protected MD5s
effdfeaf10234678d83b2668c4489552  GOVERNANCE/FINAL_DECISION.md
1a02c01563c93b07a7cdb92c0462bf36  GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md
ea3969d09aaf7b0b28a065838b44a594  GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md

## production_ready_items
480:    "production_ready_items": 0
600:  "production_ready_items": 0,

## Files changed by P-16
 M backend/app/services/patient_service.py
?? backend/tests/test_p16_mpi_identity_integrity.py

## Verification
- RED: 5 failed / 1 passed (before implementation) — exact defects captured.
  Corrected per independent review F3: the unverified-NID invariant test calls
  the resolver directly and passes against HEAD; it is a guard, not a RED
  detector for the P-16 delta.
- GREEN: 6 passed in 123.02s (exit 0) — initial implementation
- GREEN (post-review): **11 passed** in 175.13s (exit 0) — 6 original + 5
  condition-regression tests (F1, F2, F4, F5 x2)
- related-path: 105 passed in 140.91s (exit 0); re-run after review fixes:
  **105 passed** in 184.15s (exit 0)
- ruff: All checks passed (exit 0); git diff --check exit 0
- protected MD5s: all 3 unchanged; protected sibling HEAD unchanged

## Test evidence summary
Synthetic data only; isolated SQLite; no production DB/service/PHI/secret.
Covered: degraded temporary identity on MPI outage (care not denied), explicit
status/source/confidence, monitored reconciliation key, pending_review audit,
idempotent retry (one claim/one citizen), no unverified-NID auto-merge, no
silent promotion, no merge call in patient creation.

## Production diff
diff --git a/backend/app/services/patient_service.py b/backend/app/services/patient_service.py
index 40057321..e58029b3 100644
--- a/backend/app/services/patient_service.py
+++ b/backend/app/services/patient_service.py
@@ -17,6 +17,31 @@ from ..services.mpi import resolver as mpi_resolver
 
 
 @dataclass
+@dataclass(frozen=True)
+class MpiResolution:
+    """Explicit identity outcome for a locally created patient.
+
+    ``status`` is one of:
+      * ``resolved``  — canonical citizen linked with an authoritative method;
+      * ``temporary`` — citizen claimed but awaiting human review (unverified
+        national ID or ambiguous match); never a confirmed national identity;
+      * ``degraded``  — MPI was unavailable. Care continues under a temporary
+        local identity and the reconciliation key is monitored via audit.
+
+    This result is deliberately explicit: a resolver failure must never be
+    collapsed into a silent ``(None, None)`` that looks like success.
+    """
+
+    status: str
+    citizen_ulid: str | None
+    source: str
+    confidence: float | None
+    match_method: str | None
+    reconciliation_key: str | None
+    reconciliation_required: bool
+    error_type: str | None = None
+
+
 class PatientDict:
     """DTO for patient serialization."""
 
@@ -138,16 +163,61 @@ def create_patient(
     national_id: str | None = None,
     family_id: str | None = None,
     force_create: bool = False,
+    force_reason: str | None = None,
     guardian_id: int | None = None,
     ip_address: str | None = None,
 ) -> dict:
-    """Create a new patient with duplicate detection."""
+    """Create a new patient with duplicate detection.
+
+    AUD-PRV-003: ``force_create`` is a privileged duplicate-detection override.
+    The route enforces authorization and a mandatory reason; this service adds
+    defense in depth plus a transaction-safe guard against silently persisting a
+    SECOND record for the same national ID at the same facility (an exact NID
+    collision is a true duplicate and must go through MPI merge, not force-create).
+    """
     # Hash national ID and family ID if provided
     nid_hash = hash_national_id(national_id) if national_id else None
     fid_hash = hash_family_id(family_id) if family_id else None
 
-    # Duplicate detection (unless force_create is True)
-    if not force_create:
+    if force_create:
+        # Defense in depth: the override is never anonymous or reason-less, even
+        # if a future caller bypasses the route-level checks.
+        if not force_reason or len(force_reason.strip()) < 10:
+            return {
+                "error": "A documented reason (min 10 characters) is required for a duplicate override",
+                "status_code": 422,
+            }
+        # Transaction-safe identity guard: an exact national-ID match inside the
+        # SAME facility is the same person, not a fuzzy duplicate. Refuse to
+        # create a second record; route it to the MPI merge path instead.
+        if nid_hash is not None:
+            exact = (
+                db.query(Patient.id)
+                .filter(Patient.lab_id == lab_id, Patient.national_id_hash == nid_hash)
+                .first()
+            )
+            if exact:
+                return {
+                    "error": (
+                        "A patient with this national ID already exists in this facility; "
+                        "use MPI merge instead of force_create"
+                    ),
+                    "status_code": 409,
+                }
+        log_action(
+            db,
+            action="patient_duplicate_override",
+            resource_type="patient",
+            user_id=user_id,
+            user_role=user_role,
+            details=(
+                f"force_create override authorized; reason={force_reason.strip()[:300]!r}; "
+                f"phone={phone}; national_id_present={bool(nid_hash)}"
+            ),
+            ip_address=ip_address,
+        )
+    else:
+        # Duplicate detection (unless force_create is True)
         duplicate_result = _check_duplicates(
             db, lab_id, full_name, phone, birth_date or "", nid_hash,
         )
@@ -179,8 +249,10 @@ def create_patient(
     db.add(patient)
     db.flush()
 
-    # MPI resolution
-    citizen_ulid, mpi_match_method = _resolve_mpi(
+    # MPI resolution — explicit status: resolved / temporary / degraded.
+    # Care is never denied when MPI is unavailable; the degraded outcome is
+    # surfaced with a monitored reconciliation key instead of a silent null.
+    mpi = _resolve_mpi(
         db, patient, national_id, family_id, user_id, lab_id,
     )
 
@@ -191,7 +263,12 @@ def create_patient(
         resource_id=patient.id,
         user_id=user_id,
         user_role=user_role,
-        details=f"Created patient {patient.full_name} (phone={phone})",
+        details=(
+            f"Created patient {patient.full_name} (phone={phone}); "
+            f"mpi_status={mpi.status}; mpi_source={mpi.source}; "
+            f"mpi_confidence={mpi.confidence}; "
+            f"mpi_reconciliation_key={mpi.reconciliation_key}"
+        ),
         ip_address=ip_address,
     )
 
@@ -199,8 +276,13 @@ def create_patient(
     db.refresh(patient)
 
     resp = patient_to_dict(patient)
-    resp["citizen_ulid"] = citizen_ulid
-    resp["mpi_match_method"] = mpi_match_method
+    resp["citizen_ulid"] = mpi.citizen_ulid
+    resp["mpi_match_method"] = mpi.match_method
+    resp["mpi_status"] = mpi.status
+    resp["mpi_identity_source"] = mpi.source
+    resp["mpi_confidence"] = mpi.confidence
+    resp["mpi_reconciliation_key"] = mpi.reconciliation_key
+    resp["mpi_reconciliation_required"] = mpi.reconciliation_required
     return {"message": "Patient created", "patient": resp}
 
 
@@ -330,16 +412,29 @@ def _check_duplicates(
     nid_hash: str | None,
 ) -> dict | None:
     """Check for duplicate patients. Returns error dict if found, None otherwise."""
-    # Check for exact national ID match first
-    if nid_hash:
-        existing = db.query(Patient).filter(Patient.national_id_hash == nid_hash).first()
+    # AUD-PRV-001: the national ID is a global identifier, but patient creation is
+    # tenant-scoped. The previous lookup was global AND returned patient_to_dict()
+    # of the matched record, so a user at one facility who knew a national ID could
+    # obtain another facility's PHI (name, phone, DOB, gender, email, health id,
+    # guardian link). Two independent controls now apply:
+    #   1. the lookup is partitioned by the caller's lab_id (matching the intent of
+    #      the composite ix_patients_lab_nid index and every other branch here);
+    #   2. only a non-identifying conflict marker is returned — never another
+    #      patient's record, internal id, or facility.
+    # Selecting Patient.id alone also avoids loading any PHI into memory.
+    if nid_hash and lab_id is not None:
+        existing = (
+            db.query(Patient.id)
+            .filter(Patient.lab_id == lab_id, Patient.national_id_hash == nid_hash)
+            .first()
+        )
         if existing:
             return {
                 "error": {
                     "duplicate": True,
-                    "message": "Patient with this national ID already exists",
-                    "message_ar": "يوجد مريض مسجل بنفس الرقم الوطني",
-                    "existing_patient": patient_to_dict(existing),
+                    "message": "A patient with this national ID already exists in this facility",
+                    "message_ar": "يوجد مريض مسجل بنفس الرقم الوطني في هذه المنشأة",
+                    "conflict": {"scope": "national_id", "facility_scoped": True},
                 },
                 "status_code": 409,
             }
@@ -411,8 +506,22 @@ def _resolve_mpi(
     family_id: str | None,
     user_id: int,
     lab_id: int,
-) -> tuple[str | None, str | None]:
-    """Resolve MPI identity. Returns (citizen_ulid, match_method)."""
+) -> MpiResolution:
+    """Resolve the canonical identity, returning an explicit MpiResolution.
+
+    AUD-F16: the old broad handler logged the failure and returned bare
+    ``(None, None)``, indistinguishable from a successful resolution with no
+    citizen. The failure now yields a ``degraded`` temporary identity with a
+    stable reconciliation key. The patient is still created (no denial of
+    care), and the outcome is observable in both the API response and the
+    canonical audit trail. Retrying reconciliation is idempotent because the
+    resolver keys its claim on ``(lab_id, local_patient_id)``.
+
+    No automatic merge is performed here, and an unverified national ID is
+    never promoted to a confirmed identity: those remain human-governed MPI
+    operations.
+    """
+    reconciliation_key = f"mpi:{lab_id}:{patient.id}"
     birth_year = birth_month = birth_day = None
     if patient.birth_date:
         birth_year, birth_month, birth_day = (
@@ -420,8 +529,6 @@ def _resolve_mpi(
             patient.birth_date.month,
             patient.birth_date.day,
         )
-    citizen_ulid = None
-    mpi_match_method = None
     try:
         outcome = mpi_resolver.resolve_identity(
             db,
@@ -437,9 +544,8 @@ def _resolve_mpi(
             family_id=family_id,
             claimed_by_user_id=user_id,
         )
-        citizen_ulid = outcome.citizen.citizen_ulid
-        mpi_match_method = outcome.match_method
     except Exception as mpi_err:
+        error_type = type(mpi_err).__name__
         log_action(
             db,
             action="mpi_resolve_failed",
@@ -447,6 +553,56 @@ def _resolve_mpi(
             resource_id=patient.id,
             user_id=user_id,
             user_role="system",
-            details=f"MPI resolve failed: {type(mpi_err).__name__}: {str(mpi_err)[:200]}",
+            lab_id=lab_id,
+            details={
+                "status": "degraded",
+                "source": "mpi_resolver",
+                "confidence": None,
+                "reconciliation_key": reconciliation_key,
+                "error_type": error_type,
+                "error": str(mpi_err)[:200],
+            },
+        )
+        return MpiResolution(
+            status="degraded",
+            citizen_ulid=None,
+            source="mpi_resolver",
+            confidence=None,
+            match_method=None,
+            reconciliation_key=reconciliation_key,
+            reconciliation_required=True,
+            error_type=error_type,
+        )
+
+    match_method = outcome.match_method
+    confidence = float(outcome.match_score) if outcome.match_score is not None else None
+    pending = match_method == "pending_review"
+    resolution = MpiResolution(
+        status="temporary" if pending else "resolved",
+        citizen_ulid=outcome.citizen.citizen_ulid,
+        source=match_method,
+        confidence=confidence,
+        match_method=match_method,
+        reconciliation_key=reconciliation_key if pending else None,
+        reconciliation_required=pending,
+    )
+    if pending:
+        # Monitored queue: ops can filter audit logs on mpi_pending_review and
+        # the shared reconciliation key. No automatic promotion or merge.
+        log_action(
+            db,
+            action="mpi_pending_review",
+            resource_type="patient",
+            resource_id=patient.id,
+            user_id=user_id,
+            user_role="system",
+            lab_id=lab_id,
+            details={
+                "status": "temporary",
+                "source": match_method,
+                "confidence": confidence,
+                "reconciliation_key": reconciliation_key,
+                "citizen_ulid": resolution.citizen_ulid,
+            },
         )
-    return citizen_ulid, mpi_match_method
+    return resolution

## P-16 independent review
**Verdict: PASS WITH CONDITIONS. CRITICAL: 0. HIGH: 0.** Fresh-context
read-only reviewer (no repository modification). Focused suite 6/6, exit 0;
related subset 25/25, exit 0. Old-code silent `(None, None)` defect confirmed
from `git show HEAD:backend/app/services/patient_service.py`. All 7 mandate
requirements assessed: temporary identity, source/confidence/change history,
no auto-merge, no duplicate identities on retry, no silent promotion, and no
denial of care were met; monitored reconciliation was partially met (F1).

### Conditions — ALL ADDRESSED, each with a regression test

| ID | Sev | Condition | Resolution | Evidence |
|---|---|---|---|---|
| F1 | MED | No consumer watched the reconciliation audit markers | Added admin-only `GET /mpi/reconciliation/outstanding` in `app/services/mpi/api.py` + `ReconciliationItem/Page` schemas. Reads `mpi_pending_review`/`mpi_resolve_failed` audit rows (the claim-based `/mpi/review` cannot see outage patients because no claim was written), groups by `reconciliation_key`, returns identifiers/status only (no NID/name/phone/error text). | `test_p16_f1_outstanding_reconciliation_monitor_groups_markers_without_phi` |
| F2 | MED | `mpi_pending_review` marker duplicated on every retry | Emit only when no prior marker exists for `(action, resource_id)`; retries still resolve idempotently but do not inflate the queue. | `test_p16_f2_pending_review_marker_is_idempotent_on_retry` |
| F3 | MED | Record overstated RED as 6 failed | Corrected to 5 failed / 1 passed with rationale above. | record text |
| F4 | LOW | Stacked `@dataclass` decorators; `frozen` param overwritten | Removed outer decorator; `__dataclass_params__.frozen is True`. | `test_p16_f4_mpi_resolution_is_genuinely_frozen` |
| F5 | LOW | `float(match_score)` unguarded; NaN/Inf/non-numeric could abort creation or emit non-standard JSON | Added `_safe_match_score`: finite check, [0,1] clamp, graceful `None`. | `test_p16_f5_safe_match_score_normalises_malformed_values`, `test_p16_f5_non_finite_score_never_emits_nonstandard_json` |

### Residual risks disclosed, NOT self-accepted

- **F7 (LOW, pre-existing)** — audit write inside the MPI failure handler can itself raise, which would turn a swallowed outage into a 500. The same property exists on the unchanged unconditional `create` audit row. Changing it would alter the fail-closed audit policy established in P-13/P-15; therefore left unchanged and recorded for owner decision.
- **F6 (LOW, pre-existing)** — raw exception text is persisted in audit details; unchanged from HEAD, no raw NID/name/phone field added by P-16.
- **F9 (INFO, pre-existing)** — a client ignoring `mpi_status` could treat a `pending_review` ULID as confirmed; no in-repo consumer reads these keys; mitigated by `mpi_status="temporary"` + `mpi_reconciliation_required=true`.
- Reconciliation key is carried in audit details and the API response, not a persisted DB column with uniqueness enforcement.

Status: `TESTED` + `INDEPENDENTLY REVIEWED` (conditions cleared). NOT `ACCEPTED`, NOT
`PRODUCTION READY`. No commit, staging, merge, deploy or production action performed.
