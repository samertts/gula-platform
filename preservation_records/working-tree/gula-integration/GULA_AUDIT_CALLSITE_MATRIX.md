# GULA AUDIT CALL-SITE MATRIX — COMPREHENSIVE REVIEW

**Directive:** `GULA-AUDIT-COMPREHENSIVE-REVIEW` (owner-authorized, 2026-11-20)
**Repository / HEAD:** `gula-integration` @ `integration/gula-unification-v1` / `2206654dc713ea2de8c564a3207dfe05fde23549`
**Method:** Python 3.12.13 AST parse of all `.py` files (3,269 parsed / 3,270 on disk / 0 parse errors), detecting `ast.Call` where `func` is `Name("log_action")` or `Attribute(attr="log_action")`; parent map for enclosing function/class/`ExceptHandler`. Python 3.10.12 failed to parse 7 PEP 695/701 files; counts for parseable files matched 3.12 exactly.
**Release posture:** **HOLD** — no `PRODUCTION READY` — `production_ready_items = 0`.

Companion deliverables: `GULA_AUDIT_COMPLETE_INVENTORY.md`, `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md`, `GULA_AUDIT_SECURITY_FINDINGS.md`, `GULA_AUDIT_REMEDIATION_ROADMAP.md`, `GULA_AUDIT_ACCEPTANCE_CRITERIA.md`.
**Governance reference:** `OD-001` is recorded `ACCEPTED` in `GULA_OWNER_DECISION_REGISTER.md` for the defined SEC-015/F-01 engineering scope only (Review-3 PASS, `GULA_SEC015_F01_INDEPENDENT_REVIEW_3_REPORT.md`). This matrix does not extend that acceptance to release readiness or any R4 remediation.

---

## 1. Counts by scope

| Scope | `log_action` calls | Files |
|---|---:|---:|
| `backend/app` | **203** | **56** |
| `shared` | **0** | 0 |
| `scripts` | 0 | 0 |
| `backend/tests` | 12 | 7 |
| migrations | 0 | 0 |
| `archive` | 2 | 1 |
| other (`nhop-platform` 19/5; all other trees 0) | 19 | 5 |
| **Repository total** | **236** | **69** |

**Reconciliation:** the previously reported **203 calls / 56 files** is confirmed exactly for `backend/app`; `shared` contributes zero, so `backend/app + shared` = **203 / 56**. The repo-wide 236 includes a **separate legacy `nhop-platform` implementation** (19 calls, different signature/table) and an **archive JSON-file writer** (2 calls). A filtered text scan in this review returned 200 calls / 54 modules after excluding tests, `def` declarations and the NHOP function — a scope difference, not a contradiction (AUD-F14). Full-detail TSV: `/tmp/opencode/audit_log_action_calls.tsv`; exact 203-row TSV: `/tmp/opencode/audit_log_action_backend_app_shared.tsv`.

**Canonical signature** (`backend/app/services/audit_service.py:256`):
`log_action(db, action, resource_type, resource_id=None, user_id=None, user_role=None, lab_id=None, details=None, ip_address=None)`.

---

## 2. Full 203-row matrix — `backend/app` + `shared`

Format: `path:line | enclosing function | enclosing class | except handler`. `-` = none. `EXC(...)` = inside that handler.

