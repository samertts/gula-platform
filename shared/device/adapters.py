from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger("gula.device")


@dataclass
class DeviceResult:
    device_id: str
    patient_id: str
    test_code: str
    test_name: str
    result_value: str
    unit: str = ""
    reference_range: str = ""
    timestamp: str = ""


class DeviceAdapter(ABC):
    @abstractmethod
    def parse(self, raw_data: bytes) -> list[DeviceResult]:
        ...

    @abstractmethod
    def get_device_type(self) -> str:
        ...


class AdapterRegistry:
    def __init__(self):
        self._adapters: dict[str, type[DeviceAdapter]] = {}

    def register(self, device_type: str, adapter: type[DeviceAdapter]) -> None:
        self._adapters[device_type] = adapter
        logger.info("Registered adapter for device type: %s", device_type)

    def get(self, device_type: str) -> type[DeviceAdapter] | None:
        return self._adapters.get(device_type)

    def list_types(self) -> list[str]:
        return list(self._adapters.keys())
