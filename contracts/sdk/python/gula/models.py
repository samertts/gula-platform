from __future__ import annotations

from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class PageMetadata(BaseModel):
    total: int
    page: int = Field(default=1)
    limit: int = Field(default=50)
    total_pages: int = Field(default=0)

    model_config = ConfigDict(from_attributes=True)


# ── Auth Domain ────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=100)
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class LabRegisterRequest(BaseModel):
    lab_name: str = Field(..., min_length=2, max_length=200)
    license_number: str | None = None
    lab_type: str | None = Field(None, pattern=r"^(private|government|hospital|clinic)$")
    director_name: str | None = Field(None, min_length=2, max_length=200)
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    website: str | None = None
    admin_name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class CitizenRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    email: str | None = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    gender: str | None = None
    birth_date: str | None = None
    national_id: str | None = Field(None, pattern=r"^[0-9]{10,14}$")


class StaffRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str | None = Field(None, pattern=r"^(technician|doctor|receptionist|staff)$")


class DoctorRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: str
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    password: str = Field(..., min_length=8, max_length=128)
    license_number: str = Field(..., min_length=3, max_length=100)
    specialty: str | None = None
    workplace: str | None = None
    national_id: str | None = Field(None, pattern=r"^[0-9]{10,14}$")


class DeviceTokenRequest(BaseModel):
    device_token: str = Field(..., min_length=10, max_length=512)
    platform: str = Field(..., pattern=r"^(android|ios)$")
    app_version: str | None = None


class CitizenLoginRequest(BaseModel):
    identifier: str
    email: str | None = None
    password: str


class NationalIdRequest(BaseModel):
    national_id: str = Field(..., min_length=5, max_length=20)


class CreateLabRequest(BaseModel):
    name: str = Field(..., min_length=2)
    city: str | None = None
    phone: str | None = None
    admin_email: str
    admin_password: str = Field(..., min_length=8)
    admin_name: str
    province_id: int | None = None


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=8)
    role: str
    lab_id: int | None = None
    province_id: int | None = None
    national_id: str | None = None


class ChangeRoleRequest(BaseModel):
    role: str
    province_id: int | None = None


class KillSwitchRequest(BaseModel):
    reason: str | None = None


class LinkIdentityRequest(BaseModel):
    patient_id: int
    national_id: str
    confirm_name: str | None = None


# ── Patients Domain ────────────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r"^(07\d{9}|9647\d{9})$")
    birth_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    gender: str | None = Field(None, pattern=r"^(male|female|M|F)$")
    email: str | None = Field(None, max_length=100)
    national_id: str | None = Field(None, pattern=r"^\d{12,13}$")
    family_id: str | None = Field(None, pattern=r"^\d{1,15}$")
    force_create: bool | None = None
    guardian_id: int | None = None


class PatientUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=200)
    phone: str | None = None
    birth_date: str | None = None
    gender: str | None = None
    email: str | None = None
    family_id: str | None = Field(None, pattern=r"^\d{1,15}$")


class ScanRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


# ── Labs Domain ────────────────────────────────────────────────────────────────


class LabUpdate(BaseModel):
    name: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    license_number: str | None = None
    lab_type: str | None = Field(None, pattern=r"^(private|government|hospital|clinic)$")
    director_name: str | None = None
    website: str | None = None


class CreateEmployeeRequest(BaseModel):
    name: str
    email: str
    password: str = Field(..., min_length=8)
    role: str | None = Field(None, pattern=r"^(admin|staff|technician)$")


class UpdateEmployeeRequest(BaseModel):
    is_active: bool | None = None
    role: str | None = Field(None, pattern=r"^(admin|staff|technician)$")


# ── Orders & Results Domain ────────────────────────────────────────────────────


