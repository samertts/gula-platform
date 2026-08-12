from __future__ import annotations

from app._compat import StrEnum


class PlatformComponent(StrEnum):
    PROJECT = "project"
    APP = "app"
    SERVICE = "service"
    MODULE = "module"
    PLUGIN = "plugin"
    WORKER = "worker"
    AGENT = "agent"
    API = "api"
    DB = "db"
    QUEUE = "queue"
    EVENT = "event"
    FHIR_RESOURCE = "fhir_resource"


class ComponentStatus(StrEnum):
    REGISTERED = "registered"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class TenantLevel(StrEnum):
    NATIONAL = "national"
    MINISTRY = "ministry"
    DIRECTORATE = "directorate"
    HOSPITAL = "hospital"
    LABORATORY = "laboratory"
    DEPARTMENT = "department"


class ReleaseChannel(StrEnum):
    STABLE = "stable"
    BETA = "beta"
    CANARY = "canary"
    EXPERIMENTAL = "experimental"


class ConfigurationScope(StrEnum):
    GLOBAL = "global"
    TENANT = "tenant"
    COMPONENT = "component"
    ENVIRONMENT = "environment"