```
backend/app/audit/__init__.py:45 | wrapper | - | -
backend/app/citizen_platform/routes.py:50 | _record_access_decision | - | -
backend/app/clinical/command_guard.py:200 | reject | ClinicalCommandGuard | -
backend/app/clinical/command_guard.py:247 | complete | ClinicalCommandGuard | -
backend/app/ehr/clinical_read_gate.py:180 | _audit | ClinicalEhrReadGate | -
backend/app/ems/application/service.py:83 | _audit | EMSService | -
backend/app/financial/routes.py:313 | create_transaction | - | -
backend/app/financial/routes.py:368 | run_billing_cycle | - | -
backend/app/financial/services.py:131 | create_invoice | InvoiceService | -
backend/app/financial/services.py:247 | process_payment | PaymentService | -
backend/app/identity/services/citizen_relationship_service.py:245 | create_pending | CitizenRelationshipWorkflow | -
backend/app/identity/services/citizen_relationship_service.py:388 | create_pending_guardian | CitizenRelationshipWorkflow | -
backend/app/identity/services/citizen_relationship_service.py:435 | activate | CitizenRelationshipWorkflow | -
backend/app/identity/services/citizen_relationship_service.py:475 | revoke | CitizenRelationshipWorkflow | -
backend/app/insurance/api/claims.py:328 | create_claim | - | -
backend/app/insurance/api/claims.py:387 | update_claim | - | -
backend/app/insurance/api/claims.py:426 | submit_claim | - | -
backend/app/insurance/api/claims.py:460 | validate_claim | - | -
backend/app/insurance/api/claims.py:507 | adjudicate_claim | - | -
backend/app/insurance/api/claims.py:541 | approve_claim | - | -
backend/app/insurance/api/claims.py:574 | reject_claim | - | -
backend/app/insurance/api/claims.py:605 | cancel_claim | - | -
backend/app/insurance/api/claims.py:685 | file_appeal | - | -
backend/app/insurance/api/coverages.py:142 | create_coverage | - | -
backend/app/insurance/api/coverages.py:192 | update_coverage | - | -
backend/app/insurance/api/coverages.py:224 | terminate_coverage | - | -
backend/app/insurance/api/network.py:178 | add_network_provider | - | -
backend/app/insurance/api/network.py:212 | update_network_provider | - | -
backend/app/insurance/api/network.py:241 | remove_from_network | - | -
backend/app/insurance/api/network.py:298 | add_network_service | - | -
backend/app/insurance/api/payments.py:184 | record_payment | - | -
backend/app/insurance/api/payments.py:217 | reverse_payment | - | -
backend/app/insurance/api/payments.py:255 | reconcile_payment | - | -
backend/app/insurance/api/payments.py:341 | create_settlement | - | -
backend/app/insurance/api/payments.py:384 | calculate_settlement | - | -
backend/app/insurance/api/payments.py:416 | reconcile_settlement | - | -
backend/app/insurance/api/payments.py:449 | close_settlement | - | -
backend/app/insurance/api/payments.py:605 | create_budget | - | -
backend/app/insurance/api/payments.py:679 | track_budget_spend | - | -
backend/app/insurance/api/policies.py:192 | create_policy | - | -
backend/app/insurance/api/policies.py:242 | update_policy | - | -
backend/app/insurance/api/policies.py:274 | cancel_policy | - | -
backend/app/insurance/api/policies.py:337 | add_policy_coverage | - | -
backend/app/insurance/api/policies.py:406 | add_policy_benefit | - | -
backend/app/insurance/api/providers.py:175 | create_provider | - | -
backend/app/insurance/api/providers.py:225 | update_provider | - | -
backend/app/insurance/api/providers.py:255 | deactivate_provider | - | -
backend/app/insurance/api/providers.py:320 | add_provider_contract | - | -
backend/app/insurance/api/referrals.py:191 | create_referral | - | -
backend/app/insurance/api/referrals.py:242 | update_referral | - | -
backend/app/insurance/api/referrals.py:279 | send_referral | - | -
backend/app/insurance/api/referrals.py:316 | accept_referral | - | -
backend/app/insurance/api/referrals.py:354 | decline_referral | - | -
backend/app/insurance/api/referrals.py:394 | complete_referral | - | -
backend/app/insurance/api/referrals.py:434 | cancel_referral | - | -
backend/app/insurance/api/referrals.py:479 | validate_referral | - | -
backend/app/lims/routes.py:344 | create_department | - | -
backend/app/lims/routes.py:993 | order_fhir_bundle | - | -
backend/app/lims/services.py:78 | register | SpecimenService | -
backend/app/lims/services.py:131 | transition | SpecimenService | -
backend/app/lims/services.py:209 | create_lims_order | OrderService | -
backend/app/lims/services.py:297 | create_result | ResultService | -
backend/app/national/api/routes/interop.py:202 | pix_query | - | -
backend/app/national/api/routes/interop.py:354 | mhd_provide_document | - | -
backend/app/nhdw/offline.py:213 | apply_batch | OfflineService | -
backend/app/nhdw/offline.py:239 | resolve_conflict | OfflineService | -
backend/app/nhdw/services.py:85 | create_admission | NHDWService | -
backend/app/nhdw/services.py:117 | update_admission | NHDWService | -
backend/app/nhdw/services.py:187 | discharge_patient | NHDWService | -
backend/app/nhdw/services.py:244 | transfer_patient | NHDWService | -
backend/app/nhdw/services.py:260 | add_queue_entry | NHDWService | -
backend/app/nhdw/services.py:325 | _update_queue_status | NHDWService | -
backend/app/nhdw/services.py:362 | add_waiting_list | NHDWService | -
backend/app/nhdw/services.py:402 | convert_waiting_to_admission | NHDWService | -
backend/app/nhdw/services.py:418 | create_clinical_task | NHDWService | -
backend/app/nhdw/services.py:443 | update_clinical_task | NHDWService | -
backend/app/nhdw/services.py:467 | assign_clinical_task | NHDWService | -
backend/app/nhdw/services.py:491 | complete_clinical_task | NHDWService | -
backend/app/nhdw/services.py:553 | create_ward_round | NHDWService | -
backend/app/nhdw/services.py:631 | create_care_plan | NHDWService | -
backend/app/nhdw/services.py:664 | update_care_plan | NHDWService | -
backend/app/nhdw/services.py:689 | review_care_plan | NHDWService | -
backend/app/nhdw/services.py:747 | send_message | NHDWService | -
backend/app/nhdw/services.py:820 | create_alert | NHDWService | -
backend/app/nhdw/services.py:874 | resolve_alert | NHDWService | -
backend/app/nhdw/services.py:908 | create_telemedicine_session | NHDWService | -
backend/app/nhdw/services.py:991 | create_resource_schedule | NHDWService | -
backend/app/nhdw/services.py:1050 | save_dashboard_config | NHDWService | -
backend/app/nhdw/services.py:1065 | save_dashboard_config | NHDWService | -
backend/app/nhdw/services.py:1096 | create_shift_report | NHDWService | -
backend/app/nursing/coordination.py:34 | send_physician_message | CareCoordinatorService | -
backend/app/nursing/coordination.py:58 | request_lab_collection | CareCoordinatorService | -
backend/app/nursing/coordination.py:87 | coordinate_radiology | CareCoordinatorService | -
backend/app/nursing/coordination.py:117 | coordinate_pharmacy | CareCoordinatorService | -
backend/app/nursing/coordination.py:148 | manage_referral | CareCoordinatorService | -
backend/app/nursing/coordination.py:178 | plan_discharge | CareCoordinatorService | -
backend/app/nursing/coordination.py:206 | family_communication | CareCoordinatorService | -
backend/app/nursing/coordination.py:236 | home_care_handover | CareCoordinatorService | -
backend/app/nursing/medication.py:94 | record_administration | MedicationAdminService | -
backend/app/nursing/medication.py:205 | electronic_signature | MedicationAdminService | -
backend/app/nursing/services.py:64 | assign_patient | NursingService | -
backend/app/nursing/services.py:95 | unassign_patient | NursingService | -
backend/app/nursing/services.py:170 | create_task | NursingService | -
backend/app/pharmacy/inventory.py:33 | _audit | StockAdjustmentService | -
backend/app/pharmacy/inventory.py:518 | initiate_recall | RecallService | -
backend/app/pharmacy/inventory.py:544 | resolve_recall | RecallService | -
backend/app/pharmacy/services.py:64 | _audit | PharmacyService | -
backend/app/platform/audit.py:42 | create_entry | AuditService | -
backend/app/radiology/clinical_read_gate.py:173 | _audit | ClinicalRadiologyReadGate | -
backend/app/radiology/services.py:86 | _audit | RadiologyService | -
backend/app/routes/admin.py:197 | toggle_lab | - | -
backend/app/routes/admin.py:236 | activate_lab | - | -
backend/app/routes/admin.py:402 | approve_doctor | - | -
backend/app/routes/admin.py:435 | revoke_doctor | - | -
backend/app/routes/admin.py:512 | toggle_citizen | - | -
backend/app/routes/admin.py:548 | verify_citizen | - | -
backend/app/routes/admin.py:625 | create_lab | - | -
backend/app/routes/admin.py:787 | create_user | - | -
backend/app/routes/admin.py:852 | change_user_role | - | -
backend/app/routes/admin.py:887 | toggle_user | - | -
backend/app/routes/admin.py:986 | kill_switch_activate | - | -
backend/app/routes/admin.py:1012 | kill_switch_deactivate | - | -
backend/app/routes/ai.py:659 | _emit_critical_alert | - | -
backend/app/routes/canonical_patient.py:80 | _write_canonical_audit | - | -
backend/app/routes/citizen_portal.py:199 | citizen_login | - | -
backend/app/routes/citizen_portal.py:225 | citizen_login | - | -
backend/app/routes/compliance.py:601 | get_dhis2_aggregate | - | -
backend/app/routes/demo.py:122 | start_demo_session | - | -
backend/app/routes/device_results.py:115 | receive_device_results | - | -
backend/app/routes/integrations.py:211 | reject_inbox_event | - | -
backend/app/routes/login.py:103 | _complete_login | - | -
backend/app/routes/login.py:187 | login | - | -
backend/app/routes/login.py:205 | login | - | -
backend/app/routes/login.py:223 | login | - | -
backend/app/routes/login.py:249 | login | - | -
backend/app/routes/login.py:263 | login | - | -
backend/app/routes/login.py:293 | login | - | -
backend/app/routes/login.py:323 | login | - | -
backend/app/routes/login.py:399 | privileged_mfa_verify | - | -
backend/app/routes/login.py:431 | privileged_mfa_verify | - | -
backend/app/routes/login.py:451 | privileged_mfa_verify | - | -
backend/app/routes/mobile.py:172 | refresh_access_token | - | -
backend/app/routes/mobile.py:345 | register_device | - | -
backend/app/routes/password_reset.py:53 | forgot_password | - | -
backend/app/routes/password_reset.py:81 | reset_password | - | -
backend/app/routes/patient_card.py:70 | get_patient_card | - | -
backend/app/routes/patient_card.py:131 | scan_patient_card | - | EXC(CardTokenError)
backend/app/routes/patient_card.py:145 | scan_patient_card | - | -
backend/app/routes/patient_card.py:162 | scan_patient_card | - | -
backend/app/routes/patient_card.py:196 | get_patient_full_history | - | -
backend/app/routes/patient_card.py:297 | get_patient_card_print | - | -
backend/app/routes/patients.py:197 | create_patient_route | - | -
backend/app/routes/register.py:238 | register_lab | - | -
backend/app/routes/register.py:382 | register_citizen | - | -
backend/app/routes/register.py:484 | register_staff | - | -
backend/app/routes/register.py:647 | register_doctor | - | -
backend/app/routes/samples.py:83 | create_sample | - | -
backend/app/routes/samples.py:187 | update_sample | - | -
backend/app/routes/test_results.py:377 | create_test_result | - | -
backend/app/routes/test_results.py:563 | verify_test_result | - | -
backend/app/routes/tiers.py:169 | request_upgrade | - | -
backend/app/routes/tiers.py:261 | submit_upgrade_demand | - | -
backend/app/routes/tiers.py:404 | set_lab_tier | - | -
backend/app/routes/tiers.py:486 | set_feature_flag | - | -
backend/app/routes/user_preferences.py:115 | _audit | - | -
backend/app/routes/verification.py:145 | request_verification | - | -
backend/app/routes/verification.py:187 | confirm_verification | - | -
backend/app/routes/verification.py:202 | confirm_verification | - | -
backend/app/security/session.py:128 | bump_perm_version | - | -
backend/app/services/admin_service.py:120 | toggle_lab | - | -
backend/app/services/admin_service.py:146 | activate_lab | - | -
backend/app/services/admin_service.py:264 | create_lab | - | -
backend/app/services/admin_service.py:364 | create_user | - | -
backend/app/services/admin_service.py:403 | change_user_role | - | -
backend/app/services/admin_service.py:431 | toggle_user | - | -
backend/app/services/consent_service.py:158 | grant_consent | - | -
backend/app/services/consent_service.py:206 | revoke_consent | - | -
backend/app/services/consent_service.py:232 | log_access_decision | - | -
backend/app/services/hospital_service.py:70 | create_hospital | HospitalService | -
backend/app/services/hospital_service.py:100 | update_hospital | HospitalService | -
backend/app/services/hospital_service.py:125 | deactivate_hospital | HospitalService | -
backend/app/services/hospital_service.py:174 | create_campus | HospitalService | -
backend/app/services/hospital_service.py:348 | assign_bed | HospitalService | -
backend/app/services/hospital_service.py:400 | discharge_bed | HospitalService | -
backend/app/services/hospital_service.py:472 | transfer_bed | HospitalService | -
backend/app/services/hospital_service.py:540 | update_operation_theater_status | HospitalService | -
backend/app/services/hospital_service.py:610 | complete_surgical_safety_checklist | HospitalService | -
backend/app/services/hospital_service.py:811 | create_appointment | HospitalService | -
backend/app/services/mobile_service.py:83 | refresh_token | - | -
backend/app/services/order_service.py:439 | create_order | - | -
backend/app/services/order_service.py:609 | update_result | - | -
backend/app/services/order_service.py:673 | validate_order | - | -
backend/app/services/order_service.py:717 | cancel_order | - | -
backend/app/services/order_service.py:788 | get_public_result | - | -
backend/app/services/order_service.py:887 | download_result_pdf | - | -
backend/app/services/patient_service.py:182 | create_patient | - | -
backend/app/services/patient_service.py:232 | create_patient | - | -
backend/app/services/patient_service.py:291 | update_patient | - | -
backend/app/services/patient_service.py:501 | _resolve_mpi | - | EXC(Exception)
backend/app/services/sample_service.py:101 | create_sample | - | -
backend/app/services/sample_service.py:187 | update_sample | - | -
backend/app/services/test_result_service.py:189 | create_result | - | -
backend/app/services/test_result_service.py:295 | verify_result | - | -
```

