from __future__ import annotations

import logging
import os
import uuid
from typing import Annotated, Literal

from app.core.alerting import AlertManager
from app.core.device_manager import DeviceManager
from app.core.device_onboarding import DeviceFingerprint, DeviceOnboardingDirector
from app.core.modes import CommunicationMode
from app.edge.sync_engine import SyncEngine
from app.integration.gula_client import GulaClient
from app.pipeline.data_pipeline import DataPipeline
from app.pipeline.normalizer import NormalizedResult, Normalizer
from app.pipeline.parser_engine import ASTMParser
from app.security.auth import verify_api_key
from app.storage.db import InMemoryDB
from app.storage.result_repository import LogRepository, ResultRepository
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lablink.api")

app = FastAPI(title="LabLink Core", version="0.6.0")

GULA_BACKEND_URL_ENV = "GULA_BACKEND_URL"

repository = ResultRepository(InMemoryDB())
device_manager = DeviceManager()
alerts = AlertManager()
sync_engine = SyncEngine()
mode = CommunicationMode.HYBRID
onboarding_director = DeviceOnboardingDirector()

# docker-compose passes GULA_BACKEND_URL ("http://gula-backend:8000") and the
# configuration reference documents it as "used by the device bridge to forward
# results". Nothing read it: the URL was hardcoded to http://gula.local, a host
# that does not exist on the compose network, so every forward failed on DNS
# before it could fail on anything else.
_gula_base_url = os.getenv(GULA_BACKEND_URL_ENV, "").strip() or "http://gula.local"

# result_repo/log_repo: the pipeline writes into the same store the API serves.
# Left to its defaults it built its own InMemoryDB, so every row it wrote -- the
# per-chunk log row and, now, every rejection -- went to a store no endpoint
# reads, and /ingest had to save the results a second time into this one.
pipeline = DataPipeline(
    parser=ASTMParser(),
    normalizer=Normalizer(),
    gula_client=GulaClient(base_url=_gula_base_url, lab_id="LAB001"),
    result_repo=repository,
    log_repo=LogRepository(repository.db),
)

Auth = Annotated[str, Depends(verify_api_key)]


class IngestRequest(BaseModel):
    patient_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    chunk: str = Field(min_length=1, description="Raw ASTM chunk; may include control chars")
    vendor: str | None = None
    barcode: str | None = None


class IngestResponse(BaseModel):
    status: Literal["ok"]
    processed: int
    results: list[NormalizedResult]


class RegisterDeviceRequest(BaseModel):
    device_id: str
    type: Literal["tcp", "serial"]
    host: str | None = None
    port: int | None = None
    path: str | None = None
    baudrate: int = 9600
    vendor: str = "unknown"
    device_type: str = "unknown"
    protocol: str = "ASTM"


class CommandRequest(BaseModel):
    command: str = Field(min_length=1)


class RoutingPolicyRequest(BaseModel):
    policy: Literal["gula", "offline", "both"]


class ModeRequest(BaseModel):
    mode: CommunicationMode



class DeviceScanRequest(BaseModel):
    os_name: Literal["windows", "linux", "macos"]
    supports_wireless: bool = True
    required_mbps: int = Field(default=50, ge=1, le=10_000)
    max_latency_ms: int = Field(default=20, ge=1, le=1_000)
    distance_meters: int = Field(default=10, ge=1, le=200)
    deployment_target: Literal["local", "global", "hybrid"] = "hybrid"
    region: str = Field(default="global", min_length=2, max_length=32)
    protocol_hint: str = "ASTM"
    vendor_id: str | None = None
    product_id: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    device_class: str | None = None


class DeviceScanResponse(BaseModel):
    identity: str
    protocol: str
    device_class: str
    confidence: float
    driver_candidates: list[dict[str, str]]
    install_plan: list[str]
    transport: dict[str, str | int]
    connectivity_profile: dict[str, str | int]


class OnboardingExecuteRequest(DeviceScanRequest):
    device_id: str = Field(min_length=1)
    connector_type: Literal["tcp", "serial"]
    host: str | None = None
    port: int | None = None
    path: str | None = None
    baudrate: int = 9600
    vendor: str = "unknown"
    device_type: str = "unknown"
    dry_run: bool = False
    min_confidence: float = Field(default=0.7, ge=0.5, le=0.99)
    allow_generic_driver: bool = False


