from __future__ import annotations

import logging
import secrets
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.config import NID_HMAC_KEY
from app.national.domain.citizen import Citizen
from app.national.domain.newborn import Newborn
from app.national.enums import Gender, IdentityStatus
from app.national.exceptions import (
    DuplicateNewbornRegistrationError,
    ForeignerRegistrationError,
    NewbornRegistrationError,
)
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService
from shared.events import events
from shared.identity.service import hash_national_id


audit_logger = logging.getLogger("audit.identity.newborn")


class IdentityService:
    def __init__(self, citizen_service: CitizenService, citizen_repo: CitizenRepository, db: Session | None = None) -> None:
        self.citizen_service = citizen_service
        self.citizen_repo = citizen_repo
        self.db = db

    async def register_newborn(self, data: dict[str, Any]) -> dict:
        """Create a temporary newborn health record without persisting parent NIDs.

        Parent NIDs exist only for the duration of this request.  They are HMACed and
        matched to locally registered parents; this method never calls a real NID
        provider and never logs the raw values.
        """
        birth_certificate_number = (data.get("birth_certificate_number") or "").strip().upper()
        mother_national_id = (data.get("mother_national_id") or "").strip()
        father_national_id = (data.get("father_national_id") or "").strip()
        birth_date = data.get("date_of_birth")
        lab_id = data.get("lab_id")

        if not birth_certificate_number:
            raise NewbornRegistrationError("Birth certificate number is required")
        if not mother_national_id or not father_national_id:
            raise NewbornRegistrationError("Both parent national IDs are required")
        if not isinstance(birth_date, date):
            raise NewbornRegistrationError("Date of birth is required")
        if not isinstance(lab_id, int) or lab_id <= 0:
            raise NewbornRegistrationError("A valid facility tenant is required")
        if self.db is None:
            raise NewbornRegistrationError("Newborn registration storage is unavailable")
        if not NID_HMAC_KEY:
            raise NewbornRegistrationError("Identity verification is unavailable")

        try:
            gender = Gender(data.get("gender", Gender.UNKNOWN.value))
        except ValueError as exc:
            raise NewbornRegistrationError("Invalid gender") from exc

        mother_hash = hash_national_id(mother_national_id, NID_HMAC_KEY)
        father_hash = hash_national_id(father_national_id, NID_HMAC_KEY)
        mother = await self.citizen_repo.get_by_national_id_hash(mother_hash)
        father = await self.citizen_repo.get_by_national_id_hash(father_hash)
        if not mother or not father:
            raise NewbornRegistrationError("Parent identity records could not be verified")

        duplicate = (
            self.db.query(Newborn)
            .filter(
                Newborn.birth_certificate_number == birth_certificate_number,
                Newborn.is_deleted.isnot(True),
            )
            .first()
        )
        if duplicate:
            raise DuplicateNewbornRegistrationError()

        health_number = self._generate_temporary_health_number()
        citizen = Citizen(
            health_number=health_number,
            first_name=(data.get("first_name") or "حديث الولادة").strip(),
            father_name=father.first_name,
            last_name=(data.get("last_name") or mother.last_name or "").strip(),
            mother_name=mother.full_name,
            date_of_birth=birth_date,
            gender=gender,
            identity_status=IdentityStatus.PENDING_VERIFICATION,
            tags={"identity_type": "newborn", "health_number_type": "temporary"},
        )
        newborn = Newborn(
            lab_id=lab_id,
            birth_certificate_number=birth_certificate_number,
            hospital_registration_number=data.get("hospital_registration_number"),
            temporary_health_number=health_number,
            first_name=citizen.first_name,
            father_name=father.first_name,
            last_name=citizen.last_name,
            date_of_birth=birth_date,
            gender=gender.value,
            birth_weight_grams=data.get("birth_weight_grams"),
            birth_place=data.get("birth_place"),
            birth_place_type=data.get("birth_place_type"),
            delivery_method=data.get("delivery_method"),
            mother_id=mother.id,
            mother_name=mother.full_name,
            father_id=father.id,
            citizen_id=citizen.id,
            registered_by_hospital=bool(data.get("registered_by_hospital", True)),
            notes=data.get("notes"),
            created_by=self._audit_actor_id(data.get("actor_id")),
        )

        try:
            self.db.add(citizen)
            self.db.flush()
            newborn.citizen_id = citizen.id
            self.db.add(newborn)
            self.db.commit()
            self.db.refresh(citizen)
            self.db.refresh(newborn)
        except Exception:
            self.db.rollback()
            raise

        event_payload = {
            "newborn_id": newborn.id,
            "citizen_id": citizen.id,
            "actor_id": str(data.get("actor_id") or ""),
            "lab_id": lab_id,
        }
        events.emit("NewbornHealthRecordRegistered", event_payload)
        audit_logger.info("newborn_health_record_registered %s", event_payload)
        return {
            "citizen": citizen,
            "newborn_id": newborn.id,
            "health_number": health_number,
            "is_temporary": True,
        }

    def _generate_temporary_health_number(self) -> str:
        for _ in range(10):
            candidate = f"THN-{secrets.token_hex(7).upper()}"
            citizen_exists = self.db.query(Citizen).filter(Citizen.health_number == candidate).first()
            newborn_exists = self.db.query(Newborn).filter(Newborn.temporary_health_number == candidate).first()
            if not citizen_exists and not newborn_exists:
                return candidate
        raise NewbornRegistrationError("Temporary health number generation failed")

    @staticmethod
    def _audit_actor_id(actor_id: Any) -> int | None:
        try:
            return int(actor_id) if actor_id is not None else None
        except (TypeError, ValueError):
            return None

    async def register_foreigner(self, data: dict[str, Any]) -> dict:
        if not data.get("passport_number"):
            raise ForeignerRegistrationError("Passport number is required")
        if not data.get("passport_country"):
            raise ForeignerRegistrationError("Passport country is required")
        health_number = f"FR{data['passport_number'][:8].upper()}"
        citizen_data = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender"),
            "nationality": data.get("nationality", data.get("passport_country")),
            "health_number": health_number,
            "phone": data.get("phone"),
            "identity_status": "active",
        }
        citizen = await self.citizen_service.register_citizen(citizen_data)
        return {"citizen": citizen, "health_number": health_number}

    async def register_visitor(self, data: dict[str, Any]) -> dict:
        health_number = f"VS{data.get('passport_number', 'UNKNOWN')[:8].upper()}"
        citizen_data = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender", "unknown"),
            "nationality": data.get("nationality", data.get("passport_country")),
            "health_number": health_number,
            "phone": data.get("phone"),
            "identity_status": "active",
        }
        citizen = await self.citizen_service.register_citizen(citizen_data)
        return {"citizen": citizen, "health_number": health_number, "is_temporary": True}

    async def register_unknown_patient(self, data: dict[str, Any]) -> dict:
        import uuid
        emergency_hn = f"EM{str(uuid.uuid4())[:8].upper()}"
        citizen_data = {
            "first_name": data.get("description", "Unknown"),
            "last_name": "Patient",
            "date_of_birth": data.get("approximate_date_of_birth") or "2000-01-01",
            "gender": data.get("gender", "unknown"),
            "health_number": emergency_hn,
            "phone": data.get("found_location", ""),
            "identity_status": "pending_verification",
        }
        citizen = await self.citizen_service.register_citizen(citizen_data)
        return {"citizen": citizen, "health_number": emergency_hn, "is_temporary": True, "requires_merge": True}
