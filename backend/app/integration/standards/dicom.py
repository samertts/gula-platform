from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("gula.integration.standards.dicom")

DICOM_SERVICES = frozenset({"C-FIND", "C-MOVE", "C-STORE", "C-ECHO", "C-GET"})


@dataclass
class DICOMStudy:
    study_uid: str = ""
    patient_id: str = ""
    patient_name: str = ""
    study_date: str = ""
    study_description: str = ""
    modality: str = ""
    accession_number: str = ""
    series_count: int = 0
    instance_count: int = 0


@dataclass
class DICOMInstance:
    sop_instance_uid: str = ""
    study_uid: str = ""
    series_uid: str = ""
    sop_class_uid: str = ""
    instance_number: int = 0
    transfer_syntax: str = ""
    data: bytes = field(default_factory=bytes)


class DICOMService:
    def __init__(self):
        self._ae_title = "GULA"

    def create_study(self, **kwargs: Any) -> DICOMStudy:
        return DICOMStudy(**{k: v for k, v in kwargs.items() if k in DICOMStudy.__dataclass_fields__})

    def supports_service(self, service: str) -> bool:
        return service.upper() in DICOM_SERVICES

    def validate_study(self, study: DICOMStudy) -> list[str]:
        errors: list[str] = []
        if not study.study_uid:
            errors.append("Missing StudyUID")
        if not study.patient_id:
            errors.append("Missing PatientID")
        return errors

    def ae_title(self) -> str:
        return self._ae_title

    def modalities(self) -> list[str]:
        return ["CR", "CT", "MR", "US", "DX", "MG", "NM", "PET", "XA", "RF", "OT"]

    def dicom_services(self) -> frozenset:
        return DICOM_SERVICES
