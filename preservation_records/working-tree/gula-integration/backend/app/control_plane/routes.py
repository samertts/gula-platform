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
from app.control_plane.release.manager import ReleaseStatus
from app.control_plane.sdk import ControlPlaneSDK
from app.security.dependencies import get_current_user
from app.security.rbac import require_role

logger = logging.getLogger("gula.control_plane.routes")

router = APIRouter(prefix="/control-plane", tags=["control-plane"])

sdk = ControlPlaneSDK.get_instance()

# The control plane is a platform-operator surface, not a clinical one.
# Authorization policy (S-01):
#   * reads  → national oversight + platform operator
#   * writes → platform operator only
# Authentication is provided by ``get_current_user``; these dependencies add the
# explicit authorization that used to be missing.
_PLATFORM_READ_ROLES = ("master_admin", "ministry_admin")
_PLATFORM_WRITE_ROLES = ("master_admin",)

_READ_ACCESS = Depends(require_role(*_PLATFORM_READ_ROLES))
_WRITE_ACCESS = Depends(require_role(*_PLATFORM_WRITE_ROLES))


def _user(request_user=Depends(get_current_user)):
    return request_user


def _actor_identity(user) -> str:
    """Server-derived operator identity for release approval/deployment.

    Never trust a caller-supplied ``user`` field: the audit-relevant identity
    comes from the authenticated principal resolved by ``get_current_user``.
    """
    email = getattr(user, "email", None)
    if email:
        return str(email)
    return f"user:{getattr(user, 'id', 'unknown')}"


@router.get("/registry/components", dependencies=[_READ_ACCESS])
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


@router.post("/registry/components", status_code=201, dependencies=[_WRITE_ACCESS])
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


@router.put("/registry/components/{name}", dependencies=[_WRITE_ACCESS])
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


@router.delete("/registry/components/{name}", dependencies=[_WRITE_ACCESS])
async def unregister_component(name: str, user=Depends(_user)):
    comp = sdk.registry.get(name)
    if not comp:
        raise HTTPException(status_code=404, detail=f"Component not found: {name}")
    sdk.registry.unregister(name)
    return {"status": "unregistered", "name": name}


@router.get("/registry/topology", dependencies=[_READ_ACCESS])
async def get_topology(user=Depends(_user)):
    return sdk.topology.to_dict()


@router.get("/health", dependencies=[_READ_ACCESS])
async def control_plane_health(user=Depends(_user)):
    return await sdk.health.aggregate()


@router.get("/config/{scope}/{component}", dependencies=[_READ_ACCESS])
async def get_config(scope: str, component: str, key: str | None = Query(None), user=Depends(_user)):
    try:
        s = ConfigurationScope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}") from None
    if key:
        value = sdk.config.get(key, scope=s, component=component)
        return {"key": key, "value": value, "scope": scope, "component": component}
    return {"scope": scope, "component": component, "config": sdk.config.get_scope(s, component=component)}


@router.put("/config/{scope}/{component}", dependencies=[_WRITE_ACCESS])
async def set_config(scope: str, component: str, data: dict[str, Any], user=Depends(_user)):
    try:
        s = ConfigurationScope(scope)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid scope: {scope}") from None
    for key, value in data.get("config", {}).items():
        sdk.config.set(key, value, scope=s, component=component)
    return {"status": "updated", "scope": scope, "component": component}


@router.post("/config/reload", dependencies=[_WRITE_ACCESS])
async def reload_config(user=Depends(_user)):
    return sdk.config.reload_config()


@router.get("/policies", dependencies=[_READ_ACCESS])
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


@router.post("/policies", dependencies=[_WRITE_ACCESS])
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


@router.post("/policies/evaluate", dependencies=[_READ_ACCESS])
async def evaluate_policy(data: dict[str, Any], user=Depends(_user)):
    action = data.get("action", "")
    context = data.get("context", {})
    return sdk.policies.evaluate(action, context)


@router.get("/fleet/nodes", dependencies=[_READ_ACCESS])
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


@router.post("/fleet/deploy", dependencies=[_WRITE_ACCESS])
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


@router.get("/operations/dashboard", dependencies=[_READ_ACCESS])
async def operations_dashboard(user=Depends(_user)):
    return await sdk.operations.dashboard()


@router.get("/releases", dependencies=[_READ_ACCESS])
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


@router.post("/releases", dependencies=[_WRITE_ACCESS])
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


@router.post("/releases/{release_id}/approve", dependencies=[_WRITE_ACCESS])
async def approve_release(release_id: str, user=Depends(_user)):
    """Record an independent approval for a pending release.

    The approver identity is taken from the authenticated principal — never
    from the request body. A release that has already entered or passed the
    deployment stage cannot be re-approved.
    """
    release = sdk.releases.get(release_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release.status in (
        ReleaseStatus.DEPLOYING,
        ReleaseStatus.DEPLOYED,
        ReleaseStatus.ROLLING_BACK,
        ReleaseStatus.ROLLED_BACK,
    ):
        raise HTTPException(
            status_code=409,
            detail="Release is already past the approval stage",
        )
    actor = _actor_identity(user)
    approved = sdk.releases.approve(release_id, actor)
    if not approved:
        raise HTTPException(status_code=404, detail="Release not found")
    return {
        "release_id": approved.release_id,
        "status": approved.status,
        "approved_by": approved.approved_by,
    }


@router.post("/releases/deploy", dependencies=[_WRITE_ACCESS])
async def deploy_release(data: dict[str, Any], user=Depends(_user)):
    """Deploy an approved release under a two-person rule.

    Security model (S-02):
      * caller-supplied ``user`` / ``approve_first`` are rejected — approval and
        deployment identities are always derived from the authenticated actor;
      * the release must be in ``approved`` state (approval is a separate,
        explicit step: ``POST /releases/{id}/approve``);
      * the approver and the deployer must be different principals.
    """
    for caller_field in ("user", "approve_first", "approved_by", "deployed_by"):
        if caller_field in data:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"'{caller_field}' must not be supplied by the caller; "
                    "actor identity and approval are derived server-side"
                ),
            )
    release_id = data.get("release_id")
    if not release_id:
        raise HTTPException(status_code=400, detail="'release_id' is required")

    actor = _actor_identity(user)
    release = sdk.releases.get(release_id)
    if not release:
        raise HTTPException(status_code=404, detail="Release not found")
    if release.status != ReleaseStatus.APPROVED:
        raise HTTPException(
            status_code=409,
            detail="Release must be approved before deployment",
        )
    if not release.approved_by or release.approved_by == actor:
        raise HTTPException(
            status_code=409,
            detail="Release must be approved by a different operator (two-person rule)",
        )

    try:
        deployed = await sdk.releases.deploy(release_id, actor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deployed:
        raise HTTPException(status_code=404, detail="Release not found")
    return {
        "release_id": deployed.release_id,
        "status": deployed.status,
        "approved_by": deployed.approved_by,
        "deployed_by": deployed.deployed_by,
        "deployed_at": deployed.deployed_at,
    }


@router.get("/audit-log", dependencies=[_READ_ACCESS])
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


@router.get("/digital-twin/{component_type}", dependencies=[_READ_ACCESS])
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


@router.get("/kpis", dependencies=[_READ_ACCESS])
async def get_kpis(user=Depends(_user)):
    return await sdk.analytics.all_kpis()
