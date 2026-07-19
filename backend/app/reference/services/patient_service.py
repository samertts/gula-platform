from __future__ import annotations

from collections.abc import Sequence

from app.reference.domain.exceptions import PatientNotFoundError
from app.reference.domain.interfaces import PatientRepository
from app.reference.domain.models import PatientDomain
from app.reference.domain.services import PatientValidationService


class PatientService:
    """Orchestrates patient workflows using domain services + repository."""

    def __init__(
        self,
        repository: PatientRepository,
        validation: PatientValidationService,
    ) -> None:
        self._repository = repository
        self._validation = validation

    async def create_patient(self, patient: PatientDomain) -> PatientDomain:
        self._validation.normalize_name(patient.name)
        self._validation.validate_new_patient(patient, self._repository)
        await self._validation.check_duplicate(patient, self._repository)
        return await self._repository.save(patient)

    async def get_patient(self, patient_id: str) -> PatientDomain:
        patient = await self._repository.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(patient_id)
        return patient

    async def search_patients(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        lab_id: str | None = None,
        national_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PatientDomain], int]:
        return await self._repository.search(
            name=name,
            phone=phone,
            lab_id=lab_id,
            national_id=national_id,
            limit=limit,
            offset=offset,
        )