class ResultItem(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class CreateOrderRequest(BaseModel):
    patient_id: int = Field(..., ge=1)
    doctor_name: str | None = Field(None, max_length=200)
    doctor_user_id: int | None = None
    results: list[ResultItem]


class AnalyzeRequest(BaseModel):
    results: list[ResultItem]


class BatchResultItem(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class BatchOrderItem(BaseModel):
    patient_id: int
    doctor_name: str | None = None
    results: list[BatchResultItem]


class BatchOrderRequest(BaseModel):
    orders: list[BatchOrderItem]


class TestResultCreate(BaseModel):
    health_id: str = Field(..., min_length=3, max_length=20)
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: str | None = Field(None, max_length=50)
    value: float | None = None
    value_text: str | None = Field(None, max_length=200)
    unit: str | None = Field(None, max_length=20)
    normal_range_low: float | None = None
    normal_range_high: float | None = None
    sample_type: str | None = Field(None, max_length=50)
    doctor_name: str | None = Field(None, max_length=200)
    order_id: int | None = None


class TestResultRead(BaseModel):
    id: int
    citizen_id: int
    lab_id: int
    device_id: int | None = None
    test_code: str
    test_name_en: str
    test_name_ar: str
    category: str | None = None
    result_value: float | None = None
    result_text: str | None = None
    unit: str | None = None
    reference_min: float | None = None
    reference_max: float | None = None
    status: str
    is_critical: bool
    is_abnormal: bool
    abnormality_direction: str | None = None
    sample_collected_at: str
    result_completed_at: str | None = None
    verified_at: str | None = None
    verified_by: str | None = None
    sample_barcode: str
    ordering_physician: str | None = None
    clinical_notes: str | None = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class TestResultBrief(BaseModel):
    id: int
    test_code: str
    test_name_en: str
    test_name_ar: str
    result_value: float | None = None
    result_text: str | None = None
    unit: str | None = None
    status: str
    is_abnormal: bool
    is_critical: bool
    sample_collected_at: str

    model_config = ConfigDict(from_attributes=True)


class TestResultForCitizen(BaseModel):
    id: int
    test_name_ar: str
    result_value: float | None = None
    result_text: str | None = None
    unit: str | None = None
    reference_min: float | None = None
    reference_max: float | None = None
    status: str
    is_abnormal: bool
    is_critical: bool
    abnormality_direction: str | None = None
    sample_collected_at: str
    result_completed_at: str | None = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TestResultValidateRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: str | None = Field(None, max_length=50)
    value: float | None = None
    unit: str | None = Field(None, max_length=20)
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class DeviceResult(BaseModel):
    test_name: str
    value: float | None = None
    value_text: str | None = None
    unit: str | None = None
    normal_range_low: float | None = None
    normal_range_high: float | None = None


class DeviceSubmission(BaseModel):
    barcode: str
    device_id: str | None = None
    results: list[DeviceResult]


class SuggestRequest(BaseModel):
    operation: str
    payload: dict | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    rationale: str | None = None


class RejectRequest(BaseModel):
    reason: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: str | None = Field(None, max_length=500)


# ── Samples Domain ─────────────────────────────────────────────────────────────


class SampleCreate(BaseModel):
    order_id: int
    sample_type: str
    collected_by: str | None = None
    notes: str | None = None
    storage_location: str | None = None


class SampleUpdate(BaseModel):
    status: str | None = None
    rejection_reason: str | None = None
    notes: str | None = None
    storage_location: str | None = None


# ── Consent Domain ─────────────────────────────────────────────────────────────


class GrantRequest(BaseModel):
    gpid: str = Field(..., min_length=26, max_length=26)
    grantee_id: str = Field(..., min_length=3, max_length=64)
    scope: str = Field(..., min_length=3, max_length=64)
    expires_in_hours: int = Field(..., ge=1)


class GrantResponse(BaseModel):
    consent_id: str
    gpid: str
    grantee_id: str
    scope: str
    expires_at: str

    model_config = ConfigDict(from_attributes=True)


class RevokeRequest(BaseModel):
    gpid: str = Field(..., min_length=26, max_length=26)
    grantee_id: str = Field(..., min_length=3, max_length=64)
    scope: str = Field(..., min_length=3, max_length=64)


class RevokeResponse(BaseModel):
    revoked: bool

    model_config = ConfigDict(from_attributes=True)


class CheckResponse(BaseModel):
    allowed: bool
    scope: str
    expires_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Claims Domain ──────────────────────────────────────────────────────────────


class ClaimItemCreate(BaseModel):
    test_code: str
    description: str | None = None
    quantity: int | None = Field(default=1, ge=1)
    unit_price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)


class ClaimCreate(BaseModel):
    patient_id: int
    order_id: int | None = None
    items: list[ClaimItemCreate]
    idempotency_key: str | None = None


class ClaimItemResponse(BaseModel):
    id: int
    claim_id: int
    test_code: str
    description: str | None = None
    quantity: int
    unit_price: float
    amount: float

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: int
    lab_id: int
    patient_id: int
    order_id: int | None = None
    status: str
    total_amount: float | None = None
    currency: str
    idempotency_key: str | None = None
    external_ref: str | None = None
    submitted_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    items: list[ClaimItemResponse]

    model_config = ConfigDict(from_attributes=True)


# ── Edge Domain ────────────────────────────────────────────────────────────────


class RegisterDeviceRequest(BaseModel):
    public_key_pem: str = Field(..., min_length=80, max_length=8000)
    role_mode: str | None = Field(None, pattern=r"^(personal|clinic|enterprise)$")
    display_name: str | None = Field(None, max_length=200)
    agent_version: str | None = Field(None, max_length=32)
    os_platform: str | None = Field(None, max_length=64)
    capabilities: dict | None = None
    attestation_blob: str | None = Field(None, max_length=8000)


class RegisterDeviceResponse(BaseModel):
    device_id: str
    status: str
    role_mode: str
    trust_score: float
    cert_fingerprint: str
    agent_token: str
    nonce: str

    model_config = ConfigDict(from_attributes=True)


class DeviceSummary(BaseModel):
    device_id: str
    display_name: str | None = None
    role_mode: str
    status: str
    trust_score: float
    last_seen_at: str | None = None
    agent_version: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DeviceDetail(BaseModel):
    device_id: str
    display_name: str | None = None
    role_mode: str
    status: str
    trust_score: float
    last_seen_at: str | None = None
    agent_version: str | None = None
    capabilities: dict | None = None
    registered_at: str
    revoked_at: str | None = None
    quarantined_at: str | None = None
    kill_switched: bool
    latest_telemetry: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskSubmitRequest(BaseModel):
    kind: str = Field(..., min_length=3, max_length=64)
    payload: dict | None = None
    priority: int | None = Field(None, ge=1, le=10)
    privacy_level: str | None = Field(None, pattern=r"^(standard|sensitive|phi)$")
    required_caps: list[str] | None = None
    min_trust: float | None = Field(None, ge=0.0, le=100.0)
    timeout_s: int | None = Field(None, ge=5, le=600)
    max_attempts: int | None = Field(None, ge=1, le=10)
    idempotency_key: str | None = Field(None, max_length=80)
    expires_in_s: int | None = Field(None, ge=10, le=86400)


class TaskSummary(BaseModel):
    task_uid: str
    kind: str
    status: str
    priority: int
    privacy_level: str
    device_id: str | None = None
    attempts: int
    created_at: str
    completed_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(BaseModel):
    task_uid: str
    kind: str
    status: str
    priority: int
    privacy_level: str
    device_id: str | None = None
    attempts: int
    created_at: str
    completed_at: str | None = None
    payload: dict | None = None
    result: dict | None = None
    error: str | None = None
    timeout_s: int
    max_attempts: int

    model_config = ConfigDict(from_attributes=True)


class PolicyView(BaseModel):
    max_concurrent_per_device: int
    max_devices_per_lab: int
    idle_only: bool
    battery_floor_pct: int
    cpu_cap_pct: int
    ram_cap_mb: int
    allow_kinds: list[str] | None = None
    deny_kinds: list[str] | None = None
    min_trust_score: float
    offline_queue_max: int
    kill_switch: bool

    model_config = ConfigDict(from_attributes=True)


class PolicyUpdate(BaseModel):
    max_concurrent_per_device: int | None = Field(None, ge=1, le=64)
    max_devices_per_lab: int | None = Field(None, ge=1, le=10000)
    idle_only: bool | None = None
    battery_floor_pct: int | None = Field(None, ge=0, le=100)
    cpu_cap_pct: int | None = Field(None, ge=10, le=100)
    ram_cap_mb: int | None = Field(None, ge=128, le=131072)
    allow_kinds: list[str] | None = None
    deny_kinds: list[str] | None = None
    min_trust_score: float | None = Field(None, ge=0.0, le=100.0)
    offline_queue_max: int | None = Field(None, ge=10, le=100000)
    kill_switch: bool | None = None


class HeartbeatRequest(BaseModel):
    agent_version: str | None = Field(None, max_length=32)
    capabilities: dict | None = None
    telemetry: dict | None = None
    completed_task_uids: list[str] | None = None


class HeartbeatResponse(BaseModel):
    server_time: str
    next_heartbeat_s: int
    task: dict | None = None
    models: list[dict] | None = None
    quarantined: bool | None = None
    kill_switched: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskResultRequest(BaseModel):
    success: bool
    result: dict | None = None
    error: str | None = Field(None, max_length=2000)
    duration_ms: int | None = Field(None, ge=0, le=600000)


class ModelRegisterRequest(BaseModel):
    name: str = Field(..., max_length=120)
    version: str = Field(..., max_length=40)
    runtime: str | None = Field(None, pattern=r"^(ollama|llamacpp|onnx|custom)$")
    format: str | None = Field(None, max_length=32)
    quantization: str | None = Field(None, max_length=32)
    size_mb: float | None = Field(None, ge=0)
    min_ram_mb: float | None = Field(None, ge=0)
    min_vram_mb: float | None = Field(None, ge=0)
    sha256: str | None = Field(None, max_length=80)
    source_url: str | None = Field(None, max_length=500)
    metadata: dict | None = None


class ModelStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(draft|canary|active|retired|blocked)$")
    rollout_pct: float | None = Field(None, ge=0.0, le=100.0)


class ModelAssignRequest(BaseModel):
    lab_id: int | None = None
    device_id: str | None = Field(None, max_length=64)


# ── MPI Domain ─────────────────────────────────────────────────────────────────


class ResolveRequest(BaseModel):
    lab_id: int = Field(..., ge=1)
    patient_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=2, max_length=200)
    phone: str | None = Field(None, max_length=30)
    birth_date: str | None = None
    gender: str | None = Field(None, pattern=r"^[MFmf]$")
    national_id: str | None = Field(None, max_length=30)
    family_id: str | None = Field(None, max_length=30)