---

## 3. Indirect wrappers (static call sites; runtime reachability UNKNOWN)

| Wrapper definition → canonical call | Static call sites |
|---|---|
| `backend/app/audit/__init__.py:18 audit_log` decorator → `:45` | `routes/ehr_fhir.py:1367,1391,1414` (`@audit_log(action="fhir.create"/"update"/"delete")`) |
| `backend/app/platform/audit.py:32 AuditService.create_entry` → `:42` | **0 in repo** (external callers unknown; registered but dormant — AUD-F11) |
| `backend/app/citizen_platform/routes.py:43 _record_access_decision` → `:50` | same file `:78,96,101,104` |
| `backend/app/services/consent_service.py:219 log_access_decision` → `:232` | `backend/app/security/consent_dep.py:113,139,156,184,204` |
| `backend/app/routes/canonical_patient.py:50 _write_canonical_audit` → `:80` | same file `:256,398,466` |
| `backend/app/routes/ai.py:647 _emit_critical_alert` → `:659` | `routes/ai.py:947`; `backend/tests/unit/test_audit_bypass_regression.py:77` |
| `backend/app/ehr/clinical_read_gate.py:154 ClinicalEhrReadGate._audit` → `:180` | same file `:53,151` |
| `backend/app/radiology/clinical_read_gate.py:148 ClinicalRadiologyReadGate._audit` → `:173` | same file `:58,145` |
| `backend/app/radiology/services.py:83 RadiologyService._audit` → `:86` | same file `:380,639,679,737,768,852,922,957` |
| `backend/app/ems/application/service.py:80 EMSService._audit` → `:83` | same file `:153,217,345,401` |
| `backend/app/pharmacy/services.py:63 PharmacyService._audit` → `:64` | same file (24 sites) `:81,98,107,174,211,228,243,298,310,327,410,517,632,666,685,1006,1208,1231,1240,1261,1282,1311,1340,1359` |
| `backend/app/pharmacy/inventory.py:32 StockAdjustmentService._audit` → `:33` | same file `:97,145,207` |
| `backend/app/routes/user_preferences.py:107 _audit` → `:115` | same file `:202,305,351` |

