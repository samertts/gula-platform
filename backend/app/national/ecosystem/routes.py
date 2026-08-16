from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.security.dependencies import require_permission

from .connectors import (
    BaseConnector,
    ConnectorConfig,
    ConnectorDirection,
    ConnectorProtocol,
    ConnectorRegistry,
    FHIRConnector,
    FileConnector,
    HL7Connector,
    MessagingConnector,
    RESTConnector,
    WebhookConnector,
)
from .partners import (
    AuditManager,
    CertificateManager,
    CredentialManager,
    PartnerManager,
)
from .transformation import TransformationEngine

logger = logging.getLogger("gula.ecosystem.routes")

router = APIRouter(prefix="/ecosystem", tags=["Ecosystem"])


_transformation_engine = TransformationEngine()
_schema_registry = _transformation_engine.schema_registry

_CONNECTOR_TYPES = {
    "rest": RESTConnector,
    "fhir_rest": FHIRConnector,
    "fhir_messaging": FHIRConnector,
    "hl7_v2": HL7Connector,
    "file_watcher": FileConnector,
    "csv_import": FileConnector,
    "excel_import": FileConnector,
    "mqtt": MessagingConnector,
    "amqp": MessagingConnector,
    "webhook": WebhookConnector,
}


def _build_connector(protocol: str, config: dict) -> BaseConnector:
    conn_cls = _CONNECTOR_TYPES.get(protocol)
    if not conn_cls:
        raise HTTPException(status_code=400, detail=f"unsupported protocol: {protocol}")

    try:
        protocol_enum = ConnectorProtocol(protocol)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid protocol: {protocol}") from None
    direction = ConnectorDirection(config.get("direction", "inbound"))
    conn_config = ConnectorConfig(
        name=config["name"],
        protocol=protocol_enum,
        direction=direction,
        endpoint=config.get("endpoint"),
        auth_type=config.get("auth_type"),
        credentials=config.get("credentials"),
        timeout_seconds=config.get("timeout_seconds", 30),
        retry_count=config.get("retry_count", 3),
        retry_delay_seconds=config.get("retry_delay_seconds", 5),
        circuit_breaker_threshold=config.get("circuit_breaker_threshold", 5),
        rate_limit_per_minute=config.get("rate_limit_per_minute", 60),
        batch_size=config.get("batch_size", 100),
        options=config.get("options"),
    )
    return conn_cls(conn_config)


@router.post(
    "/connectors/register",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def register_connector(config: dict = Body(...)) -> dict:
    protocol = config.get("protocol", "")
    if not protocol:
        raise HTTPException(status_code=400, detail="protocol is required")

    connector = _build_connector(protocol, config)
    connected = await connector.connect()
    ConnectorRegistry.register(config["name"], connector)

    return {
        "name": config["name"],
        "protocol": protocol,
        "connected": connected,
        "status": connector.get_status().value,
    }


@router.get(
    "/connectors",
    dependencies=[Depends(require_permission("integration:read"))],
)
async def list_connectors() -> list[dict]:
    return ConnectorRegistry.list()


@router.get(
    "/connectors/{name}/health",
    dependencies=[Depends(require_permission("integration:read"))],
)
async def connector_health(name: str) -> dict:
    connector = ConnectorRegistry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"connector not found: {name}")

    healthy = await connector.health_check()
    return {
        "name": name,
        "healthy": healthy,
        "status": connector.get_status().value,
        "metrics": connector.get_metrics(),
    }


@router.delete(
    "/connectors/{name}",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def unregister_connector(name: str) -> dict:
    connector = ConnectorRegistry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"connector not found: {name}")

    await connector.disconnect()
    ConnectorRegistry.unregister(name)
    return {"name": name, "status": "unregistered"}


@router.post(
    "/connectors/{name}/send",
    dependencies=[Depends(require_permission("integration:operate"))],
)
async def connector_send(name: str, data: Any = Body(...)) -> dict:
    connector = ConnectorRegistry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"connector not found: {name}")

    result = await connector.send(data)
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "duration_ms": result.duration_ms,
        "status_code": result.status_code,
    }


@router.post(
    "/connectors/{name}/receive",
    dependencies=[Depends(require_permission("integration:operate"))],
)
async def connector_receive(name: str) -> dict:
    connector = ConnectorRegistry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"connector not found: {name}")

    result = await connector.receive()
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
        "duration_ms": result.duration_ms,
        "status_code": result.status_code,
    }