class OnboardingExecuteResponse(BaseModel):
    status: Literal["planned", "registered"]
    device_id: str
    scan: DeviceScanResponse


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/devices/register")
def register_device(payload: RegisterDeviceRequest, _auth: Auth) -> dict[str, str]:
    config = payload.model_dump(exclude_none=True)
    try:
        device_manager.add_device(config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "registered", "device_id": payload.device_id}


@app.get("/devices")
def list_devices(_auth: Auth) -> list[dict]:
    return [
        {
            "device_id": d.device_id,
            "is_connected": d.is_connected,
        }
        for d in device_manager.list_devices()
    ]


@app.get("/registry")
def list_registry(_auth: Auth) -> list[dict]:
    return [
        {
            "device_id": item.device_id,
            "device_type": item.device_type,
            "vendor": item.vendor,
            "protocol": item.protocol,
            "connection": item.connection,
        }
        for item in device_manager.list_registry()
    ]




@app.post("/devices/onboarding/scan", response_model=DeviceScanResponse)
def scan_device_onboarding(payload: DeviceScanRequest, _auth: Auth) -> DeviceScanResponse:
    return _build_scan_response(payload)


def _build_scan_response(payload: DeviceScanRequest) -> DeviceScanResponse:
    identity = onboarding_director.identify_device(
        DeviceFingerprint(
            vendor_id=payload.vendor_id,
            product_id=payload.product_id,
            manufacturer=payload.manufacturer,
            model=payload.model,
            device_class=payload.device_class,
            protocol_hint=payload.protocol_hint,
        )
    )
    drivers = onboarding_director.driver_candidates(payload.os_name, identity["protocol"])
    plan = onboarding_director.install_plan(payload.os_name, identity["protocol"])
    transport = onboarding_director.recommend_transport(
        supports_wireless=payload.supports_wireless,
        required_mbps=payload.required_mbps,
        max_latency_ms=payload.max_latency_ms,
        distance_meters=payload.distance_meters,
    )
    connectivity_profile = onboarding_director.connectivity_profile(
        deployment_target=payload.deployment_target,
        region=payload.region,
        max_latency_ms=payload.max_latency_ms,
    )

    return DeviceScanResponse(
        identity=str(identity["identity"]),
        protocol=str(identity["protocol"]),
        device_class=str(identity["device_class"]),
        confidence=float(identity["confidence"]),
        driver_candidates=drivers,
        install_plan=plan,
        transport=transport,
        connectivity_profile=connectivity_profile,
    )


@app.post("/devices/onboarding/execute", response_model=OnboardingExecuteResponse)
def execute_device_onboarding(payload: OnboardingExecuteRequest, _auth: Auth) -> OnboardingExecuteResponse:
    scan = _build_scan_response(payload)
    if scan.confidence < payload.min_confidence:
        raise HTTPException(
            status_code=400,
            detail=f"device confidence {scan.confidence:.2f} is below required threshold {payload.min_confidence:.2f}",
        )

    uses_generic = any(item["source"] == "os-default" for item in scan.driver_candidates)
    if uses_generic and not payload.allow_generic_driver:
        raise HTTPException(
            status_code=400,
            detail="generic driver requires explicit approval via allow_generic_driver=true",
        )

    config = {
        "device_id": payload.device_id,
        "type": payload.connector_type,
        "vendor": payload.vendor,
        "device_type": payload.device_type,
        "protocol": scan.protocol,
        "baudrate": payload.baudrate,
    }
    if payload.connector_type == "tcp":
        if payload.host is None or payload.port is None:
            raise HTTPException(status_code=400, detail="host and port are required for tcp connector")
        config["host"] = payload.host
        config["port"] = payload.port
    else:
        if payload.path is None:
            raise HTTPException(status_code=400, detail="path is required for serial connector")
        config["path"] = payload.path

    if payload.dry_run:
        repository.add_audit_event(
            event_type="device_onboarding_planned",
            payload={
                "device_id": payload.device_id,
                "protocol": scan.protocol,
                "confidence": scan.confidence,
                "transport": scan.transport,
            },
        )
        return OnboardingExecuteResponse(status="planned", device_id=payload.device_id, scan=scan)

    try:
        device_manager.add_device(config)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return OnboardingExecuteResponse(status="registered", device_id=payload.device_id, scan=scan)