class ResolveResponse(BaseModel):
    citizen_ulid: str
    match_method: str
    match_score: float | None = None
    created: bool
    features: dict | None = None

    model_config = ConfigDict(from_attributes=True)


class CitizenResponse(BaseModel):
    citizen_ulid: str
    nid_verified: bool
    birth_year: int | None = None
    gender: str | None = None
    status: str
    merged_into_ulid: str | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class MergeRequest(BaseModel):
    primary_ulid: str = Field(..., min_length=26, max_length=26)
    secondary_ulid: str = Field(..., min_length=26, max_length=26)
    reason: str = Field(..., min_length=10, max_length=500)


class MergeResponse(BaseModel):
    event_id: int
    primary_ulid: str
    secondary_ulid: str
    occurred_at: str
    entry_hash: str

    model_config = ConfigDict(from_attributes=True)


class PendingReviewItem(BaseModel):
    claim_id: int
    citizen_ulid: str
    lab_id: int
    local_patient_id: int
    match_score: float | None = None
    match_features: dict | None = None
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class PendingReviewPage(BaseModel):
    total: int
    items: list[PendingReviewItem]

    model_config = ConfigDict(from_attributes=True)


class ResolveDecision(BaseModel):
    decision: str = Field(..., pattern=r"^(confirm|reject)$")
    reason: str = Field(..., min_length=10, max_length=500)


