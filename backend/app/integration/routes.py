from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Path

from app.integration.base import IntegrationStatus
from app.integration.connectors import ConnectorRegistry
from app.integration.gateway import GatewayRegistry
from app.integration.monitoring import IntegrationMonitor
from app.integration.offline import OfflineSyncEngine
from app.integration.testing import IntegrationTestSuite
from app.integration.transformation import DataTransformer, SchemaMapper

logger = logging.getLogger("gula.integration.routes")

router = APIRouter(prefix="/integration", tags=["integration"])

_integration_monitor: IntegrationMonitor | None = None
_offline_sync: OfflineSyncEngine | None = None
_test_suite: IntegrationTestSuite | None = None
_data_transformer: DataTransformer | None = None
_schema_mapper: SchemaMapper | None = None


def configure(
    monitor: IntegrationMonitor | None = None,
    offline: OfflineSyncEngine | None = None,
    test_suite: IntegrationTestSuite | None = None,
    transformer: DataTransformer | None = None,
    mapper: SchemaMapper | None = None,
) -> None:
    global _integration_monitor, _offline_sync, _test_suite, _data_transformer, _schema_mapper
    _integration_monitor = monitor or IntegrationMonitor()
    _offline_sync = offline or OfflineSyncEngine()
    _test_suite = test_suite or IntegrationTestSuite()
    _data_transformer = transformer or DataTransformer()
    _schema_mapper = mapper or SchemaMapper()


GATEWAY_PROTOCOLS = frozenset({
    "fhir", "hl7", "dicom", "soap", "sftp", "graphql", "mqtt",
    "websocket", "grpc", "file", "amqp",
})


@router.get("/gateways")
async def list_gateways() -> dict[str, Any]:
    gateways = GatewayRegistry.list_all()
    return {
        "gateways": [
            {
                "name": g.name,
                "type": type(g).__name__,
                "connected": g._connected,
            }
            for g in gateways
        ],
        "count": len(gateways),
    }


@router.get("/gateway/{protocol}")
async def get_gateway(protocol: str = Path(..., description="Gateway protocol")) -> dict[str, Any]:
    gateways = GatewayRegistry.list_by_protocol(protocol)
    if not gateways:
        raise HTTPException(status_code=404, detail=f"No gateway found for protocol: {protocol}")
    return {
        "protocol": protocol,
        "gateways": [
            {
                "name": g.name,
                "type": type(g).__name__,
                "connected": g._connected,
            }
            for g in gateways
        ],
    }


@router.post("/gateway/{protocol}/send")
async def send_via_gateway(
    protocol: str = Path(..., description="Gateway protocol"),
    payload: dict[str, Any] = Body(..., description="Message payload"),
) -> dict[str, Any]:
    gateways = GatewayRegistry.list_by_protocol(protocol)
    if not gateways:
        raise HTTPException(status_code=404, detail=f"No gateway found for protocol: {protocol}")
    gateway = gateways[0]
    try:
        from backend.app.integration.gateway import GatewayMessage
        message = GatewayMessage(**payload)
        result = await gateway.send(message)
        if _integration_monitor:
            _integration_monitor.record_api_call(f"gateway_{protocol}", result.latency_ms, result.success)
        return {
            "success": result.success,
            "status_code": result.status_code,
            "data": result.data,
            "latency_ms": result.latency_ms,
        }
    except Exception as exc:
        logger.error("Gateway send failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/gateway/{protocol}/receive")
async def receive_via_gateway(
    protocol: str = Path(..., description="Gateway protocol"),
) -> dict[str, Any]:
    gateways = GatewayRegistry.list_by_protocol(protocol)
    if not gateways:
        raise HTTPException(status_code=404, detail=f"No gateway found for protocol: {protocol}")
    gateway = gateways[0]
    try:
        message = await gateway.receive()
        if message is None:
            return {"success": True, "message": None}
        return {"success": True, "message": message}
    except Exception as exc:
        logger.error("Gateway receive failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/catalog")
