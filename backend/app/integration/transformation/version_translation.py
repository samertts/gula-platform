from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("gula.integration.transformation.version_translation")


@dataclass
class VersionAdapter:
    source_version: str = ""
    target_version: str = ""
    transform: Callable[[Any], Any] | None = None
    description: str = ""


class VersionTranslator:
    def __init__(self):
        self._adapters: dict[str, VersionAdapter] = {}
        self._supported_translations: dict[str, str] = {
            "HL7_2.3:HL7_2.5.1": "HL7 v2.3 to v2.5.1",
            "HL7_2.5.1:HL7_2.3": "HL7 v2.5.1 to v2.3",
            "FHIR_DSTU2:FHIR_R4": "FHIR DSTU2 to R4",
            "FHIR_R4:FHIR_DSTU2": "FHIR R4 to DSTU2",
            "FHIR_STU3:FHIR_R4": "FHIR STU3 to R4",
            "DICOM_2008:DICOM_2024": "DICOM 2008 to 2024",
        }

    def register_adapter(self, key: str, adapter: VersionAdapter) -> None:
        self._adapters[key] = adapter
        logger.info("Version adapter registered: %s", key)

    def translate(self, data: Any, source_version: str, target_version: str) -> Any:
        key = f"{source_version}:{target_version}"
        adapter = self._adapters.get(key)
        if adapter and adapter.transform:
            return adapter.transform(data)

        if key in self._supported_translations:
            logger.info("Using default translation for %s", key)
            return self._default_translate(data, source_version, target_version)

        if source_version == target_version:
            return data

        raise ValueError(f"No version adapter found for {key}")

    def supports(self, source_version: str, target_version: str) -> bool:
        key = f"{source_version}:{target_version}"
        return (
            key in self._adapters
            or key in self._supported_translations
            or source_version == target_version
        )

    def list_translations(self) -> list[str]:
        return list(self._supported_translations.keys()) + list(self._adapters.keys())

    def _default_translate(self, data: Any, source: str, target: str) -> Any:
        if isinstance(data, dict):
            result = dict(data)
            if "resourceType" in result:
                result["meta"] = result.get("meta", {})
                if isinstance(result["meta"], dict):
                    result["meta"]["versionId"] = target
            return result
        return data
