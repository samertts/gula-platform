from __future__ import annotations

from pathlib import Path

from app.engineering.security.bandit import BanditScanner, SecretsScanner

from . import DimensionEvaluator, DimensionResult


class SecurityEvaluator(DimensionEvaluator):
    OWASP_ASVS_LEVELS = ["L1", "L2", "L3"]

    def evaluate(self, module_path: str | None = None) -> DimensionResult:
        target = Path(module_path) if module_path else self.project_root

        bandit = BanditScanner(target)
        bandit_issues = bandit.scan(str(target))
        self._add_evidence(
            "bandit_vulnerabilities",
            value=len(bandit_issues),
            source="BanditScanner",
            passed=len(bandit_issues) == 0,
        )
        if bandit_issues:
            self._add_remediation(
                f"Fix {len(bandit_issues)} security vulnerabilities from Bandit",
                severity="high",
                effort=str(len(bandit_issues)) + "h",
            )

        secrets = SecretsScanner(target)
        secret_issues = secrets.scan(str(target))
        self._add_evidence(
            "secrets_exposed",
            value=len(secret_issues),
            source="SecretsScanner",
            passed=len(secret_issues) == 0,
        )
        if secret_issues:
            self._add_remediation(
                f"Remove {len(secret_issues)} exposed secrets from source code",
                severity="critical",
                effort=str(len(secret_issues)) + "h",
            )

        rbac_found = self._check_rbac(target)
        self._add_evidence(
            "rbac_decorators",
            value=rbac_found,
            source="AST scan",
            passed=rbac_found > 0,
        )
        if not rbac_found:
            self._add_remediation(
                "Implement RBAC decorators or dependency injection for access control",
                severity="high",
                effort="8h",
            )

        audit_found = self._check_audit_logging(target)
        self._add_evidence(
            "audit_logging",
            value=audit_found,
            source="AST scan",
            passed=audit_found > 0,
        )
        if not audit_found:
            self._add_remediation(
                "Add audit logging for all data mutations",
                severity="high",
                effort="6h",
            )

        input_validation = self._check_input_validation(target)
        self._add_evidence(
            "input_validation",
            value=input_validation,
            source="AST scan",
            passed=input_validation > 0,
        )
        if not input_validation:
            self._add_remediation(
                "Add Pydantic-based input validation on all endpoints",
                severity="medium",
                effort="4h",
            )

        score = 1.0
        score -= len(bandit_issues) * 0.1
        score -= len(secret_issues) * 0.2
        if not rbac_found:
            score -= 0.15
        if not audit_found:
            score -= 0.1
        if not input_validation:
            score -= 0.05

        return self._result(score)

    def _check_rbac(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if (
                    "get_current_user" in content
                    or "has_permission" in content
                    or "@requires" in content
                ):
                    count += 1
            except Exception:
                continue
        return count

    def _check_audit_logging(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "AuditLog" in content or "log_action" in content or "audit" in content.lower():
                    count += 1
            except Exception:
                continue
        return count

    def _check_input_validation(self, target: Path) -> int:
        count = 0
        for py_file in target.rglob("*.py"):
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            try:
                content = py_file.read_text()
                if "BaseModel" in content or "Field(" in content or "pydantic" in content:
                    count += 1
            except Exception:
                continue
        return count
