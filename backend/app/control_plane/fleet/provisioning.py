from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from app._compat import UTC
from app.control_plane.enums import ComponentStatus, PlatformComponent
from app.control_plane.fleet.manager import FleetManager
from app.control_plane.registry.component import ComponentDescriptor, ComponentRegistry

logger = logging.getLogger("gula.control_plane.fleet.provisioning")


@dataclass
class DeploymentPlan:
    deployment_id: str = field(default_factory=lambda: str(uuid4()))
    component: str = ""
    node_id: str = ""
    image: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    replicas: int = 1
    health_check_path: str = "/health"
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class ProvisioningEngine:
    def __init__(self, registry: ComponentRegistry, fleet: FleetManager):
        self._registry = registry
        self._fleet = fleet
        self._deployments: dict[str, DeploymentPlan] = {}

    async def deploy(self, plan: DeploymentPlan) -> DeploymentPlan:
        node = self._fleet.get_node(plan.node_id)
        if not node:
            raise ValueError(f"Node not found: {plan.node_id}")

        component = self._registry.get(plan.component)
        if not component:
            component = ComponentDescriptor(
                name=plan.component,
                component_type=PlatformComponent.SERVICE,
                version=plan.image.split(":")[-1] if ":" in plan.image else "latest",
            )
            self._registry.register(component)

        plan.status = "deploying"
        self._deployments[plan.deployment_id] = plan
        logger.info("Deploying %s to node %s (image: %s)", plan.component, plan.node_id, plan.image)

        try:
            success = await self._verify_deployment(plan)
            plan.status = "deployed" if success else "failed"
            if success:
                self._registry.update_status(plan.component, ComponentStatus.ACTIVE)
            logger.info("Deployment %s: %s", plan.deployment_id, plan.status)
        except Exception as e:
            plan.status = "failed"
            logger.error("Deployment %s failed: %s", plan.deployment_id, e)

        return plan

    async def _verify_deployment(self, plan: DeploymentPlan) -> bool:
        import asyncio

        await asyncio.sleep(0.5)
        return True

    async def rollback(self, deployment_id: str) -> bool:
        plan = self._deployments.get(deployment_id)
        if not plan:
            return False
        plan.status = "rolled_back"
        self._registry.update_status(plan.component, ComponentStatus.REGISTERED)
        logger.info("Deployment %s rolled back", deployment_id)
        return True

    def get_deployment(self, deployment_id: str) -> DeploymentPlan | None:
        return self._deployments.get(deployment_id)

    def list_deployments(self) -> list[DeploymentPlan]:
        return list(self._deployments.values())

    def summary(self) -> dict[str, Any]:
        total = len(self._deployments)
        deployed = sum(1 for d in self._deployments.values() if d.status == "deployed")
        failed = sum(1 for d in self._deployments.values() if d.status == "failed")
        return {
            "total": total,
            "deployed": deployed,
            "failed": failed,
            "pending": total - deployed - failed,
        }
