from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .interfaces import ResultRepository
    from .models import LabResultDomain

logger = logging.getLogger("gula.safety")

class ClinicalSafetyGuard:
    """
    Enforces clinical safety rules to prevent erroneous medical data.
    Implements Delta Checks and Analyte Correlation.
    """

    DELTA_THRESHOLD_PERCENT = Decimal("50")  # Flag if result changes by > 50%

    async def perform_delta_check(
        self,
        current_result: LabResultDomain,
        repository: ResultRepository
    ) -> bool:
        """
        Compares current result with previous results for the same patient/analyte.
        Returns True if the change is suspicious (Delta check failed).
        """
        # Get last 3 results for this patient and analyte
        previous_results = await repository.list_by_patient_analyte(
            patient_id=current_result.patient_id,
            analyte=current_result.analyte,
            limit=3
        )

        if not previous_results:
            return False

        last_result = previous_results[0]
        if last_result.value == Decimal(0):
            return False

        diff = abs(current_result.value - last_result.value)
        change_percent = (diff / last_result.value) * 100

        if change_percent > self.DELTA_THRESHOLD_PERCENT:
            logger.warning(
                "[SAFETY] Delta check failed for patient %s, analyte %s. Change: %.2f%%",
                current_result.patient_id, current_result.analyte, change_percent
            )
            return True

        return False

    def validate_correlation(self, results: list[LabResultDomain]) -> list[str]:
        """
        Checks for unrealistic correlations between different analytes.
        Example: Hemoglobin (HGB) vs Hematocrit (HCT) - HCT should be ~3x HGB.
        """
        warnings = []
        hgb = next((r for r in results if r.analyte.upper() in ["HGB", "HEMOGLOBIN"]), None)
        hct = next((r for r in results if r.analyte.upper() in ["HCT", "HEMATOCRIT"]), None)

        if hgb and hct:
            # HCT is usually 2.8 to 3.2 times HGB
            ratio = hct.value / hgb.value if hgb.value != 0 else 0
            if not (2.5 <= ratio <= 3.5):
                warnings.append(f"Correlation mismatch: HGB ({hgb.value}) and HCT ({hct.value}) ratio is {ratio:.2f}")

        return warnings
