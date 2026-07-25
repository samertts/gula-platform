from __future__ import annotations

from typing import Any

from app.ehr.models.clinical_summary import ConditionRecord, DiagnosisRecord, ProblemListItem


class FHIRConditionMapper:
    RESOURCE_TYPE = "Condition"

    @classmethod
    def from_ehr_model(cls, record: ConditionRecord) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": record.fhir_id or record.id,
            "clinicalStatus": cls._build_clinical_status(record.clinical_status),
            "verificationStatus": cls._build_verification_status(record.verification_status),
            "category": [{"coding": [{"code": record.category}]}] if record.category else [],
            "severity": {"coding": [{"code": record.severity}]} if record.severity else None,
            "code": {
                "coding": cls._build_codings(record),
                "text": record.code_display_ar or record.code_display,
            },
            "bodySite": [{"coding": [{"code": record.body_site}]}] if record.body_site else [],
            "subject": {"reference": f"Patient/{record.patient_id}"},
            "encounter": {"reference": f"Encounter/{record.encounter_id}"}
            if record.encounter_id
            else None,
            "recorder": {"reference": f"Practitioner/{record.practitioner_id}"}
            if record.practitioner_id
            else None,
            "onsetDateTime": record.onset_date.isoformat() if record.onset_date else None,
            "abatementDateTime": record.abatement_date.isoformat()
            if record.abatement_date
            else None,
            "recordedDate": record.recorded_date.isoformat() if record.recorded_date else None,
            "note": [{"text": record.notes}] if record.notes else [],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_diagnosis_record(cls, diagnosis: DiagnosisRecord) -> dict[str, Any]:
        coding = []
        if diagnosis.icd10_code:
            coding.append(
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": diagnosis.icd10_code,
                    "display": diagnosis.icd10_description or "",
                },
            )
        if diagnosis.snomed_code:
            coding.append(
                {
                    "system": "http://snomed.info/sct",
                    "code": diagnosis.snomed_code,
                    "display": diagnosis.snomed_description or "",
                },
            )

        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": diagnosis.fhir_id or diagnosis.id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active" if diagnosis.is_active else "resolved",
                    },
                ],
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                    },
                ],
            },
            "category": cls._build_diagnosis_category(diagnosis),
            "code": {
                "coding": coding,
                "text": diagnosis.diagnosis_text_ar or diagnosis.diagnosis_text,
            },
            "subject": {"reference": f"Patient/{diagnosis.patient_id}"},
            "encounter": {"reference": f"Encounter/{diagnosis.encounter_id}"}
            if diagnosis.encounter_id
            else None,
            "recorder": {"reference": f"Practitioner/{diagnosis.practitioner_id}"}
            if diagnosis.practitioner_id
            else None,
            "onsetDateTime": diagnosis.diagnosis_date.isoformat()
            if diagnosis.diagnosis_date
            else None,
            "abatementDateTime": diagnosis.resolution_date.isoformat()
            if diagnosis.resolution_date
            else None,
            "note": [{"text": diagnosis.notes}] if diagnosis.notes else [],
        }
        if diagnosis.is_chronic:
            resource["severity"] = {"coding": [{"code": "moderate"}]}
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_problem_list_item(cls, problem: ProblemListItem) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": problem.fhir_id or problem.id,
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": problem.clinical_status or problem.status.value,
                    },
                ],
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": problem.verification_status or "unconfirmed",
                    },
                ],
            },
            "category": [{"coding": [{"code": problem.category or "problem-list-item"}]}],
            "severity": {"coding": [{"code": problem.severity}]} if problem.severity else None,
            "code": {
                "coding": cls._build_problem_codings(problem),
                "text": problem.display_ar or problem.display,
            },
            "bodySite": [{"coding": [{"code": problem.body_site}]}] if problem.body_site else [],
            "subject": {"reference": f"Patient/{problem.patient_id}"},
            "encounter": {"reference": f"Encounter/{problem.encounter_id}"}
            if problem.encounter_id
            else None,
            "onsetDateTime": problem.onset_date.isoformat() if problem.onset_date else None,
            "abatementDateTime": problem.resolution_date.isoformat()
            if problem.resolution_date
            else None,
            "recordedDate": problem.recorded_date.isoformat() if problem.recorded_date else None,
            "note": [{"text": problem.notes}] if problem.notes else [],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_lab_result(
        cls, result: dict, patient_id: str, encounter_id: str | None = None,
    ) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": str(result.get("id", "")),
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    },
                ],
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "unconfirmed",
                    },
                ],
            },
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": result.get("test_code", ""),
                        "display": result.get("test_name", ""),
                    },
                ],
                "text": result.get("test_name", ""),
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": str(result.get("created_at", "")),
        }
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_clinical_status(cls, status: str | None) -> dict | None:
        if not status:
            return None
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": status,
                },
            ],
        }

    @classmethod
    def _build_verification_status(cls, status: str | None) -> dict | None:
        if not status:
            return None
        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": status,
                },
            ],
        }

    @classmethod
    def _build_codings(cls, record: ConditionRecord) -> list[dict]:
        codings = []
        if record.code and record.code_system:
            system_map = {
                "icd10": "http://hl7.org/fhir/sid/icd-10",
                "snomed": "http://snomed.info/sct",
                "loinc": "http://loinc.org",
            }
            codings.append(
                {
                    "system": system_map.get(record.code_system, "http://gula.health/code"),
                    "code": record.code,
                    "display": record.code_display,
                },
            )
        if record.icd10_code:
            codings.append(
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": record.icd10_code,
                    "display": record.icd10_description or "",
                },
            )
        return codings

    @classmethod
    def _build_diagnosis_category(cls, diagnosis: DiagnosisRecord) -> list[dict]:
        type_map = {
            "primary": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "secondary": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "comorbidity": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "complication": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
        }
        code_map = {"primary": "DD", "secondary": "AD", "comorbidity": "CM", "complication": "CT"}
        dt = diagnosis.diagnosis_type.value if diagnosis.diagnosis_type else "primary"
        return [
            {
                "coding": [
                    {
                        "system": type_map.get(
                            dt, "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                        ),
                        "code": code_map.get(dt, "DD"),
                    },
                ],
            },
        ]

    @classmethod
    def _build_problem_codings(cls, problem: ProblemListItem) -> list[dict]:
        if problem.code and problem.code_system:
            system_map = {
                "icd10": "http://hl7.org/fhir/sid/icd-10",
                "snomed": "http://snomed.info/sct",
                "loinc": "http://loinc.org",
            }
            return [
                {
                    "system": system_map.get(problem.code_system, "http://gula.health/code"),
                    "code": problem.code,
                    "display": problem.display,
                },
            ]
        return []
