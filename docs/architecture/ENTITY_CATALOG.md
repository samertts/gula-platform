# GULA Unified Entity Catalog

## Core Domain Entities

| Entity | Table | Module | Source |
|--------|-------|--------|--------|
| `Lab` | `labs` | `models/lab.py` | Platform-Core |
| `LabUser` | `lab_users` | `models/lab_user.py` | Platform-Core |
| `User` | `users` | `models/user.py` | Platform-Core |
| `Patient` | `patients` | `models/patient.py` | Platform-Core |
| `LabOrder` | `lab_orders` | `models/lab_order.py` | Platform-Core |
| `LabResult` | `lab_results` | `models/lab_result.py` | Platform-Core |
| `Sample` | `samples` | `models/sample.py` | Platform-Core |
| `TestType` | `test_types` | `models/test_type.py` | Platform-Core |
| `AuditLog` | `audit_logs` | `models/audit_log.py` | Platform-Core |
| `OutboxEvent` | `outbox_events` | `models/outbox.py` | Platform-Core |
| `QualityControl` | `quality_controls` | `models/quality_control.py` | Platform-Core |
| `Claim` | `claims` | `models/claim.py` | Platform-Core |
| `Consent` | `consents` | `models/consent.py` | Platform-Core |
| `TestResult` | `test_results` | `models/test_result.py` | Platform-Core |
| `Subscription` | `lab_subscriptions` | `models/subscription.py` | Platform-Core |

## Audit Trail Entities

| Entity | Table | Key Fields |
|--------|-------|------------|
| `AuditLog` | `audit_logs` | `action`, `entity_type`, `entity_id`, `user_id`, `lab_id`, `previous_hash`, `chain_hash`, `timestamp` |
| `OutboxEvent` | `outbox_events` | `event_type`, `payload`, `status`, `retry_count`, `created_at` |

## Support Entities

| Entity | Table | Module | Source |
|--------|-------|--------|--------|
| `AIInteraction` | `ai_interactions` | `models/ai_interaction.py` | Platform-Core |
| `EdgeDevice` | `edge_devices` | `models/edge.py` | Platform-Core |
| `EdgeTask` | `edge_tasks` | `models/edge.py` | Platform-Core |
| `EdgeTelemetry` | `edge_telemetry` | `models/edge.py` | Platform-Core |
| `UpgradeRequest` | `upgrade_requests` | `models/subscription.py` | Platform-Core |
| `FeatureFlag` | `feature_flags` | `models/subscription.py` | Platform-Core |
| `SkillConfig` | `skill_configs` | `skills/models.py` | Platform-Core |
| `SkillAuditLog` | `skill_audit_logs` | `skills/models.py` | Platform-Core |
| `OptimizerConfig` | `optimizer_configs` | `optimizer/models.py` | Platform-Core |

## NHOP Entities

| Entity | Table | Module |
|--------|-------|--------|
| `Citizen` | `citizens` | `nhop-platform/app/models/citizen.py` |
| `DiseaseCase` | `disease_cases` | `nhop-platform/app/models/disease_case.py` |
| `Notification` | `notifications` | `nhop-platform/app/models/notification.py` |
| `AntibioticSensitivity` | `antibiotic_sensitivities` | `nhop-platform/app/models/antibiotic_sensitivity.py` |
| `NHOPAuditLog` | `audit_logs` | `nhop-platform/app/models/audit_log.py` |

## Domain Engine Entities

| Entity | Table | Module |
|--------|-------|--------|
| `Policy` | `policies` | `policies/models.py` |
| `PolicyVersion` | `policy_versions` | `policies/models.py` |
| `PolicyEvaluation` | `policy_evaluations` | `policies/models.py` |
| `Rule` | `rules` | `rules/models.py` |
| `RuleVersion` | `rule_versions` | `rules/models.py` |
| `RuleEvaluation` | `rule_evaluations` | `rules/models.py` |
| `Workflow` | `workflows` | `workflows/models.py` |
| `WorkflowInstance` | `workflow_instances` | `workflows/models.py` |
| `WorkflowStep` | `workflow_steps` | `workflows/models.py` |
| `WorkflowVersion` | `workflow_versions` | `workflows/models.py` |
| `WorkflowTemplate` | `workflow_templates` | `workflows/templates.py` |
| `ApprovalChain` | `approval_chains` | `approvals/models.py` |
| `ApprovalRequest` | `approval_requests` | `approvals/models.py` |
| `ApprovalAction` | `approval_actions` | `approvals/models.py` |
| `Constraint` | `constraints` | `constraints/models.py` |
| `FormDefinition` | `form_definitions` | `forms/models.py` |
| `FormSubmission` | `form_submissions` | `forms/models.py` |

## Migration Status

| Entity | Migration File | Status |
|--------|---------------|--------|
| All Base Schema | `20250322_0000_create_base_schema.py` | ✅ Immutable |
| SNDHS Phase 1 | `20260505_0001` through `0006` | ✅ Applied |
| Financial Engine | `20260505_0001_financial_engine_phase_a.py` | ✅ Applied |
