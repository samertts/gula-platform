from __future__ import annotations

from typing import Any


class FHIRDiagnosticReportMapper:
    RESOURCE_TYPE = "DiagnosticReport"

    @classmethod
    def from_lab_order(
        cls, order: dict, results: list[dict], patient_id: str, encounter_id: str | None = None,
    ) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": str(order.get("id", "")),
            "status": "final",
            "category": [
                {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB"},
                    ],
                },
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": order.get("order_code", ""),
                        "display": order.get("order_name", ""),
                    },
                ],
                "text": order.get("order_name", ""),
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": str(order.get("created_at", "")),
            "issued": str(order.get("updated_at", order.get("created_at", ""))),
            "performer": cls._build_performers(order),
            "result": [{"reference": f"Observation/{r.get('id')}"} for r in results if r.get("id")],
            "conclusion": order.get("conclusion", ""),
            "conclusionCode": cls._build_conclusion_codes(order),
            "presentedForm": cls._build_presented_form(order),
        }
        if encounter_id:
            resource["encounter"] = {"reference": f"Encounter/{encounter_id}"}
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def from_observation_batch(
        cls, observations: list[dict], patient_id: str, panel_code: str = "", panel_name: str = "",
    ) -> dict[str, Any]:
        resource = {
            "resourceType": cls.RESOURCE_TYPE,
            "id": panel_code or str(hash(tuple(o.get("id", "") for o in observations))),
            "status": "final",
            "category": [
                {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": "LAB"},
                    ],
                },
            ],
            "code": {
                "coding": [
                    {"system": "http://loinc.org", "code": panel_code, "display": panel_name},
                ],
                "text": panel_name,
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": next(
                (
                    o.get("effective_datetime", "") or o.get("created_at", "")
                    for o in observations
                    if o.get("effective_datetime") or o.get("created_at")
                ),
                "",
            ),
            "issued": next(
                (
                    o.get("issued_at", "") or o.get("updated_at", "")
                    for o in observations
                    if o.get("issued_at") or o.get("updated_at")
                ),
                "",
            ),
            "result": [
                {"reference": f"Observation/{o.get('id')}"} for o in observations if o.get("id")
            ],
        }
        return {k: v for k, v in resource.items() if v is not None}

    @classmethod
    def _build_performers(cls, order: dict) -> list[dict]:
        performers = []
        lab_id = order.get("lab_id")
        if lab_id:
            performers.append({"actor": {"reference": f"Organization/{lab_id}"}})
        practitioner_id = order.get("practitioner_id")
        if practitioner_id:
            performers.append({"actor": {"reference": f"Practitioner/{practitioner_id}"}})
        return performers

    @classmethod
    def _build_conclusion_codes(cls, order: dict) -> list[dict]:
        codes = order.get("conclusion_codes")
        if not codes:
            return []
        if isinstance(codes, list):
            return [{"coding": [{"code": c}]} if isinstance(c, str) else c for c in codes]
        return [{"coding": [{"code": codes}]}]

    @classmethod
    def _build_presented_form(cls, order: dict) -> list[dict] | None:
        url = order.get("report_url") or order.get("pdf_url")
        if not url:
            return None
        return [
            {
                "url": url,
                "title": order.get("order_name", "Lab Report"),
                "contentType": "application/pdf",
            },
        ]
