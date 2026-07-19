from __future__ import annotations

from collections.abc import Sequence

from app.reference.domain.exceptions import CriticalResultError, ResultNotFoundError
from app.reference.domain.interfaces import OrderRepository, ResultRepository
from app.reference.domain.models import LabResultDomain
from app.reference.domain.services import ResultValidationService


class ResultService:
    """Orchestrates result entry, validation, and critical flag detection."""

    def __init__(
        self,
        repository: ResultRepository,
        order_repo: OrderRepository,
        validation: ResultValidationService,
    ) -> None:
        self._repository = repository
        self._order_repo = order_repo
        self._validation = validation

    async def submit_result(
        self,
        result: LabResultDomain,
    ) -> LabResultDomain:
        await self._validation.validate_result(result, self._order_repo)
        is_critical = self._validation.flag_critical(result)
        saved = await self._repository.save(result)
        if is_critical:
            raise CriticalResultError(
                analyte=result.analyte,
                value=f"{result.value}",
                unit=result.unit,
            )
        return saved

    async def get_result(self, result_id: str) -> LabResultDomain:
        result = await self._repository.get_by_id(result_id)
        if result is None:
            raise ResultNotFoundError(result_id)
        return result

    async def list_order_results(
        self,
        order_id: str,
    ) -> Sequence[LabResultDomain]:
        return await self._repository.list_by_order(order_id=order_id)

    async def list_critical_results(
        self,
        lab_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[LabResultDomain], int]:
        return await self._repository.list_critical(
            lab_id=lab_id,
            limit=limit,
            offset=offset,
        )

    async def bulk_submit_results(
        self,
        results: list[LabResultDomain],
    ) -> tuple[list[LabResultDomain], list[CriticalResultError]]:
        saved: list[LabResultDomain] = []
        criticals: list[CriticalResultError] = []

        for result in results:
            try:
                validated = await self._validation.validate_result(
                    result, self._order_repo
                )
                self._validation.flag_critical(validated)
                saved_result = await self._repository.save(validated)
                if validated.is_critical:
                    criticals.append(
                        CriticalResultError(
                            analyte=validated.analyte,
                            value=f"{validated.value}",
                            unit=validated.unit,
                        )
                    )
                saved.append(saved_result)
            except CriticalResultError as e:
                result.is_critical = True
                result.flagged = ResultValidationService.CRITICAL_FLAG
                saved_result = await self._repository.save(result)
                saved.append(saved_result)
                criticals.append(e)

        return saved, criticals