**Separate implementations (not canonical):** `nhop-platform/app/services/audit.py:13::log_action` — 19 call sites in `nhop-platform/app/api/v1/*`, different signature (`target_type`, `target_id`, `actor_id`, `metadata`) and table; `archive/experimental/autonomous_manager/action_log.py:7::log_action` — 2 call sites, JSON-file writer, bare `except:` at `:14` suppressing JSON read errors. Unrelated `_audit` methods in payments, billing, identity, `shared/communication/center.py` and `clinical_gateway/service.py` write to other sinks and are excluded.

---

## 4. Exception-handler analysis

Only **2 of 236** calls are lexically inside an `ExceptHandler`; only one is broad:

| Site | Handler | Behavior |
|---|---|---|
| `backend/app/services/patient_service.py:500` → call `:501` (`_resolve_mpi`) | `except Exception as mpi_err` | **SUPPRESSES** the original MPI failure; writes `action="mpi_resolve_failed"` and returns `(citizen_ulid, mpi_match_method)` initialized to `(None, None)` at `:481-482`. `log_action` exceptions themselves still propagate. See AUD-F16. |
| `backend/app/routes/patient_card.py:129` → call `:131` (`scan_patient_card`) | `except CardTokenError as e` | Narrow handler; **RE-RAISES** as `HTTPException(400)` after auditing. Correct pattern. |

