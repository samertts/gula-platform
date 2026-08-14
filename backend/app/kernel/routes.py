from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.kernel.integration import (
    get_kernel,
    get_kernel_health,
    is_kernel_ready,
    kernel_kill_switch_active,
)
from app.security.dependencies import require_permission

router = APIRouter(
    prefix="/kernel",
    tags=["kernel"],
    dependencies=[Depends(require_permission("system:admin"))],
)


@router.get("/status")
async def kernel_status(_user=Depends(require_permission("system:admin"))):
    return await get_kernel_health()


@router.get("/services")
async def kernel_services(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    sr = kernel.get_component("service_registry")
    if not sr:
        return {"services": []}
    services = []
    for name in sr.list_services():
        services.append({"name": name, "metadata": sr.get_metadata(name)})
    return {"services": services, "count": len(services)}


@router.get("/capabilities")
async def kernel_capabilities(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    cr = kernel.get_component("capability_registry")
    if not cr:
        return {"capabilities": []}
    caps = []
    for c in cr.list_capabilities():
        caps.append(
            {
                "name": c.name,
                "version": c.version,
                "enabled": c.enabled,
                "description": c.description,
            },
        )
    return {"capabilities": caps, "count": len(caps)}


@router.get("/plugins")
async def kernel_plugins(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    pm = kernel.get_component("plugin_manager")
    if not pm:
        return {"plugins": [], "count": 0}
    plugins = []
    for p in pm.list_plugins():
        plugins.append({"name": p.name, "version": p.version, "enabled": p.enabled, "path": p.path})
    return {"plugins": plugins, "count": len(plugins)}


@router.get("/modules")
async def kernel_modules(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    ml = kernel.get_component("module_loader")
    if not ml:
        return {"modules": [], "count": 0}
    modules = []
    for m in ml.list_modules():
        modules.append({"name": m.name, "version": m.version, "enabled": m.enabled, "path": m.path})
    return {"modules": modules, "count": len(modules)}


@router.get("/config")
async def kernel_config(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    return {
        "name": kernel.config.name,
        "version": kernel.config.version,
        "environment": kernel.config.environment,
        "debug": kernel.config.debug,
        "boot_timeout": kernel.config.boot_timeout,
        "shutdown_timeout": kernel.config.shutdown_timeout,
        "subsystems": {
            "plugins": kernel.config.enable_plugins,
            "event_bus": kernel.config.enable_event_bus,
            "background_processing": kernel.config.enable_background_processing,
            "feature_management": kernel.config.enable_feature_management,
            "config_engine": kernel.config.enable_config_engine,
            "multi_tenant": kernel.config.enable_multi_tenant,
            "internal_gateway": kernel.config.enable_internal_gateway,
        },
    }


@router.get("/events/outbox")
async def kernel_outbox(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    eb = kernel.get_component("event_bus")
    if not eb:
        return {"pending": 0}
    pending = len(eb.outbox.list_pending())
    return {"pending": pending}


@router.get("/events/dlq")
async def kernel_dead_letter_queue(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    eb = kernel.get_component("event_bus")
    if not eb:
        return {"entries": [], "count": 0}
    entries = []
    for entry in eb.dead_letter_queue.list_all():
        entries.append(
            {"event_id": entry.event.id, "event_name": entry.event.name, "reason": entry.reason},
        )
    return {"entries": entries, "count": len(entries)}


@router.get("/tenants")
async def kernel_tenants(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    tr = kernel.get_component("tenant_registry")
    if not tr:
        return {"tenants": [], "count": 0}
    tenants = []
    for t in tr.list_tenants():
        tenants.append(
            {"id": t.id, "name": t.name, "slug": t.slug, "plan": t.plan, "active": t.active},
        )
    return {"tenants": tenants, "count": len(tenants)}


@router.get("/locks")
async def kernel_locks(_user=Depends(require_permission("system:admin"))):
    if not is_kernel_ready():
        raise HTTPException(status_code=503, detail="Kernel not ready")
    kernel = get_kernel()
    scheduler = kernel.get_component("scheduler")
    if not scheduler:
        return {"locks": []}
    return {"locks": []}


@router.get("/kill-switch")
async def kernel_kill_switch(_user=Depends(require_permission("system:admin"))):
    return {"active": kernel_kill_switch_active()}
