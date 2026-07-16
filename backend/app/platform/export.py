"""Standardized import/export module — CSV, JSON, FHIR, PDF."""

from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from . import PlatformRegistry

logger = logging.getLogger("gula.platform.export")


@dataclass
class ExportResult:
    success: bool = False
    data: str | bytes | None = None
    mime_type: str = ""
    error: str | None = None


@dataclass
class ImportResult:
    success: bool = False
    count: int = 0
    errors: list[str] = field(default_factory=list)


class ExportService:
    def export_csv(self, headers: list[str], rows: list[list], filename: str = "export.csv") -> ExportResult:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return ExportResult(success=True, data=output.getvalue(), mime_type="text/csv")

    def export_json(self, data: Any, filename: str = "export.json") -> ExportResult:
        import json
        return ExportResult(success=True, data=json.dumps(data, ensure_ascii=False, default=str, indent=2), mime_type="application/json")

    def export_fhir(self, resources: list[dict], filename: str = "export.json") -> ExportResult:
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": r} for r in resources],
        }
        return ExportResult(success=True, data=json.dumps(bundle, ensure_ascii=False, default=str, indent=2), mime_type="application/fhir+json")

    def export_pdf(self, html_content: str, filename: str = "export.pdf") -> ExportResult:
        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return ExportResult(success=True, data=pdf_bytes, mime_type="application/pdf")
        except ImportError:
            return ExportResult(success=False, error="weasyprint not installed")


class ImportService:
    def import_csv(self, content: str) -> list[dict]:
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def import_json(self, content: str) -> Any:
        return json.loads(content)

    def import_fhir(self, content: str) -> list[dict]:
        data = json.loads(content)
        if isinstance(data, dict) and data.get("resourceType") == "Bundle":
            return [entry["resource"] for entry in data.get("entry", [])]
        if isinstance(data, list):
            return data
        return [data]


PlatformRegistry.register("export", ExportService(), capabilities=[
    {"name": "export_csv", "description": "Export data as CSV"},
    {"name": "export_json", "description": "Export data as JSON"},
    {"name": "export_fhir", "description": "Export data as FHIR Bundle"},
    {"name": "export_pdf", "description": "Export HTML content as PDF"},
])
PlatformRegistry.register("import", ImportService(), capabilities=[
    {"name": "import_csv", "description": "Import data from CSV"},
    {"name": "import_json", "description": "Import data from JSON"},
    {"name": "import_fhir", "description": "Import data from FHIR format"},
])