@router.post(
    "/transform",
    dependencies=[Depends(require_permission("integration:operate"))],
)
async def transform_data(
    source_data: Any = Body(...),
    source_format: str = Query("json"),
    target_format: str = Query("json"),
) -> Any:
    try:
        return _transformation_engine.transform(source_data, source_format, target_format)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid request") from exc


@router.get(
    "/schemas",
    dependencies=[Depends(require_permission("integration:read"))],
)
async def list_schemas() -> list[dict]:
    return _schema_registry.list_schemas()


@router.post(
    "/schemas",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def register_schema(data: dict = Body(...)) -> dict:
    name = data.get("name", "")
    schema = data.get("schema", {})
    version = data.get("version", "1.0.0")
    if not name or not schema:
        raise HTTPException(status_code=400, detail="name and schema are required")
    return _schema_registry.register_schema(name, schema, version)


@router.post(
    "/schemas/{schema_name}/validate",
    dependencies=[Depends(require_permission("integration:operate"))],
)
async def validate_against_schema(schema_name: str, data: Any = Body(...)) -> dict:
    valid, errors = _schema_registry.validate_against_schema(data, schema_name)
    return {"valid": valid, "errors": errors}


@router.post(
    "/partners",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def register_partner(data: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    manager = PartnerManager(db)
    partner = manager.register_partner(data)
    return partner.to_dict()


@router.get(
    "/partners",
    dependencies=[Depends(require_permission("integration:read"))],
)
async def list_partners(
    status: str | None = Query(None),
    tier: str | None = Query(None),
    org_type: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    manager = PartnerManager(db)
    partners = manager.list_partners(status=status, tier=tier, org_type=org_type, offset=offset, limit=limit)
    total = manager.count_partners(status=status)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "data": [p.to_dict() for p in partners],
    }


@router.get(
    "/partners/{partner_id}",
    dependencies=[Depends(require_permission("integration:read"))],
)
async def get_partner(partner_id: str, db: Session = Depends(get_db)) -> dict:
    from .partners.service import PartnerNotFoundError
    manager = PartnerManager(db)
    try:
        partner = manager.get_partner(partner_id)
        return partner.to_dict()
    except PartnerNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc


@router.put(
    "/partners/{partner_id}",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def update_partner(partner_id: str, data: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    from .partners.service import PartnerNotFoundError
    manager = PartnerManager(db)
    try:
        partner = manager.update_partner(partner_id, data)
        return partner.to_dict()
    except PartnerNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc


@router.post(
    "/partners/{partner_id}/credentials",
    dependencies=[Depends(require_permission("credential:issue"))],
)
async def issue_credential(partner_id: str, data: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    from .partners.service import PartnerNotFoundError
    credential_mgr = CredentialManager(db)
    try:
        api_key = credential_mgr.issue_api_key(
            partner_id,
            name=data.get("name", "default"),
            expires_in_days=data.get("expires_in_days"),
        )
        # API keys are write-only secrets: never expose the raw value in a
        # generic JSON response or allow it to enter proxy/access logs.
        del api_key
        return {
            "issued": True,
            "partner_id": partner_id,
            "type": "api_key",
            "delivery": "secure_out_of_band_required",
        }
    except PartnerNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc


@router.post(
    "/partners/{partner_id}/certificates",
    dependencies=[Depends(require_permission("integration:manage"))],
)
async def register_certificate(partner_id: str, data: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    from .partners.service import PartnerNotFoundError
    cert_mgr = CertificateManager(db)
    try:
        cert = cert_mgr.register_certificate(partner_id, data)
        return cert.to_dict()
    except PartnerNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Resource not found") from exc


@router.get(
    "/partners/{partner_id}/audit",
    dependencies=[Depends(require_permission("integration:audit"))],
)
async def get_partner_audit_log(
    partner_id: str,
    action: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    audit_mgr = AuditManager(db)
    logs = audit_mgr.query_logs(
        partner_id=partner_id,
        action=action,
        status=status,
        offset=offset,
        limit=limit,
    )
    return {
        "partner_id": partner_id,
        "offset": offset,
        "limit": limit,
        "redacted_fields": ["details", "ip_address", "user_agent"],
        "data": [
            {
                "id": log.id,
                "action": log.action,
                "resource": log.resource,
                "status": log.status,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
    }
