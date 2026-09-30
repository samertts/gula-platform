from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.healthcare_consent")


class Healthcare_consentCapability:
    """healthcare_consent capability in the identity_security domain (application layer).

    Healthcare-specific consent: patient privacy preferences, access policies, break-glass emergency override, purpose of use enforcement, granular data sharing controls
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("Healthcare_consent capability initializing")
        # Depends on: consent_management
        # Depends on: patient_management
        self._initialized = True
        logger.info("Healthcare_consent capability initialized")

    async def execute(self, input_data: Any) -> dict:
        """Not implemented. This capability must not report success (NR-089).

        The generated body returned ``{"success": True}`` without doing
        anything, and the generated unit test asserted exactly that, so the stub
        certified itself. Nothing in the platform calls it; NR-087 made the
        module importable, which is why the false claim is removed rather than
        left reachable.
        """
        raise NotImplementedError(
            "capability 'healthcare_consent' is generated scaffolding with no implementation; "
            "it must not report success",
        )

    async def validate(self, input_data: Any) -> bool:
        """Not implemented. A gate that always passes is not a gate (NR-089)."""
        raise NotImplementedError(
            "capability 'healthcare_consent' has no validation rules; "
            "returning True would assert an unchecked input is valid",
        )

    async def on_activate(self) -> None:
        logger.info("Healthcare_consent capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Healthcare_consent capability deactivated")

    async def health(self) -> dict:
        # Answers rather than raises -- a health probe should report -- but it
        # reports what is true: scaffolding, not a working capability.
        return {
            "status": "not_implemented",
            "capability": "healthcare_consent",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