A broader scan including wrapper names (`_audit`, `audit_log`, `create_entry`, `log_access_decision`, `_record_access_decision`, `_write_canonical_audit`, `_emit_critical_alert`) found **no additional** `ExceptHandler` cases. `_emit_critical_alert` (`routes/ai.py:672`) sits outside an enclosing handler but contains its own broad handler around the call — see `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md` §3.

**Method limitation — `contextlib.suppress`:** the AST analysis above detects `ExceptHandler` nodes only. `contextlib.suppress(Exception)` is a `with` statement and is therefore **not** counted here. Two canonical call sites are silently suppressed this way: `backend/app/routes/password_reset.py:53` (`password_reset_requested`) and `:81` (`password_reset_completed`), with no logger call (AUD-F17). Suppression review must include `contextlib.suppress`; see `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md` §8 and §10.

---

## 5. Signature, positional and duplicate analysis

### 5.1 Invalid keyword arguments — AUD-F15
- **0 calls** repo-wide exceed 2 positional args (AUDIT-POSITIONAL-001 guard respected): `n_pos=0` → 53, `n_pos=1` → 181, `n_pos=2` → 2 (both archive writer).
- Two canonical calls use **invalid keyword names**: `backend/app/financial/routes.py:313` and `:368` pass `entity_type=`/`entity_id=`; `log_action` accepts `resource_type`/`resource_id`. Static `TypeError` at runtime. Verified first-hand in this review.
- These are the only 2 canonical calls missing `resource_type`.

