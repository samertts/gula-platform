from dataclasses import dataclass, field
from typing import Any


@dataclass
class Component:
    id: str = ""
    name: str = ""
    component_type: str = "module"
    current_version: str = ""
    latest_version: str = ""
    stage: str = "development"
    owner: str = ""
    description: str = ""
    repository: str = ""
    documentation_url: str = ""
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Release:
    id: str = ""
    component_id: str = ""
    version: str = ""
    channel: str = "stable"
    status: str = "draft"
    release_notes: str = ""
    changelog: str = ""
    breaking_changes: list[str] = field(default_factory=list)
    certification_level: str = ""
    approved_by: str = ""
    approved_at: str = ""
    deployed_at: str = ""
    deployed_by: str = ""
    artifact_url: str = ""
    checksum: str = ""
    sbom_url: str = ""


@dataclass
class CompatibilityEntry:
    id: str = ""
    component_a: str = ""
    component_b: str = ""
    version_a: str = ""
    version_b: str = ""
    level: str = "unknown"
    tested_at: str = ""
    notes: str = ""


@dataclass
class UpgradePath:
    id: str = ""
    component: str = ""
    from_version: str = ""
    to_version: str = ""
    severity: str = "medium"
    steps: list[dict[str, Any]] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    breaking_changes: list[str] = field(default_factory=list)
    estimated_duration_minutes: int = 0
    rollback_plan: str = ""


@dataclass
class DeprecationNotice:
    id: str = ""
    component_id: str = ""
    component_name: str = ""
    current_version: str = ""
    deprecation_policy: str = "notice_90_days"
    sunset_date: str = ""
    replacement_component: str = ""
    migration_guide: str = ""
    announced_at: str = ""
    announced_by: str = ""
    rescinded_at: str = ""
