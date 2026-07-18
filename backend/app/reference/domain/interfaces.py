from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Sequence

from .models import PatientDomain, LabOrderDomain, LabResultDomain


class PatientRepository(ABC):

    @abstractmethod
    async def save(self, patient: PatientDomain) -> PatientDomain:
        ...

    @abstractmethod
    async def get_by_id(self, patient_id: str) -> Optional[PatientDomain]:
        ...

    @abstractmethod
    async def search(
        self,
        *,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        lab_id: Optional[str] = None,
        national_id: Optional[str] = None,
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
    ) -> Optional[PatientDomain]:
        ...


class OrderRepository(ABC):

    @abstractmethod
    async def save(self, order: LabOrderDomain) -> LabOrderDomain:
        ...

    @abstractmethod
    async def get_by_id(self, order_id: str) -> Optional[LabOrderDomain]:
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
    async def get_by_id(self, result_id: str) -> Optional[LabResultDomain]:
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
