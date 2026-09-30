from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.fhir_interoperability")


class Fhir_interoperabilityCapability:
    """fhir_interoperability capability in the integration domain (infrastructure layer).

    FHIR/HL7 interoperability: FHIR R4 resources, HL7 v2 messages, LOINC coding, SNOMED CT, ICD-10, ICD-11 ready, UCUM units, IHE profiles, terminology services
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        try:
            self._kernel = get_kernel()
        except RuntimeError:
            # Isolated contract workers and unit tests may start before the
            # optional application kernel. Pure validation remains available.
            self._kernel = None
            logger.debug("FHIR capability initialized without optional kernel")
        logger.info("Fhir_interoperability capability initializing")
        # Depends on: patient_management
        # Depends on: clinical_foundation
        self._initialized = True
        logger.info("Fhir_interoperability capability initialized")

    async def execute(self, input_data: Any) -> dict:
        """Not implemented. This capability must not report success (NR-089).

        The generated body returned ``{"success": True}`` without doing
        anything, and the generated unit test asserted exactly that, so the stub
        certified itself. Nothing in the platform calls it; NR-087 made the
        module importable, which is why the false claim is removed rather than
        left reachable.
        """
        raise NotImplementedError(
            "capability 'fhir_interoperability' is generated scaffolding with no implementation; "
            "it must not report success",
        )

    async def validate(self, input_data: Any) -> bool:
        """Not implemented. A gate that always passes is not a gate (NR-089)."""
        raise NotImplementedError(
            "capability 'fhir_interoperability' has no validation rules; "
            "returning True would assert an unchecked input is valid",
        )

    async def on_activate(self) -> None:
        logger.info("Fhir_interoperability capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Fhir_interoperability capability deactivated")

    async def health(self) -> dict:
        # Answers rather than raises -- a health probe should report -- but it
        # reports what is true: scaffolding, not a working capability.
        return {
            "status": "not_implemented",
            "capability": "fhir_interoperability",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
