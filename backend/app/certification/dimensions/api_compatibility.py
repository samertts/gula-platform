from __future__ import annotations

from pathlib import Path

from . import DimensionEvaluator, DimensionResult


class APICompatibilityEvaluator(DimensionEvaluator):
    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        versioning = self._check_api_versioning(target)
        self._add_evidence(
            "api_versioning",
            value=versioning,
            source="Route scan",
            passed=versioning,
        )
        if not versioning:
            self._add_remediation(
                "Add API versioning (prefix routes with /v1/, /v2/, etc.)",
                severity="high",
                effort="4h",
            )

        deprecation = self._check_deprecation_headers(target)
        self._add_evidence(
            "deprecation_headers",
            value=deprecation,
            source="AST scan",
            passed=deprecation,
        )
        if not deprecation:
            self._add_remediation(
                "Add Sunset/Deprecation HTTP headers for deprecated endpoints",
                severity="medium",
                effort="2h",
            )

        backward_compat = self._check_backward_compatibility(target)
        self._add_evidence(
            "backward_compatibility",
            value=backward_compat,
            source="AST scan",
            passed=backward_compat,
        )
        if not backward_compat:
            self._add_remediation(
                "Ensure API changes are backward-compatible (no removing fields from responses)",
                severity="high",
                effort="6h",
            )

        schema_evolution = self._check_schema_evolution(target)
        self._add_evidence(
            "schema_evolution_strategy",
            value=schema_evolution,
            source="AST scan",
            passed=schema_evolution,
        )
        if not schema_evolution:
            self._add_remediation(
                "Document schema evolution strategy (add-only fields, default values for new fields)",
                severity="medium",
                effort="2h",
            )

        pydantic_versioning = self._check_pydantic_versioning(target)
        self._add_evidence(
            "pydantic_model_versioning",
            value=pydantic_versioning,
            source="AST scan",
            passed=pydantic_versioning,
        )
        if not pydantic_versioning:
            self._add_remediation(
                "Version Pydantic response models to track API contract changes",
                severity="low",
                effort="3h",
            )

        error_consistency = self._check_error_response_consistency(target)
        self._add_evidence(
            "error_response_consistency",
            value=error_consistency,
            source="AST scan",
            passed=error_consistency,
        )
        if not error_consistency:
            self._add_remediation(
                "Standardize error response format across all endpoints",
                severity="medium",
                effort="3h",
            )

        score = 1.0
        checks = [
            (versioning, 0.2),
            (deprecation, 0.1),
            (backward_compat, 0.15),
            (schema_evolution, 0.1),
            (pydantic_versioning, 0.05),
            (error_consistency, 0.1),
        ]
        for passed, penalty in checks:
            if not passed:
                score -= penalty

        return self._result(score)

    def _check_api_versioning(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "prefix" in content and ("v1" in content or "v2" in content) and "APIRouter" in content:
                    return True
            except Exception:
                continue
        return False

    def _check_deprecation_headers(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if (
                    "Sunset" in content
                    or "Deprecation" in content
                    or "deprecated" in content.lower()
                ) and ("header" in content.lower() or "Header" in content):
                    return True
            except Exception:
                continue
        return False

    def _check_backward_compatibility(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if (
                    "backward" in content.lower()
                    or "backward_compat" in content.lower()
                    or "compat" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_schema_evolution(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "schema" in content.lower() and (
                    "evol" in content.lower()
                    or "version" in content.lower()
                    or "migrat" in content.lower()
                ):
                    return True
            except Exception:
                continue
        return False

    def _check_pydantic_versioning(self, target: Path) -> bool:
        count = 0
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if "BaseModel" in content and "Config" in content:
                    count += 1
            except Exception:
                continue
        return count >= 3

    def _check_error_response_consistency(self, target: Path) -> bool:
        for py_file in target.rglob("*.py"):
            try:
                content = py_file.read_text()
                if ("HTTPException" in content or "JSONResponse" in content) and ("detail" in content or "status_code" in content):
                    return True
            except Exception:
                continue
        return False