### 5.2 Byte-identical duplicate full calls (8 groups)
1. `backend/tests/test_disaster_recovery.py:116,148`
2. `backend/app/services/mobile_service.py:83` ↔ `backend/app/routes/mobile.py:172` (`token_refresh`)
3. `backend/app/services/admin_service.py:120` ↔ `backend/app/routes/admin.py:197` (`toggle_lab`)
4. `backend/app/services/admin_service.py:146` ↔ `backend/app/routes/admin.py:236` (`activate_lab`)
5. `backend/app/services/admin_service.py:431` ↔ `backend/app/routes/admin.py:887` (`toggle_user`)
6. `backend/app/radiology/services.py:86` ↔ `backend/app/ems/application/service.py:83` (`_audit` bodies)
7. `backend/app/radiology/clinical_read_gate.py:173` ↔ `backend/app/ehr/clinical_read_gate.py:180` (`_audit` bodies)
8. `backend/app/pharmacy/services.py:64` ↔ `backend/app/pharmacy/inventory.py:33` (`_audit` bodies)

Groups 3–5: the route files do **not** statically import/call the corresponding service functions, so these are duplicate implementations, **not** confirmed double-writes in one request path. Runtime behavior remains `UNKNOWN` without execution/tracing. No duplicate call with identical `(action, resource_type, resource_id, details, user_id)` inside one function in `backend/app`.

