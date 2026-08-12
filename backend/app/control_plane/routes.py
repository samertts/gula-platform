from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.control_plane.enums import (
    ComponentStatus,
    ConfigurationScope,
    PlatformComponent,
    ReleaseChannel,
)
from app.control_plane.policy.manager import Policy, PolicyDomain, PolicyEffect, PolicySeverity
from app.control_plane.registry.component import ComponentDescriptor
from app.control_plane.sdk import ControlPlaneSDK
from app.security.dependencies import get_current_user

logger = logging.getLogger("gula.control_plane.routes")

router = APIRouter(prefix="/control-plane", tags=["control-plane"])

sdk = ControlPlaneSDK.get_instance()


def _user(request_user=Depends(get_current_user)):
    return request_user


@router.get("/registry/components")
async def list_components(
    component_type: str | None = Query(None),
    user=Depends(_user),
):
    if component_type:
        try:
            ct = PlatformComponent(component_type)
            components = sdk.registry.list(ct)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid component type: {component_type}") from None
    else:
        components = sdk.registry.list()
    return {
        "components": [
            {
                "name": c.name,
                "type": c.component_type.value,
                "version": c.version,
                "status": c.status.value,
                "description": c.description,
                "owner": c.owner,
                "dependencies": c.dependencies,
            }
            for c in components
        ],
        "count": len(components),
    }