@app.post("/devices/{device_id}/command")
def send_device_command(device_id: str, payload: CommandRequest, _auth: Auth) -> dict[str, str]:
    try:
        device_manager.send_command(device_id, payload.command)
    except Exception as exc:
        alerts.emit(severity="error", message=str(exc), device_id=device_id)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "sent", "device_id": device_id}


@app.post("/devices/{device_id}/routing")
def set_device_routing(device_id: str, payload: RoutingPolicyRequest, _auth: Auth) -> dict[str, str]:
    pipeline.router.set_policy(device_id, payload.policy)
    return {"status": "updated", "device_id": device_id, "policy": payload.policy}


@app.post("/mode")
def set_mode(payload: ModeRequest, _auth: Auth) -> dict[str, str]:
    global mode
    mode = payload.mode
    return {"status": "updated", "mode": mode}


@app.get("/mode")
def get_mode(_auth: Auth) -> dict[str, str]:
    return {"mode": mode}


@app.post("/ingest", response_model=IngestResponse)
async def ingest(payload: IngestRequest, _auth: Auth) -> IngestResponse:
    repository.save_log(device_id=payload.device_id, raw_data=payload.chunk, status="received")

    if mode == CommunicationMode.LOCAL_ONLY:
        pipeline.router.set_policy(payload.device_id, "offline")
    elif mode == CommunicationMode.CLOUD_ONLY:
        pipeline.router.set_policy(payload.device_id, "gula")

    results = await pipeline.process_chunk(
        device_id=payload.device_id,
        fallback_patient_id=payload.patient_id,
        chunk=payload.chunk.encode("latin-1", errors="ignore"),
        vendor=payload.vendor,
        barcode=payload.barcode,
    )

    # Drain with dequeue(), not list_all(). list_all() returns a copy and removes
    # nothing, so every /ingest re-staged the whole backlog: six identical ingests
    # against an unreachable GULA produced 21 offline-queue entries and 27 audit
    # events for six results -- N(N+1)/2, every entry a duplicate of the same
    # result. RetryQueue.dequeue() existed and was called from nowhere. IA-045.
    while True:
        item = pipeline.retry_queue.dequeue()
        if item is None:
            break
        try:
            repository.enqueue_offline(item)
            sync_engine.stage(
                item_id=str(uuid.uuid4()),
                device_id=item["device_id"],
                payload=item,
                version=1,
            )
        except Exception:
            # Hand-off failed after the item left the queue: put it back rather
            # than lose the only record that this result never reached GULA.
            pipeline.retry_queue.enqueue(item)
            logger.exception(
                "Failed to stage a retry item; it was returned to the queue",
                extra={"device_id": item.get("device_id")},
            )
            raise

    for _ in results:
        repository.save_log(
            device_id=payload.device_id,
            raw_data=payload.chunk,
            status="parsed",
            error_message="",
        )

    # No repository.save_results here: the pipeline now writes into this same
    # store, so saving again would duplicate every result row.
    return IngestResponse(status="ok", processed=len(results), results=results)


@app.post("/edge/sync")
async def sync_edge_buffer(_auth: Auth) -> dict[str, int]:
    async def sender(payload: dict) -> dict:
        pipeline.edge_buffer.enqueue(payload)
        return {"status": "ok"}

    return await sync_engine.sync(sender)


@app.get("/alerts")
def list_alerts(_auth: Auth) -> list[dict[str, str]]:
    return alerts.list_alerts()


@app.get("/results")
def list_results(_auth: Auth) -> list[dict]:
    return repository.list_results()


@app.get("/logs")
def list_logs(_auth: Auth) -> list[dict]:
    return repository.list_logs()


@app.get("/audit")
def list_audit(_auth: Auth) -> list[dict]:
    return repository.list_audit_trail()


@app.get("/offline-queue")
def list_offline_queue(_auth: Auth) -> list[dict]:
    return repository.list_offline_queue()
