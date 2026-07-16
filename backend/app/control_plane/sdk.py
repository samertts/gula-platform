from __future__ import annotations

import logging

from app.control_plane.analytics import EnterpriseAnalytics
from app.control_plane.audit import EnterpriseAudit
from app.control_plane.config.features import FeatureManager
from app.control_plane.config.manager import CentralConfigManager
from app.control_plane.config.secrets import SecretsManager
from app.control_plane.digital_twin.engine import DigitalTwinEngine
from app.control_plane.fleet.manager import FleetManager
from app.control_plane.fleet.provisioning import ProvisioningEngine
from app.control_plane.multi_tenant import MultiTenantController
from app.control_plane.operations.automation import AutonomousOperations
from app.control_plane.operations.center import OperationsCenter
from app.control_plane.policy.enforcer import PolicyEnforcer
from app.control_plane.policy.manager import PolicyManager
from app.control_plane.registry.component import ComponentRegistry
from app.control_plane.registry.health import HealthAggregator
from app.control_plane.registry.topology import TopologyManager
from app.control_plane.release.manager import ReleaseManager
from app.control_plane.service_manager import ServiceManager

logger = logging.getLogger("gula.control_plane.sdk")


class ControlPlaneSDK:
    _instance: ControlPlaneSDK | None = None

    def __init__(self):
        if ControlPlaneSDK._instance is not None:
            raise RuntimeError("ControlPlaneSDK is a singleton.")
        self._registry = ComponentRegistry.get_instance()
        self._topology = TopologyManager(self._registry)
        self._health = HealthAggregator(self._registry)
        self._fleet = FleetManager.get_instance()
        self._provisioning = ProvisioningEngine(self._registry, self._fleet)
        self._config = CentralConfigManager()
        self._secrets = SecretsManager()
        self._features = FeatureManager()
        self._policies = PolicyManager()
        self._enforcer = PolicyEnforcer(self._policies)
        self._releases = ReleaseManager()
        self._tenants = MultiTenantController.get_instance()
        self._services = ServiceManager.get_instance()
        self._operations = OperationsCenter(self._registry, self._health)
        self._automation = AutonomousOperations(self._registry)
        self._digital_twin = DigitalTwinEngine(self._registry, self._fleet, self._health)
        self._analytics = EnterpriseAnalytics(self._registry, self._health)
        self._audit: EnterpriseAudit | None = None
        ControlPlaneSDK._instance = self
        logger.info("ControlPlaneSDK initialized")

    @classmethod
    def get_instance(cls) -> ControlPlaneSDK:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_audit(self, audit: EnterpriseAudit) -> None:
        self._audit = audit

    @property
    def registry(self) -> ComponentRegistry:
        return self._registry

    @property
    def topology(self) -> TopologyManager:
        return self._topology

    @property
    def health(self) -> HealthAggregator:
        return self._health

    @property
    def fleet(self) -> FleetManager:
        return self._fleet

    @property
    def provisioning(self) -> ProvisioningEngine:
        return self._provisioning

    @property
    def config(self) -> CentralConfigManager:
        return self._config

    @property
    def secrets(self) -> SecretsManager:
        return self._secrets

    @property
    def features(self) -> FeatureManager:
        return self._features

    @property
    def policies(self) -> PolicyManager:
        return self._policies

    @property
    def enforcer(self) -> PolicyEnforcer:
        return self._enforcer

    @property
    def releases(self) -> ReleaseManager:
        return self._releases

    @property
    def tenants(self) -> MultiTenantController:
        return self._tenants

    @property
    def services(self) -> ServiceManager:
        return self._services

    @property
    def operations(self) -> OperationsCenter:
        return self._operations

    @property
    def automation(self) -> AutonomousOperations:
        return self._automation

    @property
    def digital_twin(self) -> DigitalTwinEngine:
        return self._digital_twin

    @property
    def analytics(self) -> EnterpriseAnalytics:
        return self._analytics

    @property
    def audit(self) -> EnterpriseAudit | None:
        return self._audit
