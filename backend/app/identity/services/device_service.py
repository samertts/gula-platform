from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app._compat import UTC
from app.identity.models.device import Device
from app.identity.models.machine_identity import MachineIdentity
from app.identity.repositories.device_repository import DeviceRepository


class DeviceService:

    def __init__(self, session: AsyncSession) -> None:
        self.repo = DeviceRepository(session)
        self._session = session

    async def register_device(
        self,
        person_id: str,
        device_fingerprint: str,
        device_name: Optional[str] = None,
        device_type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        model: Optional[str] = None,
        os: Optional[str] = None,
        os_version: Optional[str] = None,
        browser: Optional[str] = None,
        browser_version: Optional[str] = None,
        public_key: Optional[str] = None,
        account_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Device:
        existing = await self.repo.find_by_fingerprint(device_fingerprint)
        if existing:
            existing.last_seen_at = datetime.now(UTC)
            existing.last_ip = ip_address
            if account_id:
                existing.account_id = account_id
            await self.repo.session.flush()
            return existing

        device = Device(
            id=...,
            uuid=str(uuid.uuid4()),
            person_id=person_id,
            account_id=account_id,
            device_name=device_name,
            device_type=device_type,
            manufacturer=manufacturer,
            model=model,
            os=os,
            os_version=os_version,
            browser=browser,
            browser_version=browser_version,
            device_fingerprint=device_fingerprint,
            public_key=public_key,
            trusted=False,
            last_ip=ip_address,
            first_seen_at=datetime.now(UTC),
            last_seen_at=datetime.now(UTC),
            is_active=True,
            is_locked=False,
        )
        return await self.repo.create(device)

    async def trust_device(self, device_id: str) -> Optional[Device]:
        device = await self.repo.get_by_id(device_id)
        if not device:
            return None
        device.trusted = True
        device.trusted_at = datetime.now(UTC)
        await self.repo.session.flush()
        return device

    async def revoke_device(self, device_id: str) -> bool:
        device = await self.repo.get_by_id(device_id)
        if not device:
            return False
        device.is_active = False
        await self.repo.session.flush()
        return True

    async def attest_device(self, device_id: str, attestation_data: str) -> Optional[MachineIdentity]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None
        machine.device_attestation = attestation_data
        machine.attested_at = datetime.now(UTC)
        machine.health_status = "healthy"
        await self._session.flush()
        return machine

    async def report_health(self, device_id: str, health_status: str) -> Optional[MachineIdentity]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None
        machine.health_status = health_status
        machine.last_health_check = datetime.now(UTC)
        await self._session.flush()
        return machine

    async def calculate_risk_score(self, device_id: str) -> Optional[int]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None

        score = 0
        if machine.is_compromised:
            score += 50
        if machine.health_status and machine.health_status != "healthy":
            score += 20
        if machine.attested_at:
            attested_days = (datetime.now(UTC) - machine.attested_at).days
            if attested_days > 365:
                score += 15
            elif attested_days > 180:
                score += 10
        else:
            score += 15
        if machine.last_heartbeat:
            heartbeat_days = (datetime.now(UTC) - machine.last_heartbeat).days
            if heartbeat_days > 30:
                score += 20
            elif heartbeat_days > 7:
                score += 10
        else:
            score += 10
        if machine.certificate_expires:
            cert_days = (machine.certificate_expires - datetime.now(UTC)).days
            if cert_days < 0:
                score += 25
            elif cert_days < 30:
                score += 10
        score = min(score, 100)
        machine.risk_score = score
        await self._session.flush()
        return score

    async def mark_compromised(self, device_id: str) -> Optional[MachineIdentity]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None
        machine.is_compromised = True
        machine.compromised_at = datetime.now(UTC)
        machine.health_status = "compromised"
        machine.risk_score = 100
        await self._session.flush()
        return machine

    async def transfer_device(self, device_id: str, new_person_id: str) -> Optional[MachineIdentity]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None
        machine.assigned_to_person = new_person_id
        machine.assigned_at = datetime.now(UTC)
        await self._session.flush()
        return machine

    async def report_lost(self, device_id: str) -> Optional[MachineIdentity]:
        stmt = select(MachineIdentity).where(MachineIdentity.uuid == device_id)
        result = await self._session.execute(stmt)
        machine = result.scalar_one_or_none()
        if not machine:
            return None
        machine.is_active = False
        machine.health_status = "lost"
        machine.notes = (machine.notes or "") + " [REPORTED LOST]"
        await self._session.flush()
        return machine
