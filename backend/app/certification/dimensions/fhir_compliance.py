from __future__ import annotations

from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class FHIRComplianceEvaluator(DimensionEvaluator):
    FHIR_VERSIONS = ["R4", "R5"]
    REQUIRED_RESOURCES = [
        "Patient",
        "Observation",
        "DiagnosticReport",
        "Organization",
        "Practitioner",
        "ServiceRequest",
        "Specimen",
    ]
    REQUIRED_SEARCH_PARAMS = ["_id", "_lastUpdated", "_tag", "_profile", "_security"]

    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        fhir_files = self._find_fhir_files(target)
        self._add_evidence(
            "fhir_modules_found",
            value=len(fhir_files),
            source="Path scan",
            passed=len(fhir_files) > 0,
        )

        if not fhir_files:
            self._add_remediation(
                "Create FHIR R4/R5 compliant API endpoints",
                severity="high",
                effort="16h",
            )
            return self._result(0.3)

        resources = self._check_resources(fhir_files)
        self._add_evidence(
            "fhir_resources_implemented",
            value=resources,
            source="FHIR module scan",
            passed=resources >= 3,
        )
        missing_resources = [r for r in self.REQUIRED_RESOURCES if r not in resources]
        if missing_resources:
            self._add_remediation(
                f"Implement missing FHIR resources: {', '.join(missing_resources)}",
                severity="medium",
                effort=str(len(missing_resources) * 4) + "h",
            )

        search_params = self._check_search_params(fhir_files)
        self._add_evidence(
            "fhir_search_params",
            value=search_params,
            source="FHIR module scan",
            passed=search_params >= 3,
        )
        missing_params = [p for p in self.REQUIRED_SEARCH_PARAMS if p not in search_params]
        if missing_params:
            self._add_remediation(
                f"Add missing FHIR search parameters: {', '.join(missing_params)}",
                severity="medium",
                effort=str(len(missing_params) * 2) + "h",
            )

        operations = self._check_operations(fhir_files)
        self._add_evidence(
            "fhir_operations",
            value=operations,
            source="FHIR module scan",
            passed=operations >= 2,
        )
        if operations < 2:
            self._add_remediation(
                "Implement standard FHIR operations ($everything, $validate, $docref)",
                severity="low",
                effort="8h",
            )

        validation = self._check_fhir_validation(fhir_files)
        self._add_evidence(
            "fhir_validation",
            value=validation,
            source="FHIR module scan",
            passed=validation,
        )
        if not validation:
            self._add_remediation(
                "Add FHIR resource validation against structure definitions",
                severity="medium",
                effort="6h",
            )

        profiles = self._check_profiles(fhir_files)
        self._add_evidence(
            "fhir_profiles",
            value=profiles,
            source="FHIR module scan",
            passed=profiles,
        )
        if not profiles:
            self._add_remediation(
                "Add FHIR profiles (StructureDefinition) for Iraqi healthcare context",
                severity="low",
                effort="8h",
            )

        score = 1.0
        if not fhir_files:
            score -= 0.7
        score -= max(0, 3 - resources) * 0.1
        score -= max(0, 3 - search_params) * 0.05
        score -= max(0, 2 - operations) * 0.05
        if not validation:
            score -= 0.1
        if not profiles:
            score -= 0.05

        return self._result(score)

    def _find_fhir_files(self, target: Path) -> list[Path]:
        files = []
        keywords = ["fhir", "ehr_fhir"]
        for py_file in target.rglob("*.py"):
            if any(k in str(py_file).lower() for k in keywords):
                if "test" not in py_file.parts and "__pycache__" not in py_file.parts:
                    files.append(py_file)
        return files

    def _check_resources(self, files: list[Path]) -> int:
        resources = set()
        for f in files:
            try:
                content = f.read_text()
                for resource in self.REQUIRED_RESOURCES:
                    if resource in content:
                        resources.add(resource)
            except Exception:
                continue
        return len(resources)

    def _check_search_params(self, files: list[Path]) -> int:
        params = set()
        for f in files:
            try:
                content = f.read_text()
                for param in self.REQUIRED_SEARCH_PARAMS:
                    if param in content:
                        params.add(param)
            except Exception:
                continue
        return len(params)

    def _check_operations(self, files: list[Path]) -> int:
        count = 0
        ops = ["$everything", "$validate", "$docref", "$expand", "$lookup"]
        for f in files:
            try:
                content = f.read_text()
                for op in ops:
                    if op in content:
                        count += 1
            except Exception:
                continue
        return count

    def _check_fhir_validation(self, files: list[Path]) -> bool:
        for f in files:
            try:
                content = f.read_text()
                if "validate" in content.lower() and (
                    "fhir" in content.lower() or "resource" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_profiles(self, files: list[Path]) -> bool:
        for f in files:
            try:
                content = f.read_text()
                if "StructureDefinition" in content or "profile" in content.lower():
                    return True
            except Exception:
                continue
        return False
