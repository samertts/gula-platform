# Protected Tables Registry

**Part of the GULA Data Preservation Constitution (Rule 15)**
**Version:** 1.0.0
**Last Updated:** 2026-07-22

---

## 1. PURPOSE

This registry lists all database tables that are protected under Rule 15 of the Data Preservation Constitution. Any structural change to a table in this registry requires explicit written approval from the Architecture Board.

---

## 2. PROTECTED TABLE CLASSIFICATION

### TIER 1 — Patient Safety Critical

Changes to these tables require full Architecture Board review and written approval.

| Table | Schema | Model File | Reason |
|-------|--------|-----------|--------|
| `patients` | `backend/app/models/patient.py` | `Patient` | Core patient data, national ID, clinical history |
| `canonical_patients` | `backend/app/models/canonical_patient.py` | `CanonicalPatient` | MPI deduplication master record |
| `patient_links` | `backend/app/models/canonical_patient.py` | `PatientLink` | Cross-system patient identity links |
| `citizen_links` | `backend/app/models/canonical_patient.py` | `CitizenLink` | National citizen registry links |
| `lab_orders` | `backend/app/models/lab_order.py` | `LabOrder` | Clinical laboratory orders |
| `lab_results` | `backend/app/models/lab_result.py` | `LabResult` | Clinical laboratory results |
| `samples` | `backend/app/models/sample.py` | `Sample` | Specimen/sample tracking |
| `test_results` | `backend/app/models/test_result.py` | `TestResult` | Individual test results |
| `critical_alerts` | (routes) | — | Critical/panic value alerts |

### TIER 2 — Audit & Compliance

| Table | Model File | Reason |
|-------|-----------|--------|
| `audit_logs` | `backend/app/models/audit_log.py` | Immutable audit trail (Rule 6) |
| `outbox_events` | `backend/app/models/outbox.py` | Event outbox for guaranteed delivery |

### TIER 3 — Business Operations

| Table | Model File | Reason |
|-------|-----------|--------|
| `labs` | `backend/app/models/lab.py` | Laboratory organization data |
| `organizations` | `backend/app/models/organization.py` | Healthcare organizations |
| `facilities` | `backend/app/models/organization.py` | Facility/location data |
| `lab_users` | `backend/app/models/lab_user.py` | Lab-level user assignments |
| `users` | `backend/app/models/user.py` | Platform user accounts |
| `roles` | `backend/app/models/authorization.py` | Role definitions |
| `permissions` | `backend/app/models/authorization.py` | Permission definitions |
| `role_permissions` | `backend/app/models/authorization.py` | Role-permission assignments |
| `role_assignments` | `backend/app/models/authorization.py` | User-role assignments |
| `tenants` | `backend/app/models/tenant.py` | Multi-tenant isolation |
| `lab_subscriptions` | `backend/app/models/subscription.py` | Lab subscriptions |
| `feature_flags` | `backend/app/models/subscription.py` | Per-tenant feature configuration |

### TIER 4 — Clinical Context

| Table | Model File | Reason |
|-------|-----------|--------|
| `test_types` | `backend/app/models/test_type.py` | Clinical test catalog |
| `quality_controls` | `backend/app/models/quality_control.py` | QC results and rules |
| `consents` | `backend/app/models/consent.py` | Patient consent records |
| `claims` | `backend/app/models/claim.py` | Insurance/billing claims |
| `claim_items` | `backend/app/models/claim.py` | Claim line items |

### TIER 5 — AI & Intelligence

| Table | Model File | Reason |
|-------|-----------|--------|
| `ai_embeddings` | `backend/app/models/ai.py` | AI embedding vectors |
| `ai_conversations` | `backend/app/models/ai.py` | AI chat history |
| `ai_conversation_messages` | `backend/app/models/ai.py` | AI chat messages |
| `ai_agent_executions` | `backend/app/models/ai.py` | AI agent execution history |
| `ai_knowledge_nodes` | `backend/app/models/ai.py` | AI knowledge base |
| `ai_interactions` | `backend/app/models/ai_interaction.py` | All AI interaction history |
| `ai_feedback` | `backend/app/models/ai_interaction.py` | User feedback on AI responses |

### TIER 6 — Edge & Device Integration

| Table | Model File | Reason |
|-------|-----------|--------|
| `edge_devices` | `backend/app/models/edge.py` | Edge device registry |
| `edge_tasks` | `backend/app/models/edge.py` | Edge task assignments |
| `edge_telemetry` | `backend/app/models/edge.py` | Device telemetry history |
| `edge_models` | `backend/app/models/edge.py` | Edge ML models |
| `edge_model_assignments` | `backend/app/models/edge.py` | Model-to-device assignments |

### TIER 7 — Security & Auth

| Table | Model File | Reason |
|-------|-----------|--------|
| `mfa_devices` | `backend/app/models/mfa_device.py` | Multi-factor authentication devices |
| `mfa_sessions` | `backend/app/models/mfa_device.py` | MFA session tracking |
| `oauth2_clients` | `backend/app/models/oauth2_client.py` | OAuth2 client registrations |
| `oauth2_tokens` | `backend/app/models/oauth2_token.py` | OAuth2 token store |
| `service_accounts` | `backend/app/models/service_account.py` | Service account credentials |

---

## 3. WHAT CONSTITUTES A STRUCTURAL CHANGE

