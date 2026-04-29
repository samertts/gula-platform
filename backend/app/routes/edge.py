"""Edge Control Plane HTTP API.

Two distinct surfaces:

  Operator API (authenticated lab user):
    POST   /edge/devices/register         — register a new device for the lab
    GET    /edge/devices                  — list devices in this lab
    GET    /edge/devices/{device_id}      — device detail + latest telemetry
    POST   /edge/devices/{device_id}/quarantine
    POST   /edge/devices/{device_id}/revoke
    POST   /edge/devices/{device_id}/reinstate
    POST   /edge/devices/{device_id}/kill_switch
    POST   /edge/tasks                    — submit a new edge task
    GET    /edge/tasks                    — list tasks in this lab
    GET    /edge/tasks/{task_uid}         — task detail
    POST   /edge/tasks/{task_uid}/cancel
    GET    /edge/policy                   — read effective policy for this lab
    PUT    /edge/policy                   — update policy (admin role)
    GET    /edge/fleet/summary            — aggregate fleet stats
    POST   /edge/models                   — register a model (master only)
    GET    /edge/models
    POST   /edge/models/{uid}/status
    POST   /edge/models/{uid}/assign

  Agent API (mTLS / device-token authenticated):
    POST   /edge/agent/heartbeat          — heartbeat + claim next task
    POST   /edge/agent/tasks/{task_uid}/result   — report task result
    POST   /edge/agent/telemetry          — push detailed telemetry sample

The agent endpoints rely on a per-device token issued at registration
(JWT-style, signed with EDGE_TASK_SIGNING_KEY). They never accept a normal
user JWT and never call get_current_user.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.lab_user import LabUser
from ..models.edge import (
    EdgeDevice, EdgeEvent, EdgeModel, EdgeModelAssignment, EdgePolicy, EdgeTask,
)
from ..security.dependencies import get_current_user
from ..security.rate_limit import rate_limit_user, rate_limit_public
from ..edge import (
    config as edge_config,
    governance,
    identity,
    policy as policy_mod,
    registry,
    scheduler,
    telemetry as tele,
    trust as trust_mod,
)


router = APIRouter(prefix="/edge", tags=["edge"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class RegisterDeviceRequest(BaseModel):
    public_key_pem: str = Field(..., min_length=80, max_length=8000)
    role_mode:      str = Field("personal", pattern="^(personal|clinic|enterprise)$")
    display_name:   Optional[str] = Field(None, max_length=200)
    agent_version:  Optional[str] = Field(None, max_length=32)
    os_platform:    Optional[str] = Field(None, max_length=64)
    capabilities:   Optional[dict[str, Any]] = None
    attestation_blob: Optional[str] = Field(None, max_length=8000)


class RegisterDeviceResponse(BaseModel):
    device_id:       str
    status:          str
    role_mode:       str
    trust_score:     float
    cert_fingerprint: str
    agent_token:     str  # bearer for /edge/agent/* calls
    nonce:           str  # echo-and-sign on first heartbeat


class DeviceSummary(BaseModel):
    device_id:    str
    display_name: Optional[str]
    role_mode:    str
    status:       str
    trust_score:  float
    last_seen_at: Optional[datetime]
    agent_version: Optional[str]


class DeviceDetail(DeviceSummary):
    capabilities:    Optional[dict[str, Any]]
    registered_at:   datetime
    revoked_at:      Optional[datetime]
    quarantined_at:  Optional[datetime]
    kill_switched:   bool
    latest_telemetry: Optional[dict[str, Any]] = None


class TaskSubmitRequest(BaseModel):
    kind:            str = Field(..., min_length=3, max_length=64)
    payload:         Optional[dict[str, Any]] = None
    priority:        int = Field(5, ge=1, le=10)
    privacy_level:   str = Field("standard", pattern="^(standard|sensitive|phi)$")
    required_caps:   Optional[list[str]] = None
    min_trust:       float = Field(0.0, ge=0.0, le=100.0)
    timeout_s:       int = Field(60, ge=5, le=600)
    max_attempts:    int = Field(3, ge=1, le=10)
    idempotency_key: Optional[str] = Field(None, max_length=80)
    expires_in_s:    Optional[int] = Field(None, ge=10, le=86400)


class TaskSummary(BaseModel):
    task_uid:    str
    kind:        str
    status:      str
    priority:    int
    privacy_level: str
    device_id:   Optional[str]
    attempts:    int
    created_at:  datetime
    completed_at: Optional[datetime]


class TaskDetail(TaskSummary):
    payload:    Optional[dict[str, Any]]
    result:     Optional[dict[str, Any]]
    error:      Optional[str]
    timeout_s:  int
    max_attempts: int


class PolicyView(BaseModel):
    max_concurrent_per_device: int
    max_devices_per_lab:       int
    idle_only:                 bool
    battery_floor_pct:         int
    cpu_cap_pct:               int
    ram_cap_mb:                int
    allow_kinds:               Optional[list[str]]
    deny_kinds:                Optional[list[str]]
    min_trust_score:           float
    offline_queue_max:         int
    kill_switch:               bool


class PolicyUpdate(BaseModel):
    max_concurrent_per_device: Optional[int] = Field(None, ge=1, le=64)
    max_devices_per_lab:       Optional[int] = Field(None, ge=1, le=10000)
    idle_only:                 Optional[bool] = None
    battery_floor_pct:         Optional[int] = Field(None, ge=0, le=100)
    cpu_cap_pct:               Optional[int] = Field(None, ge=10, le=100)
    ram_cap_mb:                Optional[int] = Field(None, ge=128, le=131072)
    allow_kinds:               Optional[list[str]] = None
    deny_kinds:                Optional[list[str]] = None
    min_trust_score:           Optional[float] = Field(None, ge=0.0, le=100.0)
    offline_queue_max:         Optional[int] = Field(None, ge=10, le=100000)
    kill_switch:               Optional[bool] = None


class HeartbeatRequest(BaseModel):
    agent_version: Optional[str] = Field(None, max_length=32)
    capabilities:  Optional[dict[str, Any]] = None
    telemetry:     Optional[dict[str, Any]] = None
    completed_task_uids: Optional[list[str]] = None  # for ack-style cleanup


class HeartbeatResponse(BaseModel):
    server_time:   datetime
    next_heartbeat_s: int
    task:          Optional[dict[str, Any]] = None
    models:        list[dict[str, Any]] = Field(default_factory=list)
    quarantined:   bool = False
    kill_switched: bool = False


class TaskResultRequest(BaseModel):
    success: bool
    result:  Optional[dict[str, Any]] = None
    error:   Optional[str] = Field(None, max_length=2000)
    duration_ms: Optional[int] = Field(None, ge=0, le=600_000)


class ModelRegisterRequest(BaseModel):
    name:        str = Field(..., max_length=120)
    version:     str = Field(..., max_length=40)
    runtime:     str = Field("ollama", pattern="^(ollama|llamacpp|onnx|custom)$")
    format:      str = Field("gguf", max_length=32)
    quantization: Optional[str] = Field(None, max_length=32)
    size_mb:     Optional[float] = Field(None, ge=0)
    min_ram_mb:  Optional[float] = Field(None, ge=0)
    min_vram_mb: Optional[float] = Field(None, ge=0)
    sha256:      Optional[str] = Field(None, max_length=80)
    source_url:  Optional[str] = Field(None, max_length=500)
    metadata:    Optional[dict[str, Any]] = None


class ModelStatusUpdate(BaseModel):
    status:      str = Field(..., pattern="^(draft|canary|active|retired|blocked)$")
    rollout_pct: Optional[float] = Field(None, ge=0.0, le=100.0)


class ModelAssignRequest(BaseModel):
    lab_id:    Optional[int] = None
    device_id: Optional[str] = Field(None, max_length=64)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _kill_switch_guard() -> None:
    if not edge_config.EDGE_ENABLED:
        raise HTTPException(503, "Edge platform disabled (EDGE_ENABLED=false)")
    if edge_config.EDGE_KILL_SWITCH:
        raise HTTPException(503, "Edge platform globally killed (EDGE_KILL_SWITCH)")


def _require_admin(user: LabUser) -> None:
    if user.role not in ("admin", "lab_admin", "master_admin", "ministry_admin",
                         "province_admin"):
        raise HTTPException(403, "Admin role required")


def _require_master(user: LabUser) -> None:
    if user.role not in ("master_admin", "ministry_admin"):
        raise HTTPException(403, "Master admin role required")


def _device_summary(d: EdgeDevice) -> DeviceSummary:
    return DeviceSummary(
        device_id=d.device_id, display_name=d.display_name,
        role_mode=d.role_mode, status=d.status,
        trust_score=d.trust_score, last_seen_at=d.last_seen_at,
        agent_version=d.agent_version,
    )


def _task_summary(t: EdgeTask) -> TaskSummary:
    return TaskSummary(
        task_uid=t.task_uid, kind=t.kind, status=t.status,
        priority=t.priority, privacy_level=t.privacy_level,
        device_id=t.device_id, attempts=t.attempts,
        created_at=t.created_at, completed_at=t.completed_at,
    )


# ── Agent token (lightweight HMAC-signed bearer) ─────────────────────────────
#
# We don't issue a full JWT for every device — instead a deterministic HMAC
# over (device_id, cert_fingerprint, lab_id) with the global signing key.
# Validates without a DB lookup, but must be re-checked against the device
# row every call (via _resolve_agent_device).

import hmac as _hmac
import hashlib as _hashlib


def _make_agent_token(device: EdgeDevice) -> str:
    msg = f"{device.device_id}|{device.cert_fingerprint}|{device.lab_id}".encode("utf-8")
    sig = _hmac.new(edge_config.get_task_signing_key(), msg, _hashlib.sha256).hexdigest()
    return f"{device.device_id}.{sig}"


def _resolve_agent_device(
    db: Session, *, authorization: Optional[str],
) -> EdgeDevice:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing agent bearer token")
    token = authorization.split(" ", 1)[1].strip()
    if "." not in token:
        raise HTTPException(401, "Malformed agent token")
    device_id, sig = token.split(".", 1)
    device = (
        db.query(EdgeDevice).filter(EdgeDevice.device_id == device_id).first()
    )
    if device is None:
        raise HTTPException(401, "Unknown device")
    expected = _make_agent_token(device).split(".", 1)[1]
    if not _hmac.compare_digest(expected, sig):
        # Cryptographic misbehavior — penalize and refuse.
        try:
            trust_mod.adjust(db, device, reason="signature_failure",
                             actor_user_id=None)
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(401, "Invalid agent token")
    if device.revoked_at is not None or device.kill_switched:
        raise HTTPException(403, "Device revoked or killed")
    return device


# ─────────────────────────────────────────────────────────────────────────────
# Operator API — devices
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/devices/register", response_model=RegisterDeviceResponse,
             status_code=status.HTTP_201_CREATED)
def register_device_endpoint(
    body: RegisterDeviceRequest,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=20)
    try:
        device = registry.register_device(
            db,
            lab_id=user.lab_id,
            owner_user_id=user.id,
            public_key_pem=body.public_key_pem,
            role_mode=body.role_mode,
            display_name=body.display_name,
            agent_version=body.agent_version,
            os_platform=body.os_platform,
            capabilities=body.capabilities,
            attestation_blob=body.attestation_blob,
        )
    except registry.RegistryError as e:
        raise HTTPException(400, str(e))
    db.commit()
    db.refresh(device)
    return RegisterDeviceResponse(
        device_id=device.device_id,
        status=device.status,
        role_mode=device.role_mode,
        trust_score=device.trust_score,
        cert_fingerprint=device.cert_fingerprint or "",
        agent_token=_make_agent_token(device),
        nonce=identity.make_nonce(),
    )


@router.get("/devices", response_model=list[DeviceSummary])
def list_devices(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=60)
    q = db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id)
    if status_filter:
        q = q.filter(EdgeDevice.status == status_filter)
    rows = q.order_by(EdgeDevice.last_seen_at.desc().nullslast()).limit(500).all()
    return [_device_summary(d) for d in rows]


@router.get("/devices/{device_id}", response_model=DeviceDetail)
def get_device(
    device_id: str,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=120)
    d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)
    if d is None:
        raise HTTPException(404, "Device not found")
    latest = tele.latest(db, device_id=device_id, lab_id=user.lab_id)
    latest_dict = None
    if latest is not None:
        latest_dict = {
            "ts": latest.ts.isoformat(),
            "cpu_pct": latest.cpu_pct,
            "mem_mb":  latest.mem_mb,
            "battery_pct": latest.battery_pct,
            "queue_depth": latest.queue_depth,
            "loaded_models": latest.loaded_models,
        }
    return DeviceDetail(
        **_device_summary(d).model_dump(),
        capabilities=d.capabilities,
        registered_at=d.registered_at,
        revoked_at=d.revoked_at,
        quarantined_at=d.quarantined_at,
        kill_switched=d.kill_switched,
        latest_telemetry=latest_dict,
    )


@router.post("/devices/{device_id}/quarantine")
def quarantine_device(
    device_id: str,
    request: Request,
    reason: str = Query(..., min_length=3, max_length=200),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)
    if d is None:
        raise HTTPException(404, "Device not found")
    registry.quarantine(db, d, reason=reason, actor_user_id=user.id)
    db.commit()
    return {"device_id": device_id, "status": d.status}


@router.post("/devices/{device_id}/revoke")
def revoke_device(
    device_id: str,
    request: Request,
    reason: str = Query(..., min_length=3, max_length=200),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)
    if d is None:
        raise HTTPException(404, "Device not found")
    registry.revoke(db, d, reason=reason, actor_user_id=user.id)
    db.commit()
    return {"device_id": device_id, "status": d.status}


@router.post("/devices/{device_id}/reinstate")
def reinstate_device(
    device_id: str,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)
    if d is None:
        raise HTTPException(404, "Device not found")
    try:
        registry.reinstate(db, d, actor_user_id=user.id)
    except registry.RegistryError as e:
        raise HTTPException(400, str(e))
    db.commit()
    return {"device_id": device_id, "status": d.status}


@router.post("/devices/{device_id}/kill_switch")
def device_kill_switch(
    device_id: str,
    request: Request,
    on: bool = Query(...),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    d = registry.get_device_for_lab(db, device_id=device_id, lab_id=user.lab_id)
    if d is None:
        raise HTTPException(404, "Device not found")
    registry.kill_switch_set(db, d, on, actor_user_id=user.id)
    db.commit()
    return {"device_id": device_id, "kill_switched": on}


# ─────────────────────────────────────────────────────────────────────────────
# Operator API — tasks
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/tasks", response_model=TaskDetail, status_code=status.HTTP_201_CREATED)
def submit_task_endpoint(
    body: TaskSubmitRequest,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=120)
    try:
        t = scheduler.submit_task(
            db,
            lab_id=user.lab_id,
            kind=body.kind,
            payload=body.payload,
            priority=body.priority,
            privacy_level=body.privacy_level,
            required_caps=body.required_caps,
            min_trust=body.min_trust,
            timeout_s=body.timeout_s,
            max_attempts=body.max_attempts,
            idempotency_key=body.idempotency_key,
            expires_in_s=body.expires_in_s,
            submitted_by_user_id=user.id,
        )
    except scheduler.SchedulerError as e:
        raise HTTPException(400, str(e))
    db.commit()
    db.refresh(t)
    return TaskDetail(
        **_task_summary(t).model_dump(),
        payload=t.payload, result=t.result, error=t.error,
        timeout_s=t.timeout_s, max_attempts=t.max_attempts,
    )


@router.get("/tasks", response_model=list[TaskSummary])
def list_tasks(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    kind: Optional[str] = Query(None, max_length=64),
    limit: int = Query(100, ge=1, le=500),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=120)
    q = db.query(EdgeTask).filter(EdgeTask.lab_id == user.lab_id)
    if status_filter:
        q = q.filter(EdgeTask.status == status_filter)
    if kind:
        q = q.filter(EdgeTask.kind == kind)
    rows = q.order_by(EdgeTask.created_at.desc()).limit(limit).all()
    return [_task_summary(t) for t in rows]


@router.get("/tasks/{task_uid}", response_model=TaskDetail)
def get_task(
    task_uid: str,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=240)
    t = (
        db.query(EdgeTask)
          .filter(EdgeTask.task_uid == task_uid,
                  EdgeTask.lab_id == user.lab_id)
          .first()
    )
    if t is None:
        raise HTTPException(404, "Task not found")
    return TaskDetail(
        **_task_summary(t).model_dump(),
        payload=t.payload, result=t.result, error=t.error,
        timeout_s=t.timeout_s, max_attempts=t.max_attempts,
    )


@router.post("/tasks/{task_uid}/cancel")
def cancel_task_endpoint(
    task_uid: str,
    request: Request,
    reason: str = Query("operator cancelled", min_length=3, max_length=200),
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=60)
    t = (
        db.query(EdgeTask)
          .filter(EdgeTask.task_uid == task_uid,
                  EdgeTask.lab_id == user.lab_id)
          .first()
    )
    if t is None:
        raise HTTPException(404, "Task not found")
    scheduler.cancel_task(db, t, reason=reason, actor_user_id=user.id)
    db.commit()
    return {"task_uid": task_uid, "status": t.status}


# ─────────────────────────────────────────────────────────────────────────────
# Operator API — policy & fleet
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/policy", response_model=PolicyView)
def get_lab_policy(
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=60)
    p = policy_mod.get_policy(db, user.lab_id)
    return PolicyView(**p.__dict__)


@router.put("/policy", response_model=PolicyView)
def update_lab_policy(
    body: PolicyUpdate,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    fields = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    policy_mod.upsert_policy(
        db, lab_id=user.lab_id, actor_user_id=user.id, **fields,
    )
    db.add(EdgeEvent(
        lab_id=user.lab_id, event_type="policy_updated", severity="info",
        actor_user_id=user.id, details=fields,
    ))
    db.commit()
    p = policy_mod.get_policy(db, user.lab_id)
    return PolicyView(**p.__dict__)


@router.get("/fleet/summary")
def fleet_summary_endpoint(
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=60)
    summary = tele.fleet_summary(db, lab_id=user.lab_id)
    devices_total = (
        db.query(EdgeDevice).filter(EdgeDevice.lab_id == user.lab_id).count()
    )
    pending_tasks = (
        db.query(EdgeTask)
          .filter(EdgeTask.lab_id == user.lab_id,
                  EdgeTask.status.in_(("pending", "dispatched", "running")))
          .count()
    )
    return {
        **summary,
        "devices_total":   devices_total,
        "pending_tasks":   pending_tasks,
        "kill_switched":   policy_mod.get_policy(db, user.lab_id).kill_switch,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Operator API — model governance (master / ministry only)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/models", status_code=status.HTTP_201_CREATED)
def register_model_endpoint(
    body: ModelRegisterRequest,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_master(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    try:
        m = governance.register_model(
            db, name=body.name, version=body.version,
            runtime=body.runtime, fmt=body.format,
            quantization=body.quantization, size_mb=body.size_mb,
            min_ram_mb=body.min_ram_mb, min_vram_mb=body.min_vram_mb,
            sha256=body.sha256, source_url=body.source_url,
            metadata_json=body.metadata, actor_user_id=user.id,
        )
    except governance.GovernanceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    db.refresh(m)
    return {"model_uid": m.model_uid, "status": m.status,
            "rollout_pct": m.rollout_pct}


@router.get("/models")
def list_models(
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_user(request, user.id, max_per_minute=60)
    rows = db.query(EdgeModel).order_by(EdgeModel.created_at.desc()).all()
    return [{
        "model_uid": m.model_uid, "name": m.name, "version": m.version,
        "runtime":   m.runtime,   "status": m.status,
        "rollout_pct": m.rollout_pct, "size_mb": m.size_mb,
        "created_at": m.created_at.isoformat(),
    } for m in rows]


@router.post("/models/{model_uid}/status")
def update_model_status(
    model_uid: str,
    body: ModelStatusUpdate,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    _require_master(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    try:
        m = governance.set_model_status(
            db, model_uid=model_uid, status=body.status,
            rollout_pct=body.rollout_pct, actor_user_id=user.id,
        )
    except governance.GovernanceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    return {"model_uid": m.model_uid, "status": m.status,
            "rollout_pct": m.rollout_pct}


@router.post("/models/{model_uid}/assign")
def assign_model_endpoint(
    model_uid: str,
    body: ModelAssignRequest,
    request: Request,
    user: LabUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    # Ministry can assign cross-lab; lab admin can only assign to own lab/devices
    if body.lab_id is not None and body.lab_id != user.lab_id:
        _require_master(user)
    elif body.device_id is None:
        # Global assignment
        _require_master(user)
    else:
        _require_admin(user)
    rate_limit_user(request, user.id, max_per_minute=20)
    try:
        a = governance.assign_model(
            db, model_uid=model_uid,
            lab_id=body.lab_id if body.lab_id is not None else user.lab_id,
            device_id=body.device_id, actor_user_id=user.id,
        )
    except governance.GovernanceError as e:
        raise HTTPException(400, str(e))
    db.commit()
    return {"id": a.id, "model_uid": a.model_uid,
            "lab_id": a.lab_id, "device_id": a.device_id}


# ─────────────────────────────────────────────────────────────────────────────
# Agent API
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/agent/heartbeat", response_model=HeartbeatResponse)
def agent_heartbeat(
    body: HeartbeatRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_public(request, max_per_minute=120)

    device = _resolve_agent_device(db, authorization=authorization)

    try:
        registry.heartbeat(
            db, device_id=device.device_id,
            agent_version=body.agent_version,
            capabilities=body.capabilities,
        )
    except registry.RegistryError as e:
        raise HTTPException(403, str(e))

    if body.telemetry:
        tele.record(db, lab_id=device.lab_id,
                    device_id=device.device_id, sample=body.telemetry)

    trust_mod.adjust(db, device, reason="heartbeat_ok", actor_user_id=None)

    pol = policy_mod.get_policy(db, device.lab_id)

    next_task_dict = None
    if (device.status == "active" and not pol.kill_switch
            and not device.kill_switched):
        t = scheduler.claim_next_task(db, device)
        if t is not None:
            next_task_dict = {
                "task_uid":      t.task_uid,
                "kind":          t.kind,
                "priority":      t.priority,
                "privacy_level": t.privacy_level,
                "payload":       t.payload,
                "payload_sig":   t.payload_sig,
                "timeout_s":     t.timeout_s,
                "attempt":       t.attempts,
                "max_attempts":  t.max_attempts,
            }

    models = governance.pick_models_for(db, device)

    db.commit()

    return HeartbeatResponse(
        server_time=datetime.now(timezone.utc),
        next_heartbeat_s=max(15, edge_config.EDGE_HEARTBEAT_TIMEOUT_S // 4),
        task=next_task_dict,
        models=models,
        quarantined=device.status == "quarantined",
        kill_switched=pol.kill_switch or device.kill_switched,
    )


@router.post("/agent/tasks/{task_uid}/result")
def agent_task_result(
    task_uid: str,
    body: TaskResultRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_public(request, max_per_minute=300)

    device = _resolve_agent_device(db, authorization=authorization)
    t = (
        db.query(EdgeTask)
          .filter(EdgeTask.task_uid == task_uid,
                  EdgeTask.lab_id == device.lab_id,
                  EdgeTask.device_id == device.device_id)
          .first()
    )
    if t is None:
        raise HTTPException(404, "Task not found or not assigned to this device")

    if t.status not in ("dispatched", "running"):
        # Already resolved — likely a retry. Idempotent response.
        return {"task_uid": task_uid, "status": t.status}

    if body.success:
        scheduler.complete_task(db, t, result=body.result)
        trust_mod.adjust(db, device, reason="task_completed", actor_user_id=None)
    else:
        scheduler.fail_task(db, t, error=body.error or "agent reported failure")
        trust_mod.adjust(db, device, reason="task_failed", actor_user_id=None)
    db.commit()
    return {"task_uid": task_uid, "status": t.status}


@router.post("/agent/telemetry")
def agent_telemetry(
    sample: dict[str, Any],
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    _kill_switch_guard()
    rate_limit_public(request, max_per_minute=120)
    device = _resolve_agent_device(db, authorization=authorization)
    tele.record(db, lab_id=device.lab_id, device_id=device.device_id, sample=sample)
    db.commit()
    return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# Public health for the edge plane
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health")
def edge_health():
    return {
        "enabled":      edge_config.EDGE_ENABLED,
        "kill_switch":  edge_config.EDGE_KILL_SWITCH,
        "heartbeat_timeout_s": edge_config.EDGE_HEARTBEAT_TIMEOUT_S,
        "telemetry_retention_days": edge_config.EDGE_TELEMETRY_RETENTION_DAYS,
        "allowed_kinds": sorted(edge_config.ALLOWED_TASK_KINDS),
    }
