from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.models.niam_organization import NIAMOrganization
from app.identity.models.person import Person


async def seed_master_admin(session: AsyncSession) -> str:
    admin_id = str(uuid.uuid4())
    admin = Person(
        id=admin_id,
        given_name="Master",
        family_name="Admin",
        full_name_ar="مدير النظام",
        email="admin@niam.gula.iq",
        is_active=True,
    )
    session.add(admin)
    await session.flush()
    return admin.id


async def seed_platform_organization(session: AsyncSession) -> str:
    org_id = str(uuid.uuid4())
    org = NIAMOrganization(
        id=org_id,
        org_id="GULA-PLATFORM",
        name_en="GULA National Digital Health Platform",
        name_ar="منصة جولا الوطنية للصحة الرقمية",
        org_type="ministry",
        status="active",
        is_active=True,
    )
    session.add(org)
    await session.flush()
    return org.id
