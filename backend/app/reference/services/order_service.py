from __future__ import annotations

from typing import Sequence

from app.reference.domain.exceptions import OrderNotFoundError
from app.reference.domain.interfaces import OrderRepository, PatientRepository
from app.reference.domain.models import LabOrderDomain
from app.reference.domain.services import OrderProcessingService


class OrderService:
    """Orchestrates order creation and retrieval workflows."""

    def __init__(
        self,
        repository: OrderRepository,
        patient_repo: PatientRepository,
        order_processing: OrderProcessingService,
    ) -> None:
        self._repository = repository
        self._patient_repo = patient_repo
        self._order_processing = order_processing

    async def create_order(self, order: LabOrderDomain) -> LabOrderDomain:
        await self._order_processing.validate_new_order(order, self._patient_repo)
        return await self._repository.save(order)

    async def get_order(self, order_id: str) -> LabOrderDomain:
        order = await self._repository.get_by_id(order_id)
        if order is None:
            raise OrderNotFoundError(order_id)
        return order

    async def list_patient_orders(
        self,
        patient_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[LabOrderDomain], int]:
        return await self._repository.list_by_patient(
            patient_id=patient_id,
            limit=limit,
            offset=offset,
        )
