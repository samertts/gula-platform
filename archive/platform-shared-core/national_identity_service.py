from __future__ import annotations

from typing import Any

from app.national.exceptions import ForeignerRegistrationError, NewbornRegistrationError
from app.national.repositories.citizen_repository import CitizenRepository
from app.national.services.citizen_service import CitizenService


class IdentityService:
    def __init__(self, citizen_service: CitizenService, citizen_repo: CitizenRepository) -> None:
        self.citizen_service = citizen_service
        self.citizen_repo = citizen_repo

    async def register_newborn(self, data: dict[str, Any]) -> dict:
        if not data.get("mother_id"):
            raise NewbornRegistrationError("Mother ID is required")
        if not data.get("birth_certificate_number"):
            raise NewbornRegistrationError("Birth certificate number is required")
        health_number = f"NB{data['birth_certificate_number'][:8].upper()}"
        citizen_data = {
            "first_name": data.get("first_name", ""),
            "father_name": data.get("father_name"),
            "last_name": data.get("last_name", ""),
            "date_of_birth": data.get("date_of_birth"),
            "gender": data.get("gender"),
            "phone": data.get("mother_phone"),
            "health_number": health_number,
            "identity_status": "active",
        }
        citizen = await self.citizen_service.register_citizen(citizen_data)
        return {"citizen": citizen, "health_number": health_number}

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
        return {
            "citizen": citizen,
            "health_number": emergency_hn,
            "is_temporary": True,
            "requires_merge": True,
        }
