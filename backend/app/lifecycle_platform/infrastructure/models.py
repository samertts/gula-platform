from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text

from app.national.base import AuditEntity


class ComponentRegistryModel(AuditEntity):
    __tablename__ = "lc_component_registry"

    name = Column(String(200), nullable=False, unique=True)
    component_type = Column(String(50), nullable=False)
    current_version = Column(String(50), nullable=True)
    latest_version = Column(String(50), nullable=True)
    stage = Column(String(50), default="development")
    owner = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    repository = Column(String(500), nullable=True)
    documentation_url = Column(String(500), nullable=True)
    dependencies = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)


class ReleaseModel(AuditEntity):
    __tablename__ = "lc_releases"

    component_id = Column(
        String(26), ForeignKey("lc_component_registry.id"), nullable=False, index=True,
    )
    version = Column(String(50), nullable=False)
    channel = Column(String(50), default="stable")
    status = Column(String(50), default="draft")
    release_notes = Column(Text, nullable=True)
    changelog = Column(Text, nullable=True)
    breaking_changes = Column(JSON, nullable=True)
    certification_level = Column(String(50), nullable=True)
    approved_by = Column(String(200), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    deployed_by = Column(String(200), nullable=True)
    artifact_url = Column(String(500), nullable=True)
    checksum = Column(String(128), nullable=True)
    sbom_url = Column(String(500), nullable=True)


class CompatibilityMatrixModel(AuditEntity):
    __tablename__ = "lc_compatibility_matrix"

    component_a = Column(String(200), nullable=False)
    component_b = Column(String(200), nullable=False)
    version_a = Column(String(50), nullable=False)
    version_b = Column(String(50), nullable=False)
    level = Column(String(50), default="unknown")
    tested_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)


class UpgradePathModel(AuditEntity):
    __tablename__ = "lc_upgrade_paths"

    component = Column(String(200), nullable=False)
    from_version = Column(String(50), nullable=False)
    to_version = Column(String(50), nullable=False)
    severity = Column(String(50), default="medium")
    steps = Column(JSON, nullable=True)
    prerequisites = Column(JSON, nullable=True)
    breaking_changes = Column(JSON, nullable=True)
    estimated_duration_minutes = Column(Integer, default=0)
    rollback_plan = Column(Text, nullable=True)


class DeprecationNoticeModel(AuditEntity):
    __tablename__ = "lc_deprecation_notices"

    component_id = Column(
        String(26), ForeignKey("lc_component_registry.id"), nullable=False, index=True,
    )
    component_name = Column(String(200), nullable=True)
    current_version = Column(String(50), nullable=True)
    deprecation_policy = Column(String(50), default="notice_90_days")
    sunset_date = Column(DateTime(timezone=True), nullable=True)
    replacement_component = Column(String(200), nullable=True)
    migration_guide = Column(Text, nullable=True)
    announced_at = Column(DateTime(timezone=True), nullable=True)
    announced_by = Column(String(200), nullable=True)
    rescinded_at = Column(DateTime(timezone=True), nullable=True)