### 5.3 Direct `AuditLog(...)` construction
16 constructions total; **15 outside** `backend/app/services/audit_service.py:275`:
- `backend/app/health_core/reliability/performance.py:86`, `sync_conflicts.py:162`, and tests — **in-memory** class, no DB table.
- Tests (`test_compliance_integrity.py:470,474`; `test_fhir_interoperability_hardening.py:88,96`; `test_admin_service.py:430,446,451`) — SQLAlchemy `audit_logs` rows for test setup.
- `nhop-platform/app/services/audit.py:23` (`db.add` `:32`) — separate `audit_log` table.
- `scripts/generate_demo_data.py:767` (`logs.append`, `add_all` `:779`) — canonical `audit_logs`, no `chain_hash`, `resource_id=str(i)` into an `Integer` column (AUD-F06).

No `db.add(AuditLog(...))` exists outside the legacy NHOP writer.

---

## 6. Unknowns (explicitly not claimed)

- Runtime reachability and decision coverage of all 203 call sites — static enumeration only.
- Whether `AuditService.create_entry` has external callers.
- Whether the duplicate service/route implementations are both live.
- Actual runtime behavior of the two invalid-keyword calls (static signature mismatch only; no execution).
- Whether demo-data NULL-`chain_hash` rows are accepted by all deployments (column is `nullable=True`; verification semantics not executed).

---

## 7. Commands and versions

```bash
python3 --version                    # 3.10.12
python3.12 --version                 # 3.12.13 (/usr/bin/python3.12)
python3.12 /tmp/opencode/audit_inventory.py        # 3,269 files parsed, 0 errors
python3.12 /tmp/opencode/audit_wrappers.py
grep -rn --include='*.py' -E 'def log_action|class AuditLog|AuditLog\(' .
git status --porcelain                            # read-only
```
Excluded dirs: `.git`, `__pycache__`, `node_modules`, `.venv`/`venv`, `.mypy_cache`, `.ruff_cache`, `.pytest_cache`, `.tox`. Artifacts: `/tmp/opencode/audit_log_action_calls.tsv`, `audit_log_action_backend_app_shared.tsv` (exact 203), `audit_log_action_backend_app_shared_compact.tsv`, `audit_inventory_py312.json`, `audit_wrapper_callsites.json`. No application test was run.

---

## 8. Cross-reference to findings

- AUD-F15 (invalid keyword arguments) — §5.1, `GULA_AUDIT_SECURITY_FINDINGS.md`.
- AUD-F16 (MPI-failure suppression) — §4.
- AUD-F02 (`_emit_critical_alert`) — row `routes/ai.py:659`; `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md` §3.
- AUD-F06 (demo NULL-hash rows) — §5.3.
- AUD-F11 (dormant platform wrapper) — row `platform/audit.py:42`.
- AUD-F14 (count methodology) — §1.
- AUD-F17 (password-reset `contextlib.suppress`) — rows `routes/password_reset.py:53,81` in §2 are correct; §4 limitation note explains that their `contextlib.suppress` wrapper is **not** represented by the `ExceptHandler` column (which shows `-`). The call sites are enumerated; the suppression mechanism is not.
- AUD-F20 (FHIR decorator success-only audit) — §3 wrapper row `audit/__init__.py:45`.

**Classification note:** the `EXC(...) / -` column in §2 describes lexical `ExceptHandler` context only. A `-` entry therefore does **not** prove the absence of suppression — `contextlib.suppress` (AUD-F17) and broad handlers inside the callee (e.g. `_emit_critical_alert`, AUD-F02) are separate mechanisms documented in `GULA_AUDIT_FAILURE_PROPAGATION_REPORT.md` §8.

**Status:** `HOLD`. Inventory only; no source, test, migration or staging change; no commit, push, merge or deployment.