Any of the following on a protected table requires Architecture Board approval:

- Adding or removing a column
- Changing a column's data type
- Changing a column's nullability
- Changing a column's default value
- Adding or removing a constraint
- Adding or removing an index
- Adding or removing a foreign key
- Renaming a table or column
- Changing the table's storage parameters
- Adding or removing a trigger
- Changing partition strategy

**Exempt** (no approval needed):
- Adding comments to tables/columns
- Adding non-enforced statistics
- Query performance analysis (read-only)
- Adding advisory locks

---

## 4. APPROVAL PROCESS

To request a structural change to a protected table:

1. Create a GitHub Issue with the `protected-table-change` label
2. Include:
   - Table name and tier
   - Proposed change (before/after schema)
   - Business justification
   - Migration plan (following the safe migration sequence)
   - Rollback plan
   - Data preservation impact assessment
3. Architecture Board reviews within 5 business days
4. Decision recorded in the issue
5. ADR created documenting the change

---

## 5. MAINTENANCE

This registry must be updated when:

- A new table is created that contains business data
- An existing table changes tier classification
- A table is added or removed from the codebase models

The Platform Architect is responsible for keeping this registry current.

---

## 6. AUTO-DETECTION

The `DATA_PRESERVATION_GATE` automatically scans `backend/app/models/` and cross-references against this registry. Any table defined in a model file that is not listed in this registry will generate a warning.

---

## APPENDIX A: TABLE INVENTORY SOURCE

This registry is derived from the model files in `backend/app/models/`:

```
models/__init__.py
models/ai.py
models/ai_interaction.py
models/audit_log.py
models/authorization.py
models/base.py
models/canonical_patient.py
models/claim.py
models/consent.py
models/edge.py
models/lab.py
models/lab_order.py
models/lab_result.py
models/lab_user.py
models/mfa_device.py
models/oauth2_client.py
models/oauth2_token.py
models/organization.py
models/outbox.py
models/patient.py
models/quality_control.py
models/sample.py
models/service_account.py
models/subscription.py
models/tenant.py
models/test_result.py
models/test_type.py
models/user.py
```


## 7. ADDITIONAL INVENTORIED TABLES

The following tables were present in `backend/app/models/` but were missing from the original registry inventory. They are now explicitly protected and require the same change-control process as their assigned tier.

### TIER 2 — Audit, Idempotency & Event History

| Table | Model File | Reason |
|---|---|---|
| `authorization_audit` | `backend/app/models/authorization.py` | Append-only authorization decision history |
| `clinical_command_receipts` | `backend/app/models/clinical_command.py` | Append-only idempotency claims for safety-critical commands |
| `integration_inbox_events` | `backend/app/models/integration_inbox.py` | Durable inbound event/idempotency history |

### TIER 3 — Business Operations & Preferences

| Table | Model File | Reason |
|---|---|---|
| `role_groups` | `backend/app/models/authorization.py` | Group-based authorization structure |
| `role_group_members` | `backend/app/models/authorization.py` | Group membership assignments |
| `abac_policies` | `backend/app/models/authorization.py` | Attribute-based access policy definitions |
| `field_security` | `backend/app/models/authorization.py` | Field-level access policy definitions |
| `delegations` | `backend/app/models/authorization.py` | Time-bounded authorization delegation |
| `accessibility_profiles` | `backend/app/models/user_preferences.py` | User presentation preferences |
| `health_preferences` | `backend/app/models/user_preferences.py` | Sensitive, consent-bound health preferences |

### TIER 4 — Clinical Scope & Reference Data

| Table | Model File | Reason |
|---|---|---|
| `clinical_lab_facility_bindings` | `backend/app/models/clinical_scope.py` | Reviewed legacy-lab to facility scope bridge |
| `national_facilities` | `backend/app/models/clinical_scope.py` | Canonical national EHR facility resource |
| `clinical_ehr_facility_bindings` | `backend/app/models/clinical_scope.py` | Reviewed national facility to EHR scope bridge |

### TIER 5 — AI & Intelligence

| Table | Model File | Reason |
|---|---|---|
| `ai_knowledge_edges` | `backend/app/models/ai.py` | AI knowledge graph relationships |
| `ai_model_registry` | `backend/app/models/ai.py` | Registered AI model metadata and lifecycle |
| `ai_evaluations` | `backend/app/models/ai.py` | AI evaluation and safety evidence |

### TIER 6 — Edge & Device Integration

| Table | Model File | Reason |
|---|---|---|
| `edge_policies` | `backend/app/models/edge.py` | Per-tenant edge execution policy |
| `edge_events` | `backend/app/models/edge.py` | Edge lifecycle and security event history |

### TIER 7 — Security & Auth

| Table | Model File | Reason |
|---|---|---|
| `break_glass_sessions` | `backend/app/models/authorization.py` | Emergency-access sessions with clinical justification and review |

`break_glass_sessions` is not treated as a disposable session table: its justification, patient scope, expiry, deactivation, and review fields are security and clinical evidence. It therefore requires retention, revocation, and audit controls even if a future policy permits a separate archival lifecycle.

### Registry maintenance note

This section records inventory completeness only; it does not grant a soft-delete exception and does not authorize schema changes. Each table remains subject to Rule 10 classification and Architecture Board approval before structural modification.
