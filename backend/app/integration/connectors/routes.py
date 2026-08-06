from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.integration.connectors import BaseConnector, ConnectorRegistry
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.integration.connectors.routes")

router = APIRouter(
    prefix="/integration/connectors",
    tags=["integration-connectors"],
    dependencies=[Depends(get_current_user)],
)


async def _get_connector_instance(name: str, config: dict[str, Any] | None = None) -> BaseConnector:
    try:
        cls = ConnectorRegistry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Connector not found: {name}") from None
    return cls(name=name, config=config or {})


@router.get("")
async def list_connectors() -> dict[str, Any]:
    connectors = ConnectorRegistry.list_connectors()
    return {
        "connectors": connectors,
        "count": len(connectors),
    }


@router.get("/status")
async def connectors_status() -> dict[str, Any]:
    return {"connectors": ConnectorRegistry.get_status_all()}


@router.get("/{name}")
async def get_connector(name: str) -> dict[str, Any]:
    try:
        cls = ConnectorRegistry.get(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Connector not found: {name}") from None
    return {
        "name": name,
        "connector_class": cls.__name__,
        "available": True,
    }


@router.post("/{name}/connect")
async def connect_connector(name: str) -> dict[str, Any]:
    connector = await _get_connector_instance(name)
    try:
        connected = await connector.connect()
        if connected:
            return {"name": name, "connected": True}
        raise HTTPException(status_code=502, detail=f"Failed to connect {name}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream service error") from exc


@router.post("/{name}/disconnect")
async def disconnect_connector(name: str) -> dict[str, Any]:
    connector = await _get_connector_instance(name)
    try:
        disconnected = await connector.disconnect()
        return {"name": name, "disconnected": disconnected}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream service error") from exc


@router.get("/{name}/health")
async def connector_health(name: str) -> dict[str, Any]:
    connector = await _get_connector_instance(name)
    if not connector._connected:
        await connector.connect()
    try:
        health = await connector.health_check()
        return {"name": name, **health}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream service error") from exc


@router.post("/{name}/send")
async def send_through_connector(name: str, data: dict[str, Any]) -> dict[str, Any]:
    connector = await _get_connector_instance(name)
    if not connector._connected:
        await connector.connect()
    try:
        result = await connector.send(data)
        return {"name": name, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Upstream service error") from exc


@router.post("/{name}/configure")
async def configure_connector(name: str, config: dict[str, Any]) -> dict[str, Any]:
    connector = await _get_connector_instance(name, config)
    connector.config = config
    return {
        "name": name,
        "configured": True,
        "config_keys": list(config.keys()),
    }