@router.post("/registry/components", status_code=201)
async def register_component(data: dict[str, Any], user=Depends(_user)):
    try:
        ct = PlatformComponent(data.get("type", "service"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid component type: {data.get('type')}") from e
    descriptor = ComponentDescriptor(
        name=data["name"],
        component_type=ct,
        version=data.get("version", "1.0.0"),
        description=data.get("description", ""),
        owner=data.get("owner", ""),
        dependencies=data.get("dependencies", []),
        health_endpoint=data.get("health_endpoint", ""),
        metadata=data.get("metadata", {}),
    )
    sdk.registry.register(descriptor)
    return {"status": "registered", "name": descriptor.name, "type": descriptor.component_type.value}


@router.put("/registry/components/{name}")
async def update_component(name: str, data: dict[str, Any], user=Depends(_user)):
    comp = sdk.registry.get(name)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component not found: {name}")
    if "status" in data:
        try:
            status = ComponentStatus(data["status"])
            sdk.registry.update_status(name, status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {data['status']}") from None
    return {"status": "updated", "name": name}


@router.delete("/registry/components/{name}")
async def unregister_component(name: str, user=Depends(_user)):
    comp = sdk.registry.get(name)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component not found: {name}")
    sdk.registry.unregister(name)
    return {"status": "unregistered", "name": name}


@router.get("/registry/topology")
async def get_topology(user=Depends(_user)):
    return sdk.topology.to_dict()


@router.get("/health")
async def control_plane_health(user=Depends(_user)):
    return await sdk.health.aggregate()


@router.get("/config/{scope}/{component}")
async def get_config(scope: str, component: str, key: str | None = Query(None), user=Depends(_user)):
    try:
        s = ConfigurationScope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}") from None
    if key:
        value = sdk.config.get(key, scope=s, component=component)
        return {"key": key, "value": value, "scope": scope, "component": component}
    return {"scope": scope, "component": component, "config": sdk.config.get_scope(s, component=component)}


@router.put("/config/{scope}/{component}")
async def set_config(scope: str, component: str, data: dict[str, Any], user=Depends(_user)):
    try:
        s = ConfigurationScope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}") from None
    for key, value in data.get("config", {}).items():
        sdk.config.set(key, value, scope=s, component=component)
    return {"status": "updated", "scope": scope, "component": component}


@router.post("/config/reload")
async def reload_config(user=Depends(_user)):
    return sdk.config.reload_config()


@router.get("/policies")
async def list_policies(domain: str | None = Query(None), user=Depends(_user)):
    domain_enum = None
    if domain:
        try:
            domain_enum = PolicyDomain(domain)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid domain: {domain}") from None
    policies = sdk.policies.list(domain_enum)
    return {
        "policies": [
            {
                "name": p.name,
                "domain": p.domain.value,
                "description": p.description,
                "effect": p.effect.value,
                "severity": p.severity.value,
                "enabled": p.enabled,
            }
            for p in policies
        ],
        "count": len(policies),
    }


@router.post("/policies")
async def create_policy(data: dict[str, Any], user=Depends(_user)):
    try:
        policy = Policy(
            name=data["name"],
            domain=PolicyDomain(data.get("domain", "security")),
            description=data.get("description", ""),
            effect=PolicyEffect(data.get("effect", "deny")),
            severity=PolicySeverity(data.get("severity", "medium")),
            conditions=data.get("conditions", {}),
            enabled=data.get("enabled", True),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid request") from e
    sdk.policies.register(policy)
    return {"status": "created", "name": policy.name, "domain": policy.domain.value}


@router.post("/policies/evaluate")
async def evaluate_policy(data: dict[str, Any], user=Depends(_user)):
    action = data.get("action", "")
    context = data.get("context", {})
    return sdk.policies.evaluate(action, context)


@router.get("/fleet/nodes")
async def list_nodes(role: str | None = Query(None), user=Depends(_user)):
    nodes = sdk.fleet.list_nodes(role)
    return {
        "nodes": [
            {
                "node_id": n.node_id,
                "hostname": n.hostname,
                "ip_address": n.ip_address,
                "role": n.role,
                "status": n.status,
                "last_heartbeat": n.last_heartbeat,
            }
            for n in nodes
        ],
        "count": len(nodes),
        "summary": sdk.fleet.summary(),
    }


@router.post("/fleet/deploy")
async def deploy_component(data: dict[str, Any], user=Depends(_user)):
    from app.control_plane.fleet.provisioning import DeploymentPlan
    plan = DeploymentPlan(
        component=data["component"],
        node_id=data.get("node_id", "default"),
        image=data.get("image", ""),
        config=data.get("config", {}),
        replicas=data.get("replicas", 1),
    )
    result = await sdk.provisioning.deploy(plan)
    return {
        "deployment_id": result.deployment_id,
        "component": result.component,
        "status": result.status,
    }


@router.get("/operations/dashboard")
async def operations_dashboard(user=Depends(_user)):
    return await sdk.operations.dashboard()


@router.get("/releases")
async def list_releases(
    component: str | None = Query(None),
    channel: str | None = Query(None),
    status: str | None = Query(None),
    user=Depends(_user),
):
    channel_enum = None
    if channel:
        try:
            channel_enum = ReleaseChannel(channel)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}") from None
    releases = sdk.releases.list_releases(component, channel_enum, status)
    return {
        "releases": [
            {
                "release_id": r.release_id,
                "name": r.name,
                "version": r.version,
                "channel": r.channel.value,
                "component": r.component,
                "status": r.status,
                "approved_by": r.approved_by,
                "deployed_by": r.deployed_by,
                "created_at": r.created_at,
                "deployed_at": r.deployed_at,
            }
            for r in releases
        ],
        "count": len(releases),
    }


@router.post("/releases")
async def create_release(data: dict[str, Any], user=Depends(_user)):
    try:
        channel = ReleaseChannel(data.get("channel", "stable"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid channel: {data.get('channel')}") from e
    release = sdk.releases.create_release(
        name=data["name"],
        version=data["version"],
        channel=channel,
        component=data.get("component", ""),
        artifacts=data.get("artifacts"),
        config=data.get("config"),
    )
    return {
        "release_id": release.release_id,
        "name": release.name,
        "version": release.version,
        "channel": release.channel.value,
        "status": release.status,
    }


@router.post("/releases/deploy")
async def deploy_release(data: dict[str, Any], user=Depends(_user)):
    release_id = data["release_id"]
    user_str = data.get("user", "unknown")
    if data.get("approve_first", False):
        approved = sdk.releases.approve(release_id, user_str)
        if not approved:
            raise HTTPException(status_code=404, detail="Release not found")
    release = await sdk.releases.deploy(release_id, user_str)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    return {
        "release_id": release.release_id,
        "status": release.status,
        "deployed_at": release.deployed_at,
    }


@router.get("/audit-log")
async def get_audit_log(
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    action: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    user=Depends(_user),
):
    if sdk.audit is None:
        return {"entries": [], "count": 0, "note": "Audit service not initialized"}
    entries = sdk.audit.query(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    return {"entries": entries, "count": len(entries)}


@router.get("/digital-twin/{component_type}")
async def get_digital_twin(component_type: str, user=Depends(_user)):
    await sdk.digital_twin.sync()
    mapping = {
        "infrastructure": lambda: sdk.digital_twin.get_infrastructure(),
        "service": lambda: sdk.digital_twin.get_by_component_type(PlatformComponent.SERVICE),
        "application": lambda: sdk.digital_twin.get_by_component_type(PlatformComponent.PROJECT),
        "operations": lambda: sdk.digital_twin.get_operations(),
        "security": lambda: sdk.digital_twin.get_security(),
    }
    handler = mapping.get(component_type)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown twin type: {component_type}")
    result = handler()
    if hasattr(result, "__dict__"):
        return vars(result)
    return result


@router.get("/kpis")
async def get_kpis(user=Depends(_user)):
    return await sdk.analytics.all_kpis()
