from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
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
    refresh_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class LabRegisterRequest(BaseModel):
    lab_name: str = Field(..., min_length=2, max_length=200)
    license_number: Optional[str] = None
    lab_type: Optional[str] = Field(None, pattern=r"^(private|government|hospital|clinic)$")
    director_name: Optional[str] = Field(None, min_length=2, max_length=200)
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    admin_name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class CitizenRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    email: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    national_id: Optional[str] = Field(None, pattern=r"^[0-9]{10,14}$")


class StaffRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(None, pattern=r"^(technician|doctor|receptionist|staff)$")


class DoctorRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    email: str
    phone: str = Field(..., pattern=r"^\+?[0-9]{7,15}$")
    password: str = Field(..., min_length=8, max_length=128)
    license_number: str = Field(..., min_length=3, max_length=100)
    specialty: Optional[str] = None
    workplace: Optional[str] = None
    national_id: Optional[str] = Field(None, pattern=r"^[0-9]{10,14}$")


class DeviceTokenRequest(BaseModel):
    device_token: str = Field(..., min_length=10, max_length=512)
    platform: str = Field(..., pattern=r"^(android|ios)$")
    app_version: Optional[str] = None


class CitizenLoginRequest(BaseModel):
    identifier: str
    email: Optional[str] = None
    password: str


class NationalIdRequest(BaseModel):
    national_id: str = Field(..., min_length=5, max_length=20)


class CreateLabRequest(BaseModel):
    name: str = Field(..., min_length=2)
    city: Optional[str] = None
    phone: Optional[str] = None
    admin_email: str
    admin_password: str = Field(..., min_length=8)
    admin_name: str
    province_id: Optional[int] = None


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=2)
    email: str
    password: str = Field(..., min_length=8)
    role: str
    lab_id: Optional[int] = None
    province_id: Optional[int] = None
    national_id: Optional[str] = None


class ChangeRoleRequest(BaseModel):
    role: str
    province_id: Optional[int] = None


class KillSwitchRequest(BaseModel):
    reason: Optional[str] = None


class LinkIdentityRequest(BaseModel):
    patient_id: int
    national_id: str
    confirm_name: Optional[str] = None


# ── Patients Domain ────────────────────────────────────────────────────────────


class PatientCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    phone: str = Field(..., pattern=r"^(07\d{9}|9647\d{9})$")
    birth_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    gender: Optional[str] = Field(None, pattern=r"^(male|female|M|F)$")
    email: Optional[str] = Field(None, max_length=100)
    national_id: Optional[str] = Field(None, pattern=r"^\d{12,13}$")
    family_id: Optional[str] = Field(None, pattern=r"^\d{1,15}$")
    force_create: Optional[bool] = None
    guardian_id: Optional[int] = None


class PatientUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    phone: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    family_id: Optional[str] = Field(None, pattern=r"^\d{1,15}$")


class ScanRequest(BaseModel):
    token: str = Field(..., min_length=10, max_length=200)


# ── Labs Domain ────────────────────────────────────────────────────────────────


class LabUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    license_number: Optional[str] = None
    lab_type: Optional[str] = Field(None, pattern=r"^(private|government|hospital|clinic)$")
    director_name: Optional[str] = None
    website: Optional[str] = None


class CreateEmployeeRequest(BaseModel):
    name: str
    email: str
    password: str = Field(..., min_length=8)
    role: Optional[str] = Field(None, pattern=r"^(admin|staff|technician)$")


class UpdateEmployeeRequest(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern=r"^(admin|staff|technician)$")


# ── Orders & Results Domain ────────────────────────────────────────────────────