async def api_catalog() -> dict[str, Any]:
    from backend.app.integration.api_management import APICatalog
    catalog = APICatalog()
    services = catalog.list_services()
    return {
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "version": s.version,
                "description": s.description,
                "provider": s.provider,
                "status": s.status,
                "endpoints": [
                    {
                        "path": ep.path,
                        "method": ep.method,
                        "description": ep.description,
                    }
                    for ep in s.endpoints
                ],
                "tags": s.tags,
            }
            for s in services
        ],
        "count": catalog.count(),
    }


@router.get("/connectors")
async def list_integration_connectors() -> dict[str, Any]:
    connectors = ConnectorRegistry.list_connectors()
    statuses = ConnectorRegistry.get_status_all()
    return {
        "connectors": connectors,
        "details": statuses,
        "count": len(connectors),
    }


@router.get("/standards")
async def standards_conformance() -> dict[str, Any]:
    from backend.app.integration.standards import (
        DICOMService,
        FHIRService,
        HL7Service,
        IHEService,
        TerminologyService,
    )
    fhir = FHIRService()
    hl7 = HL7Service()
    dicom = DICOMService()
    ihe = IHEService()
    terms = TerminologyService()
    return {
        "standards": {
            "fhir": {
                "version": fhir.fhir_version,
                "capabilities": list(fhir.capabilities),
            },
            "hl7": {
                "version": hl7.hl7_version,
                "message_types": hl7.supported_message_types,
            },
            "dicom": {
                "supported_sops": dicom.supported_sop_classes,
            },
            "ihe": {
                "profiles": ihe.supported_profiles,
            },
            "terminology": {
                "systems": list(terms.terminology_systems),
            },
        },
    }


@router.post("/transform")
async def run_transformation(
    data: dict[str, Any] = Body(...),
    pipeline: list[str] = Body(default=[], description="Transformation pipeline steps"),
) -> dict[str, Any]:
    if not _data_transformer:
        raise HTTPException(status_code=503, detail="Data transformer not configured")
    try:
        result = await _data_transformer.transform(data, pipeline)
        if _integration_monitor:
            _integration_monitor.record_api_call("transform", 0, result.get("success", False))
        return result
    except Exception as exc:
        logger.error("Transformation failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/monitoring/dashboard")
async def integration_health_dashboard() -> dict[str, Any]:
    if not _integration_monitor:
        raise HTTPException(status_code=503, detail="Integration monitor not configured")
    return _integration_monitor.get_health_dashboard()


@router.post("/test/run")
async def run_integration_tests(
    target_url: str = Body(default="", description="Target base URL for tests"),
    test_types: list[str] = Body(default=[], description="Test types to run (empty = all)"),
) -> dict[str, Any]:
    if not _test_suite:
        raise HTTPException(status_code=503, detail="Test suite not configured")
    try:
        results = await _test_suite.run_all(target_url)
        if test_types:
            results = {k: v for k, v in results.items() if k in test_types}
        return {"test_results": results}
    except Exception as exc:
        logger.error("Test run failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/offline/sync")
async def trigger_offline_sync() -> dict[str, Any]:
    if not _offline_sync:
        raise HTTPException(status_code=503, detail="Offline sync engine not configured")
    try:
        return await _offline_sync.sync_all()
    except Exception as exc:
        logger.error("Offline sync failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/health")
async def integration_health() -> dict[str, Any]:
    gateways = GatewayRegistry.health_all()
    connectors = ConnectorRegistry.get_status_all()
    overall = IntegrationStatus.ACTIVE
    if any(not v.get("connected", False) for v in gateways.values()):
        overall = IntegrationStatus.DEGRADED
    return {
        "status": overall.name,
        "gateways": len(gateways),
        "gateways_healthy": sum(1 for v in gateways.values() if v.get("connected", False)),
        "connectors": len(connectors),
        "offline_engine": _offline_sync is not None,
        "monitor": _integration_monitor is not None,
        "test_suite": _test_suite is not None,
    }
