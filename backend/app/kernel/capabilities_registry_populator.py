from __future__ import annotations

import logging

from app.kernel.runtime.capability_registry import CapabilityRegistry
from app.kernel.types import (
    CapabilityAPI,
    CapabilityCommand,
    CapabilityDescriptor,
    CapabilityEvent,
    CapabilityQuery,
    CapabilityStatus,
)

logger = logging.getLogger("gula.kernel.capabilities.populator")


def populate_registry(registry: CapabilityRegistry) -> int:
    descriptors = _get_all_descriptors()
    return registry.register_batch(descriptors)


def _get_all_descriptors() -> list[CapabilityDescriptor]:
    return [
        # ===== Identity & Security =====
        CapabilityDescriptor(
            name="authentication",
            version="2.1.0",
            description="JWT-based authentication with access and refresh tokens, Redis-backed JTI blacklist, httpOnly cookies",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            permissions=[],
            api_endpoints=[
                CapabilityAPI(path="/login", method="POST", description="User login"),
                CapabilityAPI(path="/logout", method="POST", description="User logout"),
                CapabilityAPI(path="/register", method="POST", description="Lab registration"),
                CapabilityAPI(
                    path="/register/citizen", method="POST", description="Citizen registration"
                ),
            ],
            dependencies=["authorization_rbac", "audit_logging"],
            tags=["auth", "jwt", "security"],
        ),
        CapabilityDescriptor(
            name="authorization_rbac",
            version="2.1.0",
            description="Role-based access control with 9 roles, 13+ permissions, permission versioning for JWT invalidation",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            permissions=[],
            dependencies=["authentication"],
            tags=["rbac", "security"],
        ),
        CapabilityDescriptor(
            name="consent_management",
            version="2.1.0",
            description="Granular data access consent with ULID-based subjects, scopes, expiry, and break-glass emergency override",
            owner="platform-team",
            domain="identity_security",
            layer="application",
            permissions=[],
            dependencies=["authentication", "audit_logging"],
            tags=["consent", "privacy"],
        ),
        CapabilityDescriptor(
            name="session_management",
            version="2.1.0",
            description="Redis-backed session management with permission version bump for instant JWT invalidation",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            dependencies=["authentication", "redis_cache"],
            tags=["session", "security"],
        ),
        CapabilityDescriptor(
            name="rate_limiting",
            version="2.1.0",
            description="Fixed-window rate limiter with Redis + in-memory fallback, dynamic IP blocking on abuse, per-endpoint tiers",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            dependencies=["redis_cache"],
            tags=["rate-limit", "security"],
        ),
        CapabilityDescriptor(
            name="intrusion_detection",
            version="2.1.0",
            description="In-memory time-windowed IP attack detection with automatic cleanup and Redis-backed cross-worker sharing",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            dependencies=["redis_cache"],
            tags=["ids", "security"],
        ),
        CapabilityDescriptor(
            name="encryption_service",
            version="2.1.0",
            description="Fernet-based encryption for sensitive data at rest (national IDs, PII) with key rotation support",
            owner="platform-team",
            domain="identity_security",
            layer="infrastructure",
            tags=["encryption", "security"],
        ),
        # ===== Clinical =====
        CapabilityDescriptor(
            name="patient_management",
            version="2.1.0",
            description="Full patient CRUD with tenant isolation, phone/name search, family relationships, duplicate detection",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["authentication", "authorization_rbac", "audit_logging"],
            tags=["patient", "clinical"],
        ),
        CapabilityDescriptor(
            name="order_management",
            version="2.1.0",
            description="Lab order lifecycle with state machine, optimistic locking, tenant isolation, patient history",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["patient_management", "authentication", "audit_logging"],
            tags=["order", "laboratory"],
        ),
        CapabilityDescriptor(
            name="result_management",
            version="2.1.0",
            description="Lab result CRUD with per-test results, normal ranges, flags, anonymous access, PDF generation",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["order_management", "patient_management", "authentication"],
            tags=["result", "laboratory"],
        ),
        CapabilityDescriptor(
            name="sample_tracking",
            version="2.1.0",
            description="Specimen tracking with barcode, type, collection info, status workflow, rejection tracking, storage location",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["order_management", "authentication", "audit_logging"],
            tags=["sample", "laboratory"],
        ),
        CapabilityDescriptor(
            name="clinical_intelligence",
            version="2.1.0",
            description="Multi-test pattern detection (sepsis, DKA, renal failure), flag summarization, clinical evaluation engine",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["result_management"],
            tags=["clinical", "ai"],
        ),
        CapabilityDescriptor(
            name="critical_alerting",
            version="2.1.0",
            description="Critical result alerts management, alert statistics, notification dispatch for critical values",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["result_management", "notification_service"],
            tags=["alert", "patient-safety"],
        ),
        CapabilityDescriptor(
            name="quality_control",
            version="2.1.0",
            description="QC tracking with Westgard rule violations, Levey-Jennings data, instrument and lot number tracking",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["authentication", "audit_logging"],
            tags=["qc", "laboratory"],
        ),
        CapabilityDescriptor(
            name="device_integration",
            version="2.1.0",
            description="ASTM/HL7 lab instrument integration via LabLink-Core, supports Sysmex, Roche, Mindray, generic devices",
            owner="platform-team",
            domain="clinical",
            layer="infrastructure",
            dependencies=["result_management"],
            tags=["device", "hl7", "astm"],
        ),
        CapabilityDescriptor(
            name="ehr_integration",
            version="2.1.0",
            description="Complete EHR with trend data, patient summary with latest value per test type, citizen-accessible health records",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["patient_management", "result_management"],
            tags=["ehr", "clinical"],
        ),
        CapabilityDescriptor(
            name="patient_card",
            version="2.1.0",
            description="Digital QR-backed patient cards with HMAC-signed tokens, Arabic-first printable HTML format",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["patient_management", "authentication"],
            tags=["patient", "qr"],
        ),
        CapabilityDescriptor(
            name="master_patient_index",
            version="2.1.0",
            description="Canonical citizen identity with probabilistic patient matching, blocking-key generation, identity resolution",
            owner="platform-team",
            domain="clinical",
            layer="application",
            dependencies=["patient_management"],
            tags=["mpi", "identity"],
        ),
        # ===== Communication =====
        CapabilityDescriptor(
            name="notification_service",
            version="2.1.0",
            description="Multi-channel notification service with email, SMS, WhatsApp, push, Telegram; circuit breaker, template rendering",
            owner="platform-team",
            domain="communication",
            layer="application",
            dependencies=["authentication"],
            tags=["notification", "communication"],
        ),
        # ===== Infrastructure =====
        CapabilityDescriptor(
            name="audit_logging",
            version="2.1.0",
            description="Immutable hash-chained audit trail with SHA-256 chain, HMAC-anchored file system checkpoints, chain verification",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            tags=["audit", "compliance"],
        ),
        CapabilityDescriptor(
            name="outbox_pattern",
            version="2.1.0",
            description="Transactional outbox for guaranteed event delivery, preventing dual-write problems",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            dependencies=["event_bus"],
            tags=["outbox", "messaging"],
        ),
        CapabilityDescriptor(
            name="event_bus",
            version="2.1.0",
            description="Internal pub/sub event bus with outbox, inbox, dead letter queue, replay, versioning",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            tags=["events", "messaging"],
        ),
        CapabilityDescriptor(
            name="background_processing",
            version="2.1.0",
            description="Distributed background processing with task queue, worker pool, scheduler, cron, distributed locks",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            dependencies=["event_bus"],
            tags=["background", "scheduler"],
        ),
        CapabilityDescriptor(
            name="feature_flags",
            version="2.1.0",
            description="Per-tenant feature flag matrix with 30+ features across Starter, Growth, Enterprise tiers",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            tags=["feature-flags", "tenancy"],
        ),
        CapabilityDescriptor(
            name="redis_cache",
            version="2.1.0",
            description="Redis client singleton with in-memory fallback for caching, rate limiting, session storage",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            tags=["cache", "redis"],
        ),
        # ===== Reporting =====
        CapabilityDescriptor(
            name="pdf_reporting",
            version="2.1.0",
            description="Bilingual (Arabic/English) PDF lab result generation with QR codes, Unicode Arabic text support",
            owner="platform-team",
            domain="reporting",
            layer="application",
            dependencies=["result_management"],
            tags=["pdf", "reporting"],
        ),
        CapabilityDescriptor(
            name="analytics",
            version="2.1.0",
            description="Dashboards and statistics with Redis-cached aggregation queries: daily trends, turnaround times, summary metrics",
            owner="platform-team",
            domain="reporting",
            layer="application",
            dependencies=["result_management"],
            tags=["analytics", "dashboard"],
        ),
        # ===== Platform =====
        CapabilityDescriptor(
            name="multi_tenant",
            version="2.1.0",
            description="Multi-tenant engine with tenant registry, isolation, quotas, per-tenant configuration and feature flags",
            owner="platform-team",
            domain="platform",
            layer="infrastructure",
            tags=["multi-tenant"],
        ),
        CapabilityDescriptor(
            name="lab_management",
            version="2.1.0",
            description="Laboratory entity management with license tracking, type, director, hierarchy support",
            owner="platform-team",
            domain="platform",
            layer="application",
            dependencies=["authentication", "authorization_rbac"],
            tags=["lab", "management"],
        ),
        CapabilityDescriptor(
            name="admin_console",
            version="2.1.0",
            description="Master admin endpoints: lab/user management, kill switch, platform stats, audit log viewing",
            owner="platform-team",
            domain="platform",
            layer="presentation",
            dependencies=["authentication", "authorization_rbac", "audit_logging"],
            tags=["admin"],
        ),
        CapabilityDescriptor(
            name="edge_platform",
            version="2.1.0",
            description="Offline-capable edge computing for remote lab sites with device/capability models",
            owner="platform-team",
            domain="platform",
            layer="infrastructure",
            dependencies=["patient_management", "order_management"],
            tags=["edge", "offline"],
        ),
        CapabilityDescriptor(
            name="id_scanning",
            version="2.1.0",
            description="Iraqi National ID card OCR scanning with OpenCV + Tesseract text extraction",
            owner="platform-team",
            domain="platform",
            layer="application",
            dependencies=["patient_management"],
            tags=["id", "ocr"],
        ),
        CapabilityDescriptor(
            name="national_identity",
            version="2.1.0",
            description="National identity lookup and verification, encrypted national ID storage with hashed lookup",
            owner="platform-team",
            domain="platform",
            layer="application",
            dependencies=["patient_management", "encryption_service"],
            tags=["national-id"],
        ),
        # ===== Financial =====
        CapabilityDescriptor(
            name="claims_processing",
            version="1.0.0",
            description="Insurance billing with claim status workflow: draft -> validated -> submitted -> accepted/rejected -> paid",
            owner="platform-team",
            domain="financial",
            layer="application",
            dependencies=["patient_management", "order_management"],
            tags=["insurance", "billing"],
        ),
        CapabilityDescriptor(
            name="subscription_tiers",
            version="1.0.0",
            description="SaaS subscription tier management with feature flag matrices, upgrade scoring, per-lab subscription plans",
            owner="platform-team",
            domain="financial",
            layer="application",
            dependencies=["feature_flags"],
            tags=["subscription", "billing"],
        ),
        # ===== Observability =====
        CapabilityDescriptor(
            name="health_checks",
            version="2.1.0",
            description="Multi-level health endpoints (live, ready, status, deep) with component latencies, memory, grade scoring",
            owner="platform-team",
            domain="observability",
            layer="infrastructure",
            tags=["health", "monitoring"],
        ),
        CapabilityDescriptor(
            name="metrics_collection",
            version="2.1.0",
            description="Prometheus-compatible metrics with bearer token auth, JSON dashboard metrics, custom metric collectors",
            owner="platform-team",
            domain="observability",
            layer="infrastructure",
            dependencies=["redis_cache"],
            tags=["metrics", "prometheus"],
        ),
        CapabilityDescriptor(
            name="self_healing",
            version="2.1.0",
            description="Three-layer self-healing: circuit breaker (DB/Redis), auto-repair engine (GC, pool recycle), adaptive concurrency",
            owner="platform-team",
            domain="observability",
            layer="infrastructure",
            dependencies=["health_checks"],
            tags=["self-healing", "resilience"],
        ),
        CapabilityDescriptor(
            name="prometheus_integration",
            version="1.0.0",
            description="Prometheus server with scrape config, alerting rules, Grafana dashboards",
            owner="platform-team",
            domain="observability",
            layer="infrastructure",
            dependencies=["metrics_collection"],
            tags=["prometheus", "grafana"],
        ),
        # ===== Integration =====
        CapabilityDescriptor(
            name="compliance",
            version="1.0.0",
            description="Government compliance reporting, FHIR-compatible patient resources, system audit data for regulatory submission",
            owner="platform-team",
            domain="integration",
            layer="application",
            dependencies=["audit_logging", "patient_management"],
            tags=["compliance", "regulatory"],
        ),
        CapabilityDescriptor(
            name="insurance_integration",
            version="1.0.0",
            description="Third-party insurance provider integration for claims submission and status tracking",
            owner="platform-team",
            domain="integration",
            layer="application",
            dependencies=["claims_processing"],
            tags=["insurance"],
        ),
        CapabilityDescriptor(
            name="sndhs_integration",
            version="1.0.0",
            description="Iraqi National Health Data System (SNDHS) integration with visit tracking, national ID, enhanced audit",
            owner="platform-team",
            domain="integration",
            layer="application",
            dependencies=["patient_management", "audit_logging"],
            tags=["sndhs", "government"],
        ),
        # ===== New M006 Capabilities (Foundation) =====
        CapabilityDescriptor(
            name="document_management",
            version="1.0.0",
            description="Document management platform: attachments, PDF, OCR, image processing, preview, digital signature, metadata, storage abstraction, versioning, document search",
            owner="platform-team",
            domain="infrastructure",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(name="DocumentUploaded", description="A document was uploaded"),
                CapabilityEvent(name="DocumentDeleted", description="A document was deleted"),
                CapabilityEvent(
                    name="DocumentSigned", description="A document was digitally signed"
                ),
            ],
            commands=[
                CapabilityCommand(
                    name="upload_document", description="Upload a document to storage"
                ),
                CapabilityCommand(name="delete_document", description="Delete a document"),
            ],
            queries=[
                CapabilityQuery(name="search_documents", description="Search across documents"),
                CapabilityQuery(
                    name="get_document", description="Get document metadata and content"
                ),
            ],
            dependencies=["storage_service", "authentication", "audit_logging"],
            tags=["document", "storage"],
        ),
        CapabilityDescriptor(
            name="workflow_engine",
            version="1.0.0",
            description="Generic workflow engine: approvals, states, transitions, business rules, timers, escalations, notifications, audit",
            owner="platform-team",
            domain="infrastructure",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(
                    name="WorkflowCreated", description="A workflow instance was created"
                ),
                CapabilityEvent(
                    name="WorkflowCompleted", description="A workflow reached terminal state"
                ),
                CapabilityEvent(name="WorkflowEscalated", description="A workflow was escalated"),
            ],
            commands=[
                CapabilityCommand(
                    name="create_workflow", description="Create a new workflow instance"
                ),
                CapabilityCommand(
                    name="transition", description="Transition workflow to next state"
                ),
            ],
            queries=[
                CapabilityQuery(name="get_workflow", description="Get workflow state and history"),
                CapabilityQuery(
                    name="get_pending_tasks", description="List pending tasks for user"
                ),
            ],
            dependencies=["notification_service", "audit_logging"],
            tags=["workflow", "bpm"],
        ),
        CapabilityDescriptor(
            name="reporting_service",
            version="1.0.0",
            description="Enterprise reporting: dashboards, charts, PDF, Excel, CSV export, scheduling, distribution",
            owner="platform-team",
            domain="reporting",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            commands=[
                CapabilityCommand(name="generate_report", description="Generate a report"),
                CapabilityCommand(
                    name="schedule_report", description="Schedule recurring report generation"
                ),
            ],
            queries=[
                CapabilityQuery(name="list_reports", description="List available reports"),
                CapabilityQuery(name="get_report_data", description="Get report data"),
            ],
            dependencies=["analytics", "pdf_reporting"],
            tags=["reporting", "bi"],
        ),
        CapabilityDescriptor(
            name="search_service",
            version="1.0.0",
            description="Unified search platform: full-text search, filters, ranking, suggestions, indexing, permissions-aware",
            owner="platform-team",
            domain="infrastructure",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            commands=[
                CapabilityCommand(name="index_document", description="Index a document for search"),
                CapabilityCommand(name="reindex", description="Rebuild search index"),
            ],
            queries=[
                CapabilityQuery(name="search", description="Execute full-text search"),
                CapabilityQuery(name="suggest", description="Get search suggestions"),
            ],
            dependencies=["authentication"],
            tags=["search", "elasticsearch"],
        ),
        CapabilityDescriptor(
            name="storage_service",
            version="1.0.0",
            description="Unified storage layer: local storage, S3 compatible, MinIO, Azure Blob, Google Storage, versioning, encryption",
            owner="platform-team",
            domain="infrastructure",
            layer="infrastructure",
            status=CapabilityStatus.ACTIVE,
            commands=[
                CapabilityCommand(
                    name="store_file", description="Store a file in the storage backend"
                ),
                CapabilityCommand(name="retrieve_file", description="Retrieve a file by key"),
            ],
            dependencies=["encryption_service"],
            tags=["storage", "s3"],
        ),
        # ===== M007 Healthcare Domain Capabilities =====
        CapabilityDescriptor(
            name="provider_management",
            version="1.0.0",
            description="Healthcare provider management: doctors, nurses, technicians, licensing, specialties, schedules, availability",
            owner="platform-team",
            domain="clinical",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(
                    name="ProviderRegistered", description="A new provider was registered"
                ),
                CapabilityEvent(name="LicenseUpdated", description="Provider license was updated"),
            ],
            commands=[
                CapabilityCommand(
                    name="register_provider", description="Register a new healthcare provider"
                ),
                CapabilityCommand(name="update_license", description="Update provider license"),
            ],
            queries=[
                CapabilityQuery(name="search_providers", description="Search healthcare providers"),
                CapabilityQuery(
                    name="list_by_specialty", description="List providers by specialty"
                ),
            ],
            dependencies=["authentication", "authorization_rbac"],
            tags=["provider", "workforce"],
        ),
        CapabilityDescriptor(
            name="encounter_management",
            version="1.0.0",
            description="Clinical encounter management: outpatient, emergency, inpatient, home visit, telemedicine, referral, admission/discharge/transfer",
            owner="platform-team",
            domain="clinical",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(
                    name="EncounterCreated", description="A new clinical encounter was created"
                ),
                CapabilityEvent(name="PatientAdmitted", description="Patient admitted to facility"),
                CapabilityEvent(
                    name="PatientDischarged", description="Patient discharged from facility"
                ),
            ],
            commands=[
                CapabilityCommand(
                    name="create_encounter", description="Create a new clinical encounter"
                ),
                CapabilityCommand(name="admit", description="Admit a patient"),
                CapabilityCommand(name="discharge", description="Discharge a patient"),
            ],
            queries=[
                CapabilityQuery(name="get_encounter", description="Get encounter details"),
                CapabilityQuery(
                    name="get_patient_timeline", description="Get patient encounter timeline"
                ),
            ],
            dependencies=["patient_management", "provider_management"],
            tags=["encounter", "clinical"],
        ),
        CapabilityDescriptor(
            name="clinical_foundation",
            version="1.0.0",
            description="Clinical data foundation: diagnoses, problems, allergies, medications, procedures, observations, vitals, immunizations",
            owner="platform-team",
            domain="clinical",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(name="DiagnosisAdded", description="A diagnosis was added"),
                CapabilityEvent(
                    name="MedicationPrescribed", description="A medication was prescribed"
                ),
                CapabilityEvent(name="AllergyRecorded", description="An allergy was recorded"),
            ],
            commands=[
                CapabilityCommand(name="add_diagnosis", description="Add a diagnosis"),
                CapabilityCommand(name="add_medication", description="Prescribe a medication"),
                CapabilityCommand(name="record_vitals", description="Record vital signs"),
            ],
            queries=[
                CapabilityQuery(
                    name="get_clinical_history", description="Get full clinical history"
                ),
                CapabilityQuery(name="get_active_problems", description="Get active problem list"),
            ],
            dependencies=["patient_management", "encounter_management"],
            tags=["clinical", "foundation"],
        ),
        CapabilityDescriptor(
            name="fhir_interoperability",
            version="1.0.0",
            description="FHIR/HL7 interoperability: FHIR R4 resources, HL7 v2 messages, LOINC coding, SNOMED CT, ICD-10, ICD-11 ready, UCUM units, IHE profiles",
            owner="platform-team",
            domain="integration",
            layer="infrastructure",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(
                    name="FhirResourceCreated", description="A FHIR resource was created"
                ),
                CapabilityEvent(
                    name="Hl7MessageReceived", description="An HL7 message was received"
                ),
            ],
            commands=[
                CapabilityCommand(
                    name="convert_to_fhir", description="Convert internal data to FHIR resource"
                ),
                CapabilityCommand(name="validate_resource", description="Validate a FHIR resource"),
            ],
            queries=[
                CapabilityQuery(name="search_fhir", description="Search FHIR resources"),
                CapabilityQuery(name="lookup_code", description="Look up a terminology code"),
            ],
            dependencies=["patient_management", "clinical_foundation"],
            tags=["fhir", "hl7", "interoperability"],
        ),
        CapabilityDescriptor(
            name="healthcare_consent",
            version="1.0.0",
            description="Healthcare-specific consent: patient privacy preferences, access policies, break-glass emergency override, purpose of use enforcement",
            owner="platform-team",
            domain="identity_security",
            layer="application",
            status=CapabilityStatus.ACTIVE,
            events=[
                CapabilityEvent(name="ConsentGranted", description="Patient consent was granted"),
                CapabilityEvent(name="ConsentRevoked", description="Patient consent was revoked"),
                CapabilityEvent(
                    name="BreakGlassActivated",
                    description="Break-glass emergency override activated",
                ),
            ],
            commands=[
                CapabilityCommand(name="grant_consent", description="Grant patient consent"),
                CapabilityCommand(name="revoke_consent", description="Revoke patient consent"),
                CapabilityCommand(name="break_glass", description="Activate break-glass override"),
            ],
            queries=[
                CapabilityQuery(name="check_consent", description="Check if consent is active"),
                CapabilityQuery(
                    name="get_active_consents", description="List active consents for patient"
                ),
            ],
            dependencies=["consent_management", "patient_management"],
            tags=["consent", "privacy"],
        ),
    ]