class ResultItem(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class CreateOrderRequest(BaseModel):
    patient_id: int = Field(..., ge=1)
    doctor_name: Optional[str] = Field(None, max_length=200)
    doctor_user_id: Optional[int] = None
    results: list[ResultItem]


class AnalyzeRequest(BaseModel):
    results: list[ResultItem]


class BatchResultItem(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class BatchOrderItem(BaseModel):
    patient_id: int
    doctor_name: Optional[str] = None
    results: list[BatchResultItem]


class BatchOrderRequest(BaseModel):
    orders: list[BatchOrderItem]


class TestResultCreate(BaseModel):
    health_id: str = Field(..., min_length=3, max_length=20)
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = Field(None, max_length=50)
    value: Optional[float] = None
    value_text: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None
    sample_type: Optional[str] = Field(None, max_length=50)
    doctor_name: Optional[str] = Field(None, max_length=200)
    order_id: Optional[int] = None


class TestResultRead(BaseModel):
    id: int
    citizen_id: int
    lab_id: int
    device_id: Optional[int] = None
    test_code: str
    test_name_en: str
    test_name_ar: str
    category: Optional[str] = None
    result_value: Optional[float] = None
    result_text: Optional[str] = None
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: str
    is_critical: bool
    is_abnormal: bool
    abnormality_direction: Optional[str] = None
    sample_collected_at: str
    result_completed_at: Optional[str] = None
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    sample_barcode: str
    ordering_physician: Optional[str] = None
    clinical_notes: Optional[str] = None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class TestResultBrief(BaseModel):
    id: int
    test_code: str
    test_name_en: str
    test_name_ar: str
    result_value: Optional[float] = None
    result_text: Optional[str] = None
    unit: Optional[str] = None
    status: str
    is_abnormal: bool
    is_critical: bool
    sample_collected_at: str

    model_config = ConfigDict(from_attributes=True)


class TestResultForCitizen(BaseModel):
    id: int
    test_name_ar: str
    result_value: Optional[float] = None
    result_text: Optional[str] = None
    unit: Optional[str] = None
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: str
    is_abnormal: bool
    is_critical: bool
    abnormality_direction: Optional[str] = None
    sample_collected_at: str
    result_completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TestResultValidateRequest(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=200)
    test_code: Optional[str] = Field(None, max_length=50)
    value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class DeviceResult(BaseModel):
    test_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    normal_range_low: Optional[float] = None
    normal_range_high: Optional[float] = None


class DeviceSubmission(BaseModel):
    barcode: str
    device_id: Optional[str] = None
    results: list[DeviceResult]


class SuggestRequest(BaseModel):
    operation: str
    payload: Optional[dict] = None
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    rationale: Optional[str] = None


class RejectRequest(BaseModel):
    reason: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context: Optional[str] = Field(None, max_length=500)


# ── Samples Domain ─────────────────────────────────────────────────────────────


class SampleCreate(BaseModel):
    order_id: int
    sample_type: str
    collected_by: Optional[str] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = None


class SampleUpdate(BaseModel):
    status: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None
    storage_location: Optional[str] = None


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
    expires_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Claims Domain ──────────────────────────────────────────────────────────────


class ClaimItemCreate(BaseModel):
    test_code: str
    description: Optional[str] = None
    quantity: Optional[int] = Field(default=1, ge=1)
    unit_price: float = Field(..., gt=0)
    amount: float = Field(..., gt=0)


class ClaimCreate(BaseModel):
    patient_id: int
    order_id: Optional[int] = None
    items: list[ClaimItemCreate]
    idempotency_key: Optional[str] = None


class ClaimItemResponse(BaseModel):
    id: int
    claim_id: int
    test_code: str
    description: Optional[str] = None
    quantity: int
    unit_price: float
    amount: float

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(BaseModel):
    id: int
    lab_id: int
    patient_id: int
    order_id: Optional[int] = None
    status: str
    total_amount: Optional[float] = None
    currency: str
    idempotency_key: Optional[str] = None
    external_ref: Optional[str] = None
    submitted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    items: list[ClaimItemResponse]

    model_config = ConfigDict(from_attributes=True)


# ── Edge Domain ────────────────────────────────────────────────────────────────


class RegisterDeviceRequest(BaseModel):
    public_key_pem: str = Field(..., min_length=80, max_length=8000)
    role_mode: Optional[str] = Field(None, pattern=r"^(personal|clinic|enterprise)$")
    display_name: Optional[str] = Field(None, max_length=200)
    agent_version: Optional[str] = Field(None, max_length=32)
    os_platform: Optional[str] = Field(None, max_length=64)
    capabilities: Optional[dict] = None
    attestation_blob: Optional[str] = Field(None, max_length=8000)


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
    display_name: Optional[str] = None
    role_mode: str
    status: str
    trust_score: float
    last_seen_at: Optional[str] = None
    agent_version: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeviceDetail(BaseModel):
    device_id: str
    display_name: Optional[str] = None
    role_mode: str
    status: str
    trust_score: float
    last_seen_at: Optional[str] = None
    agent_version: Optional[str] = None
    capabilities: Optional[dict] = None
    registered_at: str
    revoked_at: Optional[str] = None
    quarantined_at: Optional[str] = None
    kill_switched: bool
    latest_telemetry: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class TaskSubmitRequest(BaseModel):
    kind: str = Field(..., min_length=3, max_length=64)
    payload: Optional[dict] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    privacy_level: Optional[str] = Field(None, pattern=r"^(standard|sensitive|phi)$")
    required_caps: Optional[list[str]] = None
    min_trust: Optional[float] = Field(None, ge=0.0, le=100.0)
    timeout_s: Optional[int] = Field(None, ge=5, le=600)
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    idempotency_key: Optional[str] = Field(None, max_length=80)
    expires_in_s: Optional[int] = Field(None, ge=10, le=86400)


class TaskSummary(BaseModel):
    task_uid: str
    kind: str
    status: str
    priority: int
    privacy_level: str
    device_id: Optional[str] = None
    attempts: int
    created_at: str
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(BaseModel):
    task_uid: str
    kind: str
    status: str
    priority: int
    privacy_level: str
    device_id: Optional[str] = None
    attempts: int
    created_at: str
    completed_at: Optional[str] = None
    payload: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
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
    allow_kinds: Optional[list[str]] = None
    deny_kinds: Optional[list[str]] = None
    min_trust_score: float
    offline_queue_max: int
    kill_switch: bool

    model_config = ConfigDict(from_attributes=True)


class PolicyUpdate(BaseModel):
    max_concurrent_per_device: Optional[int] = Field(None, ge=1, le=64)
    max_devices_per_lab: Optional[int] = Field(None, ge=1, le=10000)
    idle_only: Optional[bool] = None
    battery_floor_pct: Optional[int] = Field(None, ge=0, le=100)
    cpu_cap_pct: Optional[int] = Field(None, ge=10, le=100)
    ram_cap_mb: Optional[int] = Field(None, ge=128, le=131072)
    allow_kinds: Optional[list[str]] = None
    deny_kinds: Optional[list[str]] = None
    min_trust_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    offline_queue_max: Optional[int] = Field(None, ge=10, le=100000)
    kill_switch: Optional[bool] = None


class HeartbeatRequest(BaseModel):
    agent_version: Optional[str] = Field(None, max_length=32)
    capabilities: Optional[dict] = None
    telemetry: Optional[dict] = None
    completed_task_uids: Optional[list[str]] = None


class HeartbeatResponse(BaseModel):
    server_time: str
    next_heartbeat_s: int
    task: Optional[dict] = None
    models: Optional[list[dict]] = None
    quarantined: Optional[bool] = None
    kill_switched: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class TaskResultRequest(BaseModel):
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = Field(None, max_length=2000)
    duration_ms: Optional[int] = Field(None, ge=0, le=600000)


class ModelRegisterRequest(BaseModel):
    name: str = Field(..., max_length=120)
    version: str = Field(..., max_length=40)
    runtime: Optional[str] = Field(None, pattern=r"^(ollama|llamacpp|onnx|custom)$")
    format: Optional[str] = Field(None, max_length=32)
    quantization: Optional[str] = Field(None, max_length=32)
    size_mb: Optional[float] = Field(None, ge=0)
    min_ram_mb: Optional[float] = Field(None, ge=0)
    min_vram_mb: Optional[float] = Field(None, ge=0)
    sha256: Optional[str] = Field(None, max_length=80)
    source_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None


class ModelStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(draft|canary|active|retired|blocked)$")
    rollout_pct: Optional[float] = Field(None, ge=0.0, le=100.0)


class ModelAssignRequest(BaseModel):
    lab_id: Optional[int] = None
    device_id: Optional[str] = Field(None, max_length=64)


# ── MPI Domain ─────────────────────────────────────────────────────────────────


class ResolveRequest(BaseModel):
    lab_id: int = Field(..., ge=1)
    patient_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=2, max_length=200)
    phone: Optional[str] = Field(None, max_length=30)
    birth_date: Optional[str] = None
    gender: Optional[str] = Field(None, pattern=r"^[MFmf]$")
    national_id: Optional[str] = Field(None, max_length=30)
    family_id: Optional[str] = Field(None, max_length=30)


class ResolveResponse(BaseModel):
    citizen_ulid: str
    match_method: str
    match_score: Optional[float] = None
    created: bool
    features: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class CitizenResponse(BaseModel):
    citizen_ulid: str
    nid_verified: bool
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    status: str
    merged_into_ulid: Optional[str] = None
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
    match_score: Optional[float] = None
    match_features: Optional[dict] = None
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
    source: Optional[str] = Field(None, max_length=64)
    doc_id: Optional[str] = Field(None, max_length=128)
    doc_title: Optional[str] = Field(None, max_length=256)
    chunk_text: Optional[str] = Field(None, max_length=4000)
    similarity: Optional[float] = Field(None, ge=0.0, le=1.0)
    rank: Optional[int] = Field(None, ge=0, le=10000)


class InteractionIn(BaseModel):
    anonymous_session_id: str = Field(..., min_length=1, max_length=128)
    language: Optional[str] = Field(None, max_length=8)
    region: Optional[str] = Field(None, max_length=64)
    intent: Optional[str] = Field(None, max_length=64)
    prompt: Optional[str] = Field(None, max_length=8000)
    prompt_redacted: Optional[bool] = None
    response: Optional[str] = Field(None, max_length=16000)
    response_model: Optional[str] = Field(None, max_length=64)
    retrieval_strategy: Optional[str] = Field(None, max_length=64)
    retrieval_refs: Optional[list[RetrievalRefIn]] = None
    biomarkers: Optional[list[str]] = None
    latency_ms: Optional[int] = Field(None, ge=0, le=600000)
    status: Optional[str] = Field(None, max_length=20)
    error_code: Optional[str] = Field(None, max_length=64)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    risk_level: Optional[str] = Field(None, max_length=32)
    escalation_recommended: Optional[bool] = None
    retrieval_used: Optional[bool] = None
    source_quality: Optional[float] = Field(None, ge=0.0, le=1.0)
    unsupported_claims: Optional[int] = Field(None, ge=0, le=1000)
    fallback_generation: Optional[bool] = None
    safety_flags: Optional[list[str]] = None


class InteractionOut(BaseModel):
    id: str
    lab_id: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class FeedbackIn(BaseModel):
    interaction_id: str
    anonymous_session_id: str = Field(..., min_length=1, max_length=128)
    signal: str
    notes: Optional[str] = Field(None, max_length=2000)


class UnresolvedIn(BaseModel):
    interaction_id: Optional[str] = None
    anonymous_session_id: Optional[str] = Field(None, max_length=128)
    question: str = Field(..., min_length=1, max_length=8000)
    language: Optional[str] = Field(None, max_length=8)
    category: Optional[str] = Field(None, max_length=64)


# ── Governance Domain ──────────────────────────────────────────────────────────


class NodeCreate(BaseModel):
    node_type: str
    code: str = Field(..., min_length=1, max_length=100)
    name_ar: str = Field(..., min_length=1, max_length=300)
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    governorate: Optional[str] = None
    district: Optional[str] = None
    metadata_json: Optional[dict] = None


class DelegationCreate(BaseModel):
    delegator_node_id: int
    delegate_node_id: int
    scope: Optional[dict] = None
    reason: Optional[str] = None


class ActingAppoint(BaseModel):
    node_id: int
    acting_node_id: int
    reason: Optional[str] = None


class WorkerCreate(BaseModel):
    employee_code: str
    full_name_ar: str
    profession: str
    full_name_en: Optional[str] = None
    national_id_hash: Optional[str] = None
    specialization: Optional[str] = None
    organization_node_id: Optional[int] = None
    department: Optional[str] = None
    unit: Optional[str] = None
    employment_date: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None


class LabRegister(BaseModel):
    lab_code: str
    name_ar: str
    lab_type: str
    name_en: Optional[str] = None
    organization_node_id: Optional[int] = None
    license_number: Optional[str] = None
    governorate: Optional[str] = None


# ── LIMS Domain ────────────────────────────────────────────────────────────────


class SpecimenRegisterRequest(BaseModel):
    order_id: int
    barcode: str
    specimen_type: str
    container_type: Optional[str] = None
    volume_ml: Optional[float] = None
    clinical_info: Optional[str] = None


class SpecimenTransitionRequest(BaseModel):
    target_status: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class OrderCreateRequest(BaseModel):
    order_id: int
    accession_number: str
    priority: Optional[str] = None
    clinical_note: Optional[str] = None
    diagnosis_code: Optional[str] = None


class ResultCreateRequest(BaseModel):
    specimen_id: int
    test_code: str
    test_name: str
    value_numeric: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    instrument_id: Optional[int] = None
    loinc_code: Optional[str] = None


class ResultValidateRequest(BaseModel):
    notes: Optional[str] = None
    signature_hash: Optional[str] = None
    action: Optional[str] = None


class IQCRunRequest(BaseModel):
    program_id: int
    test_code: str
    measured_value: float
    expected_value: float
    sd: float
    level: Optional[str] = None
    lot_number: Optional[str] = None
    instrument_id: Optional[int] = None
    notes: Optional[str] = None


class InstrumentCreateRequest(BaseModel):
    model_id: int
    instrument_code: str
    serial_number: Optional[str] = None
    workstation_id: Optional[int] = None
    ip_address: Optional[str] = None
    port: Optional[int] = None


class MaintenanceRecordRequest(BaseModel):
    maintenance_type: str
    title: str
    description: Optional[str] = None
    performed_at: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None


class CalibrationRecordRequest(BaseModel):
    calibration_type: str
    calibrator_lot: Optional[str] = None
    passed: Optional[bool] = None
    notes: Optional[str] = None


class InventoryRequest(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    current_quantity: float
    unit: str
    minimum_quantity: Optional[float] = None
    supplier_id: Optional[int] = None
    storage_location: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    order_id: int
    report_number: str
    locale: Optional[str] = None
    title: Optional[str] = None
    title_ar: Optional[str] = None


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
    target_deployment_mode: Optional[str] = None
    target_security_level: Optional[str] = None
    reason: Optional[str] = None


class DemandSignalBody(BaseModel):
    lab_id: int
    target_tier: str
    reason: Optional[str] = None


class SetTierBody(BaseModel):
    tier: str
    deployment_mode: Optional[str] = None
    security_level: Optional[str] = None
    billing_cycle: Optional[str] = None
    notes: Optional[str] = None


class FeatureFlagBody(BaseModel):
    feature_key: str
    is_enabled: bool
    reason: Optional[str] = None
    expires_at: Optional[str] = None


# ── Tasks Domain ───────────────────────────────────────────────────────────────


class TaskPayload(BaseModel):
    task_id: Optional[str] = None
    type: str
    payload: Optional[dict] = None
    retry_count: Optional[int] = None
    max_retries: Optional[int] = None
    timeout_s: Optional[int] = None
    enqueued_at: Optional[str] = None


class TaskResult(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    attempt: Optional[int] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


# ── Notifications Domain ───────────────────────────────────────────────────────


class NotifyRequest(BaseModel):
    order_id: int
    channel: Optional[str] = Field(None, pattern=r"^(whatsapp|sms)$")


# ── Quality Control Domain ─────────────────────────────────────────────────────


class QCSubmit(BaseModel):
    test_code: str
    level: str
    expected_value: float
    measured_value: float
    sd: Optional[float] = None
    unit: Optional[str] = None
    instrument_name: Optional[str] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None


class QCBatchSubmit(BaseModel):
    results: list[QCSubmit]


# ── Legacy ─────────────────────────────────────────────────────────────────────


class LegacyTestResultCreate(BaseModel):
    citizen_id: int = Field(..., ge=1)
    lab_id: int = Field(..., ge=1)
    device_id: Optional[int] = Field(None, ge=1)
    test_code: str = Field(..., min_length=1, max_length=30)
    test_name_en: str = Field(..., min_length=1, max_length=200)
    test_name_ar: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    result_value: Optional[float] = None
    result_text: Optional[str] = Field(None, max_length=200)
    unit: Optional[str] = Field(None, max_length=20)
    reference_min: Optional[float] = None
    reference_max: Optional[float] = None
    status: Optional[str] = Field(None, pattern=r"^(pending|completed|verified|rejected)$")
    is_critical: Optional[bool] = None
    is_abnormal: Optional[bool] = None
    abnormality_direction: Optional[str] = None
    sample_collected_at: str
    sample_barcode: str = Field(..., min_length=1, max_length=64)
    ordering_physician: Optional[str] = Field(None, max_length=200)
    clinical_notes: Optional[str] = None
