from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends, HTTPException

from app.security.dependencies import require_permission

from .policies import GatewayPolicyEngine, PolicyDecision

logger = logging.getLogger("gula.ecosystem.gateway")

router = APIRouter(
    prefix="/gateway",
    tags=["API Gateway"],
    dependencies=[Depends(require_permission("system:admin"))],
)

_engine = GatewayPolicyEngine()


@router.post("/route")
async def route_request(request: dict = Body(...)) -> dict:
    result = _engine.evaluate(request)
    if result.decision == PolicyDecision.DENY:
        raise HTTPException(status_code=403, detail={"error": result.reason, "policy": result.policy_name})
    return {"decision": result.decision.value, "policy": result.policy_name, "message": result.reason}


@router.get("/status")
async def gateway_status() -> dict:
    return {
        "status": "active",
        "policies": len(_engine.list_policies()),
        "routes": len(_engine.list_routes()),
    }


@router.get("/policies")
async def list_policies() -> list[dict]:
    return _engine.list_policies()


@router.post("/policies")
async def create_policy(policy_data: dict = Body(...)) -> dict:
    from .policies import (
        APIKeyPolicy,
        IPBlacklistPolicy,
        IPWhitelistPolicy,
        OAuth2Policy,
        QuotaPolicy,
        RateLimitPolicy,
        TimeRestrictionPolicy,
        mTLSPolicy,
    )

    policy_type = policy_data.get("type", "")
    name = policy_data.get("name", policy_type)
    policy_map = {
        "rate_limit": RateLimitPolicy,
        "quota": QuotaPolicy,
        "ip_whitelist": IPWhitelistPolicy,
        "ip_blacklist": IPBlacklistPolicy,
        "time_restriction": TimeRestrictionPolicy,
        "oauth2": OAuth2Policy,
        "mtls": mTLSPolicy,
        "api_key": APIKeyPolicy,
    }

    policy_class = policy_map.get(policy_type)
    if not policy_class:
        raise HTTPException(status_code=400, detail=f"unknown policy type: {policy_type}")

    policy = policy_class(name=name)

    config = policy_data.get("config", {})
    if isinstance(config, dict):
        for key, value in config.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

    _engine.register_policy(policy)
    return {"name": name, "type": policy_type, "status": "created"}


@router.put("/policies/{policy_id}")
async def update_policy(policy_id: str, policy_data: dict = Body(...)) -> dict:
    policy = _engine.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"policy not found: {policy_id}")

    config = policy_data.get("config", {})
    if isinstance(config, dict):
        for key, value in config.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
    return {"name": policy_id, "status": "updated"}


@router.delete("/policies/{policy_id}")
async def delete_policy(policy_id: str) -> dict:
    policy = _engine.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail=f"policy not found: {policy_id}")
    _engine.unregister_policy(policy_id)
    return {"name": policy_id, "status": "deleted"}


@router.get("/catalog")
async def list_api_catalog() -> list[dict]:
    return _engine.list_routes()


@router.post("/catalog")
async def register_api(api_data: dict = Body(...)) -> dict:
    method = api_data.get("method", "GET").upper()
    path = api_data.get("path", "")
    config = api_data.get("config", {})
    if not path:
        raise HTTPException(status_code=400, detail="path is required")
    _engine.register_route(method, path, config)
    return {"method": method, "path": path, "status": "registered"}