# ── AI Telemetry Domain ────────────────────────────────────────────────────────


class RetrievalRefIn(BaseModel):
    source: str | None = Field(None, max_length=64)
    doc_id: str | None = Field(None, max_length=128)
    doc_title: str | None = Field(None, max_length=256)
    chunk_text: str | None = Field(None, max_length=4000)
    similarity: float | None = Field(None, ge=0.0, le=1.0)
    rank: int | None = Field(None, ge=0, le=10000)


class InteractionIn(BaseModel):
    anonymous_session_id: str = Field(..., min_length=1, max_length=128)
    language: str | None = Field(None, max_length=8)
    region: str | None = Field(None, max_length=64)
    intent: str | None = Field(None, max_length=64)
    prompt: str | None = Field(None, max_length=8000)
    prompt_redacted: bool | None = None
    response: str | None = Field(None, max_length=16000)
    response_model: str | None = Field(None, max_length=64)
    retrieval_strategy: str | None = Field(None, max_length=64)
    retrieval_refs: list[RetrievalRefIn] | None = None
    biomarkers: list[str] | None = None
    latency_ms: int | None = Field(None, ge=0, le=600000)
    status: str | None = Field(None, max_length=20)
    error_code: str | None = Field(None, max_length=64)
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    risk_level: str | None = Field(None, max_length=32)
    escalation_recommended: bool | None = None
    retrieval_used: bool | None = None
    source_quality: float | None = Field(None, ge=0.0, le=1.0)
    unsupported_claims: int | None = Field(None, ge=0, le=1000)
    fallback_generation: bool | None = None
    safety_flags: list[str] | None = None


