from __future__ import annotations

import logging
from typing import Any

from backend.app.integration.connector.spec import (
    ConnectorSpec,
    ConnectorStatus,
    ConnectorType,
)

logger = logging.getLogger("gula.integration.connector.dicom")


class DICOMConnector:
    def __init__(self, spec: ConnectorSpec):
        if spec.connector_type != ConnectorType.DICOM:
            raise ValueError(
                f"DICOMConnector requires type DICOM, got {spec.connector_type.name}",
            )
        self.spec = spec
        self._connected = False

    async def connect(self) -> bool:
        try:
            import importlib
            importlib.import_module("pydicom")
        except ImportError:
            logger.error("pydicom library not installed")
            self.spec.status = ConnectorStatus.FAILED
            return False

        self._connected = True
        self.spec.status = ConnectorStatus.CONNECTED
        logger.info("DICOM connector ready: %s", self.spec.name)
        return True

    async def disconnect(self) -> None:
        self._connected = False
        self.spec.status = ConnectorStatus.DISCONNECTED

    async def c_find(self, query: dict[str, Any]) -> list[dict[str, Any]]:
        if not self._connected:
            raise RuntimeError("DICOM connector not connected")
        logger.info("DICOM C-FIND: %s", query)
        return []

    async def c_move(self, study_uid: str, destination: str) -> bool:
        if not self._connected:
            raise RuntimeError("DICOM connector not connected")
        logger.info("DICOM C-MOVE: %s -> %s", study_uid, destination)
        return True

    async def c_store(self, dicom_data: bytes) -> bool:
        if not self._connected:
            raise RuntimeError("DICOM connector not connected")
        logger.info("DICOM C-STORE: %d bytes", len(dicom_data))
        return True
