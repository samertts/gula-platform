from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.api.workspaces import NiamActor
from app.identity.models.audit import AuditAction
from app.identity.models.device import Device
from app.identity.models.identity import IdentityRecord
from app.identity.models.person import Person
from app.identity.services.audit_service import AuditService


async def record_authorization_denial(
    db: AsyncSession,
    actor: NiamActor,
    *,
    target_type: str,
    target_id: str | None,
    reason: str,
) -> None:
    """Record a bounded authorization denial before returning a client error."""
    await AuditService(db).record_event(
        AuditAction.authz_cross_tenant_attempt.value,
        actor_id=actor.account.id,
        target_type=target_type,
        target_id=target_id,
        metadata={"reason": reason},
        outcome="denied",
    )


async def require_account_scope(
    db: AsyncSession,
    actor: NiamActor,
    requested_account_id: str,
    *,
    target_type: str = "account",
) -> str:
    """Resolve an external account identifier to the authenticated account id."""
    if requested_account_id in {actor.account.id, actor.account.uuid}:
        return actor.account.id

    await record_authorization_denial(
        db,
        actor,
        target_type=target_type,
        target_id=requested_account_id,
        reason="account_scope_mismatch",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to this account is not permitted",
    )


async def resolve_actor_person(
    db: AsyncSession,
    actor: NiamActor,
) -> Person | None:
    """Return the active Person behind the authenticated NIAM identity."""
    stmt = (
        select(Person)
        .join(IdentityRecord, IdentityRecord.person_id == Person.id)
        .where(
            IdentityRecord.id == actor.account.identity_id,
            IdentityRecord.is_active.is_(True),
            Person.is_active.is_(True),
        )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def require_actor_person(
    db: AsyncSession,
    actor: NiamActor,
    person_uuid: str,
    *,
    target_type: str = "person",
) -> Person:
    """Resolve a person only when it belongs to the authenticated identity."""
    person = await resolve_actor_person(db, actor)
    if person is not None and person.uuid == person_uuid:
        return person

    await record_authorization_denial(
        db,
        actor,
        target_type=target_type,
        target_id=person_uuid,
        reason="person_scope_mismatch",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to this person is not permitted",
    )


async def require_actor_device(
    db: AsyncSession,
    actor: NiamActor,
    device_uuid: str,
) -> Device:
    """Resolve an active device owned by the account or its identity person."""
    person = await resolve_actor_person(db, actor)
    person_id = person.id if person is not None else None
    stmt = select(Device).where(
        Device.uuid == device_uuid,
        Device.is_active.is_(True),
    )
    result = await db.execute(stmt)
    device = result.scalar_one_or_none()
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    if device.account_id == actor.account.id or (
        person_id is not None and device.person_id == person_id
    ):
        return device

    await record_authorization_denial(
        db,
        actor,
        target_type="device",
        target_id=device_uuid,
        reason="device_scope_mismatch",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access to this device is not permitted",
    )


async def require_person_provisioning_actor(
    db: AsyncSession,
    actor: NiamActor,
) -> None:
    """Allow person provisioning only for verified workforce identities.

    The richer organization permission decision is a follow-up migration. Until
    it is wired into this legacy NIAM route, citizens/guests/machines are denied
    and authenticated workforce identities are the narrow safe subset.
    """
    identity_type = await db.scalar(
        select(IdentityRecord.identity_type).where(
            IdentityRecord.id == actor.account.identity_id,
            IdentityRecord.is_active.is_(True),
            IdentityRecord.verified_at.isnot(None),
        )
    )
    allowed_types = {
        "government_workforce",
        "private_workforce",
        "enterprise",
    }
    if identity_type in allowed_types:
        return

    await record_authorization_denial(
        db,
        actor,
        target_type="person",
        target_id=None,
        reason="person_provisioning_requires_workforce_identity",
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Person provisioning requires an authorized workforce identity",
    )