class InteractionOut(BaseModel):
    id: str
    lab_id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FeedbackIn(BaseModel):
    interaction_id: str
    anonymous_session_id: str = Field(..., min_length=1, max_length=128)
    signal: str
    notes: str | None = Field(None, max_length=2000)


class UnresolvedIn(BaseModel):
    interaction_id: str | None = None
    anonymous_session_id: str | None = Field(None, max_length=128)
    question: str = Field(..., min_length=1, max_length=8000)
    language: str | None = Field(None, max_length=8)
    category: str | None = Field(None, max_length=64)


# ── Governance Domain ──────────────────────────────────────────────────────────


class NodeCreate(BaseModel):
    node_type: str
    code: str = Field(..., min_length=1, max_length=100)
    name_ar: str = Field(..., min_length=1, max_length=300)
    name_en: str | None = None
    parent_id: int | None = None
    governorate: str | None = None
    district: str | None = None
    metadata_json: dict | None = None


class DelegationCreate(BaseModel):
    delegator_node_id: int
    delegate_node_id: int
    scope: dict | None = None
    reason: str | None = None


class ActingAppoint(BaseModel):
    node_id: int
    acting_node_id: int
    reason: str | None = None


class WorkerCreate(BaseModel):
    employee_code: str
    full_name_ar: str
    profession: str
    full_name_en: str | None = None
    national_id_hash: str | None = None
    specialization: str | None = None
    organization_node_id: int | None = None
    department: str | None = None
    unit: str | None = None
    employment_date: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class LabRegister(BaseModel):
    lab_code: str
    name_ar: str
    lab_type: str
    name_en: str | None = None
    organization_node_id: int | None = None
    license_number: str | None = None
    governorate: str | None = None


# ── LIMS Domain ────────────────────────────────────────────────────────────────


class SpecimenRegisterRequest(BaseModel):
    order_id: int
    barcode: str
    specimen_type: str
    container_type: str | None = None
    volume_ml: float | None = None
    clinical_info: str | None = None


class SpecimenTransitionRequest(BaseModel):
    target_status: str
    notes: str | None = None
    rejection_reason: str | None = None


class OrderCreateRequest(BaseModel):
    order_id: int
    accession_number: str
    priority: str | None = None
    clinical_note: str | None = None
    diagnosis_code: str | None = None


class ResultCreateRequest(BaseModel):
    specimen_id: int
    test_code: str
    test_name: str
    value_numeric: float | None = None
    value_text: str | None = None
    unit: str | None = None
    instrument_id: int | None = None
    loinc_code: str | None = None


class ResultValidateRequest(BaseModel):
    notes: str | None = None
    signature_hash: str | None = None
    action: str | None = None


class IQCRunRequest(BaseModel):
    program_id: int
    test_code: str
    measured_value: float
    expected_value: float
    sd: float
    level: str | None = None
    lot_number: str | None = None
    instrument_id: int | None = None
    notes: str | None = None


