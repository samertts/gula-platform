from __future__ import annotations

import logging
from typing import Any

from app.kernel.integration import get_kernel

logger = logging.getLogger("gula.capability.document_management")


class Document_managementCapability:
    """document_management capability in the infrastructure domain (application layer).

    Document management: attachments, PDF generation, OCR, image processing, preview, digital signature, metadata, versioning, document search
    """

    def __init__(self) -> None:
        self._initialized = False
        self._kernel = None

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._kernel = get_kernel()
        logger.info("Document_management capability initializing")
        # Depends on: storage_service
        # Depends on: authentication
        # Depends on: audit_logging
        self._initialized = True
        logger.info("Document_management capability initialized")

    async def execute(self, input_data: Any) -> dict:
        """Not implemented. This capability must not report success (NR-089).

        The generated body returned ``{"success": True}`` without doing
        anything, and the generated unit test asserted exactly that, so the stub
        certified itself. Nothing in the platform calls it; NR-087 made the
        module importable, which is why the false claim is removed rather than
        left reachable.
        """
        raise NotImplementedError(
            "capability 'document_management' is generated scaffolding with no implementation; "
            "it must not report success",
        )

    async def validate(self, input_data: Any) -> bool:
        """Not implemented. A gate that always passes is not a gate (NR-089)."""
        raise NotImplementedError(
            "capability 'document_management' has no validation rules; "
            "returning True would assert an unchecked input is valid",
        )

    async def on_activate(self) -> None:
        logger.info("Document_management capability activated")

    async def on_deactivate(self) -> None:
        logger.info("Document_management capability deactivated")

    async def health(self) -> dict:
        # Answers rather than raises -- a health probe should report -- but it
        # reports what is true: scaffolding, not a working capability.
        return {
            "status": "not_implemented",
            "capability": "document_management",
            "version": "1.0.0",
            "initialized": self._initialized,
        }
