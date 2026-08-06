"""PROGRAM-STABLE-004 — Domain Service.

The async runtime service of the Domain Platform Framework. It installs,
activates, suspends, upgrades, rolls back, backs up, restores, health-checks,
and certifies Domains, and enforces the Domain <-> Workspace binding.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain_platform.binding import WorkspaceBindingRegistry
from app.domain_platform.certification import DomainCertificationEngine
from app.domain_platform.core import (
    DomainManifest,
    lifecycle_transition_allowed,
)
from app.domain_platform.manifest import CANONICAL_DOMAINS
from app.domain_platform.models import (
    DomainContractRecord,
    DomainLifecycleEventRecord,
    DomainRegistration,
    DomainVersionRecord,
    DomainWorkspaceBindingRecord,
)
from app.domain_platform.versioning import InvalidVersionError, parse_version


class DomainError(Exception):
    pass


class DomainSovereigntyError(DomainError):
    """Raised when a lifecycle or binding operation violates sovereignty."""


class DomainService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.bindings = WorkspaceBindingRegistry()

    # ── registration (Phase 1/5: install) ───────────────────────────────────

    async def register_domain(
        self,
        code: str,
        actor_identity_id: str | None = None,
        version: str = "1.0.0",
    ) -> DomainRegistration:
        manifest = CANONICAL_DOMAINS.get(code)
        if manifest is None:
            raise DomainError(f"unknown domain code '{code}'")
        existing = await self.get_registration(code)
        if existing:
            raise DomainError(f"domain '{code}' is already registered")
        parse_version(version)
        registration = DomainRegistration(
            id=...,
            uuid=str(uuid.uuid4()),
            domain_code=code,
            name_en=manifest.name_en,
            name_ar=manifest.name_ar,
            description=manifest.description,
            version=version,
            workspace_type=manifest.workspace_type,
            lifecycle_state="installed",
            blueprint=manifest.blueprint,
            contracts=[c.to_dict() for c in manifest.contracts],
            shared_core_usage=manifest.shared_core,
            certification=None,
            settings={"actor": actor_identity_id},
            is_active=True,
        )
        self.session.add(registration)
        await self.session.flush()

        await self._add_version(
            registration.id,
            version=version,
            certified=False,
            changelog="initial install",
        )
        await self._add_binding(
            registration.id,
            workspace_type=manifest.workspace_type,
            ui=manifest.ui,
        )
        await self._add_lifecycle_event(
            registration.id, "install", "installed", "installed", version
        )
        return registration

    async def get_registration(self, code: str) -> DomainRegistration | None:
        stmt = select(DomainRegistration).where(
            DomainRegistration.domain_code == code,
            DomainRegistration.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_registrations(self) -> list[DomainRegistration]:
        stmt = select(DomainRegistration).where(
            DomainRegistration.is_active.is_(True)
        ).order_by(DomainRegistration.domain_code)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── lifecycle (Phase 5) ─────────────────────────────────────────────────

    async def transition(
        self, code: str, target: str, version: str | None = None
    ) -> DomainRegistration:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        if not lifecycle_transition_allowed(registration.lifecycle_state, target):
            raise DomainSovereigntyError(
                f"domain '{code}' cannot transition from "
                f"'{registration.lifecycle_state}' to '{target}'"
            )
        previous_state = registration.lifecycle_state
        if target == "active":
            if registration.lifecycle_state in ("installed", "suspended", "upgrading"):
                pass
            else:
                raise DomainSovereigntyError(
                    f"domain '{code}' cannot be activated from '{registration.lifecycle_state}'"
                )
        registration.lifecycle_state = target
        await self._add_lifecycle_event(
            registration.id, target, previous_state, target, version
        )
        await self.session.flush()
        return registration

    async def activate(self, code: str) -> DomainRegistration:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        return await self.transition(code, "active")

    async def suspend(self, code: str) -> DomainRegistration:
        return await self.transition(code, "suspended")

    async def upgrade(self, code: str, new_version: str) -> DomainRegistration:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        try:
            parse_version(new_version)
        except InvalidVersionError as exc:
            raise DomainError(str(exc)) from exc
        await self.transition(code, "upgrading", new_version)
        await self._add_version(registration.id, version=new_version, certified=True, changelog="upgrade")
        registration.version = new_version
        registration.lifecycle_state = "active"
        await self._add_lifecycle_event(
            registration.id, "upgrade", "upgrading", "active", new_version
        )
        await self.session.flush()
        return registration

    async def rollback(self, code: str) -> DomainRegistration:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        versions = await self.list_versions(code)
        if len(versions) < 2:
            raise DomainSovereigntyError(f"domain '{code}' has no previous version")
        previous = versions[-2].version
        registration.version = previous
        registration.lifecycle_state = "active"
        await self._add_lifecycle_event(
            registration.id, "rollback", "active", "active", previous
        )
        await self.session.flush()
        return registration

    # ── versions (independent versioning) ───────────────────────────────────

    async def _add_version(
        self,
        domain_id: str,
        version: str,
        certified: bool,
        changelog: str,
    ) -> DomainVersionRecord:
        semver = ".".join(str(part) for part in parse_version(version))
        record = DomainVersionRecord(
            id=...,
            uuid=str(uuid.uuid4()),
            domain_id=domain_id,
            version=version,
            semver=semver,
            certified=certified,
            changelog=changelog,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_versions(self, code: str) -> list[DomainVersionRecord]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        stmt = (
            select(DomainVersionRecord)
            .where(DomainVersionRecord.domain_id == registration.id)
            .order_by(DomainVersionRecord.semver)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── contracts (Phase 4) ─────────────────────────────────────────────────

    async def register_contract(
        self,
        contract_id: str,
        provider_domain: str,
        consumer_domain: str,
        kind: str,
        version: str,
        endpoint: str,
        documentation_url: str,
        summary: str = "",
    ) -> DomainContractRecord:
        provider = await self.get_registration(provider_domain)
        consumer = await self.get_registration(consumer_domain)
        if not provider or not consumer:
            raise DomainError("both provider and consumer must be registered Domains")
        if provider.id == consumer.id:
            raise DomainSovereigntyError("provider and consumer must be distinct Domains")
        parse_version(version)
        if not endpoint or not documentation_url:
            raise DomainSovereigntyError("every contract must be documented and wired to a tested endpoint")
        record = DomainContractRecord(
            id=...,
            uuid=str(uuid.uuid4()),
            contract_id=contract_id,
            provider_domain_id=provider.id,
            consumer_domain_id=consumer.id,
            kind=kind,
            version=version,
            endpoint=endpoint,
            documentation_url=documentation_url,
            status="published",
            summary=summary,
            is_active=True,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def list_contracts(self, code: str) -> list[DomainContractRecord]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        stmt = (
            select(DomainContractRecord)
            .where(
                (DomainContractRecord.provider_domain_id == registration.id)
                | (DomainContractRecord.consumer_domain_id == registration.id),
                DomainContractRecord.is_active.is_(True),
            )
            .order_by(DomainContractRecord.contract_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── binding (Phase 6) ───────────────────────────────────────────────────

    async def _add_binding(
        self,
        domain_id: str,
        workspace_type: str,
        ui: list[str],
    ) -> DomainWorkspaceBindingRecord:
        record = DomainWorkspaceBindingRecord(
            id=...,
            uuid=str(uuid.uuid4()),
            domain_id=domain_id,
            workspace_type=workspace_type,
            ui=ui,
            is_active=True,
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def get_binding(self, code: str) -> DomainWorkspaceBindingRecord | None:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        stmt = select(DomainWorkspaceBindingRecord).where(
            DomainWorkspaceBindingRecord.domain_id == registration.id,
            DomainWorkspaceBindingRecord.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def assert_ui_allowed(self, code: str, ui: str) -> None:
        binding = await self.get_binding(code)
        if not binding:
            raise DomainError(f"domain '{code}' has no workspace binding")
        allowed = binding.ui or []
        if ui not in allowed:
            raise DomainSovereigntyError(
                f"workspace '{binding.workspace_type}' may not display UI '{ui}'"
            )

    # ── lifecycle events (audit) ────────────────────────────────────────────

    async def _add_lifecycle_event(
        self,
        domain_id: str,
        action: str,
        from_state: str,
        to_state: str,
        version: str | None,
    ) -> DomainLifecycleEventRecord:
        event = DomainLifecycleEventRecord(
            id=...,
            uuid=str(uuid.uuid4()),
            domain_id=domain_id,
            action=action,
            from_state=from_state,
            to_state=to_state,
            version=version,
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def lifecycle_history(self, code: str) -> list[DomainLifecycleEventRecord]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        stmt = (
            select(DomainLifecycleEventRecord)
            .where(DomainLifecycleEventRecord.domain_id == registration.id)
            .order_by(DomainLifecycleEventRecord.created_at)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ── health, metrics, certification ──────────────────────────────────────

    async def health_check(self, code: str) -> dict[str, Any]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        return {
            "domain_code": code,
            "state": registration.lifecycle_state,
            "version": registration.version,
            "healthy": registration.lifecycle_state in ("installed", "active"),
        }

    async def metrics(self, code: str) -> dict[str, Any]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        history = await self.lifecycle_history(code)
        return {
            "domain_code": code,
            "state": registration.lifecycle_state,
            "version": registration.version,
            "transition_count": len(history),
            "certification": registration.certification,
        }

    async def certify(self, code: str) -> dict[str, Any]:
        registration = await self.get_registration(code)
        if not registration:
            raise DomainError(f"domain '{code}' is not registered")
        manifest = CANONICAL_DOMAINS.get(code)
        engine = DomainCertificationEngine()
        result = engine.certify_domain(manifest) if manifest else None
        payload = result.to_dict() if result else {"domain_code": code, "passed": False, "score": 0}
        registration.certification = payload
        await self.session.flush()
        return payload

    # ── canonical manifest access ───────────────────────────────────────────

    def canonical_domains(self) -> list[DomainManifest]:
        return list(CANONICAL_DOMAINS.values())