class InstrumentCreateRequest(BaseModel):
    model_id: int
    instrument_code: str
    serial_number: str | None = None
    workstation_id: int | None = None
    ip_address: str | None = None
    port: int | None = None


class MaintenanceRecordRequest(BaseModel):
    maintenance_type: str
    title: str
    description: str | None = None
    performed_at: str | None = None
    cost: float | None = None
    notes: str | None = None


class CalibrationRecordRequest(BaseModel):
    calibration_type: str
    calibrator_lot: str | None = None
    passed: bool | None = None
    notes: str | None = None


class InventoryRequest(BaseModel):
    code: str
    name: str
    name_ar: str | None = None
    current_quantity: float
    unit: str
    minimum_quantity: float | None = None
    supplier_id: int | None = None
    storage_location: str | None = None


class ReportGenerateRequest(BaseModel):
    order_id: int
    report_number: str
    locale: str | None = None
    title: str | None = None
    title_ar: str | None = None


class DeviceMessageRequest(BaseModel):
    instrument_id: int
    raw_message: str


class ASTMResultResponse(BaseModel):
    specimen_id: str
    test_code: str
    value: str
    unit: str
    flag: str

    model_config = ConfigDict(from_attributes=True)


# ── Subscription Domain ────────────────────────────────────────────────────────


class UpgradeRequestBody(BaseModel):
    target_tier: str
    target_deployment_mode: str | None = None
    target_security_level: str | None = None
    reason: str | None = None


class DemandSignalBody(BaseModel):
    lab_id: int
    target_tier: str
    reason: str | None = None


class SetTierBody(BaseModel):
    tier: str
    deployment_mode: str | None = None
    security_level: str | None = None
    billing_cycle: str | None = None
    notes: str | None = None


class FeatureFlagBody(BaseModel):
    feature_key: str
    is_enabled: bool
    reason: str | None = None
    expires_at: str | None = None


# ── Tasks Domain ───────────────────────────────────────────────────────────────


class TaskPayload(BaseModel):
    task_id: str | None = None
    type: str
    payload: dict | None = None
    retry_count: int | None = None
    max_retries: int | None = None
    timeout_s: int | None = None
    enqueued_at: str | None = None


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Any | None = None
    error: str | None = None
    attempt: int | None = None
    completed_at: str | None = None
    duration_ms: float | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Notifications Domain ───────────────────────────────────────────────────────


class NotifyRequest(BaseModel):
    order_id: int
    channel: str | None = Field(None, pattern=r"^(whatsapp|sms)$")


# ── Quality Control Domain ─────────────────────────────────────────────────────


class QCSubmit(BaseModel):
    test_code: str
    level: str
    expected_value: float
    measured_value: float
    sd: float | None = None
    unit: str | None = None
    instrument_name: str | None = None
    lot_number: str | None = None
    notes: str | None = None


class QCBatchSubmit(BaseModel):
    results: list[QCSubmit]


# ── Legacy ─────────────────────────────────────────────────────────────────────


class LegacyTestResultCreate(BaseModel):
    citizen_id: int = Field(..., ge=1)
    lab_id: int = Field(..., ge=1)
    device_id: int | None = Field(None, ge=1)
    test_code: str = Field(..., min_length=1, max_length=30)
    test_name_en: str = Field(..., min_length=1, max_length=200)
    test_name_ar: str = Field(..., min_length=1, max_length=200)
    category: str | None = Field(None, max_length=50)
    result_value: float | None = None
    result_text: str | None = Field(None, max_length=200)
    unit: str | None = Field(None, max_length=20)
    reference_min: float | None = None
    reference_max: float | None = None
    status: str | None = Field(None, pattern=r"^(pending|completed|verified|rejected)$")
    is_critical: bool | None = None
    is_abnormal: bool | None = None
    abnormality_direction: str | None = None
    sample_collected_at: str
    sample_barcode: str = Field(..., min_length=1, max_length=64)
    ordering_physician: str | None = Field(None, max_length=200)
    clinical_notes: str | None = None
