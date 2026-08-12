from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from .models import LabOrderDomain, LabResultDomain, PatientDomain


class PatientRepository(ABC):

    @abstractmethod
    async def save(self, patient: PatientDomain) -> PatientDomain:
        ...

    @abstractmethod
    async def get_by_id(self, patient_id: str) -> PatientDomain | None:
        ...

    @abstractmethod
    async def search(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        lab_id: str | None = None,
        national_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PatientDomain], int]:
        ...

    @abstractmethod
    async def find_duplicate(
        self,
        name: str,
        phone: str,
        lab_id: str,
    ) -> PatientDomain | None:
        ...


class OrderRepository(ABC):

    @abstractmethod
    async def save(self, order: LabOrderDomain) -> LabOrderDomain:
        ...

    @abstractmethod
    async def get_by_id(self, order_id: str) -> LabOrderDomain | None:
        ...

    @abstractmethod
    async def list_by_patient(
        self,
        patient_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[LabOrderDomain], int]:
        ...


class ResultRepository(ABC):

    @abstractmethod
    async def save(self, result: LabResultDomain) -> LabResultDomain:
        ...

    @abstractmethod
    async def get_by_id(self, result_id: str) -> LabResultDomain | None:
        ...

    @abstractmethod
    async def list_by_order(
        self,
        order_id: str,
    ) -> Sequence[LabResultDomain]:
        ...

    @abstractmethod
    async def list_critical(
        self,
        lab_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[LabResultDomain], int]:
        ...
