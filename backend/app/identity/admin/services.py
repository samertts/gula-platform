from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.admin.models import (
    EnterprisePortal,
    FHIRConnection,
    PortalAuditLog,
    PortalBranch,
    PortalDepartment,
    PortalFacility,
    PortalSubscription,
)
from app.identity.base import _ulid
from app.identity.repositories.base import IdentityRepositoryBase


class _AdminRepository(IdentityRepositoryBase[EnterprisePortal]):
    model_class = EnterprisePortal


class EnterprisePortalService:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # --- Portals ---

    async def create_portal(
        self,
        org_id: str,
        name: str,
        portal_type: str,
        features: dict[str, Any] | None,
        created_by: str,
    ) -> EnterprisePortal:
        portal = EnterprisePortal(
            uuid=_ulid(),
            portal_id=_ulid(),
            organization_id=org_id,
            name=name,
            portal_type=portal_type,
            features=features,
            status="active",
            created_by=created_by,
            activated_at=datetime.now(UTC),
            is_active=True,
        )
        self.session.add(portal)
        await self.session.flush()
        return portal

    async def get_portal(self, portal_id: str) -> EnterprisePortal | None:
        stmt = select(EnterprisePortal).where(
            EnterprisePortal.portal_id == portal_id,
            EnterprisePortal.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_portals_for_org(self, org_id: str) -> list[EnterprisePortal]:
        stmt = (
            select(EnterprisePortal)
            .where(
                EnterprisePortal.organization_id == org_id,
                EnterprisePortal.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Branches ---

    async def add_branch(
        self,
        portal_id: str,
        org_id: str,
        name_en: str,
        name_ar: str,
        address: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        manager_person_id: str | None = None,
    ) -> PortalBranch:
        branch = PortalBranch(
            uuid=_ulid(),
            branch_id=_ulid(),
            portal_id=portal_id,
            organization_id=org_id,
            name_en=name_en,
            name_ar=name_ar,
            address=address,
            phone=phone,
            email=email,
            manager_person_id=manager_person_id,
            status="active",
            is_active=True,
        )
        self.session.add(branch)
        await self.session.flush()
        return branch

    # --- Facilities ---

    async def add_facility(
        self,
        branch_id: str,
        org_id: str,
        name_en: str,
        name_ar: str,
        facility_type: str,
        license_number: str | None = None,
        accreditation: str | None = None,
        contact: dict[str, Any] | None = None,
        address: str | None = None,
    ) -> PortalFacility:
        facility = PortalFacility(
            uuid=_ulid(),
            facility_id=_ulid(),
            branch_id=branch_id,
            organization_id=org_id,
            name_en=name_en,
            name_ar=name_ar,
            facility_type=facility_type,
            license_number=license_number,
            accreditation=accreditation,
            status="active",
            contact=contact,
            address=address,
            is_active=True,
        )
        self.session.add(facility)
        await self.session.flush()
        return facility

    # --- Departments ---

    async def add_department(
        self,
        facility_id: str,
        name_en: str,
        name_ar: str,
        dept_type: str | None = None,
        head_person_id: str | None = None,
    ) -> PortalDepartment:
        dept = PortalDepartment(
            uuid=_ulid(),
            dept_id=_ulid(),
            facility_id=facility_id,
            name_en=name_en,
            name_ar=name_ar,
            dept_type=dept_type,
            head_person_id=head_person_id,
            status="active",
            is_active=True,
        )
        self.session.add(dept)
        await self.session.flush()
        return dept

    # --- Subscriptions ---

    async def manage_subscription(
        self,
        org_id: str,
        plan_type: str,
        features: dict[str, Any] | None = None,
        user_limit: int | None = None,
        storage_limit: int | None = None,
        api_call_limit: int | None = None,
        start_date: datetime | None = None,
        renewal_date: datetime | None = None,
        expiry_date: datetime | None = None,
        billing_cycle: str | None = None,
        billing_amount: int | None = None,
        currency: str = "IQD",
        payment_method: str | None = None,
        auto_renew: bool = False,
    ) -> PortalSubscription:
        stmt = (
            select(PortalSubscription)
            .where(
                PortalSubscription.organization_id == org_id,
                PortalSubscription.is_active.is_(True),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.plan_type = plan_type
            existing.features = features
            existing.user_limit = user_limit
            existing.storage_limit = storage_limit
            existing.api_call_limit = api_call_limit
            existing.start_date = start_date or existing.start_date
            existing.renewal_date = renewal_date
            existing.expiry_date = expiry_date
            existing.billing_cycle = billing_cycle
            existing.billing_amount = billing_amount
            existing.currency = currency
            existing.payment_method = payment_method
            existing.auto_renew = auto_renew
            await self.session.flush()
            return existing

        sub = PortalSubscription(
            uuid=_ulid(),
            sub_id=_ulid(),
            organization_id=org_id,
            plan_type=plan_type,
            features=features,
            user_limit=user_limit,
            storage_limit=storage_limit,
            api_call_limit=api_call_limit,
            start_date=start_date or datetime.now(UTC),
            renewal_date=renewal_date,
            expiry_date=expiry_date,
            status="active",
            billing_cycle=billing_cycle,
            billing_amount=billing_amount,
            currency=currency,
            payment_method=payment_method,
            auto_renew=auto_renew,
            is_active=True,
        )
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def get_subscription(self, org_id: str) -> PortalSubscription | None:
        stmt = (
            select(PortalSubscription)
            .where(
                PortalSubscription.organization_id == org_id,
                PortalSubscription.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_subscription(self, sub_id: str, **kwargs: Any) -> PortalSubscription | None:
        stmt = select(PortalSubscription).where(
            PortalSubscription.sub_id == sub_id,
            PortalSubscription.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        sub = result.scalar_one_or_none()
        if not sub:
            return None
        for key, value in kwargs.items():
            if hasattr(sub, key):
                setattr(sub, key, value)
        await self.session.flush()
        return sub

    # --- FHIR Connections ---

    async def create_fhir_connection(
        self,
        org_id: str,
        name: str,
        fhir_version: str,
        base_url: str,
        auth_type: str,
        credentials_encrypted: str | None = None,
    ) -> FHIRConnection:
        conn = FHIRConnection(
            uuid=_ulid(),
            conn_id=_ulid(),
            organization_id=org_id,
            name=name,
            fhir_version=fhir_version,
            base_url=base_url,
            auth_type=auth_type,
            credentials_encrypted=credentials_encrypted,
            status="inactive",
            is_active=True,
        )
        self.session.add(conn)
        await self.session.flush()
        return conn

    async def get_fhir_connections_for_org(self, org_id: str) -> list[FHIRConnection]:
        stmt = (
            select(FHIRConnection)
            .where(
                FHIRConnection.organization_id == org_id,
                FHIRConnection.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def test_fhir_connection(self, conn_id: str) -> dict[str, Any]:
        stmt = select(FHIRConnection).where(
            FHIRConnection.conn_id == conn_id,
            FHIRConnection.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        conn = result.scalar_one_or_none()
        if not conn:
            return {"success": False, "error": "connection_not_found"}

        import httpx

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers: dict[str, str] = {"Accept": "application/fhir+json"}
                if conn.auth_type == "bearer" and conn.credentials_encrypted:
                    headers["Authorization"] = f"Bearer {conn.credentials_encrypted}"
                resp = await client.get(conn.base_url.rstrip("/") + "/metadata", headers=headers)
                success = resp.is_success
                conn.last_test_at = datetime.now(UTC)
                conn.last_test_result = "success" if success else f"HTTP {resp.status_code}"
                conn.status = "active" if success else "error"
                await self.session.flush()
                return {
                    "success": success,
                    "status_code": resp.status_code,
                    "result": conn.last_test_result,
                }
        except Exception as exc:
            conn.last_test_at = datetime.now(UTC)
            conn.last_test_result = f"error: {exc}"
            conn.status = "error"
            await self.session.flush()
            return {"success": False, "error": str(exc)}

    # --- Audit Log ---

    async def log_audit_event(
        self,
        org_id: str,
        action: str,
        performed_by: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        outcome: str | None = None,
        portal_id: str | None = None,
    ) -> PortalAuditLog:
        entry = PortalAuditLog(
            uuid=_ulid(),
            log_id=_ulid(),
            organization_id=org_id,
            portal_id=portal_id,
            action=action,
            performed_by=performed_by,
            target_type=target_type,
            target_id=target_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.now(UTC),
            outcome=outcome,
            is_active=True,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def get_audit_log(self, org_id: str, limit: int = 100) -> list[PortalAuditLog]:
        stmt = (
            select(PortalAuditLog)
            .where(
                PortalAuditLog.organization_id == org_id,
                PortalAuditLog.is_active.is_(True),
            )
            .order_by(PortalAuditLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
