from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app._compat import UTC
from app.lifecycle_platform.domain.entities import (
    CompatibilityEntry,
    Component,
    DeprecationNotice,
    Release,
    UpgradePath,
)
from app.lifecycle_platform.exceptions import (
    ComponentNotFoundError,
    ReleaseNotFoundError,
    UpgradePathNotFoundError,
    VersionConflictError,
)
from app.lifecycle_platform.infrastructure.models import (
    CompatibilityMatrixModel,
    ComponentRegistryModel,
    DeprecationNoticeModel,
    ReleaseModel,
    UpgradePathModel,
)

logger = logging.getLogger("gula.lifecycle_platform")


class LifecycleService:
    def __init__(self, db: Session, event_bus: Any = None):
        self.db = db
        self.event_bus = event_bus

    # ── Component Registry ──

    def register_component(self, data: dict[str, Any]) -> Component:
        existing = (
            self.db.query(ComponentRegistryModel).filter_by(name=data.get("name", "")).first()
        )
        if existing:
            raise VersionConflictError(f"Component '{data.get('name')}' already registered")
        model = ComponentRegistryModel(
            **{k: v for k, v in data.items() if hasattr(ComponentRegistryModel, k)},
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._component_from_model(model)

    def get_component(self, component_id: str) -> Component:
        model = self.db.query(ComponentRegistryModel).filter_by(id=component_id).first()
        if not model or model.is_deleted:
            raise ComponentNotFoundError()
        return self._component_from_model(model)

    def find_component(self, name: str) -> Component:
        model = self.db.query(ComponentRegistryModel).filter_by(name=name).first()
        if not model or model.is_deleted:
            raise ComponentNotFoundError()
        return self._component_from_model(model)

    def list_components(
        self,
        component_type: str | None = None,
        stage: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Component]:
        query = self.db.query(ComponentRegistryModel).filter(
            ComponentRegistryModel.is_deleted.isnot(True),
        )
        if component_type:
            query = query.filter_by(component_type=component_type)
        if stage:
            query = query.filter_by(stage=stage)
        return [
            self._component_from_model(m)
            for m in query.order_by(ComponentRegistryModel.name).offset(skip).limit(limit).all()
        ]

    def update_component_stage(self, component_id: str, stage: str) -> Component:
        model = self.db.query(ComponentRegistryModel).filter_by(id=component_id).first()
        if not model:
            raise ComponentNotFoundError()
        model.stage = stage
        self.db.commit()
        self.db.refresh(model)
        return self._component_from_model(model)

    # ── Releases ──

    def create_release(self, data: dict[str, Any]) -> Release:
        model = ReleaseModel(**{k: v for k, v in data.items() if hasattr(ReleaseModel, k)})
        self.db.add(model)
        if data.get("component_id"):
            comp = self.db.query(ComponentRegistryModel).filter_by(id=data["component_id"]).first()
            if comp:
                comp.latest_version = data.get("version", comp.latest_version)
                if data.get("channel") == "stable":
                    comp.current_version = data.get("version", comp.current_version)
                self.db.commit()
        self.db.commit()
        self.db.refresh(model)
        return self._release_from_model(model)

    def get_release(self, release_id: str) -> Release:
        model = self.db.query(ReleaseModel).filter_by(id=release_id).first()
        if not model or model.is_deleted:
            raise ReleaseNotFoundError()
        return self._release_from_model(model)

    def list_releases(
        self,
        component_id: str | None = None,
        channel: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Release]:
        query = self.db.query(ReleaseModel).filter(ReleaseModel.is_deleted.isnot(True))
        if component_id:
            query = query.filter_by(component_id=component_id)
        if channel:
            query = query.filter_by(channel=channel)
        if status:
            query = query.filter_by(status=status)
        return [
            self._release_from_model(m)
            for m in query.order_by(ReleaseModel.created_at.desc()).offset(skip).limit(limit).all()
        ]

    def approve_release(self, release_id: str, data: dict[str, Any]) -> Release:
        model = self.db.query(ReleaseModel).filter_by(id=release_id).first()
        if not model:
            raise ReleaseNotFoundError()
        model.status = "approved"
        model.approved_by = data.get("approved_by", "")
        model.approved_at = datetime.now(UTC)
        model.certification_level = data.get("certification_level", "")
        self.db.commit()
        self.db.refresh(model)
        return self._release_from_model(model)

    # ── Compatibility Matrix ──

    def record_compatibility(self, data: dict[str, Any]) -> CompatibilityEntry:
        model = CompatibilityMatrixModel(
            **{k: v for k, v in data.items() if hasattr(CompatibilityMatrixModel, k)},
        )
        model.tested_at = datetime.now(UTC)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return CompatibilityEntry(
            id=model.id,
            component_a=model.component_a,
            component_b=model.component_b,
            version_a=model.version_a,
            version_b=model.version_b,
            level=model.level or "unknown",
            notes=model.notes or "",
        )

    def check_compatibility(
        self, component_a: str, component_b: str, version_a: str, version_b: str,
    ) -> CompatibilityEntry | None:
        model = (
            self.db.query(CompatibilityMatrixModel)
            .filter_by(
                component_a=component_a,
                component_b=component_b,
                version_a=version_a,
                version_b=version_b,
            )
            .first()
        )
        if not model:
            model = (
                self.db.query(CompatibilityMatrixModel)
                .filter_by(
                    component_a=component_b,
                    component_b=component_a,
                    version_a=version_b,
                    version_b=version_a,
                )
                .first()
            )
        if not model:
            return None
        return CompatibilityEntry(
            id=model.id,
            component_a=model.component_a,
            component_b=model.component_b,
            version_a=model.version_a,
            version_b=model.version_b,
            level=model.level or "unknown",
            notes=model.notes or "",
        )

    def list_compatibility_for(self, component: str, version: str) -> list[dict[str, Any]]:
        results = (
            self.db.query(CompatibilityMatrixModel)
            .filter(
                CompatibilityMatrixModel.component_a == component,
                CompatibilityMatrixModel.version_a == version,
                CompatibilityMatrixModel.is_deleted.isnot(True),
            )
            .all()
        )
        results += (
            self.db.query(CompatibilityMatrixModel)
            .filter(
                CompatibilityMatrixModel.component_b == component,
                CompatibilityMatrixModel.version_b == version,
                CompatibilityMatrixModel.is_deleted.isnot(True),
            )
            .all()
        )
        seen: set[str] = set()
        entries = []
        for r in results:
            other = r.component_b if r.component_a == component else r.component_a
            other_ver = r.version_b if r.version_a == version else r.version_a
            key = f"{other}@{other_ver}"
            if key not in seen:
                seen.add(key)
                entries.append(
                    {"component": other, "version": other_ver, "level": r.level, "notes": r.notes},
                )
        return entries

    # ── Upgrade Paths ──

    def create_upgrade_path(self, data: dict[str, Any]) -> UpgradePath:
        model = UpgradePathModel(**{k: v for k, v in data.items() if hasattr(UpgradePathModel, k)})
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._upgrade_from_model(model)

    def find_upgrade_path(self, component: str, from_version: str, to_version: str) -> UpgradePath:
        model = (
            self.db.query(UpgradePathModel)
            .filter_by(
                component=component,
                from_version=from_version,
                to_version=to_version,
            )
            .first()
        )
        if not model:
            raise UpgradePathNotFoundError()
        return self._upgrade_from_model(model)

    def list_upgrade_paths(self, component: str | None = None) -> list[UpgradePath]:
        query = self.db.query(UpgradePathModel).filter(UpgradePathModel.is_deleted.isnot(True))
        if component:
            query = query.filter_by(component=component)
        return [self._upgrade_from_model(m) for m in query.all()]

    # ── Deprecation ──

    def issue_deprecation(self, data: dict[str, Any]) -> DeprecationNotice:
        model = DeprecationNoticeModel(
            **{k: v for k, v in data.items() if hasattr(DeprecationNoticeModel, k)},
        )
        model.announced_at = datetime.now(UTC)
        self.db.add(model)
        if data.get("component_id"):
            comp = self.db.query(ComponentRegistryModel).filter_by(id=data["component_id"]).first()
            if comp:
                comp.stage = "deprecated"
                self.db.commit()
        self.db.commit()
        self.db.refresh(model)
        return self._deprecation_from_model(model)

    def list_deprecations(self, component_id: str | None = None) -> list[DeprecationNotice]:
        query = self.db.query(DeprecationNoticeModel).filter(
            DeprecationNoticeModel.rescinded_at.is_(None),
            DeprecationNoticeModel.is_deleted.isnot(True),
        )
        if component_id:
            query = query.filter_by(component_id=component_id)
        return [self._deprecation_from_model(m) for m in query.all()]

    # ── Dashboard ──

    def get_dashboard(self) -> dict[str, Any]:
        total_components = (
            self.db.query(ComponentRegistryModel)
            .filter(ComponentRegistryModel.is_deleted.isnot(True))
            .count()
        )
        stable = (
            self.db.query(ComponentRegistryModel)
            .filter_by(stage="stable", is_deleted=False)
            .count()
        )
        deprecated = (
            self.db.query(ComponentRegistryModel)
            .filter_by(stage="deprecated", is_deleted=False)
            .count()
        )
        total_releases = (
            self.db.query(ReleaseModel).filter(ReleaseModel.is_deleted.isnot(True)).count()
        )
        pending_approval = (
            self.db.query(ReleaseModel)
            .filter_by(status="pending_approval", is_deleted=False)
            .count()
        )
        compatibility_entries = (
            self.db.query(CompatibilityMatrixModel)
            .filter(CompatibilityMatrixModel.is_deleted.isnot(True))
            .count()
        )
        active_deprecations = (
            self.db.query(DeprecationNoticeModel)
            .filter(
                DeprecationNoticeModel.rescinded_at.is_(None),
                DeprecationNoticeModel.is_deleted.isnot(True),
            )
            .count()
        )
        return {
            "total_components": total_components,
            "stable_components": stable,
            "deprecated_components": deprecated,
            "total_releases": total_releases,
            "releases_pending_approval": pending_approval,
            "compatibility_entries": compatibility_entries,
            "active_deprecations": active_deprecations,
        }

    def _component_from_model(self, m: ComponentRegistryModel) -> Component:
        return Component(
            id=m.id,
            name=m.name,
            component_type=m.component_type,
            current_version=m.current_version or "",
            stage=m.stage or "development",
            owner=m.owner or "",
            description=m.description or "",
            repository=m.repository or "",
        )

    def _release_from_model(self, m: ReleaseModel) -> Release:
        return Release(
            id=m.id,
            component_id=m.component_id,
            version=m.version,
            channel=m.channel or "stable",
            status=m.status or "draft",
            release_notes=m.release_notes or "",
            certification_level=m.certification_level or "",
            approved_by=m.approved_by or "",
            deployed_by=m.deployed_by or "",
            artifact_url=m.artifact_url or "",
        )

    def _upgrade_from_model(self, m: UpgradePathModel) -> UpgradePath:
        return UpgradePath(
            id=m.id,
            component=m.component,
            from_version=m.from_version,
            to_version=m.to_version,
            severity=m.severity or "medium",
            estimated_duration_minutes=m.estimated_duration_minutes or 0,
        )

    def _deprecation_from_model(self, m: DeprecationNoticeModel) -> DeprecationNotice:
        return DeprecationNotice(
            id=m.id,
            component_id=m.component_id,
            component_name=m.component_name or "",
            deprecation_policy=m.deprecation_policy or "notice_90_days",
            replacement_component=m.replacement_component or "",
            migration_guide=m.migration_guide or "",
            announced_by=m.announced_by or "",
        )
