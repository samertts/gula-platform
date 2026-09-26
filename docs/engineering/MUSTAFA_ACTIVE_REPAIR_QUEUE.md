# Mustafa — Active Repair Queue

Tracks findings authorized for direct implementation on
`claude/mustafa-parallel-engineering`, per "GULA — MUSTAFA ACTIVE REPAIR &
ACCELERATION MODE" (uploaded directive, superseding the prior "do not fix
F5 on this branch" instruction). One row per item; update in place, do not
fork a new report document for the same defect.

| ID | SEVERITY | ROOT CAUSE | OWNER | STATUS | CURRENT COMMIT | BLOCKER | NEXT ACTION |
|----|----------|------------|-------|--------|----------------|---------|-------------|
| F5 | P0 (authorization) | `can_manage_user()` in `backend/app/security/rbac.py` returned `True` for every actor role except `province_admin`, with no `lab_id` check — a lab-scoped `admin`/`lab_admin` could toggle-activate or change the role of a user in **any other lab** via `PUT /admin/users/{id}/toggle` and `PATCH /admin/users/{id}/role`. | Mustafa | **FIXED — INDEPENDENTLY RE-VERIFIED** | c84171ea (fix), 9c173f51 (independent re-verification) | none | Continue continuous-assurance verification of Abu Ali's milestones. |
| nhop-trust-boundary | P0 (spoofable identity) | This branch forked before `nhop-platform` existed on Abu Ali's branch; his `eb01668b` fix to `X-Role`/`X-Actor-Id`/`X-Actor-Role` header-trust never reached this branch. Worse here: this branch's `api/v1/__init__.py` already mounts all 5 v1 routers (a prior batch fixed the shadow-route gap), so `doctor.py`'s and `outbreak.py`'s header-trust bugs were live and reachable here, not dead code. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 9580d118 | none | If Abu Ali's identity federation work ever lands a real JWT-backed context for nhop-platform, replace `require_trusted_context`'s body per its own docstring — nothing else needs to change. |
| F2 (nhop) | P1 (tenant scope / BOLA) | `create_test_result` in `nhop-platform/app/api/v1/test_results.py` used client-supplied `payload.lab_id` as sole authority for which lab a clinical result is attributed to. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 9580d118 | none | none — closed alongside the trust-boundary port, since it needed the same `TrustedContext.lab_id`. |
| authz-ownership | P1 (broken object-level authorization) | `backend/app/routes/authorization.py`: `revoke_delegation`, `deactivate_break_glass`, `assign_role`, `revoke_role_assignment` required nothing beyond `Depends(get_current_user)` — any authenticated account of any role could revoke another user's delegation, deactivate another user's active break-glass session, or grant/revoke arbitrary role assignments, by guessing a small sequential integer id. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | (pending push, next commit) | none | Currently non-exploitable for real privilege escalation as a side effect — neither `RoleAssignment` nor `BreakGlassSession` is consulted by the live JWT/RBAC enforcement path (`get_current_user`/`require_permission`) today. Re-check this the moment anything starts consulting those tables. |
| tenant-scope-sweep | P2 (candidates, fully triaged) | Superseded by `scripts/tenant_mass_assignment_scan.py` (ported from Abu Ali, then improved — see `scanner-false-positives` below), which is more precise than `scripts/security/detect_missing_tenant_scope.py`'s original 91-candidate sweep. **Full triage complete for all 32 ASSIGNABLE candidates** (`--class ASSIGNABLE` re-run confirms the set is stable): 31 create-shape sites across `biomedical`(3)/`blood_bank`(4)/`command_center`(4)/`critical_care`(5)/`ems`(6)/`pilot_platform`(4)/`public_health`(5) `application/service.py` modules + 1 update-shape site (`adaptive_auth/routes.py::update_risk_policy`, resolved separately — see `adaptive-auth-policy-authz` below). Router-level `dependencies=[Depends(require_permission("system:admin"))]` verified present (grep, not spot-check) on all 7 domain routers: biomedical, blood_bank, command_center, critical_care, ems, public_health, pilot_platform. Call-site reachability re-verified for every one of the 31 create-shape function names: 29 have exactly one (or, for `raise_alert` which exists identically named in both `critical_care` and `public_health`, two) call site inside their own gated router; 2 are **DEAD_OR_UNREACHABLE** (`critical_care/application/service.py::record_vitals` at line 344 and `ems/application/service.py::create_shift` at line 292 — neither is called anywhere outside its own module; `critical_care`'s actual `/vitals` route calls the sibling `record_vitals_safely` instead, which is itself **SERVER_DERIVED** in practice even though the scanner can't see it: the route builds `{**body, "lab_id": lab_id}` from the authenticated user's own `lab_id` before ever calling the service, so a client-supplied `lab_id` in the request body is silently overwritten, not honored). The remaining 29 reachable create-shape sites are **SYSTEM_CONTROLLED**: only `master_admin`-tier accounts reach the endpoint at all (per the router gate), and a client-supplied `lab_id` in that scenario is the same intended-admin-picks-target-lab usage already accepted for `pilot-platform-no-auth` below, not a defect. | Mustafa | **FIXED — VERIFIED / FULLY TRIAGED** | f365d3b3, e2b9dd0a, 71b30550, 739c504a, 10ec1bd4 | none | none |
| pilot-platform-no-auth | P0 (missing authentication) | `backend/app/pilot_platform/api/routes.py` had no authentication at all — no router-level dependency, no per-route `Depends(get_current_user)` — on a router wired into the live app. Every write endpoint accepted a fully unauthenticated request. Found via the tenant-scope sweep's reachability check. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 739c504a | none | none |
| scanner-false-positives | Engineering Intelligence | `tenant_mass_assignment_scan.py`'s "update" shape (1) never checked whether the mutated object's class actually has `lab_id` (flagged `ehr_service.py`'s 17 FHIR-style update functions — patient_id-scoped, not lab_id-scoped, and already guarded at the route layer), and (2) didn't recognize the `if k not in (..., "lab_id", ...): setattr(...)` exclusion-guard pattern as safe (flagged this branch's own already-fixed `care_continuum.py::api_update_primary_care_encounter`). | Mustafa | **FIXED — VERIFIED** | 739c504a | none | none |
| authz-role-hierarchy | P0 (privilege escalation) | `assign_role`/`revoke_role_assignment` in `backend/app/routes/authorization.py` checked only `platform:manage_users` possession, never `can_manage_role()` on the granted role itself — a `province_admin` (or a lab-scoped `admin`/`lab_admin`, which also holds that permission) could grant/revoke `master_admin`. Found by independently comparing against Abu Ali's convergent fix for the same finding (NR-140). | Mustafa | **FIXED — VERIFIED** (negative-proofed) | e2b9dd0a | none | none |
| nr148-canonical-patient-lab-id | P0/P1 (was live, now FIXED) | `POST /api/v1/canonical-patients` built `CanonicalPatient(**data.model_dump())` directly — the request body's `lab_id` was honored verbatim. Abu Ali's branch resolved the reserved MPI-ownership decision (`lab_id` = provenance, not tenant ownership; national scope = `platform:view_stats`) and shipped `services/mpi/scope.py`. Ported unchanged onto this branch. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 892f4550 | none | none |
| ai-approval-no-tenant | P2 (workflow integrity, not data exposure) | `backend/app/routes/ai.py`: `/ai/suggest`, `/ai/pending`, `/ai/approve/{id}`, `/ai/reject/{id}`, `/ai/execute/{id}` share one global `approval_store` with no `lab_id` on `AISuggestion`/`PendingApproval` — any doctor/admin-tier user on the platform can list, approve, reject, or execute another lab's pending AI suggestion. Severity is capped, not absent: `AISandbox.execute()` runs a whitelisted registry of pure functions over the payload the *original submitter* already supplied (never re-fetches by ID from the DB), and every registered operation is `display_only=True` with no DB write — so this is cross-lab workflow interference, not a PHI leak or a clinical-state mutation. `/ai/suggest` itself has no role gate at all (any authenticated user, not just doctors), though creating a suggestion alone has no effect until a doctor-tier user approves/executes it. | — | **NOT FIXED — documented only** | n/a | none (deliberately not actioned this pass — P2, "P0/P1 only" per this pass's own instructions) | If ever prioritized: add `lab_id` to `AISuggestion`, stamp it from the submitter's `current_user.lab_id` in `create_suggestion`, and filter `pending_list`/`approve`/`reject`/`execute`/`get` by it (platform roles — admin/lab_admin+ — keep cross-lab reach, mirroring `require_own_lab`). |
| adaptive-auth-policy-authz | P0 (missing authorization — 32nd/last ASSIGNABLE candidate) | `backend/app/identity/adaptive_auth/routes.py`: `create_risk_policy`/`update_risk_policy`/`create_session_policy`/`update_session_policy` required nothing beyond the router-level `Depends(get_current_niam_actor)` — any authenticated NIAM account of any role could rewrite platform-wide risk thresholds, mitigation actions, MFA requirements, and session limits for every tenant. `RiskPolicy`/`SessionPolicy` have no `organization_id`/`lab_id`; `AuthorizationDecisionService` is organization-scoped by design (denies when `organization_id` is absent unless `resource_type` is in `NON_ORGANIZATIONAL_READS`, which these are not) and widening that allowlist is a canonical-semantics change outside this branch's authority. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 10ec1bd4 | none | none |
| adaptive-auth-account-id-idor | P1 (candidate — broad IDOR shape, NEEDS_DECISION) | Same file, ~10 other endpoints (`evaluate_risk`, `get_risk_history`, `create_mfa_challenge`, `verify_mfa_challenge`, `list_travel_events`, `get_active_session_count`, `detect_new_device`, `enforce_session_policy`, `check_session_expiry`, `is_session_valid`) take a client-supplied `account_id`/`session_id` path or body param with zero ownership/self-check beyond bare NIAM authentication — any authenticated actor can evaluate risk for, read risk history of, create/verify MFA challenges for, or terminate sessions belonging to an arbitrary other account. Not fixed: the *correct* semantics are genuinely ambiguous without deeper context on NIAM's login/step-up-auth flow — e.g. `evaluate_risk`/`create_mfa_challenge`/`detect_new_device` plausibly need to be system-invoked mid-login (before the acting account's own session exists to compare against), not self-only; `get_risk_history`/`list_travel_events`/`get_active_session_count` plausibly need a real self-or-admin check; the write endpoints (`enforce_session_policy`, `check_session_expiry` — the latter has no `account_id` at all, looks system/cron-invoked) need separate reasoning again. Fabricating a self-only guard here risks breaking a legitimate system-to-system login flow this branch cannot observe. | — | **NOT FIXED — NEEDS_DECISION, documented only** | n/a | Reserved architectural decision: whoever owns NIAM's login/step-up-auth call graph must state, per endpoint, whether the caller is (a) the account itself, (b) an unauthenticated-at-that-point login-flow-internal caller, or (c) a legitimate cross-account admin/security caller — then a real `AuthorizationDecisionService`-based or self-check guard can be added per endpoint without guessing. Until then this is live and unguarded; flagging rather than silently leaving unrecorded. |
| lab-slice-cancel-order-cas | P0 (proven — TOCTOU race) | Laboratory vertical slice (Order → Sample → Result). `services/order_service.py::cancel_order` was the only order-mutating endpoint with no compare-and-swap at all — unlike sibling `validate_order`/`test_results.py::verify_test_result`, which both use `UPDATE ... WHERE locked_at IS NULL`. A concurrent validate committing between cancel_order's read and its own commit had the validated (locked, documented-terminal) order's status silently overwritten back to "cancelled". | Mustafa | **FIXED — VERIFIED** (negative-proofed) | fa911580 | none | none |
| lab-slice-sample-authz | P0/P1 (proven — no role gate, no state machine) | `routes/samples.py::update_sample` had zero role gate (any authenticated account of any role could reject/finalize a sample) and zero status-transition guard (arbitrary mutation via a generic update endpoint, including resurrecting an already-rejected/analyzed sample). Fixed with the same clinical-write role tier `update_result` already uses, a new `domain/sample_state.py` (mirrors `order_state.py`), and an atomic CAS write using the sample's own `status` column as the compare-and-swap token (Sample has no `version` column — see next row). | Mustafa | **FIXED — VERIFIED** (negative-proofed) | fa911580 | none | none |
| lab-slice-sample-version-column | Decision — resolved without a migration | Investigated per "SAMPLE.VERSION — DECISION-FIRST MODE": (1) exactly two call sites mutate an existing `Sample` row — `routes/samples.py::update_sample` and `routes/device_results.py::receive_device_results`; (2) the latter was found NOT to use any CAS at all (plain `sample.status = "analyzed"` / `order.status = "completed"` ORM attribute assignment) — a real, additional TOCTOU gap, now fixed the same pass (see `lab-slice-device-ingestion-cas` below) by reusing `Sample.status` as its own CAS token and `LabOrder`'s existing `locked_at`/`version` columns, exactly as `update_sample` already does — no schema change needed; (3) with both sites now atomic, every clinically-significant mutation (status transitions, terminal-state protection, races against a concurrent order lock/cancel) is closed using columns that already exist; (4) the one residual gap `Sample.status`-as-token does NOT close: two concurrent edits to *non-status* fields only (`notes`, `rejection_reason`, `storage_location`) with the sample's status unchanged throughout both requests would not collide on the CAS check (status never changes, so the guard trivially passes for both) and the second writer's commit would silently win — a plain last-write-wins lost update. This is real but low-severity: operational/logistics metadata, not a clinical-safety or security defect (unlike status, which gates terminal-state protection and is now fully guarded). **Decision: SAFE_WITH_EXISTING_CONCURRENCY_CONTROLS** — no `Sample.version` migration needed for the canonical Laboratory workflow. The residual non-status-field lost-update gap is recorded below as its own low-priority item rather than silently dropped. | Mustafa | **RESOLVED — SAFE_WITH_EXISTING_CONCURRENCY_CONTROLS** (evidence-based, no migration) | fa911580, b8ee2c2e | none | none |
| lab-slice-device-ingestion-cas | P0/P1 (proven — no CAS at all) | `routes/device_results.py::receive_device_results` wrote both `sample.status` and `order.status` as plain, non-atomic ORM attribute assignments — the only mutation site in the Laboratory slice with zero CAS. A concurrent cancel of the same (pending, unlocked) order racing between the sequential `enforce_transition` check and the eventual commit would have its cancellation silently overwritten by the device submission's plain write, and duplicate `LabResult` rows could be created alongside it. Fixed by making both writes atomic (`UPDATE ... WHERE locked_at IS NULL AND status = <status read at check time>` for the order, reusing its existing `version` column too; `UPDATE ... WHERE status = <status read at check time>` for the sample, same as `update_sample`), performed *before* any `LabResult` rows are created so a lost race leaves nothing to unwind. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | b8ee2c2e | none | none |
| lab-slice-sample-nonstatus-field-race | P3 (documented, low severity) | Two concurrent edits to `Sample.notes` / `rejection_reason` / `storage_location` only (status unchanged by either) are not guarded by the status-as-CAS-token — the second writer's commit silently wins (plain last-write-wins). Discovered while resolving `lab-slice-sample-version-column`. Not fixed: operational-metadata risk, not a clinical-safety or tenant/security defect; closing it fully would need a real `Sample.version` or `updated_at` column, which is the same migration-requires-approval boundary as before, now correctly scoped to a P3 rather than blocking anything. | — | **NOT FIXED — documented, low priority** | n/a | If ever prioritized: add `Sample.updated_at` (or `version`) via an approved additive migration and widen the existing CAS filter to include it. |
| lab-slice-device-ingestion-consistency | Engineering Intelligence (not a vulnerability) | `routes/device_results.py::receive_device_results` mutated `sample.status = "analyzed"` directly, bypassing the sample state machine introduced above — a candidate duplicate-ingestion vulnerability that negative-proofing DISPROVED: a replayed submission was already refused by the existing order-level `enforce_transition` guard (`"completed" -> "completed"` is not a legal transition), independent of sample status. Both pre-fix and post-fix code return 409 on replay for that reason. Routed through `domain/sample_state.py` anyway, recharacterized honestly as consistency/defense-in-depth hardening (the sample's own state machine is now authoritative everywhere its status is mutated), not a fixed exploit. | Mustafa | **HARDENED — NOT A PROVEN VULNERABILITY** | fa911580 | none | none |
| imaging-slice-report-authz | P0 (proven — no role gate anywhere in the module) | Imaging vertical slice (Order → Exam → Report). `app/radiology/routes.py`/`services.py`: `current_user.role` was read only to attribute audit-log entries (`actor_role=`) — never once compared against an allowed set anywhere in the module. Any authenticated `LabUser` of any role could create, draft-edit, finalize, amend, or verify a clinical radiology report, or change an exam's status. Fixed with two role tiers mirroring the Laboratory slice's own precedent (`update_result` vs `validate_order`'s narrower sign-off tier): `_RADIOLOGY_WRITE_ROLES` (admin/master_admin/doctor/radiologist/pathologist/technician) on `create_report`/`save_report_draft`/`update_order_status`/`update_exam_status`; `_REPORT_SIGNOFF_ROLES` (same minus technician) on `finalize_report`/`amend_report`/`verify_report`. Everything else in this module (report state machine, `.with_for_update()` row locks, version-checked CAS, amendment history, critical-finding-notification-before-finalize, `ClinicalCommandGuard` idempotency+audit) was already mature and untouched. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 56c652e9 | none | none |
| imaging-slice-radiologist-id-ownership | P1 (proven — unvalidated client-authored ownership field) | `create_report`'s `radiologist_id` was pure client input with zero validation, unlike `finalize_report`/`amend_report` which already correctly block a caller from claiming another identity for their OWN action. Fixed: a supplied `radiologist_id` must now resolve to a real `doctor`/`radiologist` account in the SAME lab — the same canonical pattern `services/order_service.py::create_order` already uses for `doctor_user_id`, not invented fresh. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 56c652e9 | none | none |
| imaging-slice-order-status-cas | P0 (proven — no CAS, no transition guard, arbitrary string accepted) | `services.py::update_order_status` did `order.status = status` for ANY client-supplied string, unconditionally — no role check, no state machine, no concurrency guard at all, unlike its sibling `update_exam_status`/`_locked_report` which both already use `.with_for_update()` + version checks + a real transition map. Fixed: `.with_for_update()` row lock + a new `_ORDER_TRANSITIONS` map (same shape as the existing `_EXAM_TRANSITIONS`, scoped to pre-exam order lifecycle stages) + `RadiologyOrder`'s existing `version` column (`OptimisticLockMixin` — no schema change). Deliberately did NOT add the full `ClinicalCommandGuard` If-Match/Idempotency-Key contract to this route: that would be a breaking API change (new required headers) needing approval; the internal CAS closes the concurrency gap without changing the request contract, the same choice already made for `cancel_order` in the Laboratory slice. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 56c652e9 | none | none |
| imaging-slice-order-transition-graph | Decision needed (P2, non-blocking) | `_ORDER_TRANSITIONS` (pending→scheduled/cancelled→in_progress/cancelled→completed/cancelled) is a conservative, evidence-bounded guard — the smallest graph this pass could justify from actual code usage (no other code in the repo ever set a `RadiologyOrder.status` value beyond "pending" before this fix), not a canonical business-rule decision from whoever owns the Imaging clinical workflow. If the real order lifecycle needs more nuance (e.g., can a "completed" order be reopened for an additional exam?), that is a NEEDS_DECISION, not something this pass invented further. | — | **NOT FIXED — documented, non-blocking** | n/a | If the real order lifecycle differs, a domain owner should specify the intended graph; the guard can then be widened without touching its call sites. |
| imaging-slice-broader-role-gap | RESOLVED (route-by-route review completed) | Every remaining mutating route in `app/radiology/routes.py` was individually classified (not pattern-matched) per "RADIOLOGY SECURITY CLOSURE" directive. Results below. | Mustafa | **RESOLVED — see rows below** | 658359ad | none | none |
| imaging-slice-mpps-cross-tenant | P0 (proven — cross-tenant clinical mutation + state-machine bypass) | `device.py::MPPSHandler.process_mpps` resolved its target exam by `accession_number` alone with NO lab scope anywhere in that lookup — any authenticated account of any lab could complete (or otherwise mutate) another lab's exam by supplying/guessing its accession number. It also did `exam.status = "completed"` unconditionally, bypassing the same `_EXAM_TRANSITIONS` guard `update_exam_status` enforces (e.g. a cancelled exam could be silently flipped to completed). Fixed: `routes.py::receive_mpps` now resolves the exam first and runs it through `_patient_for_user` (the same canonical tenant check used everywhere else in this file) before any mutation; `process_mpps` now checks `_EXAM_TRANSITIONS` before applying the COMPLETED side effect, recording the MPPS event either way but silently refusing an illegal transition rather than applying it. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 658359ad | none | none |
| imaging-slice-global-resource-admin-gate | P0 (proven — global resources open to every authenticated account) | `Protocol` (`radiology_protocols`) and `ReportTemplate` (`radiology_report_templates`) are genuinely global — no `lab_id` column, globally-unique codes, read by every tenant — yet `create_protocol`/`create_report_template` had no gate beyond bare authentication: any account in any lab could corrupt platform-wide clinical reference data (dosing/preparation instructions, report structure) affecting every other tenant. `ModalityDevice` (`radiology_modality_devices`) is the same shape (no `lab_id`, holds real DICOM network config: `ip_address`/`ae_title`/`port`) and `register_device` had the same gap — a one-time hardware-provisioning action, not something a not-yet-registered device could call about itself. Fixed: all three now require `Depends(require_permission("system:admin"))`, the exact mechanism already used for `pilot_platform` and the 29 SYSTEM_CONTROLLED tenant-scope candidates — not a new mechanism. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 658359ad | none | none |
| imaging-slice-critical-finding-authz | P0 (proven — no role gate on the clinical-safety escalation path) | `create_critical_finding`, and `_run_critical_finding_command` (shared by `acknowledge_critical_finding`/`notify_critical_finding`), had no role gate at all — any authenticated account of any role could create, acknowledge, or notify a critical (urgent/dangerous) imaging finding. Object-level identity checks ("may only acknowledge/notify under the caller's own identity") and tenant scope (`_critical_finding_for_user`) were already correct; only the role tier was missing. Fixed with `_RADIOLOGY_WRITE_ROLES` — the broad clinical tier, not the narrower sign-off tier, since speed of escalation on a genuine critical finding argues against over-restricting who can raise/acknowledge/notify one. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 658359ad | none | none |
| imaging-slice-exam-radiologist-id | P2 (proven, lower severity than the report-level finding) | `create_exam`'s `radiologist_id` was unvalidated client input, the same shape as `create_report`'s already-fixed gap. Investigated its actual blast radius first: `get_radiologist_worklist` does NOT filter by `radiologist_id` (it shows all completed/verified exams tenant-wide), so an unvalidated value here does not misdirect worklist visibility the way the hypothesis initially suggested — it is audit/attribution metadata, not an access-control input. Fixed anyway (same validated-same-lab-doctor-or-radiologist pattern, extracted into a shared `_validate_radiologist_id` helper reused by both `create_report` and `create_exam`) since it is a one-line reuse of an already-proven-safe check, but classified honestly as P2 data-integrity hardening, not a re-run of the P0/P1 report finding. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 658359ad | none | none |
| imaging-slice-share-audit-identity | P1 (proven — fabricated/missing audit identity) | `create_share` hardcoded `shared_by=""` (every image share ever created recorded no actor at all) and `citizen_create_share` hardcoded `shared_by="citizen"` (a generic literal, not the real authenticated principal, despite both routes requiring a real `LabUser` JWT) — a direct violation of "no client-authored/no fabricated audit identity." Fixed: both now record `str(current_user.id)`, the real authenticated actor. | Mustafa | **FIXED — VERIFIED** (negative-proofed) | 658359ad | none | none |
| imaging-slice-enum-value-mismatch | Engineering Intelligence (pre-existing, unrelated correctness bugs found while verifying the above) | Discovered while writing positive-control tests for the admin-gate and share-identity fixes, not sought out independently: `pacs.py::create_share` and `services.py::create_protocol` both passed a raw lowercase value string (`"link"`, `"standard"`) directly into a SQLAlchemy `Enum(...)`-typed column, which validates by MEMBER NAME not by value — every call to either function raised `LookupError` at commit time, in production as much as in this test suite (no existing test exercised either route end-to-end before this pass). Fixed by converting to the actual enum member (`SharingType(share_type)` / `ProtocolType(protocol_type)`) before construction, in both places. Not hunted further across the rest of the file (e.g. `modality=modality.upper()` elsewhere happens to work only because every `ModalityType`/other enum's value.upper() coincidentally equals its member name — fragile, but out of scope for this security-focused pass). | Mustafa | **FIXED — VERIFIED** (blocked otherwise-passing tests; not part of the security fix itself) | 658359ad | none | A broader pass could audit every `Enum(...)`-typed column assignment in `app/radiology/` for the same raw-string-vs-member mismatch; not attempted here (correctness, not security). |
| imaging-slice-device-status-ambiguous | NEEDS_DECISION (not fixed) | `update_device_status` (online/offline/degraded/maintenance/error) is genuinely ambiguous per the directive's own device-operations caution: `ModalityDevice` has no `lab_id` to scope by either way, and whether this is a human admin action (a technologist marking a device for maintenance) or a monitoring agent self-reporting health is not determinable from the code — DeviceStatus's values read like both an automated heartbeat (ONLINE/OFFLINE/DEGRADED/ERROR) and a human action (MAINTENANCE). Not gated with `system:admin` (unlike `register_device`) since that risks breaking a legitimate monitoring integration if one exists; not left silently unrecorded either. | — | **NOT FIXED — NEEDS_DECISION, documented** | n/a | Whoever owns the device-monitoring integration should state whether this is human-only, system-only, or both, then the correct guard (role check, a real device credential, or nothing) can be added without guessing. |
| imaging-slice-detector-decision | Engineering Intelligence — detector NOT built | Per the directive's own explicit instruction, evaluated whether "role read for audit but never enforced" is now recurrent enough to justify a deterministic detector (it has appeared in Laboratory's `samples.py` and across this entire radiology module). Decision: **NOT JUSTIFIED**. A reliable detector would need (a) inter-procedural analysis — several of the real gaps this pass found were in shared wrapper functions (`_run_report_command`, `_run_exam_status_command`, `_run_critical_finding_command`), not inline in the route body, so a single-function AST scan would miss them or need to trace call graphs; and (b) domain-semantic judgment a syntactic pass cannot safely automate — `create_order`/`create_appointment`/`checkin_appointment`/`update_exam_images` are all correctly SAFE_BY_DESIGN (intentionally broad scheduling/intake operations) and would be false positives for any detector flagging "role never checked." Per the directive's own guidance ("if inter-procedural analysis would be required, document the limitation rather than building a fragile approximation"), this is documented instead of built. | — | **DECIDED — NOT JUSTIFIED, documented limitation** | n/a | Revisit only if a third, independent domain shows the same pattern with evidence that a bounded (not repo-wide) detector could be built without the inter-procedural/semantic dependencies above. |
| ems-domain-discovery | Domain selection evidence | Evidence-based discovery across the 5 candidate domains for the next vertical slice (Hospital/EMS/Vaccination/Appointments/Referral-Care-Continuity): **Hospital** (`app/hospital/models`, `routes/hospital.py`, `services/hospital_service.py`) has NO migration building any of its tables (`hospitals`, `hospital_departments`, `bed_assignments`, etc.) — LATENT, disqualified on persistence. **Care Continuity/Referral** (`app/care_continuum/models/referral.py`, `cc_referral_requests` etc.) — confirmed still LATENT (no migration), consistent with this session's earlier NR-146-adjacent finding. **Insurance referrals** (`app/insurance/domain/referral.py`, `ins_referrals`) — also entirely unbuilt, the whole Insurance domain has zero migrations. **Appointments** — both `app/national/domain/appointment.py` (`national_appointments`) and `app/national/scheduling_platform/` (`national_scheduling_appointments` + 6 sibling tables) are LATENT; Radiology's own appointment routes were already hardened this session and are out of scope to repeat. **Vaccination**: the clinically-real version (`app/care_continuum/models/immunization.py`, `cc_vaccination_records`/`cc_immunization_schedules`) is LATENT; the LIVE version (`app/public_health/infrastructure/models.py`, `ph_immunization_records`, migration-confirmed) is a *surveillance/reporting* record, not a clinical administer-a-dose workflow, and its entire router is `system:admin`-gated ("National Public Health Surveillance") — same single-tier national-platform design as EMS, with a thinner operational journey. **EMS** (`app/ems/`) is the only candidate with BOTH a real migration (`20260716_0005_national_ems_and_disaster_response_platform_tables.py`, all 12 `ems_*` tables) AND a rich, coherent, already-mature journey (Incident → Dispatch → Triage → EPCR → Submit) with a real state machine (`_INCIDENT_TRANSITIONS`), real CAS (`.with_for_update()` + version on every other mutation), real audit, and an existing test baseline (`test_emergency_surgery_workflow_p0.py`, `test_side_door_hardening.py`). **Selected: EMS.** | Mustafa | **DECIDED — EMS selected with evidence** | n/a | none | none |
| ems-ambulance-status-cas | P0/P1 (proven — the one EMS mutation with no CAS at all) | `services.py::update_ambulance_status` did `model.status = status` for any client-supplied string, with zero version check and zero row lock — the single EMS mutation without the CAS every sibling mutation (`update_incident_status`, `dispatch_incident`, `submit_epcr`) already has. A stale status-update request racing a concurrent `dispatch_incident` call (which locks and version-checks this same ambulance row) could silently flip a just-dispatched ambulance's status back to "available", making it eligible for a second, simultaneous dispatch — the exact "duplicate resource allocation" race the rest of this domain's dispatch logic is otherwise careful to prevent. Fixed: added `AmbulanceStatus` enum-membership validation (closes "arbitrary string"), `.with_for_update()` + version CAS matching `update_incident_status`'s exact established pattern, wired through the same `_run_ems_command` wrapper (If-Match/Idempotency-Key), consistent with this domain's own sibling convention rather than importing a different domain's no-header pattern. | Mustafa | **FIXED — VERIFIED** (negative-proofed, race reproduced directly at the service layer) | bf1e9fab | none | none |
| nursing-vertical-slice | P0/P1 (proven — role gate, state machine, ownership validation) | Nursing (Patient Assignment → Task lifecycle) selected as the next vertical slice: LIVE persistence (13/15 `nursing_*` tables migration-confirmed, `20260716_0002_nursing_platform.py`), not touched by Abu Ali's recent commits (care_continuum/ehr/identity/national/national_data/orm_topology.py/trust), and an existing read-gate (`ClinicalNursingTaskReadGate`, already tested) signaling a real, partially-hardened clinical domain. Found: (1) `assign_patient`/`unassign_patient`/`create_task`/`update_task`/`complete_task`/`defer_task` had zero role check at all; (2) `update_task` did a raw `setattr` loop over the ENTIRE request body with no exclusion list — `status` included, letting a generic field-update silently rewrite clinical state and bypass `complete_task`/`defer_task`'s own (previously nonexistent) semantics entirely; (3) `assign_patient`'s `nurse_id` was pure client input, constrained only by an FK to `lab_users.id` (any user, any lab, any role). Fixed: `_NURSING_WRITE_ROLES` (admin/master_admin/doctor/nurse) gate on all 6 mutation routes; new `_TASK_TRANSITIONS` state machine (pending→completed/deferred, deferred→completed/deferred, completed terminal) + `.with_for_update()` CAS + protected-field exclusion list + audit logging, added to `update_task`/`complete_task`/`defer_task`; `assign_patient`'s `nurse_id` now validated to resolve to a real `nurse`-role `LabUser` in the same lab (same pattern as `create_order`'s `doctor_user_id`/radiology's `radiologist_id`). | Mustafa | **FIXED — VERIFIED where provable; see nursing-cross-base-fk-topology for what is BLOCKED** | 5a19361f | see next row | none |
| nursing-orm-migration-type-mismatch | P1 (proven, cross-domain pattern — correctness, not security) | All 23 `ForeignKey("lab_users.id")` columns in `app/nursing/models.py` were declared `String(26)` in the ORM while the real migration creates them `Integer` (matching `LabUser.id`'s real type). Verified against a real local PostgreSQL 16 instance (spun up specifically for this, then torn down) — not SQLite, which never enforces column types and would hide this entirely: a numeric-looking string inserts fine via Postgres's implicit text→integer cast, but any non-numeric value (e.g. a ULID, the exact shape this same file's own primary keys use) raises `psycopg2.errors.InvalidTextRepresentation` at commit time, in real production. The identical pattern (String(26) declared, Integer really stored, for a `lab_users.id`/other legacy-Integer-PK reference) also exists in `app/radiology/models.py`'s `radiologist_id` (`sa.Integer()` in its migration too) — NOT fixed there this pass (Radiology is already closed/verified; my own `radiologist_id` validation there already constrains input to numeric strings, so it isn't exploitable today, but the latent type mismatch is real and cross-domain). Fixed in Nursing only (all 23 fields, pure ORM-layer change, zero migration/schema risk since the migration was already correct). | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven) | 5a19361f | none | If a third domain shows the same String(26)-vs-Integer-for-lab_users.id pattern, this becomes Section-13-detector territory (deterministic: grep every `Column(String(26), ForeignKey(...))` against its own migration's declared type). Radiology's instance is documented, not fixed, since it's currently non-exploitable. |
| nursing-cross-base-fk-topology | BLOCKED — protected architectural decision, not mine to fix | `NursingBase` (`app/nursing/base.py`) is its own separate `declarative_base()`; every cross-domain `ForeignKey` it declares (`lab_users.id`, `patients.id`, `hospital_departments.id`, `national_encounters.id`) cannot resolve within its own `MetaData` — directly reproduced: `'lab_users' in NursingTask.metadata.tables` is `False`. This is the *exact* NR-086/NR-078 class of defect Abu Ali's branch is actively fixing via `app/orm_topology.py` ("the one MetaData the mutually-referencing bases share"), and his own commit describes precisely this failure mode (`session.add(...); session.flush()` → `NoReferencedTableError`) for 76 other tables across 5 other bases (CareContinuumBase/EHRBase/DataPlatformBase/TrustBase/IdentityBase, merged with Base+NationalBase) — `NursingBase` is not yet in that measured closure. **This means every Nursing mutation that flushes a row with one of these FK columns currently fails in production, independent of anything in this pass.** Not fixed here: this is squarely Abu Ali's active, canonical architecture work (main migration architecture / cross-domain contracts) — touching `orm_topology.py` myself would duplicate/conflict with in-progress work I do not own. Pinned with a direct reproduction (`test_nursing_cross_base_fk_topology_blocks_flush`) rather than silently worked around. | — | **BLOCKED — evidence documented, handed to Abu Ali** | n/a | Abu Ali (or whoever extends `orm_topology.py`'s measured closure) | Add `NursingBase` to the shared-metadata closure the same way the other 5 referring bases were added; the pin test will then start failing (in the good sense — `lab_users` will be present), signaling it's time to re-enable full HTTP-level nursing mutation tests. |
| nhdw-admission-vertical-slice | P0/P1 (proven — role gate, cross-tenant bed, CAS) | NHDW (`app/nhdw/`) selected as the next vertical slice after re-checking Abu Ali's recent commits (care_continuum/ehr/identity/national/national_data/orm_topology.py/trust — no overlap) and confirming the earlier ems-domain-discovery note about `app/hospital/` alone being LATENT: NHDW is a *separate*, LIVE package (own migration `20260716_0001_nhdw_platform.py`, 14 real tables, registered in `app/factory.py`) implementing a full admission→transfer→discharge journey. Found: (1) `create_admission`/`update_admission`/`discharge_admission`/`transfer_admission` had zero role check at all; (2) `transfer_patient`'s target-bed lookup (`to_bed_id`, client input) had NO `lab_id` filter — every sibling lookup in the same file (department, create_admission's own `bed_id`) was correctly scoped — letting a caller transfer a patient into another lab's bed and overwrite its `current_patient_id` across the tenant boundary; (3) `update_admission`/`discharge_patient`/`transfer_patient` read-checked-then-wrote `Admission`/`Bed` state with no row lock and never incremented the (previously unused) `version` column. Fixed: `_NHDW_ADMISSION_WRITE_ROLES` gate (admin/master_admin/doctor/nurse) on all 4 routes; `Bed.lab_id == lab_id` filter + 404-on-miss added to the `to_bed_id` lookup; `.with_for_update()` on admission/bed rows in all three mutation paths (plus `create_admission`'s own bed lookup) + `version += 1`. | Mustafa | **FIXED — VERIFIED** (the cross-base topology blocker noted below was itself resolved in a follow-up pass, `cf35ef8a`; only the migration gap remains) | 73626f5e | see rows below | none |
| nhdw-admission-cross-base-relationship-topology | RESOLVED this pass | `Admission` (and 12 sibling NHDW models) declared 21 cross-declarative-base `relationship("Patient"/"HospitalMaster"/"HospitalDepartment"/"Room"/"Bed"/"Clinic", ...)` entries; `NHDWBase` is its own `declarative_base()`, so none could resolve (`relationship()` STRING targets resolve via the declarative *registry*, not `MetaData` — a shared `MetaData` a la `orm_topology.py` does not fix this failure mode, confirmed with a minimal two-registry SQLAlchemy repro). Exhaustively grepped every call site in `routes.py`/`services.py`/`kpi.py`: zero references to any of these 21 relationships anywhere — every real cross-model lookup already goes through explicit `db.query(...)`. Proven dead, non-canonical (no `back_populates`/`backref` anywhere), no migration/data dependency, safe to remove. Removed all 21 (kept the 2 same-registry ones: `Discharge.admission`, `HospitalMessage.parent`). This was a same-file dead-code removal, not a topology/migration/canonical-ownership change, so it did not require Abu Ali's decision after all — the earlier "hand-off" was itself over-cautious once the exact mechanism was understood. Confirmed: `db.query(Admission)` and every sibling model now configure and query correctly, in SQLite and real Postgres alike. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven, negative-proofed) | cf35ef8a | none | none |
| nhdw-log-action-argument-order | P1 (proven, audit-integrity — surfaced only once the row above was fixed) | All 24 `log_action(...)` calls in `app/nhdw/services.py` used the wrong positional order against the real signature `(db, action, resource_type, resource_id, user_id, user_role, lab_id, details, ...)` — `lab_id` was never recorded on any NHDW audit entry, `resource_type`/`resource_id` were always wrong, and for the 6-arg calls the whole `details` dict landed on `user_role`, crashing outright (sqlite3 cannot bind a raw dict to any parameter) the instant any mutation with a details payload reached the audit call. Fixed: rewrote all 24 with explicit keyword arguments and a correct `resource_type` string per call. | Mustafa | **FIXED — VERIFIED** | cf35ef8a | none | If a third domain's `log_action` calls show this same positional-mismatch shape, this becomes Section-13-detector territory (deterministic: any `log_action(db, "...", X, lab_id, user_id, ...)` call where `X` isn't a string literal is suspect). |
| nhdw-model-to-dict-metadata-collision | P1 (proven, correctness — surfaced only once the row above was fixed) | `app/nhdw/routes.py::_model_to_dict` used each `Column`'s own `.key` from `__table__.columns`. For `metadata_ = Column("metadata", JSON, ...)` (present on every NHDW model, trailing underscore specifically to avoid colliding with the declarative class's own built-in `.metadata` attribute), `.key` defaults to the DB column name "metadata", not the Python attribute "metadata_" — so `getattr(instance, "metadata")` silently returned the class's SQLAlchemy `MetaData()` object instead of the JSON field's value, and FastAPI's `jsonable_encoder` recurses on that object until the recursion limit, turning every successful create/update response in this file into a 500. Fixed: iterate `sqlalchemy.inspect(instance).mapper.column_attrs` instead, which correctly maps to `"metadata_"` regardless of DB column name. | Mustafa | **FIXED — VERIFIED** | cf35ef8a | none | none |
| nhdw-audit-log-resource-id-type-mismatch | P2 (proven, cross-domain latent pattern — correctness, not exploitable) | `AuditLog.resource_id` (`app/models/audit_log.py`, shared across every domain) is `Integer`, but NHDW's (and Nursing's) primary keys are ULID `String(26)` — passing e.g. `discharge.id` as `resource_id` raises `psycopg2.errors.InvalidTextRepresentation` on real Postgres; SQLite's dynamic typing silently accepted it, hiding this entirely (the same String-vs-Integer class already fixed once this session for Nursing's `lab_users.id` FK columns — see `nursing-orm-migration-type-mismatch` above — except here it's the *shared* audit table, not a single domain's model). Widening `audit_logs.resource_id` is a schema change and out of scope for this pass (same human-approval boundary as the row below). Nursing's own `log_action(..., assignment.id, ...)` calls have this identical latent defect — not fixed there this pass (masked anyway by `nursing-cross-base-fk-topology`, which still blocks Nursing's audit calls from ever being reached). Fixed in NHDW only: all 24 calls now pass `resource_id=None` and fold the real id into `details["resource_id"]` instead. | Mustafa | **FIXED in NHDW and Nursing (`medication.py`) — VERIFIED (real-Postgres-proven for NHDW)**; LIMS/hospital_service.py instances left for human review (see `log-action-arg-order-pattern-registered` below) | 43ccfef9 | none | If a third domain hits this, `AuditLog.resource_id` widening (e.g. to `String`) becomes a real proposal to put to a human — it's a shared table, so this is not a call to make unilaterally regardless of how many domains repeat it. |
| log-action-arg-order-pattern-registered | Engineering Intelligence — pattern generalization | Per this session's engineering-control-plane directive ("convert a verified defect into a reusable pattern; search for other instances using the new mechanism, not a brute-force scan"), generalized the NHDW `log_action` finding into `scripts/log_action_arg_order_guard.py` — a deterministic AST-based detector (no LLM, no network, no DB; whole-repo scan in ~0.35s), self-tested against both confirmed-broken shapes and the fixed/unrelated shapes (4/4, `--self-test`). Repo-wide run found 28 candidates across 6 files / 4 domains. Fixed the 18 in domains already owned this session: `app/nhdw/offline.py` (2, RULE_A shape), `app/nursing/services.py` (6, the exact instance this repair queue had already flagged as "latent, masked by nursing-cross-base-fk-topology" — including two calls I myself added earlier this session, copying the pre-existing broken convention without re-verifying it at the time), `app/nursing/coordination.py` (8) and `app/nursing/medication.py` (2, not previously audited this session). Negative-proofed: stash reproduces exactly 28 hits, restore returns to 10 (the deliberately deferred count). | Mustafa | **FIXED — VERIFIED** (18/28 candidates; detector registered as a reusable repo-wide check) | 43ccfef9 | none | Re-run `python3 scripts/log_action_arg_order_guard.py` after any change to `log_action` call sites or its signature; wire into `scripts/quality_gate.py`'s orchestration if/when that consolidation pass happens (not done this pass — scope discipline). |
| log-action-arg-order-lims-needs-review | P2 (proven pattern match — FIXED this pass, was NEEDS REVIEW) | `scripts/log_action_arg_order_guard.py` flagged 5 RULE_B sites in `app/lims/routes.py:344` and `app/lims/services.py:78,123,194,275`. `resource_type`/`resource_id`/`user_id`/`user_role` were all already correct (LIMS already threads `current_user.role`/`"lab_tech"` through); only the trailing message string landed in `lab_id` (Integer) instead of `details`. Verified each call site's `lab_id`/`specimen.lab_id` availability individually rather than assuming uniformity (`SpecimenService.transition()` only has `specimen`, not a `lab_id` local — used `specimen.lab_id`). LIMS primary keys are Integer, so `resource_id` stays populated directly (no folding needed, unlike NHDW/Nursing). | Mustafa | **FIXED — VERIFIED** (existing `test_lims_release_capability_gate.py`/`test_lims_tenant_isolation.py`, 9/9, unaffected; detector 0 hits) | 8c300f88 | none | none |
| log-action-arg-order-hospital-service-needs-review | P1 (proven pattern match, same RULE_A shape as NHDW's original bug — FIXED this pass, was NEEDS REVIEW) | `scripts/log_action_arg_order_guard.py` flagged 5 RULE_A sites in `app/services/hospital_service.py:70,92,109,151,780` (backs `app/routes/hospital.py`) — identical shape to NHDW's original defect. `HospitalMaster`/`Campus` use Integer primary keys, so `resource_id` stays populated directly. This file also has 5 OTHER, newer `log_action` calls (bed assign/discharge/transfer, OT status, surgical checklist) already using the correct keyword convention — confirming the fix matches this file's own established pattern. Two findings surfaced, neither fixed here (kept out of scope to keep this a log_action-only change): (1) `update_hospital`'s `for k, v in data.items(): setattr(hospital, k, v)` is the same unguarded mass-assignment pattern already closed in Nursing/NHDW this session; (2) `create_appointment`'s `Appointment` model (`app.national.domain.appointment`) is separately already-documented this session (`ems-domain-discovery` finding) as LATENT — no migration for `national_appointments` — so that one call's fix is correctness-only, not exercised via a real flush in the new tests. Also shares NHDW's already-recorded `hospitals`/`hospital_departments`/`hospital_rooms`/`hospital_beds` migration gap (same underlying tables, reached via a second call path) — not a new blocker, the existing pin (`test_hospital_structure_tables_have_no_migration`) already covers it. | Mustafa | **FIXED — VERIFIED** (4 new tests asserting real AuditLog rows; detector 0 hits repo-wide) | 8c300f88 | none | `update_hospital`'s mass-assignment gap is a real candidate for a future, dedicated Hospital vertical-slice pass (role gate + mass-assignment guard + CAS, matching the Nursing/NHDW pattern) — not started this session. |
| self-audit-agent-mutation-hardening | P1 (autonomous-mutation safety — proven gaps, now closed) | Follow-up to the row below: hardened `scripts/self_audit_agent.py`'s `--fix` path with (1) a path allow-list (`PROTECTED_PATH_PREFIXES`/`PROTECTED_PATH_SUBSTRINGS`, checked against the RESOLVED path, fails closed on path traversal); (2) a change budget (`MAX_FILES_PER_RUN=5`, `MAX_CHARS_CHANGED_PER_FILE=400`); (3) exact-scope rollback (each target file's content snapshotted before mutation; failure restores exactly those files, no `git checkout -- .`, so unrelated uncommitted work in the tree survives); (4) impact-aware verification (`_select_impact_aware_tests` maps changed `backend/app/X.py` files to `backend/tests/test_X.py` by convention; TARGETED runs only those, UNKNOWN broadens to the full suite rather than trusting an unmapped change); (5) `_commit_fixes` now stages only the exact files touched, not `git add -A`. | Mustafa | **FIXED — VERIFIED** (9 new behavioral tests, negative-proofed) | 2ba252bb | none | none |
| autonomous-repair-family-fate-decisions | Engineering Intelligence — retirement/hardening decisions for the 4 questionable components | Per this session's directive: decided the fate of the four components classified in the row below, without deleting any of them (no active dependency alone is not sufficient grounds to delete, per this session's own retirement policy). `gula_autofix.py` → **DEPRECATE** (in-file notice added pointing to `auto_heal.sh`, its safer superset; not wired anywhere, so nothing breaks). `gula_guardian.py` → **DO NOT ACTIVATE AS-IS** (in-file notice added; its `while True: sleep(300)` must become a bounded, cron-triggered single-shot invocation before ever being wired in — never activate the standing loop). `secure_self_patcher.py` → **STUB, DO NOT TREAT AS FUNCTIONAL** (in-file notice added; `apply_patch()`/`rollback()` do nothing but log — real zero-downtime patching, if ever needed, should be built against this repo's actual `blue-green-deploy.yml`/`docker-compose.yml` path, not by completing these placeholders). `self_audit_agent.py` → **HARDEN** (done this pass, see row above). | Mustafa | **DECIDED — evidence-based, in-file guards added, nothing deleted** | 2ba252bb | none | A human/repo-owner decision to actually delete `gula_autofix.py`/`gula_guardian.py`/`secure_self_patcher.py` (rather than just mark them deprecated/non-functional in place) remains open — deletion itself was deliberately left for explicit sign-off. |
| autonomous-repair-family-inventory | Engineering Intelligence — forensic inventory (executable evidence, not docstring-based) | Per this session's engineering-control-plane directive: a focused audit of the "autonomous repair family" — `backend/app/core/self_healing.py`, `backend/app/core/auto_repair.py`, `scripts/auto_heal.sh`, `scripts/self_heal.py`, `scripts/gula_guardian.py`, `scripts/gula_autofix.py`, `scripts/secure_self_patcher.py`, `scripts/self_audit_agent.py` — classified by running/reading each, not by name or docstring. **WORKING, wired to production**: `scripts/auto_heal.sh` (cron `*/5 * * * *` via `scripts/server-setup.sh`; bash watchdog for nginx + Docker containers, has a real `MAX_RESTARTS_PER_HOUR=3` rate-limit guard) and `scripts/self_heal.py` (cron `* * * * *`, same install script; Python ASHS with a documented LOW/MEDIUM/HIGH risk policy). **DUPLICATE/OBSOLETE**: `scripts/gula_autofix.py` — a Docker-restart-on-unhealthy script covering a strict subset of `auto_heal.sh`'s logic, with NO rate-limit/backoff guard, and not referenced by any cron/systemd/Makefile/CI entry anywhere in the repo (grepped exhaustively) — an orphaned, less-safe reimplementation. **UNCONNECTED, and itself violates this session's own "no permanent polling daemon" rule**: `scripts/gula_guardian.py` — a real `while True: ...; time.sleep(300)` daemon (not wired to cron/systemd/anywhere), calling `scripts/audit_verifier.py` (a real, useful integrity check) but otherwise unreachable in this repo's actual deployment path; if ever activated, needs converting to a triggered/cron invocation rather than a standing loop. **STUB / autonomy theater — evidence, not assumption**: `scripts/secure_self_patcher.py` — `apply_patch()` only logs "Starting"/"Patch applied successfully" around 5 comment placeholders (pre-flight, backup, staging apply, health probes, traffic swap) with NO actual implementation of any of them; `rollback()` is a single log line with a comment ("# Implementation of rollback logic") and no code; only `verify_update_signature()` is genuinely implemented (real SHA-256 check). No `__main__` entry point — not even directly runnable. Hardcodes `/home/ubuntu/gula-platform/...` (doesn't match this repo's actual deployment path) and an external `UPDATE_MANIFEST_URL` never fetched by any code in the file. **PARTIAL, real but weaker than its docstring implies**: `scripts/self_audit_agent.py` — genuinely wired (`make self-audit`/`make self-audit-fix` in the Makefile; `scripts/digitalocean-manage.sh` calls `--report-only`), makes a real Claude API call, and DOES roll back via `git checkout -- .` when post-fix verification fails (contrary to an initial read suggesting no rollback existed at all) — but: (1) `print_report()` was fully dead code (see the row above, now fixed, 86389a3a); (2) `_apply_auto_fixes()` does a blind, unvalidated string search/replace anywhere under `backend/` with no path exclusion for security/migration/config files; (3) `_commit_fixes()` runs `git add -A`, staging any unrelated uncommitted changes in the tree, not just the fix; (4) `_verify_after_fix()` only checks `py_compile app/main.py` (one file) + `pytest tests/test_domain.py` (one hardcoded test file), never the actually-changed area — not impact-aware; (5) the failure-path `git checkout -- .` discards the ENTIRE working tree, not just this run's changes, with no `git status`/stash-first guard the repo's own Git Safety Protocol requires elsewhere. `--watch` mode is also dead code (`if args.watch: pass` twice). Not hardened this pass beyond the dead `print_report()` fix — the auto-fix safety redesign (path allow-list, targeted revert, impact-aware verification) is a real design decision, not a mechanical one, and is recorded as a recommendation rather than implemented unilaterally. | Mustafa | **VERIFIED (WORKING: auto_heal.sh, self_heal.py) / DUPLICATE (gula_autofix.py) / UNCONNECTED+ANTI-PATTERN (gula_guardian.py) / STUB (secure_self_patcher.py) / PARTIAL, ONE BUG FIXED (self_audit_agent.py)** | 86389a3a | none for the classification itself; `self_audit_agent.py`'s remaining safety gaps are a design decision, not mine to redesign unilaterally | Recommend, don't implement without sign-off: (a) delete or clearly deprecate `gula_autofix.py` in favor of `auto_heal.sh`; (b) either wire `gula_guardian.py` into cron with a bounded single-shot invocation (never a standing loop) or remove it; (c) either implement `secure_self_patcher.py` for real or delete it — a stub that logs "applied successfully" for actions it never performs is the exact autonomy theater this session's directive explicitly warns against; (d) harden `self_audit_agent.py`'s `--fix` path (path allow-list, `git stash`-scoped revert instead of `git checkout -- .`, impact-aware `_verify_after_fix()`) as a dedicated, reviewed change. |
| nhdw-invalid-detail-ar-kwarg | P2 (proven — unreachable error branch) | 4 call sites passed an invalid `detail_ar=` keyword to plain `fastapi.HTTPException(...)` (bed-lookup 404, bed-status 409, already-discharged 409, `get_dashboard_config` 404) — `HTTPException` has no such parameter, and this pattern appears nowhere else in the repo (no shared bilingual-exception class it was meant to route through), so each of these 4 branches raised `TypeError` instead of the intended status code whenever it should have fired. Fixed: dropped the invalid kwarg, kept the English `detail`. | Mustafa | **FIXED — VERIFIED** | cf35ef8a | none | none |
| nhdw-hospital-structure-migration-gap | P1 (proven, independent of every row above — REMAINING blocker) | No migration anywhere creates `hospitals`, `hospital_departments`, `hospital_rooms`, or `hospital_beds` (`app/hospital/models`'s own tables, which `create_admission`/`transfer_patient` query) — confirmed by exhaustive full-text grep across every file in `backend/migrations/versions/` (including the one migration with a dynamic table-name helper, `20260814_0002_organization_structure.py`, confirmed to only ever create `niam_*` tables) and, independently, against a real throwaway local PostgreSQL 16 instance (alembic's chain fails earlier for an unrelated reason — a pre-existing Pharmacy migration FK type error, Abu Ali's active work area, not investigated further). Since `Admission.department_id` is NOT NULL and `create_admission` unconditionally queries `HospitalDepartment` whenever one is supplied (every real admission), this alone still 500s a real Alembic-migrated deployment even though every other blocker in this domain is now resolved. Not fixed here: a new migration needs human approval per this repo's own CLAUDE.md ("Requires human approval: DB schema changes"). Pinned directly (`test_hospital_structure_tables_have_no_migration`). | — | **BLOCKED — evidence documented, requires human approval for a new migration** | cf35ef8a | Human approval (new migration is out of autonomous scope per CLAUDE.md) | Add an additive, idempotent migration creating `hospitals`/`hospital_departments`/`hospital_rooms`/`hospital_beds` (at minimum; `app/hospital/models` also declares campuses/buildings/floors/clinics/units/etc. if those are needed too) with nullable/server-defaulted columns per this repo's migration policy; the pin test will then start failing (in the good sense), and the NHDW admission journey becomes actually deployable end-to-end for the first time. |
| pharmacy-drug-substitution-fk-type-mismatch | P1 (proven — blocked a real `alembic upgrade head`) | `pharmacy_drug_substitution_rules`/`_requests` (`20260815_0023_drug_substitution.py`) declared `original_drug_catalog_id`/`alternative_drug_catalog_id` as `sa.String(26)` FKs against `pharmacy_drug_catalog.id`, which is really `sa.Integer()` — `DatatypeMismatch` on a real PostgreSQL 16 `alembic upgrade head`. The persistent `gula_certproof` database was confirmed NOT to be genuine sequential-replay evidence (missing this table entirely despite being stamped past this revision), so correcting the migration in place did not violate "never modify a migration existing DBs have already run." Fixed in both the migration and `app/pharmacy/models.py`'s `DrugSubstitutionRule`/`DrugSubstitutionRequest` ORM columns. | Mustafa | **FIXED — VERIFIED** (real-Postgres UP→DOWN→re-UP proven) | 0083480c | none | none |
| payments-vertical-slice-discovery | Domain selection evidence | Evidence-based discovery for the next vertical slice, continuing the master-directive baseline's execution queue: `app/payments/` (`pay_*`, 19 files) selected — LIVE, unconditionally registered (5 routers in `app/factory.py`, no feature gate, unlike the separate schema-only `ENABLE_FINANCIAL_ENGINE`-gated `app/financial/` package), backed by 5 real migrations, untouched by this session or Abu Ali's recent commits. Candidates checked and rejected as LATENT (no real migration): `insurance` (`ins_*`), `citizen_platform`, `chronic_care`, `document_intelligence` (`docint_*`), `knowledge_graph`, `fhir`, `health_data` (`hd_mdm_*`), `research_platform` (`rp_*`). `devices` (`device_*`) is also LIVE but smaller/lower-stakes; `payments` selected for being both live and the highest-severity candidate (real money movement). | Mustafa | **DECIDED — payments selected with evidence** | n/a | none | none |
| payments-role-gate-tenant-scope-audit | Audit result — CLEAN, no defect | Every mutating route across all 5 payments route files (`routes.py`/`control_routes.py`/`fx_routes.py`/`orchestration_routes.py`/`subscription_routes.py`) already has `Depends(require_permission(...))` plus `assert_institution_access(...)` tenant-scope enforcement — audited route-by-route, not pattern-matched. No role-gate or BOLA gap found (unlike Laboratory/Imaging/EMS/Nursing/NHDW's pre-audit state); this domain was already at the mature end-state those five reached only after their own hardening passes. | Mustafa | **AUDITED — CLEAN** | n/a | none | none |
| payments-capture-refund-cas | P0 (proven — double real-money postings, not just a status flip) | `capture_cash`/`close_cash_shift`/`approve_refund`/`process_cash_refund` in `app/payments/service.py` had zero concurrency guard anywhere (`grep -rn with_for_update app/payments/` = 0 matches repo-wide) — the same TOCTOU shape already fixed 5 times this session (`lab-slice-cancel-order-cas`, `lab-slice-device-ingestion-cas`, `imaging-slice-order-status-cas`, `ems-ambulance-status-cas`, NHDW's admission/bed CAS rows), now found in the highest-stakes domain: two real concurrent threads against a real disposable PostgreSQL 16 database (`gula_pay_race`) proved a double cash capture (2 `SUCCEEDED PaymentAttempt` rows, **$200 posted to the ledger's `CASH_ON_HAND` account for a single $100 invoice**) and a double refund payout (**$200 posted to `REFUNDS_AND_ALLOWANCES` for a single $100 approved refund**). None of `PaymentIntent`/`CashShift`/`PaymentRefund`/`PaymentInvoice` has a `version` column, so fixed with `SELECT ... FOR UPDATE` pessimistic row locks (zero schema/migration risk), added to all 4 mutation methods plus `request_refund` (closes a secondary refund-amount-reservation race). Full evidence: `docs/security/PAYMENTS_CAPTURE_REFUND_CAS_STATUS.md`. Sibling gap (same zero-lock pattern, lower severity — workflow/config, not direct cash movement) documented, not fixed, in `control_service.py`/`fx_service.py`/`orchestration_service.py`/`subscription_service.py`. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven both directions, negative-proofed, 2 new regression tests, 306 passed/4 skipped/0 failed) | cbb1c6a5 | none | If prioritized, the identical `for_update=True` pattern applies directly to the 4 sibling services — no new mechanism needed. |
| devices-vertical-slice-discovery-and-audit | Domain selection + audit result | `app/devices/` (`device_*`/`wearable_*`) selected next via the same discovery method — LIVE, unconditionally registered (`app/factory.py:652`), 7 real migrations, untouched by this session/Abu Ali. Role-gate/tenant-scope audit: **CLEAN** — every mutating route already requires `require_institutional_permission`, and wearable-measurement ownership (`Patient.id == payload.patient_id AND Patient.lab_id == lab_id`) is correctly validated, no BOLA. | Mustafa | **AUDITED — CLEAN** | n/a | none | none |
| device-outbox-claim-cas | P0 (proven — double dispatch of the same outbox message) | `app/devices/outbox.py::process_batch` (the transactional-outbox worker behind `POST /device-integration/outbox/process`) claimed "due" messages with a plain, unlocked `SELECT` before marking them `processing` and invoking the dispatcher — the same TOCTOU shape as `payments-capture-refund-cas`, now in the message-dispatch domain. Since GULA runs multiple backend replicas in production (`make scale REPLICAS=N`), two concurrent calls to this endpoint proved (two real threads, real disposable PostgreSQL 16) the SAME message dispatched twice (`dispatch_calls: [1, 1]`). Current dispatcher is simulation-only so today's blast radius is limited, but the module's own docstring states it "exercises durable queue semantics" ahead of real device-command dispatch — a duplicate real device command (printer job, gateway config push) the moment a real dispatcher is wired in. `DeviceOutboxMessage` has no `version` column; fixed with `.with_for_update(skip_locked=True)` on the claim query — the idiomatic outbox-pattern primitive (skip rows already claimed rather than block), zero schema change. Full evidence: `docs/security/DEVICES_OUTBOX_CAS_STATUS.md`. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, 1 new regression test spying on the real call site, 301 passed/4 skipped/0 failed) | (pending push, next commit) | none | none |
| devices-wearable-webhook-global-secret | P2 (candidate, capped severity, documented not fixed) | `ingest_wearable_webhook` authenticates with a single global per-provider HMAC secret, not per-lab, and trusts the envelope's own `lab_id` — a holder of the shared secret could attribute a measurement to an arbitrary lab/patient pair. Constrained today to `simulation_only=True` payloads only (hard-rejected otherwise with 409) and `ingest_wearable_measurement` separately re-validates patient-lab ownership, so no real clinical data can leak or be corrupted yet. Same tier as `ai-approval-no-tenant`. | — | **NOT FIXED — documented, capped severity** | n/a | none (design decision — per-lab webhook secrets, or signing `lab_id` into the HMAC — not mine to invent unilaterally) | If prioritized: either issue per-lab webhook secrets or include `lab_id` in the HMAC-signed payload so the signature itself authorizes the target lab. |
| live-surface-map-discovery | Ground-truth discovery — corrects an earlier-session classification error | Parsed all 88 `app.include_router(...)` registrations directly from `app/factory.py` (not directory-name inference) and cross-referenced every registered domain's declared `__tablename__`s against the real migration set. **Correction**: `ems-domain-discovery` (this queue, above) called `insurance`/`citizen_platform`/`document_intelligence`/`knowledge_graph`/`health_data`/`research_platform` "LATENT" based on table absence alone — they are actually **route-reachable today** (router mounted, only the backing table missing). Introduced a distinct LIVE/SCHEMA-LATENT category for this shape. Full map: `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`. | Mustafa | **DECIDED — ground truth established, prior classification corrected** | n/a | none | none |
| governance-schema-latent-gap | P1 (proven, route-live/schema-latent — new, largest single-package gap found this session) | Top-level `app/governance/` (governance_router + analytics_router, mounted unconditionally) declares 64 tables; **58 have no migration anywhere** — `gov_clinical_policies`, `gov_critical_result_policies`, `gov_professional_licenses`, `gov_security_policies`, `gov_ai_guardrails`, `gov_ai_audit_events`, `gov_llm_policies`, `gov_national_protocols`, etc. Every mutating endpoint in this router will 500 with `UndefinedTable` on a real deployment. Verified this is a **different package** from `app/identity/governance/` (NIAM identity governance, 6 tables, fully backed, already hardened this session in batches 7a/7b/7c) — the `gov_` prefix collision was checked and ruled out as a source of confusion; those prior "REAL POSTGRESQL VERIFIED" claims are unaffected. | — | **BLOCKED — evidence documented, requires human-approved migration + domain-owner scoping** | n/a | Human approval (new migration for 58 tables is out of autonomous scope per CLAUDE.md; the actual table design needs the domain owner's input, not invented here) | Whoever owns `app/governance/`'s clinical-policy/credentialing/AI-governance/national-interop scope should confirm which of the 58 tables are still wanted before any migration is authored — this is not a mechanical "just add the migration" gap the way the pharmacy FK fix was. |
| national-schema-latent-gap | P1 (proven, route-live/schema-latent — largest gap by table count) | `app/national/` backs 11 mounted routers (rules_engine, background_platform, workflow_runtime, task_engine, notification_platform, document_platform, scheduling_platform, search_platform, observability, ecosystem, ecosystem_gateway, intelligence) declaring 114 tables; **103 have no migration anywhere** (`national_addresses`, `national_admissions`, `national_advance_directives`, and 100 more). Same shape and same blocker as `governance-schema-latent-gap`, at even larger scale. | — | **BLOCKED — evidence documented, requires human-approved migration + domain-owner scoping** | n/a | Human approval + domain-owner scoping, same reasoning as the governance row | Same as governance row — not a mechanical gap. |
| schema-latent-smaller-domains | P2 (proven, same shape, smaller blast radius each) | 7 additional mounted routers with **zero** declared tables backed by any migration: `command_intelligence` (5 tables), `document_intelligence` (21), `health_data` (17), `knowledge_graph` (3), `research_platform` (7), `roadmap` (8), `simulation` (5). Same disposition as the two rows above, recorded together since each is individually smaller. | — | **BLOCKED — evidence documented, requires human-approved migration per domain** | n/a | Human approval + domain-owner scoping per domain | Lowest-effort-per-domain candidates if a human wants to unblock one of these before governance/national (e.g. `knowledge_graph` is only 3 tables). |
| outbox-implementation-inventory | Engineering Intelligence — pattern comparison (Section 6 of the concurrency-continuation directive) | 3 outbox implementations found repo-wide: (1) `app/services/outbox_service.py::OutboxWorker` — canonical, `outbox_events` table, **already uses `with_for_update(skip_locked=True)`**, wired to the `main.py` lifespan background loop — VERIFIED SAFE, no change needed; (2) `app/devices/outbox.py::process_batch` — fixed this session, see `device-outbox-claim-cas` above; (3) `app/kernel/event_bus/outbox.py::OutboxPattern` — in-memory-only (not persisted), race-shaped (`dequeue()` has the identical unlocked check-then-set pattern), but its `dequeue`/`enqueue`/`mark_completed`/`mark_failed` methods have **zero call sites anywhere in the repo** (only the read-only `list_pending()` is ever called, for a stats count in `kernel/routes.py:120`) — DEAD_OR_UNREACHABLE, not fixed since there is nothing reachable to fix. No merge of the 3 implementations proposed — devices' is intentionally tenant-scoped, the canonical one is platform-wide; different guarantees, not a duplication to collapse. Full writeup: `docs/security/SYSTEMIC_CONCURRENCY_FINDINGS.md`. | Mustafa | **DECIDED — 1 VERIFIED SAFE, 1 already fixed, 1 DEAD_OR_UNREACHABLE** | n/a | none | none |
| blood-bank-critical-care-already-hardened | Verification result — no defect, real proof performed | Checked `blood_bank` and `critical_care` (both `system:admin`-gated, table-backed, live) as concurrency-audit candidates. Both already have a mature "legacy method + `_safely`-suffixed hardened method" convention with routes exclusively calling the `_safely` variants (legacy ones confirmed DEAD_OR_UNREACHABLE via exhaustive grep — zero call sites). `blood_bank` additionally has a dedicated real-PostgreSQL concurrency/idempotency/failure-injection test suite (`tests/blood_bank/`, 7 files, env-gated on `BLOOD_BANK_POSTGRES_URL`) — re-ran it against a genuinely `alembic upgrade head`-migrated disposable database (worked around the known `nhdw-hospital-structure-migration-gap` blocker by `alembic stamp`-ing past that one already-filed broken migration in a throwaway DB only, no migration file touched): **32/32 passed**. Not marked VERIFIED merely because the code "looked safe" — actually re-run. | Mustafa | **VERIFIED SAFE — real proof, no code change** | n/a | none | none |
| biomedical-work-order-device-cas | P1 (proven — duplicate side-effect on double-completion, admin-gated so bounded blast radius) | `app/biomedical/application/service.py::update_device_status`/`complete_work_order` read `MedicalDeviceModel`/`WorkOrderModel` rows with a plain unlocked `SELECT` despite both models already inheriting `OptimisticLockMixin` (`version` column present, unused) — the same TOCTOU shape as `payments-capture-refund-cas`/`device-outbox-claim-cas`, and `complete_work_order` had no terminal-state guard at all. Proven on real disposable PostgreSQL 16: two concurrent `complete_work_order` calls on the same work order both succeeded pre-fix (`version` never incremented, side effects silently double-applied — cost totals, device release). Fixed: `.with_for_update()` + `version += 1` on both mutation paths (`create_work_order`'s device status-flip too), plus a new `WorkOrderAlreadyCompletedError` (409, not the existing 404 `WorkOrderNotFoundError` — semantically distinct) rejecting a second completion. Zero schema change (`version` already existed, just unused). Full evidence: `docs/security/BIOMEDICAL_WORK_ORDER_CAS_STATUS.md`. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, 4 new regression tests — biomedical had zero prior test coverage — 316 passed/4 skipped/0 failed) | 40aee3b6 | none | none |
| command-center-emergency-resource-cas | P1 (proven — duplicate side-effect on double-resolution/double-fulfillment, admin-gated) | `app/command_center/application/service.py::resolve_emergency`/`fulfill_resource` — identical shape to `biomedical-work-order-device-cas` (unused `OptimisticLockMixin.version`, no lock, no terminal-state guard). Proven on real disposable PostgreSQL 16: two concurrent `resolve_emergency` calls on the same emergency both succeeded pre-fix, both `[RESOLVED]` notes appended to the audit trail, `version` never incremented. Fixed: `.with_for_update()` + `version += 1` + new `EmergencyAlreadyResolvedError`/`ResourceRequestAlreadyFulfilledError` (409). Full evidence: `docs/security/COMMAND_CENTER_CONCURRENCY_STATUS.md`. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, 4 new regression tests — command_center had zero prior test coverage, 320 passed/4 skipped/0 failed) | (pending push, next commit) | none | none |
| public-health-outbreak-alert-cas | P1 (proven — duplicate transition + unvalidated status string, admin-gated) | `app/public_health/application/service.py::update_alert_status` — same unused-version/no-lock/no-terminal-guard shape, plus a genuinely unvalidated client-supplied `status` string (any value accepted, not checked against the real `OutbreakStatus` enum). Proven on real disposable PostgreSQL 16: two concurrent transitions to `declared_over` on the same outbreak both succeeded pre-fix. Fixed: `OutbreakStatus(status)` enum validation (`InvalidOutbreakStatusError`, 400) + `.with_for_update()` + `version += 1` + terminal-state guard on `DECLARED_OVER` (`OutbreakAlreadyDeclaredOverError`, 409). Deliberately did NOT invent a full legal-transition graph across the other 4 statuses — no evidence in the codebase constrains those, matching this session's own `imaging-slice-order-transition-graph` precedent. Full evidence: `docs/security/PUBLIC_HEALTH_CONCURRENCY_STATUS.md`. | Mustafa | **FIXED — VERIFIED** (real-Postgres-proven, negative-proofed, 4 new regression tests — public_health had zero prior test coverage, 320 passed/4 skipped/0 failed) | (pending push, next commit) | none | none |
| systemic-concurrency-pattern-register | Engineering Intelligence — cross-domain pattern named per Section 14 of the concurrency-continuation directive | The identical "unused `OptimisticLockMixin`, no terminal-state guard" defect shape was found and fixed independently in 3 domains this session (biomedical, command_center, public_health) — meets the 3+-domain threshold for a systemic finding. Named the pattern, documented the canonical safe fix and the regression-test convention, evaluated (and declined, per the same discipline as `imaging-slice-detector-decision`) building a repo-wide AST detector — three confirmed instances doesn't yet justify the cross-procedural/semantic complexity a reliable detector would need. Full writeup: `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md`. | Mustafa | **DECIDED — pattern registered, detector NOT built (documented limitation)** | n/a | none | Check for this exact shape first, manually, in every future domain audit before deeper investigation — it has been the highest-yield finding type this entire session. |
| idempotency-inventory-clinical-command-guard | Verification result — no defect, real evidence | `app/clinical/command_guard.py::ClinicalCommandGuard` (used by radiology/critical_care/lims/blood_bank/pharmacy/ems/hospital) is the real canonical clinical-command idempotency mechanism: atomic claim via a real DB unique constraint + `IntegrityError`→409 handling (not a check-then-insert race), explicit rejection of same-key-different-payload, and an explicit claim+complete-in-same-transaction contract stated in its own docstring. Already exercised by 9 real-Postgres failure-injection tests in `tests/blood_bank/`, re-run this session (32/32 passed against a genuinely head-migrated database). | Mustafa | **VERIFIED SAFE — real proof, no code change** | n/a | none | none |
| idempotency-core-module-dormant | P2 (documented, not fixed — no live caller, so no reachable vulnerability today) | `app/core/idempotency.py::idempotency_check` — a generic header-based idempotency dependency, migrated (`idempotency_keys` table exists) and unit-tested in isolation, but **zero call sites anywhere in the repo** outside its own test file — none of the 4 routes its own docstring claims to protect actually declare `Depends(idempotency_check)`. DORMANT, not DEAD (schema and tests exist, just never wired up). While reading it, found a latent defect: the "new key" path does `INSERT ... ON CONFLICT DO NOTHING` then unconditionally returns `is_duplicate=False` without checking whether its own insert actually won the race (no `rowcount`/`RETURNING` check) — two concurrent requests with the same never-seen key would both proceed to execute business logic, the exact class of bug already fixed 6 times this session elsewhere. Not fixed here: no live route reaches this code, so there is nothing to reproduce a real HTTP-level exploit against; fixing dead code would be scope-broadening beyond a real defect, which this session's own directives explicitly warn against. | — | **DOCUMENTED — DORMANT module, latent race recorded for whoever wires it up next** | n/a | none | Before wiring `idempotency_check` into any real route, first add the same `rowcount`-checked atomic claim pattern `ClinicalCommandGuard`/payments/devices already use. |
| capabilities-package-9-of-10-routers-dead | Live-surface correction | `app/capabilities/` was previously counted as one TABLE-BACKED domain (1 table via its one mounted router). Corrected: it actually contains 10 independent sub-packages, each with its own `routes.py` + `commands/` subpackage (46 command files) — only `fhir_interoperability` is ever imported by `app/factory.py`; the other 9 (`clinical_foundation`, `document_management`, `encounter_management`, `healthcare_consent`, `provider_management`, `reporting_service`, `search_service`, `storage_service`, `workflow_engine`) have zero references anywhere in the codebase, confirmed by exhaustive grep. Reclassified DEAD in `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`. | Mustafa | **DECIDED — 9 of 10 sub-packages reclassified DEAD** | n/a | none | If any of these 46 commands are meant to ship, mounting the router is a routing-layer decision, not something to do speculatively here. |
| authorization-expansion-capability-inventory | Engineering Intelligence — bounded discovery pass (Authorization Expansion directive) | Built an evidence-based authorization coverage matrix consolidating this session's own vertical-slice audits (10 legacy-axis domains, ~186 individually-verified routes) + the NIAM organization-RBAC axis (135 routes, prior continuation) + the Platform Authority axis (4 capabilities, ~100 routes across federation/trust/certificates/governance). Re-ran the pre-existing `tests/identity/test_platform_authority_*.py` suite (64 tests, including the exact high-risk certificate operations — `rotate_certificate`/`register_ca`/`generate_crl`/`generate_api_key`/`revoke_api_key`/`rotate_api_key` — each already both positively and negatively proofed with audit/transaction assertions): 64/64 passed, confirming VERIFIED rather than assumed. **New finding**: `PlatformAuthorityAssignment` grant/revoke has zero HTTP route anywhere — only reachable via an environment-controlled bootstrap script explicitly documented as "never exposed via any HTTP route." This makes platform-authority self-escalation structurally impossible (not merely guarded) — recorded as NOT_IMPLEMENTED (by design), not a gap. Checked 2 candidate gaps (federation's self-service session routes) via manual read: both correctly use self-ownership checks, not platform capability — confirmed not gaps. Zero new P0/P1 authorization findings; one pre-existing NEEDS_DECISION item (`adaptive-auth-account-id-idor`) carried forward unchanged. Full matrix: `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`, `docs/security/AUTHORIZATION_GAP_REGISTER.md`. | Mustafa | **DECIDED — inventory built, 0 new gaps, 0 code changes** | n/a | none | ~78 of 89 mounted routers remain UNKNOWN for authorization coverage — the honest remainder of a full repo-wide inventory, explicitly out of scope for this bounded pass. |

## F5 — Evidence

- **Fix**: `can_manage_user()` now mirrors the existing canonical
  `require_own_lab()` pattern — `master_admin`/`ministry_admin` bypass,
  `province_admin` keeps its existing province-scoped check, and every other
  role (the lab-scoped `admin`/`lab_admin` tier that actually reaches this
  function) must have `actor.lab_id == target_user.lab_id`. No new
  authorization mechanism was introduced; no second identity/RBAC system was
  created. The two existing callers (`toggle_user`, `change_user_role` in
  `backend/app/routes/admin.py`) are unchanged.
- **Tests**: `backend/tests/test_rbac_tenant_scope.py` — 8 tests, one per
  required property:
  - A: same-lab admin → toggle → ALLOWED
  - B: cross-lab admin → toggle → DENIED, target `is_active`/`perm_version` unchanged after
  - C: same-lab admin → permitted role change → ALLOWED
  - D/E/F: cross-lab admin → role change → DENIED; target role unchanged; target `perm_version` unchanged (no session invalidation); a pre-existing token for the target is still accepted afterward
  - G: `province_admin` reaches only same-province targets, denied cross-province, no side effect
  - H: a client-supplied `province_id` in the request body cannot expand cross-lab authority
  - I: an unauthenticated request is denied (401/403) before any mutation
  - J: IDOR via path `user_id` (real cross-lab id and a nonexistent id) is denied/404, no mutation
- **Negative proof**: temporarily reverted `rbac.py` to the pre-fix
  fallthrough (`git stash` of the fix), re-ran the suite — tests B, D/E/F, H,
  J failed against the vulnerable code (200 where 403 was expected); A, C, G,
  I still passed (they test same-lab/authenticated paths, which were never
  broken). Restored the fix via `git stash pop`, confirmed the diff was
  byte-identical to before the revert, and re-ran the full suite — all 8
  pass again.
- **Regression check**: `test_abac.py`, `test_tenant_isolation_matrix.py`,
  `test_security.py`, `test_feature_flags.py` (127 tests) all pass unchanged
  under the fix.
- **Caller audit**: `can_manage_user` has exactly two reachable callers in
  the entire repo (`backend/app/routes/admin.py:830,882`); both are covered
  by the new test file.

## Systemic pattern: unguarded setattr-loop mass assignment

PATTERN: `CLIENT_CONTROLLED_MASS_ASSIGNMENT` — `for k, v in data.items(): setattr(target, k, v)` (and the `key/value`, `field/value` spellings).

ROOT CAUSE: a generic request payload dict reaches an ORM instance via a bare attribute-assignment loop with no explicit writable-field boundary at the ORM/service layer — whether this is exploitable depends entirely on whether the calling route's own request schema already narrows the payload, which varies call site to call site and is not visible from the loop's syntax alone.

DETECTOR: `scripts/setattr_mass_assignment_guard.py` (new, this pass) — deterministic AST scan, self-tested (`--self-test`, 4/4: vulnerable shape, allow-listed shape, unrelated loop, alternate variable names), whole-repo scan in 0.28s. Flags every occurrence as a candidate requiring manual classification (SAFE_BY_DESIGN / SERVER_DERIVED / INTERNAL_ONLY / DEAD_OR_UNREACHABLE / VULNERABLE / NEEDS_REVIEW) and reports whether the loop body contains an inner `if` (a weak signal an allow-list may already be present — confirmed correctly `guarded=True` against this session's own just-fixed `hospital_service.py:102`, and correctly `guarded=False`/unguarded for `hospital_service.py`'s 2 still-open siblings, `update_campus`/`update_department`/`update_equipment` in `app/routes/hospital.py`).

PROOF: fixed and verified this session in `app/nursing/services.py::update_task` (earlier pass) and `app/services/hospital_service.py::update_hospital` (this pass, `0ddf1a72`), both with real behavioral tests proving protected fields survive a hostile payload.

AFFECTED DOMAINS (77 candidates across 41 files, repo-wide scan, NOT individually triaged this pass — each still needs the same manual classification Hospital's own investigation used before any fix):
- **Identity/Auth (highest priority — P0 per this session's own domain ordering, NOT audited this pass):** `app/identity/adaptive_auth/routes.py:172`, `app/identity/adaptive_auth/services.py:656`, `app/identity/admin/services.py:351`, `app/identity/federation/services.py:87`, `app/identity/services/person_service.py:77`, `app/identity/trust/services.py:112`.
- **EHR (17 sites, one file):** `app/services/ehr_service.py` — every clinical-note/care-plan/goal/activity update method.
- **NHDW (6 remaining, beyond the already-fixed `update_admission`):** `app/nhdw/services.py:112,387,506,569,843,867`, `app/nhdw/offline.py:182,191`.
- **Insurance (5, one per API file):** `app/insurance/api/{claims,coverages,network,policies,providers,referrals}.py`.
- **National platform (~15 across background/document/observability/scheduling/task_engine/ecosystem/services + 3 route files):** `app/national/**`.
- **Hospital (2 remaining, NOT fixed this pass — same file as the confirmed/closed finding but different routes):** `app/routes/hospital.py:456` (`update_campus`), `:552` (`update_department`), `:939` (`update_equipment`, has a weaker `if v is not None` null-check only, not a field allow-list) — none of these three routes has a role gate either, consistent with the "rest of hospital.py" note already recorded against `hospital-vertical-slice-remaining-scope`.
- **Others (1 each, not audited):** `app/blood_bank/application/service.py:836`, `app/citizen_platform/emergency.py:149`, `app/core/bootstrap/subscriptions.py:134`, `app/document_intelligence/infrastructure/repository.py` (4 sites), `app/edge/policy.py:121`, `app/ems/application/service.py:447`, `app/kernel/runtime_digital_twin.py:32`, `app/nursing/services.py:519` (a second Nursing instance beyond the already-fixed `update_task`), `app/pharmacy/services.py:94`, `app/radiology/services.py:666`, `app/routes/care_continuum.py:182`, `app/routes/labs.py:208`, `app/services/clinical_service.py` (4 sites).

FIX PATTERN: explicit allow-list of writable field names mirroring the actual request schema that reaches the method (not the ORM model's full column list — that couples the boundary to the wrong source of truth), checked inside the loop before `setattr`; add `.with_for_update()` + `version += 1` where the target model already has `OptimisticLockMixin` and doesn't yet use it.

PREVENTION: `scripts/setattr_mass_assignment_guard.py` is the standing regression guard — re-run after any change to a `data.items()`/`setattr` update loop, or as a periodic check; a NEW unguarded site anywhere in the tree will show up as a fresh candidate.

STATUS: **PATTERN REGISTERED, DETECTOR VERIFIED (self-tested 4/4), 2/77 candidates fixed this session (Nursing, Hospital) — the remaining 75 are explicitly NOT triaged, matching this session's "do not turn this into a full repository rewrite" boundary.** Given the volume and that several affected domains (Identity/Auth, EHR, National, Insurance) were never touched this session, classifying and fixing the remainder is sized as its own dedicated pass (or several, split by domain), starting with Identity/Auth per this session's own P0-first domain ordering — not attempted here.

| Commit: `f3cad8d8` | Owner: Mustafa | Next action: a dedicated pass (or one per domain cluster above) reading each flagged call site's actual request-schema/ownership context before fixing, starting with the Identity/Auth cluster. |

## Identity/Auth mass-assignment triage (the 6 candidates above) — TRIAGED, 0 FIXED, 2 BLOCKED-HANDOFF

Per this session's own domain ordering (IDENTITY > AUTHORIZATION > TRUST > TENANT > CLINICAL > OTHER)
and the explicit instruction that these 6 are NOT automatically vulnerabilities — each was traced
caller → route → auth dependency → request schema → service loop, on **this branch's own current
file versions** (not Abu Ali's). Prior-session finding IDs cited for this domain (AUTH-002 through
AUTH-005, NR-035/037/045-058, etc.) were checked against `git log --all`: all are real commits, but
every one exists **only** on `origin/claude/p0-2-pharmacy-reconciliation` and is confirmed
(`git merge-base --is-ancestor`) **not an ancestor of this branch** — none of that identity/auth work
has landed here, so this triage starts from this branch's pre-existing state, not from any of it.

| # | Site | Classification | Reasoning |
|---|------|-----------------|-----------|
| 1 | `adaptive_auth/routes.py:172` `update_risk_policy` | **SAFE_BY_DESIGN** | Route requires `Depends(_require_policy_admin)`, which unconditionally raises `403` (see `_POLICY_AUTHORITY_UNAVAILABLE` docstring at `routes.py:15-28`: a real platform-admin permission concept doesn't exist yet in NIAM, so this fails closed rather than guess one). The `setattr` loop is never reached by any caller. Already fixed in an earlier pass of this branch, not this one — confirmed by reading, not assumed. |
| 2 | `adaptive_auth/services.py:656` `update_session_policy` | **SAFE_BY_DESIGN** | Same as #1: its only caller, `routes.py:238`'s `update_session_policy` route, has the identical `Depends(_require_policy_admin)` gate. Unreachable. |
| 3 | `admin/services.py:351` `update_subscription` | **SAFE_SERVER_DERIVED** | Caller (`admin/routes.py:240-264`) is a narrow, explicitly-named/typed FastAPI signature (`plan_type: str = ""`, `billing_cycle: str = ""`, `billing_amount: int = 0`, `auto_renew: bool = False`) — never a raw dict. It builds `kwargs` from only those four names, gated by `_require_permission(actor, db, ..., permission_key="subscription.manage")`. The `**kwargs` loop is syntactically identical to the vulnerable shape but the reachable field set is bounded by the route signature today, matching Hospital's own "not independently exploitable through the current API surface, but no boundary of its own" finding — a hardening opportunity (explicit allow-list at the service layer), not an open vulnerability. Not fixed this pass; lower priority than #4/#6 since it already has a permission check and a narrow caller. |
| 4 | `federation/services.py:87` `update_provider` | **VERIFIED_VULNERABLE** | `PUT /niam/federation/providers/{id}` (`federation/routes.py:97-107`) takes `body: dict[str, Any]` — a raw client-controlled payload — and calls `svc.update_provider(provider_id, **body)`. `federation_routes.router` is registered in `identity/api/router.py:49` with only `dependencies=_AUTH_REQUIRED` (`[Depends(get_current_niam_actor)]` — any authenticated NIAM actor of any role, no permission check). The route itself adds no further gate. The service loop guards only `hasattr(provider, key) and value is not None` — not an allow-list. `FederatedProvider` (`federation/models.py`) includes `client_secret_encrypted`, `certificate`, `trust_anchor_id`, `issuer_url`, `status`, `is_active`, `jwks_uri`, `redirect_uris`. **Any authenticated user, regardless of role, can currently rewrite a federated identity provider's trust configuration and secrets via this endpoint.** |
| 5 | `services/person_service.py:77` `update_person` | **DEAD_OR_UNREACHABLE** | `app/identity/api/persons.py` — the only route file that constructs `PersonService` — wires exactly `create_person` and `get_person`; no route anywhere in the tree calls `.update_person(`. Confirmed by repo-wide grep, not by absence-of-evidence alone. |
| 6 | `trust/services.py:112` `update_framework` | **VERIFIED_VULNERABLE** | Same shape and same root cause as #4: `PUT /niam/trust/frameworks/{id}` (`trust/routes.py:87-97`) takes a raw `body: dict[str, Any]`, `trust_routes.router` is registered with only `dependencies=_AUTH_REQUIRED` (`identity/api/router.py:47`), no per-route permission check, `hasattr`-only guard in the service loop. `TrustFramework` includes `status`, `assurance_policies`, `scope`, `authority_id`, `supersedes_framework_id`. **Any authenticated user can currently rewrite a canonical trust framework's status/assurance/scope/lineage.** |

### Why #4 and #6 are BLOCKED-HANDOFF, not fixed here

Both are genuine, currently-live authorization gaps (missing permission check, not just missing
field allow-list) on the platform's federation and trust-framework configuration — squarely
"Identity/Trust/Federation" territory, which this branch's own division of labor (Mustafa/Abu Ali)
has treated as Abu Ali's canonical-decision domain all session, and which Section 33 of the active
directive explicitly requires stopping for ("changes... to canonical identity/ownership/federation
semantics", "weakening assurance/authorization").

Checked whether this conflicts with Abu Ali's active work before deciding:
`git diff --stat HEAD origin/claude/p0-2-pharmacy-reconciliation -- backend/app/identity/{trust,federation}/{routes,services,models}.py backend/app/identity/api/router.py`
shows **every** file in this feature area under heavy concurrent rewrite on his branch right now —
`trust/routes.py` (289 lines), `trust/services.py` (260 lines), `federation/routes.py` (104 lines),
`federation/services.py` (100 lines), even the shared `identity/api/router.py` (38 lines, i.e. the
very file that declares the `_AUTH_REQUIRED` gate these findings are missing a level beyond). There
is no untouched corner of this feature to patch around him. His commit history for this exact area
(AUTH-002 "identity bridge decision", AUTH-004 "score identity assurance per purpose", AUTH-005
"identity evidence gates health-data linkage") reads as an active authorization/assurance-model
redesign — exactly the kind of decision a fail-closed permission stub (the precedent already set in
this very codebase at `adaptive_auth/routes.py:_require_policy_admin`) would need to be built on top
of, not ahead of. Writing an independent fix now risks being silently discarded or textually
conflicting with a much larger in-flight redesign of the same authorization surface. Per this
branch's own conflict-avoidance rule ("check whether Abu Ali is actively changing the same area; if
yes, choose another domain unless P0") and Section 33's explicit BLOCKED boundary, this is handed
off rather than patched: **no changes were made to any of the 6 files in this table.**

STATUS: **6/6 Identity/Auth candidates triaged. 2 SAFE_BY_DESIGN (already fail-closed), 1 SAFE_SERVER_DERIVED (hardening opportunity only), 1 DEAD_OR_UNREACHABLE, 2 VERIFIED_VULNERABLE and BLOCKED-HANDOFF (missing authorization check on `federation/services.py::update_provider` and `trust/services.py::update_framework` — needs a real platform/organization-scoped permission decision from the identity-canonical owner, not a guess from this branch).**

| Commit: `(pending)` | Owner: Mustafa (triage) / Abu Ali (fix, canonical identity/trust/federation authorization decision required) | Blocker: `federation/services.py::update_provider` and `trust/services.py::update_framework` need a real permission check (analogous to `_require_policy_admin`'s fail-closed pattern) before their mass-assignment loop is safe to leave open; both files are under active heavy rewrite on `origin/claude/p0-2-pharmacy-reconciliation` right now. | Next action: raise these two findings directly to Abu Ali (or to whoever merges his branch) — if his in-progress rewrite doesn't already close them, the minimal safe interim fix is the same fail-closed stub pattern already used at `adaptive_auth/routes.py:_require_policy_admin`, applied to both `PUT` routes, until a real permission model for platform-wide trust/federation config exists. |

## Phase 10 — NIAM Platform Authority foundation implemented, federation/trust findings closed

Following an explicit approved-architecture directive (Assignment-bound Platform
Authority, keyed to the canonical NIAM identity — `niam_identities`, reached via
`Account.identity_id` — never an organization account role, never
`organization_id`), implemented the foundation this branch's own prior Phase 7-9
investigation said was the blocking prerequisite, then closed the two named
findings against it.

**New**: `app/identity/platform_authority/` (`models.py`, `services.py`,
`authorization.py`) — `PlatformAuthorityAssignment` (`niam_platform_authority_assignments`,
migration `20260908_0003`), four capabilities (`platform.federation.manage`,
`platform.trust.manage`, `platform.certificates.manage`,
`platform.governance.manage`), `PlatformAuthorityService` (grant/revoke/
has_capability, idempotent grant, terminal revoke — mirrors
`niam_role_assignments`' `revoked -> {}` rule), `require_platform_capability`
resolver (fail-closed, never consults `Membership`/`RoleAssignment`). At-most-
one-active-assignment-per-(identity,capability) enforced by a **real, Postgres-
verified partial unique index** (`postgresql_where=status='active'`), not just
application logic — proven via a throwaway local Postgres: duplicate-active
insert rejected, revoke-then-re-grant accepted, full upgrade/downgrade/re-upgrade
round-trip clean.

**Closed**: `federation/services.py::update_provider` and
`trust/services.py::update_framework` now require `platform.federation.manage`/
`platform.trust.manage` (route-level `require_platform_capability` call, actor
resolved via the existing `get_current_niam_actor`) and an explicit field
allow-list replacing the old `hasattr(...)`-guarded `setattr` loop — SAFE_METADATA
only (`name_en`/`name_ar`/`version`/`effective_date` for TrustFramework;
`name_en`/`name_ar`/`provider_type`/`client_id`/`scopes`/`metadata_url` for
FederatedProvider). SECURITY_SENSITIVE fields (`status`, `assurance_policies`,
`scope`, `authority_id`, `supersedes_framework_id`, `client_secret_encrypted`,
`certificate`, `trust_anchor_id`, every OAuth endpoint/redirect field) are now
unreachable via either generic-update path — deliberately not routed through any
newly-invented operation, since no dedicated-operation precedent exists for them
yet (unlike `activate_framework`/`supersede_framework`, which already existed and
were left alone, or `certificates/services.py::rotate_certificate`) — recorded as
DEFERRED, not silently dropped. Both mutations now emit real
`CanonicalAuditService`/`AuditEventInput` audit entries (reusing the same
mechanism `admin/services.py` already uses, not a second audit system).

**Found and fixed mid-implementation** (caught by the new tests, not assumed
away): the naive `service.update_x(id, actor_account_id=..., **body)` call shape
crashes with `TypeError: got multiple values for argument` whenever `body`
happens to contain a key matching the resource's own id parameter (e.g. a client
sending `{"framework_id": "..."}`) — fixed by changing both service methods to
take `data: dict` instead of `**kwargs`, matching the `HospitalService.update_hospital`
precedent from Phase 5 exactly, which structurally can't collide this way.

**Verification**: real Postgres migration round-trip (see above); repo-wide
`setattr_mass_assignment_guard.py` re-run — both sites still flagged as candidates
(correct, syntax-only detector) but now `guarded=True`; 24 new focused tests in
`backend/tests/identity/test_platform_authority_phase10.py` (fail-closed matrix,
grant/revoke/idempotency/audit, route-level negative proofs for both operations,
field-boundary proofs, cross-boundary proof that an org-RBAC-shaped actor is still
denied, and a `unittest.mock.patch`-based negative proof that removing the gate
call is exactly what reopens each vulnerability); full existing
`backend/tests/identity/` suite (195 tests) re-run unchanged, all passing —
no regression.

**Explicitly NOT done this phase** (matches the directive's own scope limits,
not an oversight): no public grant/revoke route (bootstrap remains a documented,
separate, not-yet-authorized step); `activate_framework`/`supersede_framework`/
`register_provider`/`issue_certificate`/`revoke_certificate`/`create_authority`
share the same missing-platform-authority gap but were out of this phase's named
scope and are still open; no assurance/step-up requirement added (Phase 9 §8's
open question, not resolved here); certificates/governance domains untouched.

STATUS: **Platform Authority foundation Functional/Validated (not yet Operational/
Production — no bootstrap path exists to grant a first real capability). Both
Phase 6 findings closed at the code level and covered by negative proof; not yet
exercised against production data or a real deployment.**

| Commit: `(pending)` | Owner: Mustafa | Migration: `20260908_0003_platform_authority_foundation` | Next action: decide and implement the bootstrap path for the first real Platform Authority grant (Phase 9 §13 step 2 — deliberately not invented here), then extend capability-gating to the six other routes sharing this gap. |

## Phase 11 — Authorization Coverage Batch 2: `lifecycle-platform-no-auth` P0 fixed, billing P2/P3 documented

Bounded continuation of the authorization capability inventory: traced 5
previously-unaudited LIVE+table-backed domains (`billing`,
`lifecycle_platform`, `pilot_platform`, `services/mpi`,
`capabilities/fhir_interoperability` — 23 mutating routes total, per the
directive's own ≤5-domain/≤35-route bound).

**Found and fixed** (P0, stop-and-fix per the directive's own severity
disposition): `app/lifecycle_platform/api/routes.py` had **zero**
authentication or authorization dependency on any of its 19 routes
(confirmed by grep returning 0 matches for
`Depends(get_current_user)|Depends(require_permission...|
Depends(require_platform_capability...|dependencies=\[` in the file).
Proven live with a real, anonymous `TestClient` HTTP request: `POST
/lifecycle/components` with no `Authorization` header returned `201
Created` and persisted a real row. Fixed with the same
`dependencies=[Depends(require_permission("system:admin"))]`
router-level gate already used by every sibling "National X Platform"
domain (biomedical/command_center/public_health/critical_care/
pilot_platform — the last of which had the identical finding fixed in
an earlier session). Post-fix: same request → `401
AUTHENTICATION_REQUIRED`; full matrix proven (no override → 401,
`lab_tech` → 403, `master_admin` → 201). Negative-proofed via `git
stash`/`git stash pop` with md5sum-verified byte-identical restoration
(pre-fix `28ecbe8b965596acccbfdd6b6272566c`, post-fix
`a209bdd042a1c2e819c22f527be89cf3`) — vulnerability reproduces on
revert, fix holds on restore. New permanent regression test:
`backend/tests/test_lifecycle_platform_auth.py` (3 tests, all passing).
Regression sweep (identity/tenant-isolation/feature-flags/blood_bank/
biomedical/command_center/device-outbox/payments/public_health — 178
tests) — 0 failures, 0 collateral regressions.

**Found and documented, not fixed** (P2/P3 per the directive's own
"P0/P1 fix now, P2/P3 document and continue" disposition):
`app/billing/service.py`'s `simulate_settlement`/`advance_claim` share
the session's already-registered systemic concurrency pattern (unlocked
SELECT + status-check + write, no `.with_for_update()`, no
`OptimisticLockMixin`) — classified P2 rather than P1/P0 because
`app/billing/` is explicitly a demo-safe projection layer (its own
module docstring) distinct from the already-hardened real financial
infrastructure in `app/payments/`, and because both racers converge on
the same correct final state per `advance_claim`'s explicit
state-transition map, so the failure mode is a possible duplicate audit
row, not silent corruption or a double charge. Separately,
`create_invoice`'s idempotency-key check is backed by a real
`UniqueConstraint("lab_id","idempotency_key")` but the route only
catches `ValueError`, not `IntegrityError` — a genuine race produces an
unhandled 500 rather than a clean 409 (P3). Full evidence, reasoning,
and recommended (not-applied) fixes for both:
`docs/security/AUTHORIZATION_GAP_REGISTER.md` (GAP-3, GAP-4).

**Verified clean, no gap** (re-verified rather than assumed):
`pilot_platform` (prior P0 fix confirmed still in place — router-level
gate, in-code comment documents the original finding); `services/mpi/api.py`
(3 mutating routes, ABAC self-lab + cross-lab admin-role gating, all
correct); `capabilities/fhir_interoperability/routes.py` (the one LIVE
sub-router of the otherwise-dead `app/capabilities/` package — 2
mutating routes, `require_institutional_permission` + `actor.lab_id`
scoping + real DB-constraint-backed idempotent create).

**Documentation updated this phase** (append/reconcile, not overwrite):
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md` (Batch 2 section added
to Axis 2, Phase 8 summary totals recalculated: ~372→~395 total
evidenced routes, UNKNOWN bucket ~78→~73 routers, FULLY VERIFIED
14→15), `docs/security/AUTHORIZATION_GAP_REGISTER.md` (GAP-2 CLOSED,
GAP-3/GAP-4 new P2/P3 findings, pilot_platform/mpi/fhir_interoperability
recorded VERIFIED).

STATUS: **`lifecycle-platform-no-auth` CLOSED — fixed, proven,
negative-proofed, regression-tested, zero collateral regressions.**
Billing's two concurrency findings remain **OPEN, documented, P2/P3,
not fixed** (explicitly out of this bounded batch's scope per the
directive's own disposition rule). Batch 2's 5 domains fully traced;
23 mutating routes now have route-level evidence. **This does not mean
"authorization complete" or "all routes protected"** — ~73 of 89
mounted routers remain UNKNOWN; see the coverage matrix's own honesty
note for the exact remainder and the next bounded batch's candidate
list.

| Commit: `(pending)` | Owner: Mustafa | Files: `app/lifecycle_platform/api/routes.py`, `backend/tests/test_lifecycle_platform_auth.py`, `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`, `docs/security/AUTHORIZATION_GAP_REGISTER.md` | Next action: next bounded batch should pick ≤5 more UNKNOWN-bucket domains from the ~73 remaining (e.g. the 7 schema-latent domains once/if their tables are backfilled, or further NIAM-adjacent routers not yet traced) — do not repeat billing/lifecycle_platform/pilot_platform/mpi/fhir_interoperability. Billing's P2 (`simulate_settlement`/`advance_claim` row-locking) and P3 (`create_invoice` IntegrityError handling) fixes remain available as a small, well-scoped follow-up if a future directive authorizes fixing P2/P3 findings rather than only documenting them. |

## Phase 12 — Authorization Coverage Batch 3: 5 domains traced, 0 findings, 1 test-evidence gap closed

Bounded continuation of the authorization capability inventory (third
batch). Re-baselined first per the directive's own Phase 0: `git
rev-parse HEAD` = `4d7c11f0`, clean tree, 89 mounted routers
re-confirmed by direct grep of `app/factory.py` (not trusted blindly
from the prior pass's count).

**Selected 5 domains** from the `LIVE / NO-OWNED-MODELS` bucket in
`docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md` (routers mounted, real
persistence via shared models, not yet individually confirmed),
prioritizing identity/patient-data/security-configuration relevance
per the directive's own Phase 1 ranking: `app/routes/consent.py` (2
mutating routes), `app/routes/patient_card.py` (1), `app/routes/
canonical_patient.py` (4), `app/routes/service_accounts.py` (3),
`app/routes/mfa.py` (7) — **17 mutating routes total**, well under the
35-route/5-domain bound.

**Result: zero P0/P1/P2/P3 findings.** All 5 domains read as correctly
authorized on direct trace:

- `consent`: self-or-admin ownership check (`_user_owns_gpid` — caller
  must be the citizen subject, or `master_admin`/`ministry_admin`),
  not a role-only gate.
- `patient_card`: `lab_id` tenant filter + HMAC token verification +
  explicit cross-lab token rejection + audit log on every action —
  matches CLAUDE.md's own stated invariant for this exact file.
- `canonical_patient`: gated by `app/services/mpi/scope.py`'s
  `require_national_scope`/`require_own_patient`/`provenance_lab_id` —
  a **pre-existing fix ("NR-148") closed before this session**,
  re-verified this pass rather than assumed still correct; a
  well-designed cross-tenant-by-design domain (the MPI is
  deliberately national in scope), not an authorization gap.
- `service_accounts`: role check + real DB-level `lab_id` scoping
  inside the service layer (confirmed by reading the query
  construction, not assumed). **One evidence gap found and closed**:
  no prior test proved the cross-lab-denial or non-admin-denial cases
  (existing coverage only exercised a single-lab admin happy path).
  New test file `backend/tests/test_service_accounts_authz.py` (6
  tests, all passing) closes it: non-admin role → 403, foreign
  `lab_id` in creation body → 403, Lab A admin rotating/revoking Lab
  B's service account → 404, master_admin cross-lab rotate → 200,
  unauthenticated → 401.
- `mfa`: every mutation scoped to `current_user.id` server-side, no
  client-supplied account/session identifier anywhere in the router —
  the opposite shape from the still-carried-forward
  `adaptive-auth-account-id-idor` P1. `remove_device` filters by
  `device_id AND user_id` before deleting (no cross-account IDOR).

**Zero production code changed this batch** (Phase 11's preferred
outcome, achieved because no P0/P1 was found). The only change is the
one new test file above.

**Verification**: reused substantial existing test evidence
(`tests/test_consent.py` 9 tests, `tests/test_patient_card.py` 15
tests, `tests/test_canonical_patient_scope.py` 24 tests, `tests/
test_canonical_patient_lab_id_authority.py` 2 tests, `tests/
test_auth_infrastructure.py` 30 tests including MFA/service-account/
canonical-patient route-level checks) rather than reinventing proofs
already on file, per the directive's own Phase 8 instruction. All 82
re-run green, plus the 6 new service-account tests — 88 tests total,
0 failures. No broader regression sweep run (Phase 12: "if ZERO code
changes, run only the focused tests/proofs required for evidence" —
no app code changed, so the 320-test baseline was not re-run).

**Documentation updated** (append/reconcile, not overwrite):
`docs/security/AUTHORIZATION_COVERAGE_MATRIX.md` (Batch 3 section
added, Phase 8 totals recalculated: ~395→~412 evidenced routes,
UNKNOWN bucket ~73→~68 routers, next-batch candidate list named),
`docs/security/AUTHORIZATION_GAP_REGISTER.md` (5 new VERIFIED
entries, summary table updated), `docs/architecture/
LIVE_RUNTIME_SURFACE_MAP.md` (5 routers moved out of the
`NO-OWNED-MODELS`/"not yet confirmed" list into a new "resolved this
pass" note), `docs/security/FINAL_ENGINEERING_CLOSURE_REPORT.md`
(addendum appended).

STATUS: **Batch 3 CLOSED — 5 domains traced, 0 authorization findings,
1 test-evidence gap closed (service_accounts), zero production code
changed.** This does not mean "authorization complete" or "all routes
protected" — ~68 of 89 mounted routers remain UNKNOWN; see the
coverage matrix's own honesty note for the exact remainder and named
next-batch candidates (`password_reset`, `oauth2`, `saml`, `hospital`,
`edge`, `ai_fabric`, `control_plane`, and others).

| Commit: `(pending)` | Owner: Mustafa | Files: `backend/tests/test_service_accounts_authz.py`, `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`, `docs/security/AUTHORIZATION_GAP_REGISTER.md`, `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`, `docs/security/FINAL_ENGINEERING_CLOSURE_REPORT.md` | Next action: next bounded batch should pick ≤5 more domains from the ~68 remaining UNKNOWN routers — strong candidates named in the coverage matrix's honesty note are the authentication-adjacent trio (`password_reset`/`oauth2`/`saml`, similar risk class to this batch's `mfa`) and/or `hospital` (23 mutating routes, largest single remaining candidate, would need its own bounded batch given the 35-route cap). Do not repeat any of the now ~20 audited domains. |

## Phase 14 — Accelerated Security & Authorization Closure Batch 4: Hospital vertical slice completion (3 real P1s), OAuth2 register gap closed

Combined bounded pass (authorization + transaction integrity +
idempotency + concurrency triage in one discovery sweep, per this
batch's own "accelerated" directive). Re-baselined first: `git
rev-parse HEAD` = `9680130c`, clean tree, 89 mounted routers
re-confirmed.

**Primary domain: Hospital** (`app/routes/hospital.py`, 23 mutating
routes total — 4 already gated from a prior session pass, 19 newly
traced this batch). **Three real, independent P1 findings, all closed
with full FIND→TRACE→REPRODUCE→FIX→NEGATIVE PROOF→REGRESSION
evidence:**

1. **`hospital-facility-no-role-check`** — 19 of 23 mutating routes had
   zero role check beyond bare authentication, including clinical
   patient-safety operations (bed assign/discharge/transfer, OT status
   change, surgical safety checklist completion — a WHO-mandated
   attestation). A prior session's own test file
   (`test_hospital_update_security.py`) explicitly documented this as
   deliberately deferred ("the entire hospital.py route surface still
   has no role gates beyond these four"). Fixed by reusing this
   file's own existing `_HOSPITAL_ADMIN_ROLES` convention for facility
   structure and NHDW/Nursing's existing clinical-write role
   convention (`{admin, master_admin, doctor, nurse}`) for clinical
   operations — no new role vocabulary. 25 new tests
   (`backend/tests/test_hospital_role_gate_completion.py`).

2. **`hospital-get-entity-boolean-bug`** (discovered while building
   #1's test fixtures) — `HospitalService._get_entity`'s
   `not model.is_deleted` is Python's `not` applied to the column
   attribute itself, evaluating to the literal `False` at
   query-build time (`bool(Model.column)` is always `True` by
   default), so this shared helper (17 call sites across ~10 routes)
   unconditionally matched zero rows. Fixed: `~model.is_deleted`.
   **The identical bug shape recurs at 5 more sites outside Hospital**
   (`app/radiology/pacs.py:365,375,388`, `app/pharmacy/routes.py:504`,
   `app/routes/admin.py:257`) — registered in
   `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` as Pattern
   2, not fixed (different, unaudited domains, out of this batch's
   bound).

3. **`hospital-missing-commit`** (discovered while proving #2's fix) —
   18 of Hospital's mutating routes (everything except the 5
   `ClinicalCommandGuard`-based ones) never called `db.commit()`
   anywhere. `get_db()` uses `autocommit=False` and only rolls back on
   exception; SQLAlchemy's default `Session.close()` discards a
   pending transaction. Every affected route returned a 200/201
   showing an apparently-created/updated record that was **never
   durably persisted**. Invisible to every pre-existing Hospital test
   because `tests/conftest.py`'s `client` fixture shares one session
   across all requests in a test (masks any missing commit
   completely). Proven with a standalone two-independent-session
   script against a real file-backed SQLite DB: `POST /hospital/` →
   `201`; the very next request, `POST /hospital/1/departments` → 404
   "Hospital not found" (pre-fix); → `201` (post-fix); a third,
   independent session confirmed durable persistence only post-fix.
   Fixed: `db.commit()` added to all 18 routes, matching the pattern
   already used by the file's own `_run_hospital_command` helper. 3
   new tests using a genuine two-session fixture (not the masking
   shared-session client) —
   `backend/tests/test_hospital_durable_commit.py`.

**Schema note** (re-confirmed, not new): 13 of Hospital's 14 tables
have zero Alembic migration; the 14th's own migration is itself
already-documented as blocked in the chain (missing
`hospital_operation_theaters` FK target). Hospital is SCHEMA-BLOCKED
on a real Postgres deployment — these three fixes are real, correct,
and proven via this repo's own SQLite test harness, but none of the
23 routes are currently reachable on a genuine migration-driven
deployment. Not fabricated or worked around; documented precisely in
`docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`.

**Secondary domain: OAuth2 + auth-adjacent** (`app/routes/oauth2.py`,
`password_reset.py`, `saml.py`):

- **`oauth2-register-no-role-check`** (P1, CLOSED) — `OAuth2Client` is
  a platform-global registry (no tenant column at all, by design).
  `POST /oauth2/register` had only `get_current_user`: any
  authenticated user of any role could register a client with
  attacker-chosen `redirect_uris`. Fixed with `{admin, master_admin}`,
  matching `service_accounts.py`/Hospital's convention. 3 new tests
  (`backend/tests/test_oauth2_register_authz.py`).
- `password_reset.py` — VERIFIED, no gap (identity derived solely
  from the reset token; `change_password` self-scoped +
  perm_version bump).
- `saml.py`'s `/acs` — VERIFIED not exploitable; reclassified as
  functionally incomplete (validates the SAML assertion
  cryptographically but issues no session/JWT/DB write at all — the
  `db` param is unused).
- Two P3 protocol-conformance notes on OAuth2 documented, not fixed
  (no consent screen on `/authorize`; no client auth on
  `/introspect`/`/revoke`) — see gap register.

**Verification**: 209 tests re-run across all affected + adjacent
files (Hospital's own suites, oauth2/auth infrastructure,
security/tenant-isolation/rbac/feature-flags), 0 failures. Every one
of the 4 real findings individually negative-proofed via `git
stash`/`git stash pop` with md5-verified byte-identical restoration.

**Documentation updated** (append/reconcile): `docs/security/
AUTHORIZATION_COVERAGE_MATRIX.md` (Batch 4 section, totals ~412→~436,
UNKNOWN ~68→~64), `docs/security/AUTHORIZATION_GAP_REGISTER.md`
(GAP-5/6/7/8 + password_reset/saml/oauth2-notes entries),
`docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` (2 new
pattern sections), `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`
(hospital reclassified, password_reset/oauth2/saml resolved),
`docs/architecture/PRODUCTION_READINESS_DELTA.md` (addendum, scoped
evidence only).

STATUS: **4 real P1 findings found and CLOSED this batch** (1
authorization gap with patient-safety impact, 1 data-integrity bug, 1
transaction-integrity/silent-data-loss bug, 1 security-configuration
authorization gap) — proven, fixed, negative-proofed, regression-
tested, zero collateral regressions. This is the most severe single
batch this program has run since the original `lifecycle-platform-
no-auth` P0. **Not claimed**: "authorization complete," "all routes
protected," or "production ready" — ~64 of 89 mounted routers remain
UNKNOWN, Hospital remains schema-blocked for real deployment, and 5
more instances of the boolean-filter bug remain open in other domains.

| Commit: `(pending)` | Owner: Mustafa | Files: `app/routes/hospital.py`, `app/services/hospital_service.py`, `app/routes/oauth2.py`, 3 new test files, 6 docs | Next action: fix the 5 remaining `not`-vs-`~` boolean-filter sites (`app/radiology/pacs.py`, `app/pharmacy/routes.py`, `app/routes/admin.py` — same one-line fix already proven safe here) as a small, cheap, high-confidence follow-up; or continue the authorization inventory into `edge`/`ai_fabric`/`control_plane` from the ~64 remaining UNKNOWN routers. |

## Phase 15 — Accelerated Batch 5: systemic boolean-filter closure (28 sites) + mounted-router accounting correction

Bounded pass with a single objective ("close the remaining five known
boolean-filter defects using one systemic investigation") that, per
its own explicit "discover from current source, do not assume exact
files or line numbers" instruction, uncovered a much larger scope: a
new deterministic detector (`scripts/security/boolean_not_filter_guard.py`,
AST-based, no network/AI/DB access) found **28 total repo-wide
occurrences** of the `not X.field` vs `~X.field` bug — 23 more than
the 5 originally assumed.

**All 28 fixed**, same mechanical, previously-proven-safe substitution
throughout:

- `app/lims/routes.py` — **20 sites, all LIVE**, tenant-scoped
  (`_lab_id(current_user)`) list/get/dashboard-count routes across
  Instrument/Specimen/Order/Panel/Result/Reagent/Consumable/Lot/
  ReferenceRangeDef/AutoValidationRule/LabReport/QCProgram/Supplier/
  Storage/DeltaCheckRule/Department/Manufacturer. `lims_routes.router`
  had never been individually vertical-slice-audited before — this
  batch closes that gap and, in doing so, discovers the entire LIMS
  listing surface was silently non-functional (every affected call
  returned empty/zero, not an error). Fixed via a verified uniform
  `sed` substitution (occurrence-count and semantics confirmed
  identical across all 20 before applying).
- `app/pharmacy/inventory.py` (2 sites, both DEAD — zero callers),
  `app/pharmacy/routes.py:504` (1 site, DEAD), `app/pharmacy/services.py:198`
  (1 site, LIVE — backs `GET /pharmacy/dashboard/expiry-alerts`, real
  HTTP-proven; also backs `GET /pharmacy/batches/expiring`, itself
  shadowed by a separate, pre-existing route-ordering bug found while
  writing the test for it — documented, not fixed, out of bound).
- `app/radiology/pacs.py` (3 sites: `revoke_share` LIVE via `DELETE
  /radiology/sharing/{id}`, ownership-scoped via `_study_for_user`;
  `access_share`/`list_shares` DEAD).
- `app/routes/admin.py:257` (1 site, LIVE — `GET /admin/labs/pending`,
  gated by `require_permission("platform:manage_users")`).

**False positive checked and excluded**: `app/routes/demo.py:96`'s
`not user.is_active` inside a plain `elif` — a different, correct
usage (negating an already-fetched instance's real boolean, not a
column expression inside a query filter). The detector's self-test
(6/6 passing) encodes this distinction so it won't regress.

**Detector built** (Phase 4's requirement, satisfied — the pattern
was reliably AST-detectable with zero false positives found):
`scripts/security/boolean_not_filter_guard.py`, matching the house
convention of `scripts/setattr_mass_assignment_guard.py`/
`scripts/log_action_arg_order_guard.py`. Unlike those two (which flag
candidates requiring manual classification), every hit from this
detector is a near-certain defect. `--self-test` (6/6 pass),
`--json`, exit code 1 on any hit (CI-usable). Repo-wide scan post-fix:
0 hits.

**Verification**: 5 new regression tests
(`backend/tests/test_boolean_not_filter_regression.py`) proving the
fix via real HTTP/service-level calls for all 4 LIVE-reachable
representative sites (LIMS department create+list, pharmacy
expiry-alerts route, radiology revoke_share, admin pending-labs);
confirmed to fail against the pre-fix state and pass against the fix
via `git stash`/`git stash pop` with md5-verified byte-identical
restoration. 151 regression tests re-run across LIMS/pharmacy/
radiology domain suites plus security/tenant-isolation/rbac — 0
failures.

**Mounted-router accounting correction** (Phase 11's mandatory
recalculation, not new work product): every prior batch counted
mounted routers via `grep -c "app.include_router("`, reporting 89.
This undercounts — `app/factory.py:578-579`'s `for` loop registers 29
routers in one iteration that a textual count only counts as 1.
**Corrected total: 117 mounted routers.** Of the 28 net-new routers
this surfaces, 3 (`labs`/`samples`/`results`) were already implicitly
covered by this queue's existing "Laboratory" references; `admin`
gained one route's evidence this batch; **25 are genuinely,
newly-honest UNKNOWN**, never individually accounted for before:
`login, register, verification, demo, setup, metrics, patients,
test_results, dashboard, app_updates, qr, id_scan, identity,
notifications, ehr, ehr_fhir, cds_hooks, security, device_results,
quality_control, critical_alerts, batch, admin_log_level, mobile,
compliance`. Corrected UNKNOWN: ~86 of 117 (up from ~64 of 89 — larger
because the denominator was wrong, not because coverage regressed).

**Documentation updated**: `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`
(Batch 5 section, corrected totals throughout the summary and honesty
note), `docs/security/AUTHORIZATION_GAP_REGISTER.md` (GAP-9 + the
accounting-correction note), `docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md`
(Pattern 2 fully updated with all 28 sites + detector), `docs/architecture/LIVE_RUNTIME_SURFACE_MAP.md`
(router-count correction note + lims/pharmacy authorization-coverage
note), `docs/security/FINAL_ENGINEERING_CLOSURE_REPORT.md` (addendum).

STATUS: **28 of 28 known-shape boolean-filter sites CLOSED. Mounted-
router accounting corrected from 89 to 117 (methodology fix, not new
mounting). ~86 of 117 routers remain UNKNOWN** — larger than the
previous "~64 of 89" not from regression but from correcting a
denominator that was wrong in every prior batch. Not claimed: "all
boolean-filter defects" (only this precise AST-detectable shape was
scanned for), "authorization complete," or "production ready."

| Commit: `(pending)` | Owner: Mustafa | Files: `app/lims/routes.py`, `app/pharmacy/inventory.py`, `app/pharmacy/routes.py`, `app/pharmacy/services.py`, `app/radiology/pacs.py`, `app/routes/admin.py`, `scripts/security/boolean_not_filter_guard.py`, 1 new test file, 5 docs | Next action: trace the 25 newly-surfaced UNKNOWN routers from the accounting correction (highest priority — they were invisible to every prior batch); separately, the pharmacy `/batches/expiring` route-shadowing bug (documented this pass) is a small, cheap, independent follow-up if a future batch is scoped to fix P2/P3-adjacent findings rather than only document them. |

## Batch 6 — Runtime Surface Reconciliation + Security Triage Acceleration

Combined discovery/triage pass across 16 of the 25 routers Batch 5's
accounting correction surfaced (`login, register, verification,
identity, id_scan, qr, cds_hooks, security, patients, test_results,
notifications, compliance, admin_log_level, setup` fully traced;
`ehr, ehr_fhir` sampled/structurally confirmed).

**Confirmed and CLOSED — same systemic shape recurring a 4th and 5th
time this session**: a route depends only on `Depends(get_current_user)`
(authentication) with zero `require_permission(...)` call anywhere in
the function (authorization), while tenant isolation
(`current_user.lab_id`) is correctly enforced. Confirmed exploitable
via direct RBAC query against all 10 roles (`cashier`, `citizen`,
`finance_auditor`, `finance_controller`, `finance_operator`,
`reconciler`, `refund_reviewer` lack `patients:read` entirely; those
plus `doctor`, `ministry_admin`, `province_admin`, `technician` also
lack `patients:write`).

**7 routes fixed across 4 files** (all `require_permission(...)` added,
reusing existing RBAC permission strings — no new permissions, no RBAC
matrix changes):
- `app/routes/identity.py::link_national_id` → `patients:write`
- `app/routes/patients.py` — all 6 routes (4 → `patients:read`, 2 →
  `patients:write`) — the largest single-router blast radius this
  batch: the entire canonical patient-management surface (full_name,
  phone, birth_date, gender, email, national_id, family_id) was
  previously reachable by any authenticated LabUser regardless of role
- `app/routes/test_results.py::create_test_result` → `results:write`
  (plus `list_citizen_results`/`citizen_timeline` → `results:read`,
  same-file, low-risk, fixed alongside for consistency)
- `app/routes/compliance.py` — 4 FHIR export routes
  (`get_fhir_patient` → `patients:read`; `get_fhir_observations`,
  `get_fhir_diagnostic_report`, `get_fhir_service_request` →
  `results:read`)

**Negative-proofed**: `git stash push --` on all 4 files, reproduced
all 7 findings live via a new permanent regression test
(`backend/tests/test_batch6_permission_gates.py`, 10 tests — 7
negative-proof + 3 sanity), `git stash pop`, md5-verified byte-identical
restoration, re-ran to confirm 10/10 pass post-fix. 163 + 58 = 221
adjacent regression tests re-run — 0 failures.

**New P1-candidate systemic gap found, documented, NOT fixed this
pass**: `app/routes/ehr.py` (86 routes) + `app/routes/ehr_fhir.py` (29
routes) — the identical missing-permission-check shape, confirmed via
`grep -c require_permission` returning 0 across both files plus
representative sampling, but **no existing RBAC permission string
fits** (`ehr:read`/`ehr:write` do not exist) — fixing this correctly
requires a permission-taxonomy decision (reuse `patients:*`/`results:*`
vs. add new `ehr:*` permissions to the RBAC matrix for all 10 roles)
that is out of this batch's bound. See GAP-3 in
`docs/security/AUTHORIZATION_GAP_REGISTER.md` for full detail.

**Also traced this pass, VERIFIED SAFE, no fix needed**: `login`,
`register`, `verification`, `id_scan`, `qr` (intentional capability-URL
design), `cds_hooks`, `admin_log_level` (already correctly gated),
`setup` (intentionally public). `notifications` (tenant-scoped,
no state mutation — low-risk, not fixed). `security` (`/security/status`
— P3, platform-scoped aggregate counts, SYSTEM_CONTROLLED allowance,
documented not fixed).

**Boolean-filter detector re-run this pass** (`scripts/security/boolean_not_filter_guard.py`):
0 hits — no regression of the Batch 5 pattern.

**UNKNOWN accounting (exact this pass, not approximate)**: 86 (Batch
5's figure) − 16 (routers moved to VERIFIED/PARTIALLY VERIFIED this
pass) = **70 of 117 mounted routers remain UNKNOWN.** 9 of the 25
Batch-5-surfaced routers not yet examined: `demo, metrics, dashboard,
app_updates, device_results, quality_control, critical_alerts, batch,
mobile`.

**Documentation updated**: `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`
(Batch 6 section + exact UNKNOWN recalculation), `docs/security/AUTHORIZATION_GAP_REGISTER.md`
(GAP-2 closed, GAP-3 opened/documented), this queue (Batch 6 entry).

STATUS: **7 P1 findings + 1 systemic P2 CLOSED across 4 files (12
routes). 1 new P1-candidate systemic gap (GAP-3, 115 routes) OPEN —
BLOCKED on a permission-taxonomy decision, documented not fixed. 16 of
25 newly-surfaced routers resolved; 70 of 117 mounted routers remain
UNKNOWN.** Not claimed: "authorization complete," "security complete,"
"production ready," or "national scale ready." Carried forward
unchanged: `adaptive-auth-account-id-idor` (P1, BLOCKED —
NEEDS_DECISION), Hospital schema blocker (13/14 tables lack Alembic
migrations), external CI runner blocker, pharmacy `/batches/expiring`
route-shadowing bug (P3, documented not fixed).

| Commit: `(pending)` | Owner: Mustafa | Files: `app/routes/identity.py`, `app/routes/patients.py`, `app/routes/test_results.py`, `app/routes/compliance.py`, 1 new test file, 3 docs | Next action: resolve GAP-3's permission-taxonomy question (reuse `patients:*`/`results:*` vs. add `ehr:*` to the RBAC matrix) then apply the fix across `ehr.py`/`ehr_fhir.py`'s 115 routes with the same negative-proof discipline; separately, trace the remaining 9 UNKNOWN routers from Batch 5's surfacing (`demo, metrics, dashboard, app_updates, device_results, quality_control, critical_alerts, batch, mobile`). |

## Batch 7 — EHR Authorization Taxonomy + Remaining Small Router Sweep

Two linked objectives: (A) resolve Batch 6's open `ehr`/`ehr_fhir`
taxonomy question — **without** directly patching all 115 routes,
establishing the authorization model first; (B) trace the 9 remaining
Batch-5-surfaced routers Batch 6 didn't reach.

**Canonical ownership established (the real work this batch)**: full
route-family inventory of `ehr.py` (86 routes) + `ehr_fhir.py` (29
routes) found EHR's clinical resources are genuinely EHR/National-owned
— keyed to `app.national.domain.patient.Patient` (`national_patients`
table), the National platform's own canonical patient identity,
structurally distinct from the legacy `patients` table that
`patients:read`/`patients:write` guard (confirmed via `app/national/ADR.md`
ADR-001, which already documents EHR's separate declarative base).
Tenant isolation across this boundary is sound (both share the same
`lab_id` value space). **Critical discovery**: the National domain
already has its own, considerably more sophisticated authorization
layer — `app/national/security/{rbac,abac,consent_enforcement,
break_glass}.py`, a 16-role × 42-permission ABAC/RBAC engine with
consent enforcement and break-glass, documented as built in
`app/national/DOMAIN_AUDIT_REPORT.md` — but confirmed, by grep, **never
wired to any live route** (its own route files aren't mounted in
`app/factory.py`; `ehr.py`/`ehr_fhir.py`/`ehr_service.py` never import
it). `NationalRole` doesn't map onto `LabUser.role` (the legacy 10-role
space actually issued in JWTs) — no mapping function exists anywhere.

Rather than guess between "reuse the legacy flat RBAC" and "wire in the
dormant National layer," this was recorded as **`docs/national/ADR.md`
ADR-009** — an explicit, evidence-backed architecture decision put to a
domain owner, with all 3 options (reuse legacy, wire in National's own
layer, or a hybrid interim) laid out with consequences.

**Family-level classification of the 115 routes** (not exhaustive
per-route patching, per this batch's own instruction): 109 routes
(clinical sub-resource CRUD, FHIR reads/searches over EHR-native +
National models, the generic FHIR create/update/delete/batch
dispatcher) are **BLOCKED pending ADR-009**. 3 routes
(`ehr_fhir.py`'s `fhir_read_observation`, `fhir_search_observation`,
`fhir_search_provenance`) turned out to project the legacy
`LabResult`/`LabOrder`/`AuditLog` canonical resources — **already
permissioned elsewhere in the codebase** — and were fixed with
`require_permission("results:read")`/`require_permission("audit:read")`,
the precise, unambiguous, already-established fit. 3 routes (FHIR
metadata, population-summary analytics, one cross-facility-gated note
route with its own pre-existing `ClinicalEhrReadGate`) are VERIFIED,
not gaps.

**Small-router sweep (Phase 8) — all 9 remaining Batch-5-surfaced
routers traced**: `demo`, `metrics`, `dashboard`, `app_updates`,
`mobile` (11 routes) — **VERIFIED SAFE** (fail-closed demo gate,
production-Bearer-gated Prometheus endpoint, already-correctly-gated
dashboard, intentionally-public update manifest, all-self-scoped
mobile routes). `device_results.py::receive_device_results`,
`critical_alerts.py` (both routes), `batch.py::create_batch_orders` —
the same Batch-6-established missing-permission-check P1 shape (a
mutation or PII-bearing read on the same canonical `LabResult`/
`LabOrder` resources Batch 6 already permissioned, gated with nothing
but `get_current_user`) — **fixed** with the already-correct
`results:write`/`results:read`/`orders:write`. `quality_control.py` (4
routes) — same shape, but `QualityControl` has no existing precise-fit
permission (not the same resource as `patients:*`/`results:*`/
`orders:*`) — **documented, not fixed** (P2/P3: tenant-isolated, no
PII, no patient-safety bypass).

**Negative-proofed**: `git stash`/`pop` on all 4 fixed files (2
separate cycles — `ehr_fhir.py` alone, then
`device_results.py`+`critical_alerts.py`+`batch.py` together),
md5-verified byte-identical restoration both times; 2 new permanent
regression test files
(`backend/tests/test_batch7_ehr_fhir_permission_gates.py`, 5 tests;
`backend/tests/test_batch7_small_router_permission_gates.py`, 7 tests)
reproduce every one of the 7 findings live against the reverted state
(200/201 where 403 is expected) and confirm the fix post-restore.
Full backend suite re-run: 3099 passed (2 pre-existing, unrelated
failures excluded — already confirmed identical on unmodified HEAD in
Batch 6).

**Detectors re-run**: `scripts/security/boolean_not_filter_guard.py` —
0 hits. `scripts/log_action_arg_order_guard.py` — 0 hits.
`scripts/setattr_mass_assignment_guard.py` — flagged 17 candidates in
`app/services/ehr_service.py` (unguarded `setattr` loops in every
`update_*` function); checked and confirmed not exploitable through
the live route surface today (every `ehr.py` Update Pydantic model
declares only safe fields, no `extra="allow"` override) — recorded as
a defense-in-depth observation, not fixed (out of this batch's
authorization-taxonomy mandate).

**UNKNOWN accounting (exact)**: 70 (Batch 6) − 9 (all remaining
Batch-5-surfaced routers now examined) = **61 of 117 mounted routers
remain UNKNOWN.** All 25 routers from Batch 5's router-count correction
have now been examined (16 in Batch 6, 9 in Batch 7).

**Documentation updated**: `docs/security/AUTHORIZATION_COVERAGE_MATRIX.md`
(Batch 7 section + exact UNKNOWN recalculation), `docs/security/AUTHORIZATION_GAP_REGISTER.md`
(GAP-3 refined with family-level classification, GAP-4 closed, GAP-5
opened/documented), `docs/national/ADR.md` (new ADR-009), this queue
(Batch 7 entry).

STATUS: **6 P1 findings CLOSED across 4 files (device_results.py,
critical_alerts.py, batch.py, ehr_fhir.py). 1 new architecture decision
recorded (ADR-009) covering 109 EHR/FHIR routes — OPEN, BLOCKED on a
human decision, explicitly not guessed. 1 new small P2/P3 finding
documented (quality_control.py). All 25 of the routers Batch 5's
accounting correction surfaced have now been examined; 61 of 117
mounted routers remain UNKNOWN.** Not claimed: "authorization
complete," "security complete," "production ready," or "national scale
ready." Carried forward unchanged: `adaptive-auth-account-id-idor` (P1,
BLOCKED — NEEDS_DECISION), Hospital schema blocker, external CI runner
blocker, pharmacy `/batches/expiring` route-shadowing bug (P3).

| Commit: `(pending)` | Owner: Mustafa | Files: `app/routes/ehr_fhir.py`, `app/routes/device_results.py`, `app/routes/critical_alerts.py`, `app/routes/batch.py`, 2 new test files, `docs/national/ADR.md` (new ADR-009), 4 other docs | Next action: a domain owner must pick ADR-009's option (reuse legacy `patients:*`/`results:*`, wire in `app/national/security/*`, or a hybrid interim) so the remaining 109 EHR/FHIR routes can be fixed with the same negative-proof discipline; separately, decide `quality_control.py`'s permission (reuse `staff:manage` or add `qc:*`); then trace the still-untraced routers (`edge`, `ai_fabric`, `control_plane`, `integrations`, `chronic_care`, `certification`, `citizen_platform`, `contracts`, `ai_telemetry`, `kernel`/`clinical_gateway`, and the generic `routes/` package's remaining untraced files). |

## Batch 8 — Full Forensic Production Closure (bounded)

**BRANCH/BASELINE DISCREPANCY FOUND FIRST — read before anything else.**
This batch's directive stated `HEAD 96f40e02`, "3338 passed, 329 skipped, 0
failed." That commit does not exist on `claude/mustafa-parallel-engineering`.
It lives on a sibling branch, `claude/p0-2-pharmacy-reconciliation`, forked
from the same `main` commit (`46158e90`) but independently developed under
an entirely different, NR-numbered engineering program (pharmacy
reconciliation, MPI, ORM writability across 76 tables, LIMS result-release,
national-ID identity work — verified via `git log --oneline --all | grep
96f40e02` + `git merge-base`). Continued this batch on
`claude/mustafa-parallel-engineering` (this session's designated,
continuously-worked branch; switching branches without explicit
instruction would violate this session's own git-safety rules). Re-measured
this branch's real baseline: **3099 passed, 27 skipped, 2 pre-existing
failures** (same 2 as every batch since Batch 6), **117 mounted router
modules** (re-derived via the known `app.factory.py` for-loop structure,
unchanged since Batch 5), **2103 individual route operations across 1794
distinct paths** (new precision this pass, via a live `app.openapi()`
schema dump rather than router-module counting). **HUMAN ACTION REQUIRED**:
confirm which branch this production-closure effort should track — these
two branches cannot be silently reconciled by an automated pass.

**Phase 4 (LIMS audit role) + the same pattern found in Hospital**: fixed
the 4 known `user_role="lab_tech"` hardcode sites in
`app/lims/services.py`, and — per this batch's own "if a repair reveals a
broader pattern, inspect all reachable instances" principle — searched for
and found the identical shape in `app/services/hospital_service.py` (5
sites, `user_role="hospital_staff"`). Both fixed by threading a required
`user_role: str` parameter from `current_user.role` at every route call
site; confirmed non-spoofable (no request schema in either domain declares
a `role` field). See
`docs/security/SYSTEMIC_CONCURRENCY_PATTERN_REGISTER.md` Pattern 4 and
`docs/security/AUTHORIZATION_GAP_REGISTER.md` GAP-6 for full detail. 29 new
regression tests (17 LIMS + 12 Hospital), 2 negative-proof cycles
(git stash/pop, md5-verified byte-identical restoration both times).

**Bounded forensic sweep** (not an exhaustive 24-phase rewrite): re-ran
both existing detectors (`boolean_not_filter_guard.py`,
`log_action_arg_order_guard.py` — 0 hits each); ran
`setattr_mass_assignment_guard.py` repo-wide (77 candidates, 50
self-flagged already-guarded, 27 unguarded — spot-checked 20 of the 27
across 3 domains and confirmed not exploitable via the live route surface
in every one checked, 7 left as UNKNOWN rather than assumed safe); grepped
the full tree for hardcoded tenant IDs (found exactly one,
`telegram_bot_commands.py`'s `lab_id=1`, confirmed dead code — its router
is never mounted in `app/factory.py`).

**Built `docs/security/PRODUCTION_READINESS_MATRIX.md`** (new this pass,
per Phase 20) — an honest, evidence-cited status for every category the
directive required, using only VERIFIED/PARTIALLY VERIFIED/BLOCKED/UNKNOWN/
NOT STARTED, built from real evidence gathered across all 8 batches plus
this pass's own fresh checks — not fabricated for categories (AI, Frontend,
Infrastructure, Recovery, Performance) this program has never actually
touched.

**Flagged, not fixed**: `test_icu_lab_workflow_p0.py`'s transfusion-safety
test failure (pre-existing since Batch 6, confirmed identical on
unmodified HEAD) is re-flagged this pass as deserving dedicated clinical-
safety triage rather than remaining a routine "known pre-existing failure"
line item, given what it actually asserts (independent crossmatch +
bedside verification before transfusion).

**Regression**: full suite, 3128 passed (3099 + the 29 new tests), same 2
pre-existing failures, 0 new failures.

STATUS: **1 new systemic P1 CLOSED (audit-role hardcoding, 9 sites across
2 domains, full negative-proof discipline). 1 major branch/baseline
discrepancy surfaced and documented (human action required). Bounded
forensic sweep complete — 1 P3 dead-code observation, 7 mass-assignment
candidates left honestly UNKNOWN. Production readiness matrix built from
real evidence, no category fabricated.** Not claimed: authorization
complete, security complete, production ready, or national scale ready.
Carried forward unchanged: `adaptive-auth-account-id-idor` (P1, BLOCKED),
ADR-009's 109-route decision, `quality_control.py`'s permission question,
Hospital schema blocker, external CI runner blocker, pharmacy
route-shadowing bug (P3), the ICU transfusion test failure (now flagged
for dedicated triage instead of routine carry-forward).

| Commit: `(pending)` | Owner: Mustafa | Files: `app/lims/services.py`, `app/lims/routes.py`, `app/services/hospital_service.py`, `app/routes/hospital.py`, `tests/test_emergency_surgery_workflow_p0.py` (updated for new signature), 2 new test files, `docs/security/PRODUCTION_READINESS_MATRIX.md` (new), 3 other docs | Next action: get a human decision on which branch (`claude/mustafa-parallel-engineering` vs `claude/p0-2-pharmacy-reconciliation`) this production-closure program should actually track — this is the single highest-value next action, ahead of any further code fix, since continuing to fix code on the wrong branch risks the two engineering efforts silently diverging further or conflicting at merge time; separately, triage the `test_icu_lab_workflow_p0.py` failure as a dedicated task rather than a routine carry-forward. |

---

## Abu Ali lane — appended 2026-09-26 (branch `claude/autonomous-run-1`)

Ported this file from `claude/mustafa-parallel-engineering` rather than starting a
second queue, so the two hands share one document. Rows below use the same
columns. `claude/canonical-reconciliation` does not exist on any reachable ref,
so peer state was reconstructed from this queue, branch history and committed
evidence.

| ID | SEVERITY | ROOT CAUSE | OWNER | STATUS | CURRENT COMMIT | BLOCKER | NEXT ACTION |
|----|----------|------------|-------|--------|----------------|---------|-------------|
| NR-052 | P0 (token scanning / DoS) | `/oauth2/introspect` and `/oauth2/revoke` called no `_authenticate_client`, though `/token` in the same file always had. Introspect disclosed `client_id`, `user_id`, `scope`, `exp` for any supplied token; revoke revoked any supplied token. | Abu Ali | **FIXED — VERIFIED** (negative-proofed) | f69d32a1 | none | Residual recorded, not invented: a public client (`token_endpoint_auth_method='none'`) still passes on `client_id` alone — standards-conformant for revoke (RFC 7009 §2.1), a policy question for introspect. |
| NR-053 | P0 (whole provider dead) | Migration 20260716_0015 created 4 columns as `sa.Boolean()`; all four ORM models declared `Integer`, and the routes compared integer literals. `operator does not exist: boolean = integer`. | Abu Ali | **FIXED — VERIFIED** | f69d32a1 | none | `POST /oauth2/token` went 500 → 200 with a real token. Attribution measured: the route literals are load-bearing, the type corrections are defence-in-depth. |
| NR-058/059/060/061 | P1/P2 (fake conformance) | ISO 15189 evaluator scored −500% as `"passed"`, denied all 4 CAP indicators with a false 404, had an `else True` fallback that could never fail, and its 2 routes were the LIMS module's only anonymous ones of 69. | Abu Ali | **FIXED — VERIFIED** | d5c2901b | none | NR-060 recorded as LATENT, not live: all 10 shipped ISO targets carry an operator, so that branch was unreachable. |
| NR-057 / NR-062 | P0/P1 (two identity generations) | 8 domain bases declare `id = Column(String(26), default=_ulid)`; the database uses integer sequences for 70 tables and varchar for 11, with pharmacy split 4/23 inside itself. 162 columns sit in type families PostgreSQL refuses. | Abu Ali | **CONTAINED — pin applied, repair is a decision** | f9a4645e | Identity-model decision for nursing / radiology / nhdw. Pharmacy half DECIDED by PR #258 (integer wins). | Growth blocked by `test_hard_error_type_drift.py` (subset semantics: a repair passes and is reported, only growth fails). |
| NR-064/065/066 | P0 (silent data loss) | 5 `log_action` calls positionally misaligned (`user_role` received the payload dict → `can't adapt type 'dict'` → every route 500); underneath, all 20 mutating `HospitalService` methods flushed and none committed; 10 wrote no audit row; 5 hardcoded `user_role="hospital_staff"`, a value in none of the three role catalogues. | Abu Ali | **FIXED — VERIFIED (code) / BLOCKED (not deployable here — NR-073)** | 7e8e57b5, af6e9e1e, be92ce13 | NR-073 | Two-stage proof established the masking: fixing the audit call alone turned a visible 500 into silent loss (201 with zero rows, and a 404 on the child it had just "created"). 5 guard-owned methods deliberately do NOT commit — `ClinicalCommandGuard` owns their transaction. |
| NR-068 | P1 (token theft by registration) | `POST /oauth2/register` had only `get_current_user`; any authenticated user of any role could register a client with attacker-chosen `redirect_uris` and receive real users' tokens. | Abu Ali | **FIXED — VERIFIED** (ported from Mustafa 60c7aa85, re-verified independently) | 825f0747 | none | Also added the audit row the registration never wrote — actor, real role, redirect_uris, source IP; the plaintext secret is asserted absent from the trail. |
| NR-069 | P1 (authz absent) | 14 routes across patients/test_results/compliance/identity enforced authentication and no authorization. `citizen`, `cashier` and 5 finance roles hold none of the 4 permissions; `technician` holds `results:*` but not `patients:*` yet had patient CRUD. | Abu Ali | **FIXED — VERIFIED** (ported from Mustafa aefeff7f, re-verified) | 8a599536 | none | Negative proof: `cashier` reached `GET /patients` and got 200. Asserted 403 for EVERY role the matrix says lacks the permission, not one sample. |
| NR-070 | P1 (authz absent, larger) | `ehr.py` (86 routes) and `ehr_fhir.py` (29) contain zero `require_permission` calls and are mounted with a bare `include_router`. | Abu Ali | **OPEN — measured, deliberately not bulk-fixed** | — | Needs a per-resource decision; ADR-009 is the input, and the dormant National ABAC layer is a separate architectural question. | Do NOT bulk-assign one permission across 115 routes. |
| NR-054 | P1 (three subsystems empty) | 13 inline `:param::type` casts. SQLAlchemy eats the last character of the parameter name (`caps`→`cap`, `vec`→`ve`), so the value never reaches the statement; every failure was swallowed at WARNING. `ai_model_registry` and `ai_evaluations` held 0 rows. | Abu Ali | **FIXED — VERIFIED** (negative-proofed) | 5106eecd | none | Detector added, because the defect is invisible in the source and only visible by asking SQLAlchemy what it parsed. Carries a positive control so a future SQLAlchemy fix fails the test rather than leaving a dead ban. |
| NR-055 / NR-071 | P0/P1 (clinical) | `calculate_renal_adjustment` answered `requires_adjustment=false, "No adjustment needed"` when it held NO guideline — absence asserted as a clinical negative. Separately, the physical column is `text` while this branch's ORM says JSON, so after PR #258 lands every drug would report "not assessed". | Abu Ali | **FIXED — VERIFIED** | d296c30e, 4323173d | none | NR-071 found by reading #258's models, not by testing this branch — no test here could have found it, because here the column really is JSON. |
| NR-072 | P0 (whole domain ORM-dead) | All 27 pharmacy tables exist physically and 0 of 27 can answer their own SELECT. Missing: `metadata` (23 tables), `fhir_id`/`fhir_resource_type` (20 each). `pharmacy_drug_catalog` declares 25 columns the table lacks. | PR #258 | **OPEN — measured here, deliberately NOT rebuilt** | — | Owned by #258's M1–M4 (0 drift across all 27, down from 243). | Land #258. Re-deriving it here would create a second competing pharmacy reconciliation. |
| NR-073 | P0 (not deployable) | `hospitals`, `hospital_departments` and `hospital_operation_theaters` are created by NO migration on this branch; `20260820_0004` then carries an unconditional FK to the uncreated theatres table. `efcc4b6e` is not an ancestor of HEAD. | Abu Ali → HUMAN GATE for schema shape | **OPEN — confirmed independently, broader than first recorded** | — | The table SHAPE is a domain design; inventing columns to satisfy a foreign key would be fabrication. | Land `efcc4b6e`, or author an additive guarded migration once the shape is decided. **Confirms and broadens Mustafa's `nhdw-hospital-structure-migration-gap` — he recorded one uncreated table; measured here it is three.** |
| NR-074 / NR-075 / NR-006 | P0 (100 tables unwritable) | **This closes Mustafa's `nursing-cross-base-fk-topology` handoff, and it was much bigger than one base.** His row asked me to add `NursingBase` to `orm_topology.py`'s closure. Measured here: `orm_topology.py` does not exist on this branch at all — it lives on `claude/p0-2-pharmacy-reconciliation` (`7c7d21ee`), which is **not** an ancestor of HEAD, so all 21 bases still called a bare `declarative_base()` and the whole NR-086 defect was unfixed here. Re-measured from the live registry: **374 unresolvable FK columns across 100 mapped tables**, not the 310/76 that commit recorded — Nursing (49) and Pharmacy (8) only became referrers after BATCH-3 and M4, `InsBase` adds 6, and `HospitalBase` enters purely as the target of `nursing_*.department_id`. The closure on today's code is **eleven bases, not seven**. Ported the module, extended it to the measured closure, and proved it: `NoReferencedTableError` on `NursingTask` flush → real SQL; assembled app 374 → 3 → 0. The residual 3 were a separate defect (NR-075): three `ForeignKey` strings named `niam_identity_authorities` and `niam_user_sessions`, which exist in no model, no migration and no database, while PostgreSQL's own constraints name `niam_gov_authorities` and `niam_sessions`. The merge also **forced** NR-006, open since the register began as "DECISION REQUIRED": `national_facilities` had two owners, and the `national` one carried `extend_existing=True`, so under one namespace it silently unioned itself into the other, producing a measured 30-column `Table` with 24 phantom columns and breaking the owner that had been correct. | Abu Ali | **FIXED — VERIFIED** (measured per base, live on real PostgreSQL, negative-proofed 3 ways, regression measured and closed) | (this commit) | NR-076 — see next row | Autogenerate scope was held at NR-018's ten bases with an explicit `include_name` filter rather than inherited from the shared object, and NR-080's destructive-diff refusal was ported in the same change, because making autogenerate runnable without it would trade a loud honest failure for a quiet dangerous capability. |
| NR-076 | P0 (all 15 nursing tables unwritable) | **Re-derived from scratch on this branch's own lineage, and it is far larger than I first reported.** Built a clean database with `alembic upgrade 20260716_0002` (116 tables, 15 nursing) and compared column by column — then verified that schema **byte-identical** to the harness database, so unlike NR-073's hospital tables this carries no foreign-lineage caveat. Measured: **149** columns the ORM declares that the table lacks, **176** the table has that the ORM ignores, **41** type mismatches, **15 of 15** primary keys disagreeing (ORM `String(26)` ULID via `NursingBaseEntity` vs `integer`+sequence), **0 rows** anywhere. Not drift — two generations of the nursing data model over one table set. My first report said "encounter_id and id"; that was wrong by two orders of magnitude. Also corrected: models.py/services.py/routes.py are **identical to main** and the router **is mounted** (`factory.py:737`), so 66 clinical routes ship on main on a model that cannot write — BATCH-3 did not cause this and cannot have reconciled it. | Abu Ali → **HUMAN GATE** | **BLOCKED — P0, evidence complete, decision packet written** | (this commit) | Both directions cross a *different* documented approval gate, and Option B additionally cannot be completed (see NR-079). | `docs/architecture/NR-076-nursing-identity-decision.md` costs both options and asks the decision as three questions. Three needed answers: integer or ULID for the nursing PK; which clinical instrument is canonical per assessment table; should `national_encounters` exist. **Do not map one field set onto the other** — the fall-risk table holds the six Morse items while the ORM holds Morse *plus* `elimination` and `age_ge_65` from a different instrument, and scores it `INTEGER` against the table's `double precision`. |
| NR-077 | P1 (two tables unreadable as well as unwritable) | Fell out of the NR-076 re-derivation. `ClinicalChecklist` mapped `nursing_checklists` and `EscalationRecord` mapped `nursing_escalations`; **neither name is created by any migration on any of the 130+ reachable refs.** The real tables are `nursing_clinical_checklists` and `nursing_escalation_records` — which `20260716_0002`'s own docstring names and which the two classes are named after. Three signals to one. These two also read as "absent tables" in every drift measurement before the fix, which is why my first NR-076 totals (137/152/35) were wrong; corrected they are 149/176/41. | Abu Ali | **FIXED — VERIFIED** (negative-proofed) | (this commit) | none | Two strings. Explicitly does **not** make those tables writable — they remain blocked by NR-076, and the pin asserts that rather than letting a name fix look like a repair. |
| NR-079 | P0 (39% of the ORM is undeployable) | **This is `nhdw-hospital-structure-migration-gap` / NR-073 generalised, and it is what removed the obvious answer to NR-076.** Measured against the richest reachable database with the app assembled: of **564** ORM-mapped tables, **222 are absent and not one is created by any migration** — none is merely an unreached lineage. Four of the absent are FK targets of tables that *do* exist: `national_encounters` (13 FK columns), `national_patients` (4), `national_practitioners` (4), `national_citizens` (1); the first and third are not mentioned in any migration at all. All four are ORM-mapped, which is exactly why NR-074's topology guard passes — the FK resolves in the namespace and fails only against a real database. So NR-076's "just add the 149 columns" is unavailable: 12 of them are FKs to a table the migration layer has never heard of. Guarded: the same scan finds 328/342 (95%) of mapped-and-present tables, so **222 is an upper bound** with a measured ~4% false-positive rate, and the four load-bearing cases were each verified by direct grep instead. | Abu Ali → **HUMAN GATE** per domain | **OPEN — measured, deliberately not fixed** | (this commit) | Table shape is a domain design decision in all 222 cases. | Classify the 222 as intended-but-unmigrated / abandoned / renamed; only the first is a migration. **Do not author 222 tables from ORM declarations** — that is inventing schema at scale. Any readiness or certification count computed from mapped rather than physical tables overstates the platform by ~39%. |

### Reconciliation of Mustafa's rows against this branch

| Mustafa's item | Classification here | Evidence |
|---|---|---|
| `60c7aa85` hospital `_get_entity` boolean bug | **DUPLICATE** | Independently found and fixed here with the same `~` remedy. |
| `60c7aa85` note: same bug open in `radiology/pacs.py`, `pharmacy/routes.py`, `routes/admin.py` | **ALREADY FIXED HERE** | An AST sweep finds zero `not <Model>.<attr>` anywhere under `backend/app`. NR-039/NR-042 covered all three. He can strike them. |
| `60c7aa85` `oauth2-register-no-role-check` | **PORTED** | NR-068, re-verified independently rather than taken on trust. |
| `aefeff7f` 7 permission gaps | **PORTED** | NR-069, all 14 assignments re-verified against the 16-role matrix. |
| `0083480c` drug-substitution FK → Integer | **PRECEDENT ADOPTED** | Settled the direction NR-062/NR-063 were blocked on: where a ULID table references an integer-keyed legacy table, integer is canonical. |
| `0083480c` note: `20260820_0004` blocks the chain | **CONFIRMED AND BROADENED** | NR-073 — three uncreated tables, not one. |
| `nhdw-hospital-structure-migration-gap` | **CONFIRMED ON THIS BRANCH** | Same blocker, independently measured, wider scope. |
| `nursing-cross-base-fk-topology` (handed to Abu Ali) | **CLOSED — and his premise corrected** | His next action assumed `orm_topology.py` exists here; it does not (`7c7d21ee` is not an ancestor of HEAD), so the whole NR-086 defect was live on this branch, not just the missing base. Re-measured: eleven bases / 374 FKs / 100 tables, against his 7/310/76. Landed with `NursingBase` in the closure and proved by flush. His pin test `test_nursing_cross_base_fk_topology_blocks_flush` should now be **inverted or retired** on his branch — `lab_users` and `patients` are present, which is the "good sense" failure he predicted. But nursing writes are still broken for an unrelated reason, and on re-derivation that reason is far larger than first reported: see NR-076 (149/176/41 and 15 of 15 primary keys), NR-077 and NR-079. His queue's own figure — "13/15 `nursing_*` tables migration-confirmed" — was **right about the count and right to be cautious**: the two he could not confirm are the two NR-077 fixed, and they exist under different names. |
| PR #258 M4 `DoseGuideline` | **CONSUMED, NOT REBUILT** | Answered my NR-056 human gate outright: years not months, `drug_id` integer FK, global reference data. Nothing invented here. |
| `MUSTAFA_ACTIVE_REPAIR_QUEUE.md` | **PORTED** | This file. One document, two hands. |

### Standing caveat on this lane's evidence base

`gula_canon` is stamped at head `20260909_0001` with 423 tables, but it was built
from a lineage that includes `efcc4b6e`, which is **not** an ancestor of this
branch. Three hospital tables in it are created by no migration here. So every
drift figure this session measured against it — the 162-column pin, the
407-of-423 comparison, the 27-of-27 pharmacy count — is correct **about that
database** and is not a statement about what an operator of this branch can
deploy. Defects proven by execution against it are real; deployability is
separately blocked by NR-073. Recorded against NR-043.
